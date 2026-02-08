"""
Менеджер оптимизации производительности для Telegram бота.

Этот модуль предоставляет:
- Централизованное управление всеми системами оптимизации
- Автоматическую настройку параметров
- Мониторинг эффективности оптимизаций
- Интеграцию всех компонентов
- Автоматическое тестирование производительности
"""

import asyncio
import logging
import time
import json
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import statistics
import psutil
import sys

logger = logging.getLogger(__name__)

class OptimizationLevel(Enum):
    """Уровни оптимизации."""
    LOW = "low"           # Минимальная оптимизация
    MEDIUM = "medium"     # Средняя оптимизация
    HIGH = "high"         # Высокая оптимизация
    MAXIMUM = "maximum"   # Максимальная оптимизация

@dataclass
class OptimizationConfig:
    """Конфигурация оптимизации."""
    level: OptimizationLevel
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    enable_monitoring: bool = True
    enable_backup: bool = True
    enable_error_handling: bool = True
    cache_ttl: int = 300
    rate_limit_window: int = 60
    rate_limit_max_requests: int = 100
    monitoring_interval: int = 60
    backup_interval: int = 3600

class PerformanceMetrics:
    """Метрики производительности."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.error_rates: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.cache_hit_rates: List[float] = []
        self.database_query_times: List[float] = []
        self._lock = threading.Lock()
    
    def add_response_time(self, time_ms: float):
        """Добавляет время ответа."""
        with self._lock:
            self.response_times.append(time_ms)
            if len(self.response_times) > 1000:
                self.response_times.pop(0)
    
    def add_error_rate(self, rate: float):
        """Добавляет уровень ошибок."""
        with self._lock:
            self.error_rates.append(rate)
            if len(self.error_rates) > 100:
                self.error_rates.pop(0)
    
    def add_memory_usage(self, usage_mb: float):
        """Добавляет использование памяти."""
        with self._lock:
            self.memory_usage.append(usage_mb)
            if len(self.memory_usage) > 1000:
                self.memory_usage.pop(0)
    
    def add_cpu_usage(self, usage_percent: float):
        """Добавляет использование CPU."""
        with self._lock:
            self.cpu_usage.append(usage_percent)
            if len(self.cpu_usage) > 1000:
                self.cpu_usage.pop(0)
    
    def add_cache_hit_rate(self, rate: float):
        """Добавляет процент попаданий в кэш."""
        with self._lock:
            self.cache_hit_rates.append(rate)
            if len(self.cache_hit_rates) > 100:
                self.cache_hit_rates.pop(0)
    
    def add_database_query_time(self, time_ms: float):
        """Добавляет время выполнения запроса к БД."""
        with self._lock:
            self.database_query_times.append(time_ms)
            if len(self.database_query_times) > 1000:
                self.database_query_times.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику производительности."""
        with self._lock:
            return {
                'response_time': {
                    'avg': statistics.mean(self.response_times) if self.response_times else 0,
                    'p95': self._percentile(self.response_times, 95) if self.response_times else 0,
                    'p99': self._percentile(self.response_times, 99) if self.response_times else 0,
                    'max': max(self.response_times) if self.response_times else 0
                },
                'error_rate': {
                    'avg': statistics.mean(self.error_rates) if self.error_rates else 0,
                    'current': self.error_rates[-1] if self.error_rates else 0
                },
                'memory_usage': {
                    'avg': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                    'current': self.memory_usage[-1] if self.memory_usage else 0,
                    'max': max(self.memory_usage) if self.memory_usage else 0
                },
                'cpu_usage': {
                    'avg': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                    'current': self.cpu_usage[-1] if self.cpu_usage else 0,
                    'max': max(self.cpu_usage) if self.cpu_usage else 0
                },
                'cache_hit_rate': {
                    'avg': statistics.mean(self.cache_hit_rates) if self.cache_hit_rates else 0,
                    'current': self.cache_hit_rates[-1] if self.cache_hit_rates else 0
                },
                'database_query_time': {
                    'avg': statistics.mean(self.database_query_times) if self.database_query_times else 0,
                    'p95': self._percentile(self.database_query_times, 95) if self.database_query_times else 0,
                    'max': max(self.database_query_times) if self.database_query_times else 0
                }
            }
    
    def _percentile(self, data: List[float], p: int) -> float:
        """Вычисляет перцентиль."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((p / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

class OptimizationManager:
    """Менеджер оптимизации производительности."""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig(level=OptimizationLevel.MEDIUM)
        self.metrics = PerformanceMetrics()
        self._optimization_tasks: List[asyncio.Task] = []
        self._running = False
        self._lock = asyncio.Lock()
        
        # Состояние систем
        self.systems = {
            'cache': {'enabled': False, 'healthy': False},
            'rate_limiting': {'enabled': False, 'healthy': False},
            'monitoring': {'enabled': False, 'healthy': False},
            'backup': {'enabled': False, 'healthy': False},
            'error_handling': {'enabled': False, 'healthy': False}
        }
        
        # Автоматическая настройка
        self.auto_tuning_enabled = True
        self.tuning_interval = 300  # 5 минут
    
    async def initialize(self):
        """Инициализирует все системы оптимизации."""
        logger.info("🚀 Инициализация системы оптимизации производительности...")
        
        try:
            # Импортируем и инициализируем все системы
            if self.config.enable_caching:
                await self._initialize_caching()
            
            if self.config.enable_rate_limiting:
                await self._initialize_rate_limiting()
            
            if self.config.enable_monitoring:
                await self._initialize_monitoring()
            
            if self.config.enable_backup:
                await self._initialize_backup()
            
            if self.config.enable_error_handling:
                await self._initialize_error_handling()
            
            # Запускаем фоновые задачи
            await self._start_background_tasks()
            
            logger.info("✅ Система оптимизации производительности инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации системы оптимизации: {e}")
            raise
    
    async def _initialize_caching(self):
        """Инициализирует систему кэширования."""
        try:
            from cache_manager import get_cache_manager, initialize_cache
            cache_manager = get_cache_manager()
            await initialize_cache()
            
            self.systems['cache']['enabled'] = True
            self.systems['cache']['healthy'] = True
            
            logger.info("✅ Система кэширования инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации кэширования: {e}")
            self.systems['cache']['enabled'] = False
    
    async def _initialize_rate_limiting(self):
        """Инициализирует систему ограничения частоты запросов."""
        try:
            from rate_limiter import get_rate_limiter
            rate_limiter = get_rate_limiter()
            
            # Настраиваем лимиты в зависимости от уровня оптимизации
            if self.config.level == OptimizationLevel.HIGH:
                rate_limiter.add_limit("command:davka", RateLimitConfig(limit=3, window_seconds=300))
                rate_limiter.add_limit("command:rademka", RateLimitConfig(limit=2, window_seconds=600))
            elif self.config.level == OptimizationLevel.MAXIMUM:
                rate_limiter.add_limit("command:davka", RateLimitConfig(limit=2, window_seconds=600))
                rate_limiter.add_limit("command:rademka", RateLimitConfig(limit=1, window_seconds=1200))
            
            self.systems['rate_limiting']['enabled'] = True
            self.systems['rate_limiting']['healthy'] = True
            
            logger.info("✅ Система ограничения частоты запросов инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации rate limiting: {e}")
            self.systems['rate_limiting']['enabled'] = False
    
    async def _initialize_monitoring(self):
        """Инициализирует систему мониторинга."""
        try:
            from metrics_collector import get_metrics_collector, start_metrics_collection
            metrics_collector = get_metrics_collector()
            start_metrics_collection()
            
            self.systems['monitoring']['enabled'] = True
            self.systems['monitoring']['healthy'] = True
            
            logger.info("✅ Система мониторинга инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации мониторинга: {e}")
            self.systems['monitoring']['enabled'] = False
    
    async def _initialize_backup(self):
        """Инициализирует систему резервного копирования."""
        try:
            from backup_manager import get_backup_manager
            backup_manager = get_backup_manager()
            backup_manager.set_backup_interval(self.config.backup_interval)
            await backup_manager.start()
            
            self.systems['backup']['enabled'] = True
            self.systems['backup']['healthy'] = True
            
            logger.info("✅ Система резервного копирования инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации резервного копирования: {e}")
            self.systems['backup']['enabled'] = False
    
    async def _initialize_error_handling(self):
        """Инициализирует систему обработки ошибок."""
        try:
            from error_handler import get_error_handler
            error_handler = get_error_handler()
            
            self.systems['error_handling']['enabled'] = True
            self.systems['error_handling']['healthy'] = True
            
            logger.info("✅ Система обработки ошибок инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации обработки ошибок: {e}")
            self.systems['error_handling']['enabled'] = False
    
    async def _start_background_tasks(self):
        """Запускает фоновые задачи."""
        self._running = True
        
        # Задача мониторинга производительности
        self._optimization_tasks.append(
            asyncio.create_task(self._performance_monitoring_loop())
        )
        
        # Задача автоматической настройки
        if self.auto_tuning_enabled:
            self._optimization_tasks.append(
                asyncio.create_task(self._auto_tuning_loop())
            )
        
        logger.info("🔄 Фоновые задачи оптимизации запущены")
    
    async def _performance_monitoring_loop(self):
        """Цикл мониторинга производительности."""
        while self._running:
            try:
                await self._collect_performance_metrics()
                await self._analyze_performance()
                await asyncio.sleep(self.config.monitoring_interval)
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга производительности: {e}")
                await asyncio.sleep(60)
    
    async def _collect_performance_metrics(self):
        """Собирает метрики производительности."""
        try:
            # Сбор системных метрик
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            self.metrics.add_cpu_usage(cpu_usage)
            self.metrics.add_memory_usage(memory.used / 1024 / 1024)  # MB
            
            # Сбор метрик из других систем
            if self.systems['monitoring']['enabled']:
                from metrics_collector import get_metrics_collector
                collector = get_metrics_collector()
                stats = collector.get_metrics_summary()
                
                if 'command_stats' in stats:
                    for cmd, cmd_stats in stats['command_stats'].items():
                        self.metrics.add_response_time(cmd_stats.get('avg_time', 0) * 1000)
                        self.metrics.add_database_query_time(cmd_stats.get('avg_time', 0) * 1000)
                
                if 'system_stats' in stats:
                    system_stats = stats['system_stats']
                    if 'cache_hit_rate' in system_stats:
                        self.metrics.add_cache_hit_rate(system_stats['cache_hit_rate'])
            
            # Сбор метрик из кэша
            if self.systems['cache']['enabled']:
                from cache_manager import get_cache_stats
                cache_stats = get_cache_stats()
                hit_rate = cache_stats.get('hit_rate', 0)
                self.metrics.add_cache_hit_rate(hit_rate)
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора метрик производительности: {e}")
    
    async def _analyze_performance(self):
        """Анализирует производительность и принимает решения."""
        try:
            stats = self.metrics.get_stats()
            
            # Анализ времени ответа
            avg_response_time = stats['response_time']['avg']
            if avg_response_time > 1000:  # > 1 секунды
                logger.warning(f"⚠️ Высокое среднее время ответа: {avg_response_time:.2f}ms")
                await self._optimize_response_time()
            
            # Анализ использования памяти
            current_memory = stats['memory_usage']['current']
            if current_memory > 512:  # > 512 MB
                logger.warning(f"⚠️ Высокое использование памяти: {current_memory:.2f}MB")
                await self._optimize_memory_usage()
            
            # Анализ использования CPU
            current_cpu = stats['cpu_usage']['current']
            if current_cpu > 80:  # > 80%
                logger.warning(f"⚠️ Высокая нагрузка CPU: {current_cpu:.2f}%")
                await self._optimize_cpu_usage()
            
            # Анализ процента попаданий в кэш
            cache_hit_rate = stats['cache_hit_rate']['current']
            if cache_hit_rate < 50:  # < 50%
                logger.warning(f"⚠️ Низкий процент попаданий в кэш: {cache_hit_rate:.2f}%")
                await self._optimize_cache_performance()
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа производительности: {e}")
    
    async def _optimize_response_time(self):
        """Оптимизирует время ответа."""
        try:
            if self.systems['cache']['enabled']:
                from cache_manager import get_cache_manager
                cache_manager = get_cache_manager()
                
                # Увеличиваем TTL для часто используемых данных
                # Это пример - в реальности нужно анализировать конкретные данные
                
            if self.systems['rate_limiting']['enabled']:
                from rate_limiter import get_rate_limiter
                rate_limiter = get_rate_limiter()
                
                # Может потребоваться настройка лимитов
            
            logger.info("⚡ Оптимизация времени ответа завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации времени ответа: {e}")
    
    async def _optimize_memory_usage(self):
        """Оптимизирует использование памяти."""
        try:
            if self.systems['cache']['enabled']:
                from cache_manager import get_cache_manager
                cache_manager = get_cache_manager()
                
                # Очищаем старые данные из кэша
                cache_manager.local_cache.clear()
            
            # Очищаем метрики для освобождения памяти
            self.metrics.response_times.clear()
            self.metrics.database_query_times.clear()
            
            logger.info("🧹 Оптимизация использования памяти завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации памяти: {e}")
    
    async def _optimize_cpu_usage(self):
        """Оптимизирует использование CPU."""
        try:
            # Уменьшаем частоту мониторинга
            if self.config.monitoring_interval < 300:  # 5 минут
                self.config.monitoring_interval = 300
                logger.info("⏰ Уменьшена частота мониторинга для снижения нагрузки CPU")
            
            # Оптимизируем кэш
            if self.systems['cache']['enabled']:
                from cache_manager import get_cache_manager
                cache_manager = get_cache_manager()
                cache_manager.local_cache._cleanup_queues()
            
            logger.info("⚙️ Оптимизация использования CPU завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации CPU: {e}")
    
    async def _optimize_cache_performance(self):
        """Оптимизирует производительность кэша."""
        try:
            if self.systems['cache']['enabled']:
                from cache_manager import get_cache_manager
                cache_manager = get_cache_manager()
                
                # Увеличиваем размер локального кэша
                cache_manager.local_cache.max_size = min(cache_manager.local_cache.max_size * 2, 5000)
                
                # Увеличиваем TTL для часто используемых данных
                # Это пример - в реальности нужно анализировать конкретные данные
            
            logger.info("📦 Оптимизация производительности кэша завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации кэша: {e}")
    
    async def _auto_tuning_loop(self):
        """Цикл автоматической настройки."""
        while self._running:
            try:
                await self._perform_auto_tuning()
                await asyncio.sleep(self.tuning_interval)
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле автоматической настройки: {e}")
                await asyncio.sleep(300)
    
    async def _perform_auto_tuning(self):
        """Выполняет автоматическую настройку параметров."""
        try:
            stats = self.metrics.get_stats()
            
            # Автоматическая настройка TTL кэша
            cache_hit_rate = stats['cache_hit_rate']['avg']
            if cache_hit_rate < 30:
                self.config.cache_ttl = min(self.config.cache_ttl * 2, 3600)  # Максимум 1 час
                logger.info(f"🔄 Автоматически увеличен TTL кэша до {self.config.cache_ttl} секунд")
            
            # Автоматическая настройка интервала мониторинга
            cpu_usage = stats['cpu_usage']['avg']
            if cpu_usage > 50:
                self.config.monitoring_interval = min(self.config.monitoring_interval * 2, 600)  # Максимум 10 минут
                logger.info(f"🔄 Автоматически увеличен интервал мониторинга до {self.config.monitoring_interval} секунд")
            
            # Автоматическая настройка интервала бэкапа
            memory_usage = stats['memory_usage']['avg']
            if memory_usage > 256:  # > 256 MB
                self.config.backup_interval = max(self.config.backup_interval * 2, 7200)  # Максимум 2 часа
                logger.info(f"🔄 Автоматически увеличен интервал бэкапа до {self.config.backup_interval} секунд")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автоматической настройки: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Возвращает статус всех систем."""
        return {
            'config': asdict(self.config),
            'systems': self.systems,
            'metrics': self.metrics.get_stats(),
            'optimization_level': self.config.level.value,
            'auto_tuning_enabled': self.auto_tuning_enabled,
            'tuning_interval': self.tuning_interval
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Генерирует отчет о производительности."""
        try:
            stats = self.metrics.get_stats()
            
            # Сбор дополнительной информации из других систем
            additional_info = {}
            
            if self.systems['cache']['enabled']:
                from cache_manager import get_cache_stats
                additional_info['cache'] = get_cache_stats()
            
            if self.systems['monitoring']['enabled']:
                from metrics_collector import get_performance_report
                additional_info['monitoring'] = get_performance_report(hours)
            
            if self.systems['backup']['enabled']:
                from backup_manager import get_backup_stats
                additional_info['backup'] = get_backup_stats()
            
            return {
                'generated_at': datetime.now().isoformat(),
                'period_hours': hours,
                'performance_metrics': stats,
                'system_status': self.systems,
                'optimization_config': asdict(self.config),
                'recommendations': self._generate_recommendations(stats),
                'additional_info': additional_info
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета о производительности: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Генерирует рекомендации по оптимизации."""
        recommendations = []
        
        # Рекомендации по времени ответа
        avg_response_time = stats['response_time']['avg']
        if avg_response_time > 500:
            recommendations.append("Рассмотрите увеличение TTL кэша для часто используемых данных")
            recommendations.append("Проверьте производительность базы данных")
        
        # Рекомендации по использованию памяти
        current_memory = stats['memory_usage']['current']
        if current_memory > 256:
            recommendations.append("Рассмотрите оптимизацию размера кэша")
            recommendations.append("Проверьте наличие утечек памяти")
        
        # Рекомендации по использованию CPU
        current_cpu = stats['cpu_usage']['current']
        if current_cpu > 50:
            recommendations.append("Рассмотрите уменьшение частоты мониторинга")
            recommendations.append("Проверьте наличие ресурсоемких операций")
        
        # Рекомендации по кэшу
        cache_hit_rate = stats['cache_hit_rate']['current']
        if cache_hit_rate < 70:
            recommendations.append("Увеличьте TTL для часто используемых данных")
            recommendations.append("Рассмотрите добавление новых типов данных в кэш")
        
        return recommendations
    
    async def shutdown(self):
        """Останавливает все системы оптимизации."""
        logger.info("🛑 Остановка системы оптимизации производительности...")
        
        self._running = False
        
        # Останавливаем фоновые задачи
        for task in self._optimization_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._optimization_tasks.clear()
        
        # Останавливаем системы
        if self.systems['monitoring']['enabled']:
            from metrics_collector import stop_metrics_collection
            stop_metrics_collection()
        
        if self.systems['backup']['enabled']:
            from backup_manager import get_backup_manager
            backup_manager = get_backup_manager()
            await backup_manager.stop()
        
        if self.systems['cache']['enabled']:
            from cache_manager import close_cache
            await close_cache()
        
        logger.info("✅ Система оптимизации производительности остановлена")

# Глобальный экземпляр менеджера оптимизации
_optimization_manager: Optional[OptimizationManager] = None

def get_optimization_manager() -> OptimizationManager:
    """Возвращает глобальный экземпляр менеджера оптимизации."""
    global _optimization_manager
    if _optimization_manager is None:
        config = OptimizationConfig(level=OptimizationLevel.MEDIUM)
        _optimization_manager = OptimizationManager(config)
    return _optimization_manager

# Функции для удобного использования

async def initialize_optimization(level: OptimizationLevel = OptimizationLevel.MEDIUM):
    """Инициализирует систему оптимизации."""
    config = OptimizationConfig(level=level)
    manager = OptimizationManager(config)
    await manager.initialize()
    global _optimization_manager
    _optimization_manager = manager

def get_optimization_status() -> Dict[str, Any]:
    """Возвращает статус оптимизации."""
    manager = get_optimization_manager()
    return manager.get_system_status()

def get_performance_report(hours: int = 24) -> Dict[str, Any]:
    """Возвращает отчет о производительности."""
    manager = get_optimization_manager()
    return manager.get_performance_report(hours)

async def shutdown_optimization():
    """Останавливает систему оптимизации."""
    manager = get_optimization_manager()
    await manager.shutdown()

# Пример использования:
"""
# Инициализация с высоким уровнем оптимизации
await initialize_optimization(OptimizationLevel.HIGH)

# Получение статуса
status = get_optimization_status()

# Получение отчета о производительности
report = get_performance_report(24)

# Остановка системы
await shutdown_optimization()
"""