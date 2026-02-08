"""
Система сбора и анализа метрик производительности для Telegram бота.

Этот модуль предоставляет:
- Сбор метрик производительности
- Мониторинг использования ресурсов
- Анализ производительности команд
- Генерацию отчетов
- Интеграцию с внешними системами мониторинга
"""

import asyncio
import logging
import time
import json
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import platform
import sys
import os

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Типы метрик."""
    COUNTER = "counter"      # Счетчик (увеличивается)
    GAUGE = "gauge"         # Гейдж (текущее значение)
    HISTOGRAM = "histogram" # Гистограмма (распределение значений)
    TIMER = "timer"         # Таймер (время выполнения)

@dataclass
class Metric:
    """Метрика."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str]
    metric_type: MetricType

@dataclass
class CommandMetrics:
    """Метрики команды."""
    command: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    error_count: int = 0
    last_call: float = 0.0
    recent_times: List[float] = None
    
    def __post_init__(self):
        if self.recent_times is None:
            self.recent_times = []
    
    def add_call(self, execution_time: float, error: bool = False) -> None:
        """Добавляет вызов команды."""
        self.total_calls += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.last_call = time.time()
        
        if error:
            self.error_count += 1
        
        # Храним последние 100 измерений для статистики
        self.recent_times.append(execution_time)
        if len(self.recent_times) > 100:
            self.recent_times.pop(0)
        
        self.avg_time = self.total_time / self.total_calls
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по команде."""
        if not self.recent_times:
            return {
                'command': self.command,
                'total_calls': self.total_calls,
                'avg_time': 0.0,
                'min_time': 0.0,
                'max_time': 0.0,
                'error_count': self.error_count,
                'error_rate': 0.0,
                'p95_time': 0.0,
                'p99_time': 0.0
            }
        
        p95 = statistics.quantiles(self.recent_times, n=20)[-1] if len(self.recent_times) >= 20 else 0.0
        p99 = statistics.quantiles(self.recent_times, n=100)[-1] if len(self.recent_times) >= 100 else 0.0
        
        return {
            'command': self.command,
            'total_calls': self.total_calls,
            'avg_time': round(self.avg_time, 3),
            'min_time': round(self.min_time, 3),
            'max_time': round(self.max_time, 3),
            'error_count': self.error_count,
            'error_rate': round((self.error_count / self.total_calls) * 100, 2) if self.total_calls > 0 else 0.0,
            'p95_time': round(p95, 3),
            'p99_time': round(p99, 3),
            'last_call': datetime.fromtimestamp(self.last_call).isoformat() if self.last_call > 0 else None
        }

class MetricsCollector:
    """Сборщик метрик."""
    
    def __init__(self, max_metrics: int = 10000, collection_interval: int = 60):
        self.max_metrics = max_metrics
        self.collection_interval = collection_interval
        
        # Хранилище метрик
        self.metrics: deque = deque(maxlen=max_metrics)
        self.command_metrics: Dict[str, CommandMetrics] = {}
        
        # Системные метрики
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': {'bytes_sent': 0, 'bytes_recv': 0},
            'process_count': 0
        }
        
        # Статистика использования
        self.usage_stats = {
            'total_commands': 0,
            'active_users': set(),
            'active_chats': set(),
            'start_time': time.time(),
            'uptime': 0
        }
        
        # Конфигурация
        self.collectors: List[Callable] = []
        self.exporters: List[Callable] = []
        
        # Состояние
        self._running = False
        self._lock = threading.Lock()
        self._task: Optional[asyncio.Task] = None
        
        # Инициализация
        self._init_collectors()
    
    def _init_collectors(self) -> None:
        """Инициализирует встроенные сборщики метрик."""
        self.add_collector(self._collect_system_metrics)
        self.add_collector(self._collect_usage_stats)
    
    def add_collector(self, collector_func: Callable) -> None:
        """Добавляет функцию-сборщик метрик."""
        self.collectors.append(collector_func)
    
    def add_exporter(self, exporter_func: Callable) -> None:
        """Добавляет функцию-экспортёра метрик."""
        self.exporters.append(exporter_func)
    
    def start(self) -> None:
        """Запускает сбор метрик."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("📊 Сбор метрик запущен")
    
    def stop(self) -> None:
        """Останавливает сбор метрик."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                asyncio.get_event_loop().run_until_complete(self._task)
            except asyncio.CancelledError:
                pass
        logger.info("📊 Сбор метрик остановлен")
    
    async def _collection_loop(self) -> None:
        """Цикл сбора метрик."""
        while self._running:
            try:
                await self._collect_all_metrics()
                await self._export_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле сбора метрик: {e}")
                await asyncio.sleep(5)  # Пауза перед повторной попыткой
    
    async def _collect_all_metrics(self) -> None:
        """Собирает все метрики."""
        for collector in self.collectors:
            try:
                await asyncio.to_thread(collector)
            except Exception as e:
                logger.error(f"❌ Ошибка в сборщике метрик {collector.__name__}: {e}")
    
    async def _export_metrics(self) -> None:
        """Экспортирует метрики."""
        for exporter in self.exporters:
            try:
                await asyncio.to_thread(exporter)
            except Exception as e:
                logger.error(f"❌ Ошибка в экспортёре метрик {exporter.__name__}: {e}")
    
    def _collect_system_metrics(self) -> None:
        """Собирает системные метрики."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Update internal stats
            self.system_metrics.update({
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_io': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process_count': process_count
            })
            
            # Store as metrics
            timestamp = time.time()
            self._add_metric("system.cpu.usage", cpu_usage, {"unit": "percent"})
            self._add_metric("system.memory.usage", memory_usage, {"unit": "percent"})
            self._add_metric("system.disk.usage", disk_usage, {"unit": "percent"})
            self._add_metric("system.process.count", process_count, {})
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сборе системных метрик: {e}")
    
    def _collect_usage_stats(self) -> None:
        """Собирает статистику использования."""
        current_time = time.time()
        self.usage_stats['uptime'] = current_time - self.usage_stats['start_time']
        
        # Store as metrics
        self._add_metric("bot.uptime", self.usage_stats['uptime'], {"unit": "seconds"})
        self._add_metric("bot.active_users", len(self.usage_stats['active_users']), {})
        self._add_metric("bot.active_chats", len(self.usage_stats['active_chats']), {})
        self._add_metric("bot.total_commands", self.usage_stats['total_commands'], {})
    
    def _add_metric(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Добавляет метрику."""
        if tags is None:
            tags = {}
        
        metric = Metric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags,
            metric_type=MetricType.GAUGE
        )
        
        with self._lock:
            self.metrics.append(metric)
    
    def record_command_call(self, command: str, execution_time: float, error: bool = False, 
                          user_id: Optional[int] = None, chat_id: Optional[int] = None) -> None:
        """Фиксирует вызов команды."""
        with self._lock:
            # Обновляем статистику использования
            self.usage_stats['total_commands'] += 1
            if user_id:
                self.usage_stats['active_users'].add(user_id)
            if chat_id:
                self.usage_stats['active_chats'].add(chat_id)
            
            # Обновляем метрики команды
            if command not in self.command_metrics:
                self.command_metrics[command] = CommandMetrics(command=command)
            
            self.command_metrics[command].add_call(execution_time, error)
    
    def get_command_stats(self, command: Optional[str] = None) -> Dict[str, Any]:
        """Возвращает статистику по командам."""
        with self._lock:
            if command:
                if command in self.command_metrics:
                    return self.command_metrics[command].get_stats()
                return {}
            
            return {
                cmd: metrics.get_stats() 
                for cmd, metrics in self.command_metrics.items()
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Возвращает системную статистику."""
        with self._lock:
            return {
                **self.system_metrics,
                'bot_info': {
                    'python_version': sys.version,
                    'platform': platform.platform(),
                    'bot_uptime': self.usage_stats['uptime'],
                    'start_time': datetime.fromtimestamp(self.usage_stats['start_time']).isoformat()
                }
            }
    
    def get_recent_metrics(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает недавние метрики по имени."""
        with self._lock:
            recent_metrics = [
                asdict(m) for m in reversed(self.metrics) 
                if m.name == name
            ][:limit]
            return recent_metrics
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по метрикам."""
        with self._lock:
            # Подсчет метрик по типам
            metric_counts = defaultdict(int)
            for metric in self.metrics:
                metric_counts[metric.name] += 1
            
            return {
                'total_metrics': len(self.metrics),
                'metric_types': dict(metric_counts),
                'command_stats': self.get_command_stats(),
                'system_stats': self.get_system_stats(),
                'usage_stats': {
                    'total_commands': self.usage_stats['total_commands'],
                    'active_users': len(self.usage_stats['active_users']),
                    'active_chats': len(self.usage_stats['active_chats']),
                    'uptime': self.usage_stats['uptime']
                }
            }
    
    def export_to_json(self, filepath: str) -> None:
        """Экспортирует метрики в JSON файл."""
        try:
            data = {
                'timestamp': time.time(),
                'summary': self.get_metrics_summary(),
                'raw_metrics': [asdict(m) for m in self.metrics]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Метрики экспортированы в {filepath}")
        except Exception as e:
            logger.error(f"❌ Ошибка при экспорте метрик в JSON: {e}")
    
    def export_to_prometheus(self) -> str:
        """Экспортирует метрики в формате Prometheus."""
        try:
            lines = []
            
            # Системные метрики
            for key, value in self.system_metrics.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        lines.append(f"bot_system_{key}_{subkey} {subvalue}")
                else:
                    lines.append(f"bot_system_{key} {value}")
            
            # Статистика использования
            for key, value in self.usage_stats.items():
                if key in ['active_users', 'active_chats']:
                    lines.append(f"bot_usage_{key} {len(value)}")
                elif key != 'start_time':  # Пропускаем start_time как set
                    lines.append(f"bot_usage_{key} {value}")
            
            # Метрики команд
            for cmd, metrics in self.command_metrics.items():
                stats = metrics.get_stats()
                for key, value in stats.items():
                    if key != 'command' and key != 'last_call':
                        lines.append(f"bot_command_{cmd}_{key} {value}")
            
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"❌ Ошибка при экспорте в Prometheus: {e}")
            return ""
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Генерирует отчет о производительности."""
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            # Фильтрация метрик по времени
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            
            # Анализ команд
            command_analysis = {}
            for cmd, metrics in self.command_metrics.items():
                if metrics.last_call >= cutoff_time:
                    stats = metrics.get_stats()
                    command_analysis[cmd] = stats
            
            # Анализ системных метрик
            cpu_metrics = [m.value for m in recent_metrics if m.name == "system.cpu.usage"]
            memory_metrics = [m.value for m in recent_metrics if m.name == "system.memory.usage"]
            
            system_analysis = {
                'cpu_avg': statistics.mean(cpu_metrics) if cpu_metrics else 0,
                'cpu_max': max(cpu_metrics) if cpu_metrics else 0,
                'memory_avg': statistics.mean(memory_metrics) if memory_metrics else 0,
                'memory_max': max(memory_metrics) if memory_metrics else 0,
                'total_metrics': len(recent_metrics)
            }
            
            return {
                'period_hours': hours,
                'generated_at': datetime.now().isoformat(),
                'system_analysis': system_analysis,
                'command_analysis': command_analysis,
                'summary': {
                    'total_commands': sum(m.total_calls for m in self.command_metrics.values()),
                    'total_errors': sum(m.error_count for m in self.command_metrics.values()),
                    'avg_response_time': statistics.mean([
                        m.avg_time for m in self.command_metrics.values() 
                        if m.total_calls > 0
                    ]) if any(m.total_calls > 0 for m in self.command_metrics.values()) else 0
                }
            }

# Глобальный экземпляр сборщика метрик
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Возвращает глобальный экземпляр сборщика метрик."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

# Декоратор для измерения времени выполнения команд
def measure_performance(command_name: str):
    """Декоратор для измерения производительности команд."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            error = False
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = True
                raise e
            finally:
                execution_time = time.time() - start_time
                
                # Извлечение user_id и chat_id из аргументов
                user_id = None
                chat_id = None
                
                if args:
                    try:
                        # Предполагаем, что первый аргумент - это update
                        update = args[0]
                        if hasattr(update, 'effective_user') and update.effective_user:
                            user_id = update.effective_user.id
                        if hasattr(update, 'effective_chat') and update.effective_chat:
                            chat_id = update.effective_chat.id
                    except Exception:
                        pass
                
                collector.record_command_call(command_name, execution_time, error, user_id, chat_id)
        
        return wrapper
    return decorator

# Функции для удобного использования

def start_metrics_collection() -> None:
    """Запускает сбор метрик."""
    collector = get_metrics_collector()
    collector.start()

def stop_metrics_collection() -> None:
    """Останавливает сбор метрик."""
    collector = get_metrics_collector()
    collector.stop()

def get_performance_stats() -> Dict[str, Any]:
    """Возвращает статистику производительности."""
    collector = get_metrics_collector()
    return collector.get_metrics_summary()

def export_metrics_to_file(filepath: str) -> None:
    """Экспортирует метрики в файл."""
    collector = get_metrics_collector()
    collector.export_to_json(filepath)

def get_performance_report(hours: int = 24) -> Dict[str, Any]:
    """Генерирует отчет о производительности."""
    collector = get_metrics_collector()
    return collector.get_performance_report(hours)

# Пример использования в handlers/commands.py:
"""
@measure_performance("davka")
@handle_errors("davka")
async def handle_davka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ваш код команды давки
    pass
"""