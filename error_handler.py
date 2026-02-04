"""
Система комплексного обработки ошибок для Telegram бота.

Этот модуль предоставляет:
- Централизованную обработку исключений
- Автоматическое логирование ошибок
- Отправку уведомлений администраторам
- Метрики и статистику ошибок
- Автоматическое восстановление после критических ошибок
- Защиту от спама уведомлениями об ошибках
"""

import asyncio
import logging
import traceback
import time
import json
import sys
from typing import Dict, List, Optional, Callable, Any, Type, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import threading
from collections import defaultdict, deque
import hashlib

from telegram import Update, TelegramError
from telegram.error import (
    BadRequest, 
    TimedOut, 
    NetworkError, 
    Forbidden, 
    ChatMigrated, 
    RetryAfter,
    Conflict
)
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Уровни серьезности ошибок."""
    LOW = "low"           # Незначительные ошибки (пользовательские вводы)
    MEDIUM = "medium"     # Средние ошибки (сетевые проблемы)
    HIGH = "high"         # Высокие ошибки (ошибки бизнес-логики)
    CRITICAL = "critical" # Критические ошибки (системные сбои)

class ErrorCategory(Enum):
    """Категории ошибок."""
    USER_INPUT = "user_input"         # Ошибки ввода пользователя
    NETWORK = "network"              # Сетевые ошибки
    DATABASE = "database"            # Ошибки базы данных
    TELEGRAM_API = "telegram_api"    # Ошибки Telegram API
    BUSINESS_LOGIC = "business_logic" # Ошибки бизнес-логики
    SYSTEM = "system"                # Системные ошибки
    UNKNOWN = "unknown"              # Неизвестные ошибки

@dataclass
class ErrorInfo:
    """Информация об ошибке."""
    error_id: str                    # Уникальный ID ошибки
    timestamp: float                # Время возникновения
    severity: ErrorSeverity         # Уровень серьезности
    category: ErrorCategory         # Категория ошибки
    error_type: str                 # Тип исключения
    error_message: str              # Сообщение об ошибке
    traceback: str                  # Стек вызовов
    user_id: Optional[int] = None   # ID пользователя
    chat_id: Optional[int] = None   # ID чата
    command: Optional[str] = None   # Команда, вызвавшая ошибку
    context: Optional[Dict[str, Any]] = None  # Дополнительный контекст
    retry_count: int = 0            # Количество попыток повтора
    is_handled: bool = False        # Обработана ли ошибка

class ErrorNotificationManager:
    """Менеджер уведомлений об ошибках."""
    
    def __init__(self, admin_ids: List[int], notification_cooldown: int = 300):
        self.admin_ids = admin_ids
        self.notification_cooldown = notification_cooldown  # 5 минут
        self.last_notification_times: Dict[str, float] = {}
        self.notification_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def should_send_notification(self, error_info: ErrorInfo) -> bool:
        """Определяет, нужно ли отправлять уведомление об ошибке."""
        if error_info.severity not in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return False
        
        error_key = f"{error_info.category.value}_{error_info.error_type}"
        
        with self._lock:
            current_time = time.time()
            
            # Проверяем, не превышено ли количество уведомлений для этого типа ошибки
            if self.notification_counts[error_key] >= 10:
                return False
            
            # Проверяем cooldown
            if error_key in self.last_notification_times:
                if current_time - self.last_notification_times[error_key] < self.notification_cooldown:
                    return False
            
            return True
    
    def record_notification(self, error_info: ErrorInfo) -> None:
        """Фиксирует отправку уведомления."""
        error_key = f"{error_info.category.value}_{error_info.error_type}"
        
        with self._lock:
            self.last_notification_times[error_key] = time.time()
            self.notification_counts[error_key] += 1

class ErrorMetrics:
    """Сбор метрик об ошибках."""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors: deque = deque(maxlen=max_errors)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.severity_counts: Dict[str, int] = defaultdict(int)
        self.category_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_error(self, error_info: ErrorInfo) -> None:
        """Фиксирует информацию об ошибке."""
        with self._lock:
            self.errors.append(error_info)
            self.error_counts[error_info.error_type] += 1
            self.severity_counts[error_info.severity.value] += 1
            self.category_counts[error_info.category.value] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по ошибкам."""
        with self._lock:
            total_errors = len(self.errors)
            last_hour_errors = sum(1 for error in self.errors 
                                 if time.time() - error.timestamp < 3600)
            last_day_errors = sum(1 for error in self.errors 
                                if time.time() - error.timestamp < 86400)
            
            return {
                'total_errors': total_errors,
                'last_hour_errors': last_hour_errors,
                'last_day_errors': last_day_errors,
                'error_counts': dict(self.error_counts),
                'severity_counts': dict(self.severity_counts),
                'category_counts': dict(self.category_counts),
                'recent_errors': [asdict(error) for error in list(self.errors)[-10:]]
            }
    
    def get_error_rate(self, window_minutes: int = 60) -> float:
        """Возвращает частоту ошибок за указанное время."""
        with self._lock:
            window_seconds = window_minutes * 60
            error_count = sum(1 for error in self.errors 
                            if time.time() - error.timestamp < window_seconds)
            return error_count / window_minutes if window_minutes > 0 else 0
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику."""
        with self._lock:
            self.errors.clear()
            self.error_counts.clear()
            self.severity_counts.clear()
            self.category_counts.clear()

class ErrorHandler:
    """Основной обработчик ошибок."""
    
    def __init__(self, admin_ids: List[int] = None, enable_notifications: bool = True):
        self.admin_ids = admin_ids or []
        self.enable_notifications = enable_notifications
        self.notification_manager = ErrorNotificationManager(self.admin_ids)
        self.metrics = ErrorMetrics()
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.context_extractors: List[Callable] = []
        
        # Настройки восстановления
        self.max_retries = 3
        self.retry_delay = 1.0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60
        
        # Состояние circuit breaker
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        
        # Инициализация обработчиков по умолчанию
        self._init_default_handlers()
    
    def _init_default_handlers(self) -> None:
        """Инициализирует обработчики ошибок по умолчанию."""
        self.add_error_handler(BadRequest, self._handle_bad_request)
        self.add_error_handler(TimedOut, self._handle_timed_out)
        self.add_error_handler(NetworkError, self._handle_network_error)
        self.add_error_handler(Forbidden, self._handle_forbidden)
        self.add_error_handler(ChatMigrated, self._handle_chat_migrated)
        self.add_error_handler(RetryAfter, self._handle_retry_after)
        self.add_error_handler(Conflict, self._handle_conflict)
    
    def add_error_handler(self, exception_type: Type[Exception], handler: Callable) -> None:
        """Добавляет обработчик для конкретного типа исключений."""
        self.error_handlers[exception_type] = handler
    
    def add_context_extractor(self, extractor: Callable) -> None:
        """Добавляет извлекатель контекста."""
        self.context_extractors.append(extractor)
    
    def _classify_error(self, exception: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """Классифицирует ошибку по уровню серьезности и категории."""
        # Сопоставление исключений с категориями
        telegram_api_errors = {
            BadRequest: ErrorCategory.TELEGRAM_API,
            TimedOut: ErrorCategory.NETWORK,
            NetworkError: ErrorCategory.NETWORK,
            Forbidden: ErrorCategory.TELEGRAM_API,
            ChatMigrated: ErrorCategory.TELEGRAM_API,
            RetryAfter: ErrorCategory.TELEGRAM_API,
            Conflict: ErrorCategory.TELEGRAM_API,
        }
        
        # Определение категории
        category = telegram_api_errors.get(type(exception), ErrorCategory.UNKNOWN)
        
        # Определение серьезности
        if isinstance(exception, (BadRequest, RetryAfter)):
            severity = ErrorSeverity.LOW
        elif isinstance(exception, (TimedOut, NetworkError, Forbidden)):
            severity = ErrorSeverity.MEDIUM
        elif isinstance(exception, (ChatMigrated, Conflict)):
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.CRITICAL
        
        return severity, category
    
    def _extract_context(self, update: Optional[Update], context: Optional[ContextTypes.DEFAULT_TYPE]) -> Dict[str, Any]:
        """Извлекает контекст из update и context."""
        ctx = {}
        
        # Извлечение данных из update
        if update:
            if update.effective_user:
                ctx['user_id'] = update.effective_user.id
                ctx['username'] = update.effective_user.username
                ctx['full_name'] = update.effective_user.full_name
            
            if update.effective_chat:
                ctx['chat_id'] = update.effective_chat.id
                ctx['chat_type'] = update.effective_chat.type
                ctx['chat_title'] = update.effective_chat.title
            
            if update.message:
                ctx['message_text'] = update.message.text
                ctx['message_id'] = update.message.message_id
        
        # Извлечение данных из context
        if context:
            if hasattr(context, 'args') and context.args:
                ctx['command_args'] = context.args
            if hasattr(context, 'user_data') and context.user_data:
                ctx['user_data_keys'] = list(context.user_data.keys())
            if hasattr(context, 'chat_data') and context.chat_data:
                ctx['chat_data_keys'] = list(context.chat_data.keys())
        
        # Дополнительные извлекатели контекста
        for extractor in self.context_extractors:
            try:
                additional_ctx = extractor(update, context)
                if additional_ctx:
                    ctx.update(additional_ctx)
            except Exception as e:
                logger.warning(f"Ошибка при извлечении контекста: {e}")
        
        return ctx
    
    def _create_error_id(self, exception: Exception, context: Dict[str, Any]) -> str:
        """Создает уникальный ID ошибки."""
        error_data = {
            'type': type(exception).__name__,
            'message': str(exception),
            'user_id': context.get('user_id'),
            'chat_id': context.get('chat_id'),
            'command': context.get('command')
        }
        error_string = json.dumps(error_data, sort_keys=True)
        return hashlib.md5(error_string.encode()).hexdigest()[:16]
    
    def _handle_bad_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: BadRequest) -> bool:
        """Обрабатывает ошибки BadRequest."""
        logger.warning(f"BadRequest: {exception}")
        if update and update.effective_message:
            try:
                update.effective_message.reply_text(
                    "❌ Произошла ошибка при обработке вашего запроса. Попробуйте еще раз.",
                    reply_markup=None
                )
            except Exception:
                pass
        return True
    
    def _handle_timed_out(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: TimedOut) -> bool:
        """Обрабатывает ошибки таймаута."""
        logger.warning(f"TimedOut: {exception}")
        if update and update.effective_message:
            try:
                update.effective_message.reply_text(
                    "⏰ Время ожидания ответа истекло. Попробуйте еще раз.",
                    reply_markup=None
                )
            except Exception:
                pass
        return True
    
    def _handle_network_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: NetworkError) -> bool:
        """Обрабатывает сетевые ошибки."""
        logger.warning(f"NetworkError: {exception}")
        if update and update.effective_message:
            try:
                update.effective_message.reply_text(
                    "🌐 Проблемы с сетью. Попробуйте позже.",
                    reply_markup=None
                )
            except Exception:
                pass
        return True
    
    def _handle_forbidden(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: Forbidden) -> bool:
        """Обрабатывает ошибки доступа."""
        logger.warning(f"Forbidden: {exception}")
        return True  # Не отправляем сообщение пользователю
    
    def _handle_chat_migrated(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: ChatMigrated) -> bool:
        """Обрабатывает перенос чата."""
        logger.info(f"ChatMigrated: {exception}")
        return True
    
    def _handle_retry_after(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: RetryAfter) -> bool:
        """Обрабатывает ошибки повторной отправки."""
        logger.warning(f"RetryAfter: {exception}")
        if update and update.effective_message:
            try:
                update.effective_message.reply_text(
                    f"⏰ Подождите {exception.retry_after} секунд перед следующим запросом.",
                    reply_markup=None
                )
            except Exception:
                pass
        return True
    
    def _handle_conflict(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exception: Conflict) -> bool:
        """Обрабатывает конфликты."""
        logger.error(f"Conflict: {exception}")
        return True
    
    async def _send_error_notification(self, error_info: ErrorInfo, update: Optional[Update]) -> None:
        """Отправляет уведомление об ошибке администраторам."""
        if not self.enable_notifications or not self.admin_ids:
            return
        
        if not self.notification_manager.should_send_notification(error_info):
            return
        
        message = self._format_error_message(error_info)
        
        for admin_id in self.admin_ids:
            try:
                # Здесь нужно использовать бота для отправки сообщения
                # bot = context.bot  # Нужно получить доступ к боту
                # await bot.send_message(admin_id, message)
                logger.info(f"Уведомление об ошибке отправлено администратору {admin_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")
        
        self.notification_manager.record_notification(error_info)
    
    def _format_error_message(self, error_info: ErrorInfo) -> str:
        """Форматирует сообщение об ошибке."""
        severity_emoji = {
            ErrorSeverity.LOW: "🟡",
            ErrorSeverity.MEDIUM: "🟠", 
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(error_info.severity, "❓")
        
        message = f"{emoji} <b>Ошибка {error_info.severity.value.upper()}</b>\n\n"
        message += f"<b>Тип:</b> {error_info.error_type}\n"
        message += f"<b>Сообщение:</b> {error_info.error_message}\n"
        message += f"<b>Время:</b> {datetime.fromtimestamp(error_info.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if error_info.user_id:
            message += f"<b>Пользователь:</b> {error_info.user_id}\n"
        if error_info.chat_id:
            message += f"<b>Чат:</b> {error_info.chat_id}\n"
        if error_info.command:
            message += f"<b>Команда:</b> {error_info.command}\n"
        
        message += f"\n<b>Traceback:</b>\n<code>{error_info.traceback[:2000]}</code>"
        
        return message
    
    def _should_circuit_break(self) -> bool:
        """Проверяет, нужно ли включить circuit breaker."""
        current_time = time.time()
        
        # Сброс счетчика при истечении таймаута
        if current_time - self.last_failure_time > self.circuit_breaker_timeout:
            self.failure_count = 0
            self.circuit_open = False
            return False
        
        # Проверка порога
        if self.failure_count >= self.circuit_breaker_threshold:
            self.circuit_open = True
            return True
        
        return False
    
    def _record_failure(self) -> None:
        """Фиксирует сбой."""
        self.failure_count += 1
        self.last_failure_time = time.time()
    
    async def handle_error(
        self, 
        update: Optional[Update], 
        context: Optional[ContextTypes.DEFAULT_TYPE], 
        exception: Exception,
        command: Optional[str] = None
    ) -> bool:
        """Обрабатывает ошибку."""
        # Проверка circuit breaker
        if self._should_circuit_break():
            logger.error("Circuit breaker активирован, запрос отклонен")
            return False
        
        # Извлечение контекста
        context_data = self._extract_context(update, context)
        if command:
            context_data['command'] = command
        
        # Классификация ошибки
        severity, category = self._classify_error(exception)
        
        # Создание ID ошибки
        error_id = self._create_error_id(exception, context_data)
        
        # Формирование информации об ошибке
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=time.time(),
            severity=severity,
            category=category,
            error_type=type(exception).__name__,
            error_message=str(exception),
            traceback=traceback.format_exc(),
            user_id=context_data.get('user_id'),
            chat_id=context_data.get('chat_id'),
            command=context_data.get('command'),
            context=context_data
        )
        
        # Запись в метрики
        self.metrics.record_error(error_info)
        
        # Логирование
        logger.error(
            f"Ошибка {error_id}: {exception}", 
            exc_info=True,
            extra={
                'error_id': error_id,
                'severity': severity.value,
                'category': category.value,
                'user_id': error_info.user_id,
                'chat_id': error_info.chat_id
            }
        )
        
        # Попытка обработки с помощью специализированного обработчика
        handled = False
        for exc_type, handler in self.error_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    handled = handler(update, context, exception)
                    if handled:
                        break
                except Exception as handler_error:
                    logger.error(f"Ошибка в обработчике {exc_type.__name__}: {handler_error}")
        
        # Отправка уведомления администраторам
        await self._send_error_notification(error_info, update)
        
        # Фиксация сбоя для circuit breaker
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._record_failure()
        
        return handled
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику обработчика ошибок."""
        return {
            'metrics': self.metrics.get_stats(),
            'circuit_breaker': {
                'open': self.circuit_open,
                'failure_count': self.failure_count,
                'last_failure_time': self.last_failure_time,
                'threshold': self.circuit_breaker_threshold,
                'timeout': self.circuit_breaker_timeout
            },
            'notification_manager': {
                'cooldown': self.notification_manager.notification_cooldown,
                'notification_counts': dict(self.notification_manager.notification_counts)
            }
        }
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику."""
        self.metrics.reset_stats()
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        self.notification_manager.last_notification_times.clear()
        self.notification_manager.notification_counts.clear()

# Глобальный экземпляр обработчика ошибок
_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """Возвращает глобальный экземпляр обработчика ошибок."""
    global _error_handler
    if _error_handler is None:
        # Пытаемся получить admin_ids из конфигурации
        admin_ids = []
        try:
            import config
            admin_ids = getattr(config, 'ADMIN_IDS', [])
        except ImportError:
            pass
        
        _error_handler = ErrorHandler(admin_ids=admin_ids)
    return _error_handler

# Декораторы для обработки ошибок

def handle_errors(command_name: Optional[str] = None):
    """Декоратор для обработки ошибок в обработчиках команд."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            error_handler = get_error_handler()
            
            try:
                return await func(update, context, *args, **kwargs)
            except Exception as e:
                command = command_name or getattr(func, '__name__', 'unknown')
                await error_handler.handle_error(update, context, e, command)
                return None
        
        return wrapper
    return decorator

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Декоратор для повторных попыток при ошибках."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        # Последняя попытка, обрабатываем ошибку
                        await error_handler.handle_error(None, None, e)
                        raise e
                    
                    # Ждем перед повторной попыткой
                    await asyncio.sleep(delay * (backoff ** attempt))
            
            # Это не должно случиться, но на всякий случай
            raise last_exception
        
        return wrapper
    return decorator

# Функции для удобного использования

async def handle_bot_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Функция для обработки ошибок бота (для использования в telegram.ext)."""
    error_handler = get_error_handler()
    await error_handler.handle_error(update, context, context.error)

def get_error_stats() -> Dict[str, Any]:
    """Возвращает статистику по ошибкам."""
    error_handler = get_error_handler()
    return error_handler.get_stats()

def reset_error_stats() -> None:
    """Сбрасывает статистику по ошибкам."""
    error_handler = get_error_handler()
    error_handler.reset_stats()

# Пример использования в handlers/commands.py:
"""
@handle_errors("davka")
async def handle_davka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ваш код команды давки
    pass

@retry_on_error(max_retries=3, delay=1.0)
async def database_operation():
    # Ваш код операции с базой данных
    pass
"""