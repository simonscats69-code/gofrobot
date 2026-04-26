import aiosqlite
import asyncio
import os
import json
import logging
import time
import shutil
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import sqlite3

# Импортируем конфигурацию
from config import (
    BALANCE, GOFRY_MM, ATM_MAX, ATM_BASE_TIME,
    DB_CONFIG, ADMIN_CONFIG
)

logger = logging.getLogger(__name__)

# Глобальные переменные для базы данных
DB_PATH = "storage/bot_database.db"
BACKUP_DIR = "storage/backups"
DATABASE_VERSION = 5

# Импортируем функции форматирования из utils.display
from utils.display import format_length, Display

# Алиас для форматирования времени
ft = Display.format_time

# Единое соединение с базой данных (для Telegram бота этого более чем достаточно)
_db_connection = None
_db_lock = asyncio.Lock()

async def get_connection() -> aiosqlite.Connection:
    """Получить соединение с базой данных."""
    global _db_connection
    
    async with _db_lock:
        if _db_connection is None:
            _db_connection = await aiosqlite.connect(DB_PATH, timeout=60)
            _db_connection.row_factory = aiosqlite.Row
            
            # Оптимизация SQLite
            await _db_connection.execute("PRAGMA journal_mode=WAL")
            await _db_connection.execute("PRAGMA synchronous=NORMAL")
            await _db_connection.execute("PRAGMA temp_store=MEMORY")
            await _db_connection.execute("PRAGMA cache_size=-20000")
            await _db_connection.execute("PRAGMA foreign_keys=ON")
            
            logger.info("✅ Соединение с базой данных установлено")
        
        return _db_connection

async def release_connection(conn: aiosqlite.Connection):
    """Ничего не делаем - используем одно глобальное соединение."""
    pass

async def close_pool():
    """Закрыть соединение с базой данных."""
    global _db_connection
    
    async with _db_lock:
        if _db_connection is not None:
            await _db_connection.close()
            _db_connection = None
            logger.info("🔌 Соединение с базой данных закрыто")



async def ensure_storage_dirs():
    """Убедиться, что все необходимые директории существуют."""
    os.makedirs("storage", exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs("storage/logs", exist_ok=True)

async def init_db():
    """Инициализирует базу данных с необходимыми таблицами."""
    await ensure_storage_dirs()
    conn = await get_connection()
    try:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT DEFAULT 'Неизвестно',
            gofra_mm REAL DEFAULT 10.0,
            cable_mm REAL DEFAULT 10.0,
            atm_count INTEGER DEFAULT 12,
            zmiy_grams REAL DEFAULT 0.0,
            total_zmiy_grams REAL DEFAULT 0.0,
            cable_power INTEGER DEFAULT 2,
            gofra INTEGER DEFAULT 1,
            last_atm_regen INTEGER DEFAULT 0,
            last_davka INTEGER DEFAULT 0,
            last_rademka INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS rademka_fights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner_id INTEGER,
            loser_id INTEGER,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (winner_id) REFERENCES users(user_id),
            FOREIGN KEY (loser_id) REFERENCES users(user_id)
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_stats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            chat_type TEXT,
            total_players INTEGER DEFAULT 0,
            active_players INTEGER DEFAULT 0,
            total_zmiy_all REAL DEFAULT 0.0,
            total_davki_all INTEGER DEFAULT 0,
            last_activity INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_chat_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            total_zmiy_grams REAL DEFAULT 0.0,
            last_activity INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (chat_id) REFERENCES chat_stats(chat_id),
            UNIQUE(user_id, chat_id)
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS database_version (
            version INTEGER PRIMARY KEY,
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        # Проверяем и обновляем версию базы данных
        await check_and_update_db_version(conn)

        await conn.commit()
    finally:
        await release_connection(conn)

async def check_and_update_db_version(conn: aiosqlite.Connection):
    """Проверяет версию базы данных и применяет необходимые миграции."""
    # Проверяем текущую версию
    cursor = await conn.execute("SELECT version FROM database_version ORDER BY version DESC LIMIT 1")
    row = await cursor.fetchone()

    if row is None:
        # Если таблица пустая, устанавливаем текущую версию
        current_version = 1
    else:
        current_version = row[0]

    logger.info(f"Текущая версия БД: {current_version}, требуемая: {DATABASE_VERSION}")

    # Применяем миграции по порядку
    if current_version < 1:
        await apply_migration_v1(conn)
        current_version = 1

    if current_version < 2:
        await apply_migration_v2(conn)
        current_version = 2

    if current_version < 3:
        await apply_migration_v3(conn)
        current_version = 3

    if current_version < 4:
        await apply_migration_v4(conn)
        current_version = 4

    # Обновляем версию в базе
    await conn.execute("INSERT OR REPLACE INTO database_version (version) VALUES (?)", (DATABASE_VERSION,))

async def apply_migration_v1(conn: aiosqlite.Connection):
    """Миграция для версии 1 - добавление базовых таблиц."""
    logger.info("Применение миграции v1...")
    # Базовые таблицы уже созданы в init_db, поэтому здесь могут быть дополнительные настройки

async def apply_migration_v2(conn: aiosqlite.Connection):
    """Миграция для версии 2 - добавление новых полей и оптимизаций."""
    logger.info("Применение миграции v2...")

    # Добавляем новые поля, если их нет
    try:
        # Проверяем, есть ли поле cable_power
        cursor = await conn.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'cable_power' not in column_names:
            await conn.execute("ALTER TABLE users ADD COLUMN cable_power INTEGER DEFAULT 2")

        if 'gofra' not in column_names:
            await conn.execute("ALTER TABLE users ADD COLUMN gofra INTEGER DEFAULT 1")

        if 'last_rademka' not in column_names:
            await conn.execute("ALTER TABLE users ADD COLUMN last_rademka INTEGER DEFAULT 0")

    except Exception as e:
        logger.error(f"Ошибка при миграции v2: {e}")
        raise

async def apply_migration_v3(conn: aiosqlite.Connection):
    """Миграция для версии 3 - исправление начальных атмосфер."""
    logger.info("Применение миграции v3...")

    try:
        # Обновляем всех пользователей с 0 атмосферами до 12
        cursor = await conn.execute("UPDATE users SET atm_count = 12 WHERE atm_count = 0")
        update_count = cursor.rowcount
        logger.info(f"Обновлено {update_count} пользователей с 0 атмосферами до 12")

        # Обновляем DEFAULT значение для будущих пользователей
        # Note: В SQLite нельзя изменить DEFAULT значение существующего столбца через ALTER TABLE
        # Поэтому мы просто документируем, что новые пользователи должны иметь 12 атмосфер

    except Exception as e:
        logger.error(f"Ошибка при миграции v3: {e}")
        raise

async def apply_migration_v4(conn: aiosqlite.Connection):
    """Миграция для версии 4 - добавление индексов для производительности."""
    logger.info("Применение миграции v4 (индексы)...")

    try:
        # Индексы для таблицы users
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_atm_count ON users(atm_count)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_gofra_mm ON users(gofra_mm)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_cable_mm ON users(cable_mm)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_davka ON users(last_davka)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_rademka ON users(last_rademka)")
        
        # Индексы для таблицы user_chat_stats
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_chat_stats_chat_user ON user_chat_stats(chat_id, user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_chat_stats_total_zmiy ON user_chat_stats(total_zmiy_grams)")
        
        # Индексы для таблицы rademka_fights
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_rademka_fights_winner ON rademka_fights(winner_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_rademka_fights_loser ON rademka_fights(loser_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_rademka_fights_created ON rademka_fights(created_at)")
        
        # Индексы для таблицы chat_stats
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_stats_total_zmiy ON chat_stats(total_zmiy_all)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_stats_total_davki ON chat_stats(total_davki_all)")
        
        logger.info("✅ Индексы для производительности добавлены")

    except Exception as e:
        logger.error(f"Ошибка при миграции v4 (индексы): {e}")
        raise

async def repair_database():
    """Функция для ремонта и восстановления базы данных."""
    logger.info("🔧 Запуск процедуры ремонта базы данных...")

    # 1. Создаем резервную копию перед ремонтом
    backup_filename = f"repair_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
            logger.info(f"✅ Создана резервная копия: {backup_path}")
        else:
            logger.warning("⚠️ База данных не существует, создаем новую")

        # 2. Проверяем целостность базы данных
        await check_database_integrity()

        # 3. Восстанавливаем структуру базы данных
        await rebuild_database_structure()

        # 4. Оптимизируем базу данных
        await optimize_database()

        logger.info("✅ Процедура ремонта базы данных завершена успешно!")
        return True, "Ремонт базы данных завершен успешно"

    except Exception as e:
        logger.error(f"❌ Ошибка при ремонте базы данных: {e}")
        return False, f"Ошибка при ремонте базы данных: {e}"

async def check_database_integrity():
    """Проверяет целостность базы данных и исправляет ошибки."""
    logger.info("🔍 Проверка целостности базы данных...")

    try:
        # Проверяем, существует ли файл базы данных
        if not os.path.exists(DB_PATH):
            logger.info("📁 База данных не существует, будет создана при инициализации")
            return

        # Подключаемся к базе данных с помощью стандартного sqlite3 для проверки
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Проверяем целостность базы данных
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()

        if result and result[0] == "ok":
            logger.info("✅ База данных в хорошем состоянии")
        else:
            logger.warning(f"⚠️ Проблемы с целостностью базы данных: {result}")
            # Попробуем восстановить базу
            cursor.execute("PRAGMA quick_check")
            quick_result = cursor.fetchall()
            logger.info(f"Быстрая проверка: {quick_result}")

        # Проверяем наличие необходимых таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['users', 'rademka_fights', 'chat_stats', 'user_chat_stats', 'database_version']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            logger.warning(f"⚠️ Отсутствуют таблицы: {missing_tables}")
            # Эти таблицы будут созданы при инициализации

        conn.close()

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке целостности базы данных: {e}")
        raise


async def backup_all_data():
    """Создает резервную копию всех данных из базы данных."""
    logger.info("💾 Создание резервной копии данных...")

    try:
        if not os.path.exists(DB_PATH):
            return {}

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        backup_data = {
            'users': [],
            'rademka_fights': [],
            'chat_stats': [],
            'user_chat_stats': [],
            'database_version': []
        }

        # Копируем данные из каждой таблицы
        for table in backup_data.keys():
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                if rows:
                    # Получаем имена колонок
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    backup_data[table] = [dict(zip(columns, row)) for row in rows]
            except sqlite3.OperationalError:
                # Таблица не существует
                continue

        conn.close()
        logger.info("✅ Резервная копия данных создана")
        return backup_data

    except Exception as e:
        logger.error(f"❌ Ошибка при создании резервной копии данных: {e}")
        return {}

async def restore_all_data(backup_data: dict):
    """Восстанавливает данные из резервной копии."""
    logger.info("🔄 Восстановление данных из резервной копии...")

    try:
        conn = await get_connection()
        try:
            # Восстанавливаем пользователей
            if backup_data.get('users'):
                for user in backup_data['users']:
                    try:
                        await conn.execute("""
                        INSERT OR REPLACE INTO users (
                            user_id, nickname, gofra_mm, cable_mm, atm_count,
                            zmiy_grams, total_zmiy_grams, cable_power, gofra,
                            last_atm_regen, last_davka, last_rademka, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user.get('user_id'),
                            user.get('nickname', 'Неизвестно'),
                            user.get('gofra_mm', 10.0),
                            user.get('cable_mm', 10.0),
                            user.get('atm_count', 0),
                            user.get('zmiy_grams', 0.0),
                            user.get('total_zmiy_grams', 0.0),
                            user.get('cable_power', 2),
                            user.get('gofra', 1),
                            user.get('last_atm_regen', 0),
                            user.get('last_davka', 0),
                            user.get('last_rademka', 0),
                            user.get('created_at', int(time.time())),
                            user.get('updated_at', int(time.time()))
                        ))
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при восстановлении пользователя {user.get('user_id')}: {e}")

            # Восстанавливаем бои радёмок
            if backup_data.get('rademka_fights'):
                for fight in backup_data['rademka_fights']:
                    try:
                        await conn.execute("""
                        INSERT INTO rademka_fights (
                            id, winner_id, loser_id, created_at
                        ) VALUES (?, ?, ?, ?)
                        """, (
                            fight.get('id'),
                            fight.get('winner_id'),
                            fight.get('loser_id'),
                            fight.get('created_at', int(time.time()))
                        ))
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при восстановлении боя {fight.get('id')}: {e}")

            # Восстанавливаем статистику чатов
            if backup_data.get('chat_stats'):
                for chat in backup_data['chat_stats']:
                    try:
                        await conn.execute("""
                        INSERT OR REPLACE INTO chat_stats (
                            chat_id, chat_title, chat_type, total_players,
                            active_players, total_zmiy_all, total_davki_all,
                            last_activity, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            chat.get('chat_id'),
                            chat.get('chat_title', ''),
                            chat.get('chat_type', 'private'),
                            chat.get('total_players', 0),
                            chat.get('active_players', 0),
                            chat.get('total_zmiy_all', 0.0),
                            chat.get('total_davki_all', 0),
                            chat.get('last_activity', 0),
                            chat.get('created_at', int(time.time()))
                        ))
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при восстановлении статистики чата {chat.get('chat_id')}: {e}")

            # Восстанавливаем статистику пользователей в чатах
            if backup_data.get('user_chat_stats'):
                for user_chat in backup_data['user_chat_stats']:
                    try:
                        await conn.execute("""
                        INSERT OR REPLACE INTO user_chat_stats (
                            id, user_id, chat_id, total_zmiy_grams, last_activity
                        ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            user_chat.get('id'),
                            user_chat.get('user_id'),
                            user_chat.get('chat_id'),
                            user_chat.get('total_zmiy_grams', 0.0),
                            user_chat.get('last_activity', 0)
                        ))
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при восстановлении статистики пользователя в чате {user_chat.get('id')}: {e}")

            # Восстанавливаем версию базы данных
            if backup_data.get('database_version'):
                for version in backup_data['database_version']:
                    try:
                        await conn.execute("""
                        INSERT OR REPLACE INTO database_version (
                            version, updated_at
                        ) VALUES (?, ?)
                        """, (
                            version.get('version'),
                            version.get('updated_at', int(time.time()))
                        ))
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при восстановлении версии базы данных: {e}")

            await conn.commit()
            logger.info("✅ Данные восстановлены из резервной копии")

        finally:
            await release_connection(conn)

    except Exception as e:
        logger.error(f"❌ Ошибка при восстановлении данных: {e}")
        raise

async def optimize_database():
    """Оптимизирует базу данных для лучшей производительности."""
    logger.info("⚡ Оптимизация базы данных...")

    try:
        conn = await get_connection()
        try:
            # Включаем WAL режим для лучшей производительности
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA temp_store=MEMORY")
            await conn.execute("PRAGMA cache_size=-20000")  # 20MB cache

            # Перестраиваем индексы
            await conn.execute("PRAGMA optimize")

            # Вакуумируем базу данных
            await conn.execute("VACUUM")

            logger.info("✅ База данных оптимизирована")

        finally:
            await release_connection(conn)

    except Exception as e:
        logger.error(f"❌ Ошибка при оптимизации базы данных: {e}")
        raise

async def repair_save_directory():
    """Ремонтирует директорию с сейвами и файлами."""
    logger.info("🔧 Ремонт директории с сейвами...")

    try:
        # 1. Проверяем и создаем необходимые директории
        await ensure_storage_dirs()

        # 2. Проверяем и чистим старые резервные копии
        await cleanup_old_backups()

        # 3. Проверяем и восстанавливаем файлы конфигурации
        await repair_config_files()

        # 4. Проверяем и восстанавливаем логи
        await repair_log_files()

        logger.info("✅ Ремонт директории с сейвами завершен")
        return True, "Ремонт директории с сейвами завершен успешно"

    except Exception as e:
        logger.error(f"❌ Ошибка при ремонте директории с сейвами: {e}")
        return False, f"Ошибка при ремонте директории с сейвами: {e}"


async def repair_config_files():
    """Восстанавливает файлы конфигурации."""
    logger.info("🔧 Восстановление файлов конфигурации...")

    try:
        # Проверяем и восстанавливаем bothost.json
        bothost_path = "bothost.json"
        if not os.path.exists(bothost_path):
            default_config = {
                "bot_token": "",
                "admin_ids": [],
                "backup_interval": 3600,
                "max_backups": 5
            }
            with open(bothost_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info("📄 Создан новый файл конфигурации bothost.json")

        # Проверяем и восстанавливаем config.py если нужно
        # (не перезаписываем существующий, так как он может содержать важные настройки)

        logger.info("✅ Файлы конфигурации проверены и восстановлены")

    except Exception as e:
        logger.error(f"❌ Ошибка при восстановлении файлов конфигурации: {e}")
        raise

async def repair_log_files():
    """Восстанавливает и оптимизирует файлы логов."""
    logger.info("📝 Восстановление файлов логов...")

    try:
        log_dir = "storage/logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logger.info("📁 Создана директория для логов")

        # Проверяем размер текущего лог-файла
        current_log = "storage/logs/bot_current.log"
        if os.path.exists(current_log):
            file_size = os.path.getsize(current_log) / (1024 * 1024)  # в МБ
            if file_size > 10:  # Если больше 10 МБ
                # Архивируем текущий лог
                archive_name = f"storage/logs/bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                shutil.move(current_log, archive_name)
                logger.info(f"🗄️ Архивирован большой лог-файл: {archive_name}")

        # Создаем новый лог-файл если нужно
        if not os.path.exists(current_log):
            open(current_log, 'w').close()
            logger.info("📄 Создан новый лог-файл")

        logger.info("✅ Файлы логов проверены и восстановлены")

    except Exception as e:
        logger.error(f"❌ Ошибка при восстановлении файлов логов: {e}")
        raise

async def full_system_repair():
    """
    Полный ремонт системы: проверка базы данных и директории с сейвами.
    ВНИМАНИЕ: Эта функция НЕ удаляет и не пересоздаёт базу данных!
    Для пересоздания БД используйте rebuild_database_structure() вручную.
    """
    logger.info("🛠️ Запуск полной проверки системы...")

    try:
        # 1. Только проверяем целостность БД (НЕ пересоздаём!)
        logger.info("🔍 Проверка целостности базы данных...")
        await check_database_integrity()

        # 2. Ремонт директории с сейвами
        dir_success, dir_message = await repair_save_directory()
        if not dir_success:
            logger.warning(f"⚠️ Ремонт директории с сейвами завершен с предупреждениями: {dir_message}")

        logger.info("✅ Полная проверка системы завершена успешно!")
        return True, "Проверка системы завершена успешно. База данных НЕ была изменена."

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке системы: {e}")
        return False, f"Ошибка при проверке системы: {e}"


async def rebuild_database_structure():
    """
    Пересоздаёт структуру базы данных (УДАЛЯЕТ старую!).
    Использовать только вручную для разработки!
    """
    logger.info("⚠️ ВНИМАНИЕ! Пересоздание структуры базы данных...")
    
    confirm = input("Эта операция УДАЛИТ ВСЕ ДАННЫЕ! Продолжить? (yes/no): ")
    if confirm.lower() != "yes":
        logger.info("❌ Операция отменена пользователем")
        return
    
    try:
        # Получаем текущие данные перед перестроением
        old_data = await backup_all_data()
        logger.info(f"💾 Сохранено {len(old_data.get('users', []))} пользователей")

        # Удаляем старую базу данных
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logger.info("🗑️ Старая база данных удалена")

        # Инициализируем новую базу данных
        await init_db()

        # Восстанавливаем данные
        await restore_all_data(old_data)

        logger.info("✅ Структура базы данных пересоздана")

    except Exception as e:
        logger.error(f"❌ Ошибка при пересоздании структуры базы данных: {e}")
        raise

# Остальные существующие функции из оригинального файла
async def get_patsan(user_id: int) -> Dict[str, Any]:
    """Получает данные пользователя из базы данных."""
    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            # Получаем имена колонок
            cursor = await conn.execute("PRAGMA table_info(users)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            # Создаем словарь из результата
            return dict(zip(column_names, row))
        else:
            # Создаем нового пользователя, если его нет в базе
            await conn.execute("""
                INSERT OR IGNORE INTO users (user_id) VALUES (?)
            """, (user_id,))
            await conn.commit()
            # Повторно получаем данные созданного пользователя
            cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                cursor = await conn.execute("PRAGMA table_info(users)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                return dict(zip(column_names, row))
            # Если все еще None, возвращаем дефолтные данные
            return {
                'user_id': user_id,
                'nickname': 'Неизвестно',
                'gofra_mm': 10.0,
                'cable_mm': 10.0,
                'atm_count': 12,
                'zmiy_grams': 0.0,
                'total_zmiy_grams': 0.0,
                'cable_power': 2,
                'gofra': 1,
                'last_atm_regen': 0,
                'last_davka': 0,
                'last_rademka': 0,
                'created_at': int(time.time()),
                'updated_at': int(time.time())
            }
    finally:
        await release_connection(conn)

async def save_patsan(patsan_data: Dict[str, Any]):
    """Сохраняет данные пользователя в базу данных."""
    conn = await get_connection()
    try:
        await conn.execute("""
            INSERT OR REPLACE INTO users (
                user_id, nickname, gofra_mm, cable_mm, atm_count,
                zmiy_grams, total_zmiy_grams, cable_power, gofra,
                last_atm_regen, last_davka, last_rademka, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patsan_data['user_id'],
            patsan_data.get('nickname', 'Неизвестно'),
            patsan_data.get('gofra_mm', 10.0),
            patsan_data.get('cable_mm', 10.0),
            patsan_data.get('atm_count', 0),
            patsan_data.get('zmiy_grams', 0.0),
            patsan_data.get('total_zmiy_grams', 0.0),
            patsan_data.get('cable_power', 2),
            patsan_data.get('gofra', 1),
            patsan_data.get('last_atm_regen', 0),
            patsan_data.get('last_davka', 0),
            patsan_data.get('last_rademka', 0),
            int(time.time())
        ))
        await conn.commit()
    finally:
        await release_connection(conn)

async def change_nickname(user_id: int, new_nickname: str) -> Tuple[bool, str]:
    """Изменяет никнейм пользователя."""
    conn = None
    try:
        conn = await get_connection()
        # Проверяем, не используется ли этот никнейм уже
        cursor = await conn.execute("SELECT user_id FROM users WHERE nickname = ? AND user_id != ?", (new_nickname, user_id))
        existing = await cursor.fetchone()
        if existing:
            return False, "Этот никнейм уже используется"

        await conn.execute("UPDATE users SET nickname = ?, updated_at = ? WHERE user_id = ?",
                         (new_nickname, int(time.time()), user_id))
        await conn.commit()
        return True, "Никнейм успешно изменен"
    except Exception as e:
        logger.error(f"Ошибка при изменении никнейма: {e}")
        return False, f"Ошибка при изменении никнейма: {e}"
    finally:
        if conn is not None:
            await release_connection(conn)

async def get_top_players(limit: int = 10, sort_by: str = "gofra") -> List[Dict[str, Any]]:
    """Получает топ игроков по указанному критерию с оптимизированным запросом."""
    conn = await get_connection()
    try:
        # Используем подготовленный запрос для безопасности
        valid_sort_fields = ["gofra_mm", "cable_mm", "zmiy_grams", "total_zmiy_grams", "atm_count"]
        if sort_by not in valid_sort_fields:
            sort_by = "gofra_mm"
        
        query = f"SELECT user_id, nickname, gofra_mm, cable_mm, zmiy_grams, total_zmiy_grams, atm_count FROM users ORDER BY {sort_by} DESC LIMIT ?"
        cursor = await conn.execute(query, (limit,))
        
        # Получаем имена колонок ПРЯМО ИЗ КУРСОРА
        column_names = [desc[0] for desc in cursor.description]
        
        rows = await cursor.fetchall()

        # Преобразуем строки в словари
        result = []
        for row in rows:
            result.append(dict(zip(column_names, row)))
        return result
    finally:
        await release_connection(conn)

async def bulk_update_users(users_data: List[Dict[str, Any]]):
    """Пакетное обновление пользователей для улучшения производительности."""
    if not users_data:
        return
    
    conn = await get_connection()
    try:
        # Используем транзакцию для пакетного обновления
        await conn.execute("BEGIN")
        
        for user_data in users_data:
            await conn.execute("""
                INSERT OR REPLACE INTO users (
                    user_id, nickname, gofra_mm, cable_mm, atm_count,
                    zmiy_grams, total_zmiy_grams, cable_power, gofra,
                    last_atm_regen, last_davka, last_rademka, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['user_id'],
                user_data.get('nickname', 'Неизвестно'),
                user_data.get('gofra_mm', 10.0),
                user_data.get('cable_mm', 10.0),
                user_data.get('atm_count', 0),
                user_data.get('zmiy_grams', 0.0),
                user_data.get('total_zmiy_grams', 0.0),
                user_data.get('cable_power', 2),
                user_data.get('gofra', 1),
                user_data.get('last_atm_regen', 0),
                user_data.get('last_davka', 0),
                user_data.get('last_rademka', 0),
                int(time.time())
            ))
        
        await conn.commit()
    except Exception as e:
        await conn.rollback()
        logger.error(f"Ошибка при пакетном обновлении пользователей: {e}")
        raise
    finally:
        await release_connection(conn)

async def get_multiple_users(user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Пакетная загрузка пользователей для улучшения производительности."""
    if not user_ids:
        return {}
    
    conn = await get_connection()
    try:
        # Создаем плейсхолдеры для IN запроса
        placeholders = ','.join(['?'] * len(user_ids))
        query = f"""
            SELECT * FROM users WHERE user_id IN ({placeholders})
        """
        
        cursor = await conn.execute(query, user_ids)
        rows = await cursor.fetchall()
        
        # Получаем имена колонок
        cursor = await conn.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Преобразуем строки в словари и группируем по user_id
        result = {}
        for row in rows:
            user_data = dict(zip(column_names, row))
            result[user_data['user_id']] = user_data
        
        return result
    finally:
        await release_connection(conn)

async def save_rademka_fight(winner_id: int, loser_id: int, money_taken: int = 0):
    """Сохраняет результат боя радёмки."""
    conn = await get_connection()
    try:
        await conn.execute("""
            INSERT INTO rademka_fights (winner_id, loser_id, created_at)
            VALUES (?, ?, ?)
        """, (winner_id, loser_id, int(time.time())))
        await conn.commit()
    finally:
        await release_connection(conn)

def get_gofra_info(gofra_mm: float) -> Dict[str, Any]:
    """Возвращает информацию о гофрошке на основе её длины."""
    gofra_levels = [
        {"threshold": 10.0, "name": "Новичок", "emoji": "🐣", "atm_speed": 1.0, "min_grams": 50, "max_grams": 100},
        {"threshold": 50.0, "name": "Ученик", "emoji": "👶", "atm_speed": 1.1, "min_grams": 100, "max_grams": 200},
        {"threshold": 150.0, "name": "Подмастерье", "emoji": "👷", "atm_speed": 1.2, "min_grams": 200, "max_grams": 300},
        {"threshold": 300.0, "name": "Мастер", "emoji": "👨‍🔧", "atm_speed": 1.3, "min_grams": 300, "max_grams": 400},
        {"threshold": 600.0, "name": "Эксперт", "emoji": "👨‍💼", "atm_speed": 1.4, "min_grams": 400, "max_grams": 500},
        {"threshold": 1200.0, "name": "Гуру", "emoji": "🧙", "atm_speed": 1.5, "min_grams": 500, "max_grams": 600},
        {"threshold": 2500.0, "name": "Легенда", "emoji": "🏆", "atm_speed": 1.6, "min_grams": 600, "max_grams": 700},
        {"threshold": 5000.0, "name": "Бог гофрошки", "emoji": "👑", "atm_speed": 1.7, "min_grams": 700, "max_grams": 800},
        {"threshold": 10000.0, "name": "Гофроцентрал", "emoji": "🏗️", "atm_speed": 1.8, "min_grams": 800, "max_grams": 900},
        {"threshold": 20000.0, "name": "Коричневый бог", "emoji": "💩", "atm_speed": 2.0, "min_grams": 900, "max_grams": 1100}
    ]

    # Находим текущий уровень гофрошки
    current_level = None
    next_level = None

    for i, level in enumerate(gofra_levels):
        if gofra_mm >= level["threshold"]:
            current_level = level
            if i + 1 < len(gofra_levels):
                next_level = gofra_levels[i + 1]
            else:
                next_level = None
        else:
            break

    if not current_level:
        current_level = gofra_levels[0]
        next_level = gofra_levels[1] if len(gofra_levels) > 1 else None

    # Вычисляем прогресс до следующего уровня
    if next_level:
        current_threshold = current_level["threshold"]
        next_threshold = next_level["threshold"]
        progress = (gofra_mm - current_threshold) / (next_threshold - current_threshold)
    else:
        progress = 1.0
        next_level = None

    return {
        "name": current_level["name"],
        "emoji": current_level["emoji"],
        "atm_speed": current_level["atm_speed"],
        "min_grams": current_level["min_grams"],
        "max_grams": current_level["max_grams"],
        "length_display": f"{gofra_mm/10:.1f} см",
        "width_display": f"{gofra_mm:.1f} см",
        "progress": progress,
        "next_threshold": next_level["threshold"] if next_level else None
    }

# format_length импортируется из utils.display (строка 66)

async def calculate_atm_regen_time(patsan: Dict[str, Any]) -> Dict[str, Any]:
    """Вычисляет время восстановления атмосфер."""
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
    atm_speed = gofra_info['atm_speed']

    base_time_per_atm = ATM_BASE_TIME  # 2 часа из config.py
    actual_time_per_atm = base_time_per_atm / atm_speed

    current_atm = patsan.get('atm_count', 0)
    max_atm = 12
    needed_atm = max_atm - current_atm

    total_time = needed_atm * actual_time_per_atm
    time_to_next_atm = actual_time_per_atm if current_atm < max_atm else 0

    return {
        'per_atm': actual_time_per_atm,
        'total': total_time,
        'needed': needed_atm,
        'time_to_next_atm': time_to_next_atm,
        'time_to_one_atm': actual_time_per_atm
    }

async def davka_zmiy(user_id: int, chat_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
    """Обрабатывает давку змия пользователем."""
    try:
        patsan = await get_patsan(user_id)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        # Проверяем, есть ли атмосферы для давки
        if patsan.get('atm_count', 0) < 12:
            return False, None, {"error": "Нужно 12 атмосфер для давки змия!"}

        # Вычисляем вес змия
        zmiy_grams = random.randint(gofra_info['min_grams'], gofra_info['max_grams'])

        # Обновляем данные пользователя
        old_gofra_mm = patsan.get('gofra_mm', 10.0)
        old_cable_mm = patsan.get('cable_mm', 10.0)

        # Получаем опыт за змия (0.025 мм за 1 грамм - для достижения 70-100 мм за месяц)
        exp_gained_mm = zmiy_grams * 0.025

        new_gofra_mm = old_gofra_mm + exp_gained_mm
        new_cable_mm = old_cable_mm + (zmiy_grams / 1000) * 150.0  # 150.0 мм за 1 кг - для достижения 300-500 мм за месяц

        # Специальное сообщение для килограммовых змеев
        special_message = None
        if zmiy_grams > 1000:
            special_message = "КИЛОГРАММ ГОВНА ЗА ДВАДЦАТЬ ПЯТЬ СЕКУНД"

        # Сбрасываем атмосферы
        patsan['atm_count'] = 0
        patsan['zmiy_grams'] = zmiy_grams
        patsan['total_zmiy_grams'] = patsan.get('total_zmiy_grams', 0) + zmiy_grams
        patsan['gofra_mm'] = new_gofra_mm
        patsan['cable_mm'] = new_cable_mm
        patsan['cable_power'] = int(new_cable_mm / 5)
        patsan['gofra'] = int(new_gofra_mm / 10)
        patsan['last_davka'] = int(time.time())

        await save_patsan(patsan)

        # Обновляем статистику чата если нужно
        if chat_id:
            await ChatManager.update_user_chat_stats(user_id, chat_id, zmiy_grams)

        return True, patsan, {
            'zmiy_grams': zmiy_grams,
            'old_gofra_mm': old_gofra_mm,
            'new_gofra_mm': new_gofra_mm,
            'old_cable_mm': old_cable_mm,
            'new_cable_mm': new_cable_mm,
            'exp_gained_mm': exp_gained_mm
        }

    except Exception as e:
        logger.error(f"Ошибка при давке змия: {e}")
        return False, None, {"error": f"Ошибка при давке змия: {e}"}

async def uletet_zmiy(user_id: int) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
    """Обрабатывает отправку змия в коричневую страну."""
    try:
        patsan = await get_patsan(user_id)

        # Проверяем, есть ли змий для отправки
        if patsan.get('zmiy_grams', 0) <= 0:
            return False, None, {"error": "Нет змия для отправки!"}

        zmiy_grams = patsan.get('zmiy_grams', 0)
        patsan['zmiy_grams'] = 0
        # Удаляем восстановление атмосфер - это было багом
        # patsan['atm_count'] = 12  # Восстанавливаем атмосферы

        await save_patsan(patsan)

        return True, patsan, {
            'zmiy_grams': zmiy_grams
        }

    except Exception as e:
        logger.error(f"Ошибка при отправке змия: {e}")
        return False, None, {"error": f"Ошибка при отправке змия: {e}"}

async def can_fight_pvp(user_id: int) -> Tuple[bool, str]:
    """Проверяет, может ли пользователь участвовать в PvP."""
    patsan = await get_patsan(user_id)

    # Проверяем лимит боёв (10 боёв в час)
    last_fight = patsan.get('last_rademka', 0)
    current_time = int(time.time())

    if current_time - last_fight < 3600:
        # Проверяем количество боёв за последний час
        conn = await get_connection()
        try:
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM rademka_fights
                WHERE (winner_id = ? OR loser_id = ?) AND created_at > ?
            """, (user_id, user_id, current_time - 3600))
            fight_count = await cursor.fetchone()

            if fight_count and fight_count[0] >= 10:
                remaining_time = 3600 - (current_time - last_fight)
                minutes = remaining_time // 60
                return False, f"Лимит боёв: 10/час. Подожди {minutes} минут"
    finally:
        await release_connection(conn)

    return True, "Можно драться"

async def calculate_pvp_chance(attacker: Dict[str, Any], defender: Dict[str, Any]) -> float:
    """Вычисляет шанс победы в PvP бою."""
    # Базовый шанс
    base_chance = 50.0

    # Влияние гофрошки
    attacker_gofra = attacker.get('gofra_mm', 10.0)
    defender_gofra = defender.get('gofra_mm', 10.0)
    gofra_diff = attacker_gofra - defender_gofra
    gofra_bonus = (gofra_diff / 100) * 2  # 2% за каждые 10 мм разницы

    # Влияние кабеля
    attacker_cable = attacker.get('cable_mm', 10.0)
    defender_cable = defender.get('cable_mm', 10.0)
    cable_diff = attacker_cable - defender_cable
    cable_bonus = (cable_diff / 10) * 0.2  # 0.2% за каждый 1 мм разницы

    # Общий шанс
    total_chance = base_chance + gofra_bonus + cable_bonus

    # Ограничиваем шанс от 10% до 90%
    return max(10.0, min(90.0, total_chance))

async def calculate_davka_cooldown(patsan: Dict[str, Any]) -> Dict[str, Any]:
    """Вычисляет время до следующей давки змия."""
    current_time = int(time.time())
    last_davka = patsan.get('last_davka', 0)

    # Если никогда не давил, то можно давить сразу
    if last_davka == 0:
        return {
            'can_davka': True,
            'time_until_next': 0,
            'formatted_time': "Можно давить"
        }

    # Время между давками - 24 часа (86400 секунд)
    cooldown_seconds = 86400
    time_since_last_davka = current_time - last_davka

    if time_since_last_davka >= cooldown_seconds:
        return {
            'can_davka': True,
            'time_until_next': 0,
            'formatted_time': "Можно давить"
        }
    else:
        remaining_time = cooldown_seconds - time_since_last_davka
        return {
            'can_davka': False,
            'time_until_next': remaining_time,
            'formatted_time': ft(remaining_time)
        }

class ChatManager:
    """Менеджер для работы со статистикой чатов."""

    @staticmethod
    async def register_chat(chat_id: int, chat_title: str, chat_type: str):
        """Регистрирует чат в системе."""
        conn = await get_connection()
        try:
            await conn.execute("""
                INSERT OR IGNORE INTO chat_stats (
                    chat_id, chat_title, chat_type
                ) VALUES (?, ?, ?)
            """, (chat_id, chat_title, chat_type))
            await conn.commit()
        finally:
            await conn.close()

    @staticmethod
    async def update_chat_activity(chat_id: int):
        """Обновляет время последней активности в чате."""
        conn = await get_connection()
        try:
            await conn.execute("""
                UPDATE chat_stats
                SET last_activity = ?, active_players = active_players + 1
                WHERE chat_id = ?
            """, (int(time.time()), chat_id))
            await conn.commit()
        finally:
            await conn.close()

    @staticmethod
    async def get_chat_stats(chat_id: int) -> Dict[str, Any]:
        """Получает статистику чата."""
        conn = await get_connection()
        try:
            cursor = await conn.execute("""
                SELECT * FROM chat_stats WHERE chat_id = ?
            """, (chat_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            else:
                return {
                    'chat_id': chat_id,
                    'chat_title': '',
                    'chat_type': 'private',
                    'total_players': 0,
                    'active_players': 0,
                    'total_zmiy_all': 0.0,
                    'total_davki_all': 0,
                    'last_activity': 0,
                    'created_at': int(time.time())
                }
        finally:
            await conn.close()

    @staticmethod
    async def update_user_chat_stats(user_id: int, chat_id: int, zmiy_grams: float):
        """Обновляет статистику пользователя в чате."""
        conn = await get_connection()
        try:
            # Обновляем или создаем запись для пользователя в чате
            await conn.execute("""
                INSERT OR IGNORE INTO user_chat_stats (
                    user_id, chat_id, total_zmiy_grams, last_activity
                ) VALUES (?, ?, ?, ?)
            """, (user_id, chat_id, 0.0, int(time.time())))

            await conn.execute("""
                UPDATE user_chat_stats
                SET total_zmiy_grams = total_zmiy_grams + ?,
                    last_activity = ?
                WHERE user_id = ? AND chat_id = ?
            """, (zmiy_grams, int(time.time()), user_id, chat_id))

            # Обновляем общую статистику чата
            await conn.execute("""
                UPDATE chat_stats
                SET total_zmiy_all = total_zmiy_all + ?,
                    total_davki_all = total_davki_all + 1
                WHERE chat_id = ?
            """, (zmiy_grams, chat_id))

            # Проверяем, есть ли пользователь в общем списке чата
            cursor = await conn.execute("""
                SELECT user_id FROM user_chat_stats WHERE chat_id = ? AND user_id = ?
            """, (chat_id, user_id))
            exists = await cursor.fetchone()

            if not exists:
                # Увеличиваем количество игроков в чате
                await conn.execute("""
                    UPDATE chat_stats
                    SET total_players = total_players + 1
                    WHERE chat_id = ?
                """, (chat_id,))

            await conn.commit()
        finally:
            await conn.close()

    @staticmethod
    async def get_user_total_in_chat(chat_id: int, user_id: int) -> float:
        """Получает общее количество змия, которое пользователь выдавил в чате."""
        conn = await get_connection()
        try:
            cursor = await conn.execute("""
                SELECT total_zmiy_grams FROM user_chat_stats
                WHERE chat_id = ? AND user_id = ?
            """, (chat_id, user_id))
            row = await cursor.fetchone()
            return row[0] if row else 0.0
        finally:
            await conn.close()

    @staticmethod
    async def get_chat_top(chat_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает топ игроков в чате."""
        conn = await get_connection()
        try:
            cursor = await conn.execute("""
                SELECT u.user_id, u.nickname, u.gofra_mm, u.cable_mm, uc.total_zmiy_grams,
                       RANK() OVER (ORDER BY uc.total_zmiy_grams DESC) as rank
                FROM user_chat_stats uc
                JOIN users u ON uc.user_id = u.user_id
                WHERE uc.chat_id = ?
                ORDER BY uc.total_zmiy_grams DESC
                LIMIT ?
            """, (chat_id, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()


# ============ AUTO BACKUP SYSTEM ============

_backup_task = None
_backup_interval = 3600  # 1 час по умолчанию

async def create_backup() -> str:
    """Создаёт бэкап базы данных."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
            logger.info(f"💾 Создан бэкап: {backup_filename}")
            
            # Удаляем старые бэкапы
            await cleanup_old_backups(max_keep=5)
            
            return backup_filename
        else:
            logger.warning("⚠️ База данных не существует для бэкапа")
            return ""
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return ""

async def cleanup_old_backups(max_keep: int = 5):
    """Удаляет старые бэкапы, оставляя только max_keep последних."""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        
        backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_') and f.endswith('.db')]
        if len(backups) <= max_keep:
            return
        
        backups.sort()
        for old in backups[:-max_keep]:
            old_path = os.path.join(BACKUP_DIR, old)
            try:
                os.remove(old_path)
                logger.info(f"🗑️ Удалён старый бэкап: {old}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось удалить {old}: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка очистки бэкапов: {e}")

async def auto_backup_loop():
    """Фоновый цикл автобэкапа."""
    global _backup_task, _backup_interval
    
    logger.info("🚀 Запущен фоновый автобэкап")
    
    while True:
        try:
            await asyncio.sleep(_backup_interval)
            await create_backup()
        except asyncio.CancelledError:
            logger.info("🛑 Остановлен фоновый автобэкап")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле автобэкапа: {e}")
            await asyncio.sleep(60)  # Ждём минуту перед повторной попыткой

async def start_auto_backup(interval_seconds: int = 3600):
    """Запускает автобэкап."""
    global _backup_task, _backup_interval
    
    _backup_interval = interval_seconds
    
    if _backup_task is None or _backup_task.done():
        _backup_task = asyncio.create_task(auto_backup_loop())
        logger.info(f"✅ Автобэкап запущен (интервал: {interval_seconds}с)")
    else:
        logger.info("ℹ️ Автобэкап уже запущен")

async def stop_auto_backup():
    """Останавливает автобэкап."""
    global _backup_task
    
    if _backup_task is not None and not _backup_task.done():
        _backup_task.cancel()
        try:
            await _backup_task
        except asyncio.CancelledError:
            pass
        _backup_task = None
        logger.info("🛑 Автобэкап остановлен")

async def upload_backup_to_telegram(bot, admin_id: int) -> bool:
    """Отправляет последний бэкап в Telegram админу."""
    try:
        if not os.path.exists(DB_PATH):
            logger.warning("⚠️ База данных не существует для отправки")
            return False
        
        # Находим последний бэкап
        backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_') and f.endswith('.db')]
        if not backups:
            logger.info("📭 Нет бэкапов для отправки")
            return False
        
        latest_backup = sorted(backups)[-1]
        backup_path = os.path.join(BACKUP_DIR, latest_backup)
        
        # Отправляем файл
        with open(backup_path, 'rb') as f:
            await bot.send_document(
                chat_id=admin_id,
                document=f,
                caption=f"💾 Бэкап бота: {latest_backup}",
                protect_content=True
            )
        
        logger.info(f"✅ Бэкап отправлен в Telegram: {latest_backup}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки бэкапа в Telegram: {e}")
        return False

async def get_backup_info() -> dict:
    """Возвращает информацию о бэкапах."""
    try:
        if not os.path.exists(BACKUP_DIR):
            return {"count": 0, "backups": [], "total_size": 0}
        
        backups = []
        total_size = 0
        
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if f.startswith('backup_') and f.endswith('.db'):
                fpath = os.path.join(BACKUP_DIR, f)
                size = os.path.getsize(fpath)
                total_size += size
                backups.append({
                    "name": f,
                    "size": size,
                    "size_mb": round(size / (1024*1024), 2),
                    "created": datetime.fromtimestamp(os.path.getctime(fpath)).isoformat()
                })
        
        return {
            "count": len(backups),
            "backups": backups,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024*1024), 2)
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения инфо о бэкапах: {e}")
        return {"count": 0, "backups": [], "total_size": 0, "error": str(e)}
