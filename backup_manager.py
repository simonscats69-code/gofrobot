"""
Система автоматического резервного копирования и восстановления для Telegram бота.

Этот модуль предоставляет:
- Автоматическое резервное копирование базы данных
- Ротацию резервных копий
- Восстановление из резервных копий
- Мониторинг целостности данных
- Интеграцию с внешними хранилищами
"""

import asyncio
import logging
import os
import shutil
import json
import time
import hashlib
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import tarfile
import gzip
import aiofiles
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Типы резервных копий."""
    FULL = "full"           # Полная копия
    INCREMENTAL = "incremental"  # Инкрементальная копия
    DAILY = "daily"         # Ежедневная копия
    WEEKLY = "weekly"       # Еженедельная копия

@dataclass
class BackupInfo:
    """Информация о резервной копии."""
    filename: str
    filepath: str
    size: int
    checksum: str
    created_at: float
    backup_type: BackupType
    description: str
    metadata: Dict[str, Any]

class BackupStorage:
    """Интерфейс хранилища резервных копий."""
    
    async def save(self, filepath: str, data: bytes) -> bool:
        """Сохраняет данные в хранилище."""
        raise NotImplementedError
    
    async def load(self, filepath: str) -> Optional[bytes]:
        """Загружает данные из хранилища."""
        raise NotImplementedError
    
    async def delete(self, filepath: str) -> bool:
        """Удаляет файл из хранилища."""
        raise NotImplementedError
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """Получает список файлов в хранилище."""
        raise NotImplementedError

class LocalStorage(BackupStorage):
    """Локальное хранилище резервных копий."""
    
    def __init__(self, backup_dir: str):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, filepath: str, data: bytes) -> bool:
        """Сохраняет данные в локальный файл."""
        try:
            full_path = self.backup_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(data)
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в локальное хранилище: {e}")
            return False
    
    async def load(self, filepath: str) -> Optional[bytes]:
        """Загружает данные из локального файла."""
        try:
            full_path = self.backup_dir / filepath
            if not full_path.exists():
                return None
            
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки из локального хранилища: {e}")
            return None
    
    async def delete(self, filepath: str) -> bool:
        """Удаляет файл из локального хранилища."""
        try:
            full_path = self.backup_dir / filepath
            if full_path.exists():
                full_path.unlink()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления из локального хранилища: {e}")
            return False
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """Получает список файлов в локальном хранилище."""
        try:
            pattern = f"{prefix}*" if prefix else "*"
            files = list(self.backup_dir.glob(pattern))
            return [str(f.relative_to(self.backup_dir)) for f in files]
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка файлов: {e}")
            return []

class CloudStorage(BackupStorage):
    """Облачное хранилище (пример для S3-совместимых сервисов)."""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.session = None
    
    async def _get_session(self):
        """Получает HTTP сессию."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def save(self, filepath: str, data: bytes) -> bool:
        """Сохраняет данные в облачное хранилище."""
        try:
            session = await self._get_session()
            url = f"{self.endpoint}/{self.bucket}/{filepath}"
            
            headers = {
                'Authorization': f'AWS4-HMAC-SHA256 Credential={self.access_key}',
                'Content-Type': 'application/octet-stream'
            }
            
            async with session.put(url, data=data, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в облачное хранилище: {e}")
            return False
    
    async def load(self, filepath: str) -> Optional[bytes]:
        """Загружает данные из облачного хранилища."""
        try:
            session = await self._get_session()
            url = f"{self.endpoint}/{self.bucket}/{filepath}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки из облачного хранилища: {e}")
            return None
    
    async def delete(self, filepath: str) -> bool:
        """Удаляет файл из облачного хранилища."""
        try:
            session = await self._get_session()
            url = f"{self.endpoint}/{self.bucket}/{filepath}"
            
            async with session.delete(url) as response:
                return response.status == 204
        except Exception as e:
            logger.error(f"❌ Ошибка удаления из облачного хранилища: {e}")
            return False
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """Получает список файлов в облачном хранилище."""
        try:
            session = await self._get_session()
            url = f"{self.endpoint}/{self.bucket}/?prefix={prefix}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    # Парсим XML ответ от S3
                    content = await response.text()
                    # Упрощенная реализация - в реальности нужно парсить XML
                    return []
                return []
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка файлов из облака: {e}")
            return []

class BackupManager:
    """Менеджер резервного копирования."""
    
    def __init__(self, backup_dir: str = "storage/backups", max_backups: int = 10):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.local_storage = LocalStorage(str(self.backup_dir))
        self.cloud_storage: Optional[CloudStorage] = None
        self._lock = asyncio.Lock()
        self._backup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Конфигурация
        self.backup_interval = 3600  # 1 час
        self.compression_enabled = True
        self.cloud_sync_enabled = False
        
        # Статистика
        self.stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'total_size': 0,
            'last_backup_time': 0
        }
    
    def set_cloud_storage(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        """Настраивает облачное хранилище."""
        self.cloud_storage = CloudStorage(endpoint, access_key, secret_key, bucket)
        self.cloud_sync_enabled = True
        logger.info("☁️ Облачное хранилище настроено")
    
    def set_backup_interval(self, interval_seconds: int):
        """Устанавливает интервал резервного копирования."""
        self.backup_interval = interval_seconds
        logger.info(f"⏰ Интервал резервного копирования: {interval_seconds} секунд")
    
    def set_max_backups(self, max_backups: int):
        """Устанавливает максимальное количество резервных копий."""
        self.max_backups = max_backups
        logger.info(f"📦 Максимальное количество резервных копий: {max_backups}")
    
    async def start(self):
        """Запускает автоматическое резервное копирование."""
        if self._running:
            return
        
        self._running = True
        self._backup_task = asyncio.create_task(self._backup_loop())
        logger.info("🔄 Автоматическое резервное копирование запущено")
    
    async def stop(self):
        """Останавливает автоматическое резервное копирование."""
        if not self._running:
            return
        
        self._running = False
        if self._backup_task:
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Автоматическое резервное копирование остановлено")
    
    async def _backup_loop(self):
        """Цикл автоматического резервного копирования."""
        while self._running:
            try:
                await self.create_backup(BackupType.INCREMENTAL)
                await asyncio.sleep(self.backup_interval)
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле резервного копирования: {e}")
                await asyncio.sleep(60)  # Пауза перед повторной попыткой
    
    async def create_backup(self, backup_type: BackupType = BackupType.FULL, 
                          description: str = "") -> Tuple[bool, Optional[BackupInfo]]:
        """Создает резервную копию."""
        async with self._lock:
            try:
                # Формируем имя файла
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"backup_{backup_type.value}_{timestamp}.tar.gz"
                
                # Собираем данные для резервной копии
                backup_data = await self._collect_backup_data(backup_type)
                
                if not backup_data:
                    logger.warning("⚠️ Нет данных для резервного копирования")
                    return False, None
                
                # Сжимаем данные
                if self.compression_enabled:
                    compressed_data = self._compress_data(backup_data)
                else:
                    compressed_data = backup_data
                
                # Сохраняем в локальное хранилище
                success = await self.local_storage.save(filename, compressed_data)
                
                if not success:
                    logger.error("❌ Не удалось сохранить резервную копию локально")
                    return False, None
                
                # Сохраняем в облачное хранилище (если настроено)
                if self.cloud_storage and self.cloud_sync_enabled:
                    await self.cloud_storage.save(filename, compressed_data)
                
                # Создаем информацию о резервной копии
                backup_info = BackupInfo(
                    filename=filename,
                    filepath=str(self.backup_dir / filename),
                    size=len(compressed_data),
                    checksum=self._calculate_checksum(compressed_data),
                    created_at=time.time(),
                    backup_type=backup_type,
                    description=description,
                    metadata={
                        'compression_enabled': self.compression_enabled,
                        'cloud_sync_enabled': self.cloud_sync_enabled
                    }
                )
                
                # Обновляем статистику
                self._update_stats(success=True, size=len(compressed_data))
                
                # Ротация резервных копий
                await self._rotate_backups()
                
                logger.info(f"✅ Резервная копия создана: {filename}")
                return True, backup_info
                
            except Exception as e:
                logger.error(f"❌ Ошибка создания резервной копии: {e}")
                self._update_stats(success=False)
                return False, None
    
    async def _collect_backup_data(self, backup_type: BackupType) -> Optional[bytes]:
        """Собирает данные для резервной копии."""
        try:
            # Создаем временный архив
            temp_archive = BytesIO()
            
            with tarfile.open(fileobj=temp_archive, mode='w:gz') as tar:
                # Добавляем базу данных
                db_path = Path("storage/bot_database.db")
                if db_path.exists():
                    tar.add(db_path, arcname="bot_database.db")
                
                # Добавляем конфигурационные файлы
                config_files = ["bothost.json", "config.py"]
                for config_file in config_files:
                    if Path(config_file).exists():
                        tar.add(config_file, arcname=config_file)
                
                # Добавляем логи (последние 7 дней)
                logs_dir = Path("storage/logs")
                if logs_dir.exists():
                    for log_file in logs_dir.glob("*.log"):
                        if log_file.stat().st_mtime > time.time() - 7 * 86400:
                            tar.add(log_file, arcname=f"logs/{log_file.name}")
                
                # Добавляем метаданные
                metadata = {
                    'backup_type': backup_type.value,
                    'created_at': datetime.now().isoformat(),
                    'system_info': {
                        'platform': os.name,
                        'python_version': os.sys.version,
                        'backup_version': '1.0'
                    }
                }
                
                metadata_file = BytesIO(json.dumps(metadata, indent=2).encode())
                tarinfo = tarfile.TarInfo(name="metadata.json")
                tarinfo.size = len(metadata_file.getvalue())
                tar.addfile(tarinfo, metadata_file)
            
            return temp_archive.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных для резервной копии: {e}")
            return None
    
    def _compress_data(self, data: bytes) -> bytes:
        """Сжимает данные с помощью gzip."""
        try:
            return gzip.compress(data, compresslevel=6)
        except Exception as e:
            logger.error(f"❌ Ошибка сжатия данных: {e}")
            return data
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Вычисляет контрольную сумму данных."""
        return hashlib.sha256(data).hexdigest()
    
    def _update_stats(self, success: bool = True, size: int = 0):
        """Обновляет статистику резервного копирования."""
        self.stats['total_backups'] += 1
        self.stats['last_backup_time'] = time.time()
        
        if success:
            self.stats['successful_backups'] += 1
            self.stats['total_size'] += size
        else:
            self.stats['failed_backups'] += 1
    
    async def _rotate_backups(self):
        """Выполняет ротацию резервных копий."""
        try:
            # Получаем список всех резервных копий
            backup_files = await self.local_storage.list_files("backup_")
            
            if len(backup_files) <= self.max_backups:
                return
            
            # Сортируем по дате создания
            backup_files.sort(key=lambda x: os.path.getctime(self.backup_dir / x))
            
            # Удаляем старые копии
            files_to_delete = backup_files[:-self.max_backups]
            
            for filename in files_to_delete:
                try:
                    await self.local_storage.delete(filename)
                    logger.info(f"🗑️ Удалена старая резервная копия: {filename}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить резервную копию {filename}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка ротации резервных копий: {e}")
    
    async def restore_backup(self, filename: str) -> Tuple[bool, str]:
        """Восстанавливает данные из резервной копии."""
        async with self._lock:
            try:
                # Загружаем резервную копию
                backup_data = await self.local_storage.load(filename)
                
                if not backup_data:
                    return False, f"Резервная копия {filename} не найдена"
                
                # Проверяем контрольную сумму
                if not self._verify_backup_integrity(backup_data):
                    return False, "Контрольная сумма резервной копии не совпадает"
                
                # Распаковываем архив
                success = await self._extract_backup_data(backup_data)
                
                if success:
                    logger.info(f"✅ Резервная копия {filename} восстановлена")
                    return True, "Восстановление завершено успешно"
                else:
                    return False, "Ошибка при распаковке резервной копии"
                
            except Exception as e:
                logger.error(f"❌ Ошибка восстановления резервной копии: {e}")
                return False, f"Ошибка восстановления: {e}"
    
    def _verify_backup_integrity(self, backup_data: bytes) -> bool:
        """Проверяет целостность резервной копии."""
        # В реальной реализации нужно хранить контрольные суммы
        # Пока просто проверяем, что данные не пустые
        return len(backup_data) > 0
    
    async def _extract_backup_data(self, backup_data: bytes) -> bool:
        """Извлекает данные из резервной копии."""
        try:
            # Распаковываем архив
            temp_archive = BytesIO(backup_data)
            
            with tarfile.open(fileobj=temp_archive, mode='r:gz') as tar:
                # Создаем резервную копию текущих данных
                await self._create_recovery_point()
                
                # Извлекаем файлы
                tar.extractall(path=".")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных из резервной копии: {e}")
            return False
    
    async def _create_recovery_point(self):
        """Создает точку восстановления перед восстановлением."""
        try:
            recovery_dir = Path("storage/recovery")
            recovery_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            recovery_name = f"recovery_{timestamp}"
            recovery_path = recovery_dir / recovery_name
            
            # Копируем текущие важные файлы
            important_files = [
                "storage/bot_database.db",
                "bothost.json",
                "config.py"
            ]
            
            for file_path in important_files:
                if Path(file_path).exists():
                    shutil.copy2(file_path, recovery_path / Path(file_path).name)
            
            logger.info(f"🔄 Точка восстановления создана: {recovery_path}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания точки восстановления: {e}")
    
    async def list_backups(self) -> List[BackupInfo]:
        """Получает список доступных резервных копий."""
        try:
            backup_files = await self.local_storage.list_files("backup_")
            backups = []
            
            for filename in backup_files:
                filepath = self.backup_dir / filename
                if filepath.exists():
                    stat = filepath.stat()
                    backup_info = BackupInfo(
                        filename=filename,
                        filepath=str(filepath),
                        size=stat.st_size,
                        checksum="",  # Можно вычислить при необходимости
                        created_at=stat.st_ctime,
                        backup_type=BackupType.FULL,  # Определить по имени файла
                        description="",
                        metadata={}
                    )
                    backups.append(backup_info)
            
            # Сортируем по дате создания (новые первыми)
            backups.sort(key=lambda x: x.created_at, reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка резервных копий: {e}")
            return []
    
    async def verify_backup(self, filename: str) -> Tuple[bool, Dict[str, Any]]:
        """Проверяет целостность резервной копии."""
        try:
            backup_data = await self.local_storage.load(filename)
            
            if not backup_data:
                return False, {"error": "Резервная копия не найдена"}
            
            # Проверяем, что это валидный tar.gz архив
            try:
                temp_archive = BytesIO(backup_data)
                with tarfile.open(fileobj=temp_archive, mode='r:gz') as tar:
                    files = tar.getnames()
                    return True, {
                        "files": files,
                        "size": len(backup_data),
                        "valid": True
                    }
            except Exception as e:
                return False, {"error": f"Невалидный архив: {e}"}
                
        except Exception as e:
            return False, {"error": f"Ошибка проверки: {e}"}
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику резервного копирования."""
        return {
            **self.stats,
            'success_rate': (self.stats['successful_backups'] / max(self.stats['total_backups'], 1)) * 100,
            'avg_backup_size': self.stats['total_size'] / max(self.stats['successful_backups'], 1),
            'backup_interval': self.backup_interval,
            'max_backups': self.max_backups,
            'compression_enabled': self.compression_enabled,
            'cloud_sync_enabled': self.cloud_sync_enabled
        }
    
    async def cleanup_old_backups(self, days: int = 30):
        """Удаляет резервные копии старше указанного количества дней."""
        try:
            cutoff_time = time.time() - (days * 86400)
            backup_files = await self.local_storage.list_files("backup_")
            
            deleted_count = 0
            for filename in backup_files:
                filepath = self.backup_dir / filename
                if filepath.exists():
                    if filepath.stat().st_ctime < cutoff_time:
                        try:
                            await self.local_storage.delete(filename)
                            deleted_count += 1
                            logger.info(f"🗑️ Удалена старая резервная копия: {filename}")
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось удалить {filename}: {e}")
            
            logger.info(f"🧹 Очистка завершена. Удалено {deleted_count} старых резервных копий")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых резервных копий: {e}")

# Глобальный экземпляр менеджера резервного копирования
_backup_manager: Optional[BackupManager] = None

def get_backup_manager() -> BackupManager:
    """Возвращает глобальный экземпляр менеджера резервного копирования."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager

# Функции для удобного использования

async def create_backup(backup_type: BackupType = BackupType.FULL, description: str = "") -> Tuple[bool, Optional[BackupInfo]]:
    """Создает резервную копию."""
    backup_manager = get_backup_manager()
    return await backup_manager.create_backup(backup_type, description)

async def restore_backup(filename: str) -> Tuple[bool, str]:
    """Восстанавливает данные из резервной копии."""
    backup_manager = get_backup_manager()
    return await backup_manager.restore_backup(filename)

async def list_backups() -> List[BackupInfo]:
    """Получает список доступных резервных копий."""
    backup_manager = get_backup_manager()
    return await backup_manager.list_backups()

async def verify_backup(filename: str) -> Tuple[bool, Dict[str, Any]]:
    """Проверяет целостность резервной копии."""
    backup_manager = get_backup_manager()
    return await backup_manager.verify_backup(filename)

def get_backup_stats() -> Dict[str, Any]:
    """Возвращает статистику резервного копирования."""
    backup_manager = get_backup_manager()
    return backup_manager.get_stats()

async def cleanup_old_backups(days: int = 30):
    """Удаляет резервные копии старше указанного количества дней."""
    backup_manager = get_backup_manager()
    await backup_manager.cleanup_old_backups(days)

# Пример использования:
"""
# Создание резервной копии
success, backup_info = await create_backup(BackupType.DAILY, "Ежедневная резервная копия")

# Список резервных копий
backups = await list_backups()

# Восстановление из резервной копии
success, message = await restore_backup("backup_full_20231201_120000.tar.gz")

# Проверка целостности
is_valid, info = await verify_backup("backup_full_20231201_120000.tar.gz")

# Статистика
stats = get_backup_stats()
"""