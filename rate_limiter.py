"""
Система ограничения частоты запросов (Rate Limiting) для Telegram бота.

Этот модуль предоставляет:
- Защиту от спама и abuse
- Разные лимиты для разных типов команд
- Поддержку Redis и локального fallback
- Гибкую настройку лимитов
- Статистику использования
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Типы лимитов."""
    GLOBAL = "global"           # Глобальный лимит для всех команд
    COMMAND = "command"         # Лимит для конкретной команды
    USER = "user"              # Лимит для конкретного пользователя
    CHAT = "chat"              # Лимит для конкретного чата
    USER_COMMAND = "user_command"  # Лимит для пользователя + команда
    USER_CHAT = "user_chat"    # Лимит для пользователя в чате

@dataclass
class RateLimitConfig:
    """Конфигурация лимита."""
    limit: int                    # Максимальное количество запросов
    window_seconds: int          # Временное окно в секундах
    block_duration: int = 300    # Время блокировки в секундах (по умолчанию 5 минут)
    enabled: bool = True         # Включен ли лимит

@dataclass
class RateLimitResult:
    """Результат проверки лимита."""
    allowed: bool               # Разрешен ли запрос
    remaining: int             # Оставшиеся запросы
    reset_time: int            # Время сброса лимита
    retry_after: Optional[int] = None  # Время ожидания до следующей попытки
    limit_type: Optional[str] = None   # Тип сработавшего лимита

class LocalRateLimiter:
    """Локальный рейт-лимитер с поддержкой разных типов лимитов."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._limits: Dict[str, RateLimitConfig] = {}
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._blocked: Dict[str, int] = {}  # user_id: block_until
        self._lock = threading.RLock()
        self._stats = {
            'checks': 0,
            'blocked': 0,
            'allowed': 0,
            'blocked_users': 0
        }
    
    def add_limit(self, limit_key: str, config: RateLimitConfig) -> None:
        """Добавляет новый лимит."""
        with self._lock:
            self._limits[limit_key] = config
            logger.info(f"➕ Добавлен лимит: {limit_key} - {config.limit}/{config.window_seconds}s")
    
    def remove_limit(self, limit_key: str) -> None:
        """Удаляет лимит."""
        with self._lock:
            if limit_key in self._limits:
                del self._limits[limit_key]
                logger.info(f"➖ Удален лимит: {limit_key}")
    
    def is_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь."""
        with self._lock:
            current_time = time.time()
            if user_id in self._blocked:
                if current_time < self._blocked[user_id]:
                    return True
                else:
                    del self._blocked[user_id]
            return False
    
    def block_user(self, user_id: int, duration: int) -> None:
        """Блокирует пользователя на указанное время."""
        with self._lock:
            block_until = time.time() + duration
            self._blocked[user_id] = block_until
            self._stats['blocked_users'] += 1
            logger.warning(f"🚫 Пользователь {user_id} заблокирован на {duration} секунд")
    
    def unblock_user(self, user_id: int) -> bool:
        """Разблокирует пользователя."""
        with self._lock:
            if user_id in self._blocked:
                del self._blocked[user_id]
                logger.info(f"✅ Пользователь {user_id} разблокирован")
                return True
            return False
    
    def check_limit(self, user_id: int, chat_id: int, command: str) -> RateLimitResult:
        """Проверяет лимиты для пользователя."""
        with self._lock:
            self._stats['checks'] += 1
            current_time = time.time()
            
            # Проверяем блокировку
            if self.is_blocked(user_id):
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=int(current_time) + 60,
                    retry_after=60,
                    limit_type="blocked"
                )
            
            # Собираем все возможные ключи для проверки
            limit_keys = [
                f"{RateLimitType.GLOBAL.value}:*",
                f"{RateLimitType.COMMAND.value}:{command}",
                f"{RateLimitType.USER.value}:{user_id}",
                f"{RateLimitType.CHAT.value}:{chat_id}",
                f"{RateLimitType.USER_COMMAND.value}:{user_id}:{command}",
                f"{RateLimitType.USER_CHAT.value}:{user_id}:{chat_id}"
            ]
            
            # Проверяем каждый активный лимит
            for limit_key in limit_keys:
                if limit_key not in self._limits:
                    continue
                
                config = self._limits[limit_key]
                if not config.enabled:
                    continue
                
                # Получаем очередь запросов для этого лимита
                requests = self._requests[limit_key]
                
                # Удаляем старые запросы
                cutoff_time = current_time - config.window_seconds
                while requests and requests[0] <= cutoff_time:
                    requests.popleft()
                
                # Проверяем лимит
                if len(requests) >= config.limit:
                    # Лимит превышен
                    self._stats['blocked'] += 1
                    reset_time = requests[0] + config.window_seconds if requests else current_time + config.window_seconds
                    
                    # Блокируем пользователя при многократном превышении
                    if len(requests) >= config.limit * 2:
                        self.block_user(user_id, config.block_duration)
                    
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=int(reset_time),
                        retry_after=max(0, int(reset_time - current_time)),
                        limit_type=limit_key
                    )
            
            # Если лимит не превышен, добавляем запрос
            for limit_key in limit_keys:
                if limit_key in self._limits and self._limits[limit_key].enabled:
                    self._requests[limit_key].append(current_time)
            
            self._stats['allowed'] += 1
            
            # Ограничиваем размер очередей
            self._cleanup_queues()
            
            return RateLimitResult(
                allowed=True,
                remaining=max(0, config.limit - len(self._requests[limit_keys[0]]) if limit_keys[0] in self._requests else config.limit),
                reset_time=int(current_time + config.window_seconds),
                limit_type=None
            )
    
    def _cleanup_queues(self) -> None:
        """Очищает старые запросы из очередей."""
        current_time = time.time()
        
        # Ограничиваем общее количество ключей
        if len(self._requests) > self.max_size:
            # Удаляем самые старые ключи
            sorted_keys = sorted(self._requests.keys(), key=lambda k: max(self._requests[k]) if self._requests[k] else 0)
            keys_to_remove = sorted_keys[:len(self._requests) - self.max_size]
            for key in keys_to_remove:
                del self._requests[key]
        
        # Очищаем пустые очереди
        empty_keys = [k for k, v in self._requests.items() if not v]
        for key in empty_keys:
            del self._requests[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования."""
        with self._lock:
            return {
                **self._stats,
                'active_limits': len(self._limits),
                'active_queues': len(self._requests),
                'blocked_users_count': len(self._blocked),
                'blocked_users': list(self._blocked.keys())
            }
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику."""
        with self._lock:
            self._stats = {
                'checks': 0,
                'blocked': 0,
                'allowed': 0,
                'blocked_users': 0
            }
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Возвращает статистику по пользователю."""
        with self._lock:
            user_queues = {k: list(v) for k, v in self._requests.items() if f":{user_id}:" in k or k.endswith(f":{user_id}")}
            return {
                'user_id': user_id,
                'is_blocked': self.is_blocked(user_id),
                'active_queues': len(user_queues),
                'user_queues': user_queues,
                'blocked_until': self._blocked.get(user_id, 0)
            }

class RedisRateLimiter:
    """Redis-реализация рейт-лимитера."""
    
    def __init__(self, redis_client, prefix: str = "rate_limit:"):
        self.redis = redis_client
        self.prefix = prefix
        self._lock = asyncio.Lock()
    
    async def check_limit(self, user_id: int, chat_id: int, command: str, config: RateLimitConfig) -> RateLimitResult:
        """Проверяет лимит с использованием Redis."""
        try:
            current_time = time.time()
            key = f"{self.prefix}{user_id}:{chat_id}:{command}"
            
            # Используем Redis Lua скрипт для атомарной проверки и обновления
            lua_script = """
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            local cutoff_time = current_time - window
            
            -- Удаляем старые записи
            redis.call('ZREMRANGEBYSCORE', key, 0, cutoff_time)
            
            -- Получаем текущее количество запросов
            local current_count = redis.call('ZCARD', key)
            
            if current_count >= limit then
                -- Лимит превышен
                local oldest_request = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local reset_time = tonumber(oldest_request[2]) + window
                return {0, current_count, reset_time}
            else
                -- Добавляем новый запрос
                redis.call('ZADD', key, current_time, current_time .. ':' .. math.random(1000000))
                redis.call('EXPIRE', key, window)
                return {1, current_count + 1, current_time + window}
            end
            """
            
            result = await self.redis.eval(lua_script, 1, key, config.limit, config.window_seconds, current_time)
            
            allowed = bool(result[0])
            current_count = int(result[1])
            reset_time = float(result[2])
            
            if allowed:
                return RateLimitResult(
                    allowed=True,
                    remaining=config.limit - current_count,
                    reset_time=int(reset_time)
                )
            else:
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=int(reset_time),
                    retry_after=max(0, int(reset_time - current_time))
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка Redis при проверке лимита: {e}")
            # Fallback на разрешение запроса при ошибке Redis
            return RateLimitResult(
                allowed=True,
                remaining=config.limit,
                reset_time=int(current_time + config.window_seconds)
            )

class RateLimiter:
    """Основной класс системы рейт-лимитинга."""
    
    def __init__(self, use_redis: bool = True, redis_client = None):
        self.use_redis = use_redis
        self.redis_client = redis_client
        self.local_limiter = LocalRateLimiter()
        
        # Конфигурация лимитов по умолчанию
        self.default_limits = {
            "global:*": RateLimitConfig(limit=100, window_seconds=60, block_duration=300),
            "command:davka": RateLimitConfig(limit=5, window_seconds=300, block_duration=600),  # 5 раз в 5 минут
            "command:uletet": RateLimitConfig(limit=10, window_seconds=60, block_duration=300),  # 10 раз в минуту
            "command:rademka": RateLimitConfig(limit=3, window_seconds=600, block_duration=900),  # 3 раза в 10 минут
            "command:stats": RateLimitConfig(limit=20, window_seconds=60, block_duration=300),   # 20 раз в минуту
            "user:*": RateLimitConfig(limit=50, window_seconds=60, block_duration=300),          # 50 запросов в минуту на пользователя
            "user_command:*": RateLimitConfig(limit=10, window_seconds=300, block_duration=600), # 10 раз в 5 минут на пользователя+команду
        }
        
        # Инициализируем лимиты по умолчанию
        self._init_default_limits()
    
    def _init_default_limits(self) -> None:
        """Инициализирует лимиты по умолчанию."""
        for limit_key, config in self.default_limits.items():
            self.local_limiter.add_limit(limit_key, config)
    
    def add_limit(self, limit_key: str, config: RateLimitConfig) -> None:
        """Добавляет новый лимит."""
        self.local_limiter.add_limit(limit_key, config)
        self.default_limits[limit_key] = config
    
    def remove_limit(self, limit_key: str) -> None:
        """Удаляет лимит."""
        self.local_limiter.remove_limit(limit_key)
        if limit_key in self.default_limits:
            del self.default_limits[limit_key]
    
    def update_limit(self, limit_key: str, config: RateLimitConfig) -> None:
        """Обновляет существующий лимит."""
        self.local_limiter.add_limit(limit_key, config)
        self.default_limits[limit_key] = config
    
    def is_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь."""
        return self.local_limiter.is_blocked(user_id)
    
    def block_user(self, user_id: int, duration: int = 300) -> None:
        """Блокирует пользователя."""
        self.local_limiter.block_user(user_id, duration)
    
    def unblock_user(self, user_id: int) -> bool:
        """Разблокирует пользователя."""
        return self.local_limiter.unblock_user(user_id)
    
    async def check_rate_limit(self, user_id: int, chat_id: int, command: str) -> RateLimitResult:
        """Проверяет лимиты для пользователя."""
        # Сначала проверяем блокировку
        if self.local_limiter.is_blocked(user_id):
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=int(time.time()) + 60,
                retry_after=60,
                limit_type="blocked"
            )
        
        # Проверяем лимиты
        if self.use_redis and self.redis_client:
            try:
                # Пытаемся использовать Redis для наиболее строгих лимитов
                strict_limits = ["command:davka", "command:rademka"]
                for limit_key in strict_limits:
                    if limit_key in self.default_limits:
                        config = self.default_limits[limit_key]
                        result = await self.redis_client.check_limit(user_id, chat_id, command, config)
                        if not result.allowed:
                            return result
            except Exception as e:
                logger.warning(f"⚠️ Ошибка Redis, используем локальный лимитер: {e}")
        
        # Используем локальный лимитер
        return self.local_limiter.check_limit(user_id, chat_id, command)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования."""
        local_stats = self.local_limiter.get_stats()
        return {
            **local_stats,
            'use_redis': self.use_redis,
            'redis_available': self.redis_client is not None,
            'default_limits_count': len(self.default_limits)
        }
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Возвращает статистику по пользователю."""
        return self.local_limiter.get_user_stats(user_id)
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику."""
        self.local_limiter.reset_stats()
    
    def get_active_users(self) -> List[int]:
        """Возвращает список активных пользователей."""
        user_ids = set()
        for key in self.local_limiter._requests.keys():
            parts = key.split(':')
            if len(parts) >= 2:
                try:
                    user_id = int(parts[1])
                    user_ids.add(user_id)
                except ValueError:
                    pass
        return list(user_ids)
    
    def cleanup_old_data(self) -> None:
        """Очищает старые данные."""
        self.local_limiter._cleanup_queues()
        # Очищаем заблокированных пользователей
        current_time = time.time()
        blocked_users = list(self.local_limiter._blocked.keys())
        for user_id in blocked_users:
            if self.local_limiter._blocked[user_id] < current_time:
                del self.local_limiter._blocked[user_id]

# Глобальный экземпляр рейт-лимитера
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Возвращает глобальный экземпляр рейт-лимитера."""
    global _rate_limiter
    if _rate_limiter is None:
        # Пытаемся получить Redis из конфигурации
        redis_client = None
        try:
            import config
            if hasattr(config, 'redis_client'):
                redis_client = config.redis_client
        except ImportError:
            pass
        
        _rate_limiter = RateLimiter(use_redis=redis_client is not None, redis_client=redis_client)
    return _rate_limiter

# Функции для удобного использования

async def check_rate_limit(user_id: int, chat_id: int, command: str) -> RateLimitResult:
    """Проверяет лимиты для пользователя."""
    rate_limiter = get_rate_limiter()
    return await rate_limiter.check_rate_limit(user_id, chat_id, command)

def block_user(user_id: int, duration: int = 300) -> None:
    """Блокирует пользователя."""
    rate_limiter = get_rate_limiter()
    rate_limiter.block_user(user_id, duration)

def unblock_user(user_id: int) -> bool:
    """Разблокирует пользователя."""
    rate_limiter = get_rate_limiter()
    return rate_limiter.unblock_user(user_id)

def is_user_blocked(user_id: int) -> bool:
    """Проверяет, заблокирован ли пользователь."""
    rate_limiter = get_rate_limiter()
    return rate_limiter.is_blocked(user_id)

def get_rate_limit_stats() -> Dict[str, Any]:
    """Возвращает статистику использования."""
    rate_limiter = get_rate_limiter()
    return rate_limiter.get_stats()

def get_user_rate_limit_stats(user_id: int) -> Dict[str, Any]:
    """Возвращает статистику по пользователю."""
    rate_limiter = get_rate_limiter()
    return rate_limiter.get_user_stats(user_id)

# Декоратор для защиты команд
def rate_limit_required(command_name: str):
    """Декоратор для проверки лимитов команд."""
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            # Проверяем лимиты
            result = await check_rate_limit(user_id, chat_id, command_name)
            
            if not result.allowed:
                # Формируем сообщение о превышении лимита
                if result.limit_type == "blocked":
                    await update.message.reply_text(
                        "🚫 Вы временно заблокированы за нарушение правил использования бота.",
                        reply_markup=None
                    )
                else:
                    retry_after = result.retry_after or 60
                    await update.message.reply_text(
                        f"⏰ Слишком много запросов! Подождите {retry_after} секунд.",
                        reply_markup=None
                    )
                return
            
            # Выполняем команду
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator

# Пример использования в handlers/commands.py:
"""
@rate_limit_required("davka")
async def handle_davka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ваш код команды давки
    pass

@rate_limit_required("rademka")
async def handle_rademka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ваш код команды радёмки
    pass
"""