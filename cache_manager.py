"""
Redis-кеширование с локальным fallback для Telegram бота.

Этот модуль предоставляет:
- Redis-кеширование для высокой производительности
- Локальное кэширование в качестве fallback при недоступности Redis
- Автоматическое переключение между Redis и локальным кэшем
- Поддержку TTL (времени жизни) для кэшированных данных
- Сериализацию данных в JSON для совместимости
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
import threading
from collections import OrderedDict

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

<<<<<<< HEAD
class LocalCache:
    """Локальный кэш с поддержкой TTL и LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        
    def _cleanup_expired(self):
        """Очищает просроченные записи."""
        current_time = time.time()
        expired_keys = []
        
        for key, value in self._cache.items():
            if current_time > value['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Получает значение из локального кэша."""
        with self._lock:
            self._cleanup_expired()
            
            if key not in self._cache:
                return None
            
            value = self._cache[key]
            current_time = time.time()
            
            if current_time > value['expires_at']:
                del self._cache[key]
                return None
            
            # Обновляем порядок использования (LRU)
            self._cache.move_to_end(key)
            return value['data']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохраняет значение в локальный кэш."""
        with self._lock:
            self._cleanup_expired()
            
            if ttl is None:
                ttl = self.default_ttl
            
            expires_at = time.time() + ttl
            
            # Если достигли лимита, удаляем самую старую запись
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = {
                'data': value,
                'expires_at': expires_at
=======
# Local cache storage with LRU
_local_cache = {}
_local_cache_hits = 0
_local_cache_misses = 0
_cache_access_times = {}  # Для LRU
_MAX_CACHE_SIZE = 1000  # Максимальный размер локального кэша

try:
    if REDIS_CONFIG["enabled"]:
        import redis.asyncio as redis
        redis_client = None
    else:
        redis_client = None
        logger.info("Redis caching disabled in config")
except ImportError:
    redis_client = None
    logger.warning("Redis library not installed, using local cache only")

async def init_redis():
    """Initialize Redis connection if enabled"""
    global redis_client
    if REDIS_CONFIG["enabled"] and redis_client is None:
        try:
            redis_client = redis.Redis(
                host=REDIS_CONFIG["host"],
                port=REDIS_CONFIG["port"],
                db=REDIS_CONFIG["db"],
                password=REDIS_CONFIG["password"],
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            redis_client = None
            logger.error(f"❌ Redis connection failed: {e}")
            logger.info("Falling back to local cache")

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

def _generate_cache_key(prefix: str, *args) -> str:
    """Generate consistent cache key"""
    key_parts = [str(arg) for arg in args]
    return f"{prefix}:{':'.join(key_parts)}"

async def get_cached(key: str, fallback_func: callable, ttl: int = None) -> Any:
    """
    Get cached value or compute and cache if not found with LRU

    Args:
        key: Cache key
        fallback_func: Function to call if cache miss
        ttl: Time to live in seconds (uses default if None)

    Returns:
        Cached or computed value
    """
    global _local_cache_hits, _local_cache_misses

    ttl = ttl or DB_CONFIG["cache_ttl"]

    # Try local cache first
    if key in _local_cache:
        cached_data, timestamp = _local_cache[key]
        if time.time() - timestamp < ttl:
            _local_cache_hits += 1
            # Обновляем время доступа для LRU
            _cache_access_times[key] = time.time()
            return cached_data
        else:
            # Удаляем просроченные данные
            del _local_cache[key]
            del _cache_access_times[key]

    # Try Redis cache if available
    if redis_client:
        try:
            cached_data = await redis_client.get(key)
            if cached_data:
                _local_cache_hits += 1
                # Update local cache with LRU
                _update_local_cache(key, json.loads(cached_data))
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")

    # Cache miss - compute value
    _local_cache_misses += 1
    result = await fallback_func()

    # Update local cache with LRU
    _update_local_cache(key, result)

    # Update Redis cache if available
    if redis_client:
        try:
            await redis_client.setex(key, ttl, json.dumps(result))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    return result

def _update_local_cache(key: str, value: Any):
    """Update local cache with LRU eviction"""
    current_time = time.time()
    
    # Если кэш переполнен, удаляем наименее используемые элементы
    if len(_local_cache) >= _MAX_CACHE_SIZE:
        # Находим и удаляем элемент с самым старым временем доступа
        oldest_key = min(_cache_access_times.items(), key=lambda x: x[1])[0]
        del _local_cache[oldest_key]
        del _cache_access_times[oldest_key]
    
    # Добавляем новый элемент
    _local_cache[key] = (value, current_time)
    _cache_access_times[key] = current_time

async def get_gofra_info_optimized(gofra_value_mm: float) -> Dict[str, Any]:
    """
    Optimized version of get_gofra_info with caching

    Args:
        gofra_value_mm: Gofra length in millimeters

    Returns:
        Dictionary with gofra information
    """
    cache_key = _generate_cache_key("gofra_info", gofra_value_mm)

    async def compute_gofra_info():
        """Compute gofra info (fallback function)"""
        from config import GOFRY_MM, BALANCE

        # Handle cosmic gofra levels
        if gofra_value_mm >= 100000.0:
            meters = gofra_value_mm / 1000.0
            speed = 2.5 + (meters / 100) * 0.1
            weight_bonus = 1 + ((meters - 100) / 50) * 0.05
            min_grams = round(1000 * weight_bonus)
            max_grams = round(2500 * weight_bonus)

            return {
                "name": f"КОСМИЧЕСКАЯ ГОФРА {int(meters)}м",
                "emoji": "🚀",
                "atm_speed": round(speed, 2),
                "min_grams": min_grams,
                "max_grams": max_grams,
                "threshold": 100000.0,
                "next_threshold": gofra_value_mm + 5000.0,
                "progress": (gofra_value_mm % 5000.0) / 5000.0,
                "length_mm": gofra_value_mm,
                "length_display": f"{meters:.1f} м"
>>>>>>> e23d92a (🚀 Оптимизация производительности системы)
            }
            # Перемещаем в конец (самая свежая запись)
            self._cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """Удаляет значение из локального кэша."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Очищает весь локальный кэш."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Возвращает количество записей в кэше."""
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)

class CacheManager:
    """Менеджер кэширования с поддержкой Redis и локального fallback."""
    
    def __init__(self, redis_url: Optional[str] = None, local_cache_size: int = 1000):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache = LocalCache(max_size=local_cache_size)
        self._redis_available = False
        self._redis_check_lock = asyncio.Lock()
        self._redis_check_task: Optional[asyncio.Task] = None
        self._redis_check_interval = 30  # Проверять доступность Redis каждые 30 секунд
        
        # Префиксы для разных типов данных
        self.prefixes = {
            'user': 'user:',
            'chat': 'chat:',
            'stats': 'stats:',
            'rademka': 'rademka:',
            'config': 'config:',
            'session': 'session:'
        }
        
        # Статистика использования кэша
        self.stats = {
            'redis_hits': 0,
            'redis_misses': 0,
            'local_hits': 0,
            'local_misses': 0,
            'redis_errors': 0,
            'fallbacks': 0
        }
    
    async def initialize(self):
        """Инициализирует Redis-клиент и запускает фоновую проверку."""
        if REDIS_AVAILABLE and self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Проверяем доступность Redis
                await self.redis_client.ping()
                self._redis_available = True
                logger.info("✅ Redis подключен и доступен")
            except Exception as e:
                logger.warning(f"⚠️ Redis недоступен, будет использоваться локальный кэш: {e}")
                self._redis_available = False
        else:
            logger.info("📝 Redis не доступен, будет использоваться локальный кэш")
            self._redis_available = False
        
        # Запускаем фоновую проверку доступности Redis
        self._redis_check_task = asyncio.create_task(self._redis_health_check())
    
    async def close(self):
        """Закрывает соединение с Redis."""
        if self._redis_check_task:
            self._redis_check_task.cancel()
            try:
                await self._redis_check_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def _redis_health_check(self):
        """Фоновая проверка доступности Redis."""
        while True:
            try:
                await asyncio.sleep(self._redis_check_interval)
                
                if not self.redis_client:
                    continue
                
                # Проверяем доступность Redis
                await self.redis_client.ping()
                if not self._redis_available:
                    logger.info("✅ Redis снова доступен")
                    self._redis_available = True
                    self.stats['fallbacks'] += 1
                    
            except Exception as e:
                if self._redis_available:
                    logger.warning(f"⚠️ Redis недоступен, переключаемся на локальный кэш: {e}")
                    self._redis_available = False
                    self.stats['fallbacks'] += 1
                    self.stats['redis_errors'] += 1
    
    def _get_key(self, prefix: str, key: str) -> str:
        """Формирует полный ключ с префиксом."""
        return f"{self.prefixes.get(prefix, prefix)}{key}"
    
    def _serialize(self, data: Any) -> str:
        """Сериализует данные в JSON."""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"❌ Ошибка сериализации данных: {e}")
            return json.dumps({"error": "serialization_failed", "data": str(data)})
    
    def _deserialize(self, data: str) -> Any:
        """Десериализует данные из JSON."""
        try:
            return json.loads(data)
        except Exception as e:
            logger.error(f"❌ Ошибка десериализации данных: {e}")
            return None
    
    async def get(self, prefix: str, key: str) -> Optional[Any]:
        """Получает значение из кэша (Redis или локального)."""
        full_key = self._get_key(prefix, key)
        
        if self._redis_available:
            try:
                value = await self.redis_client.get(full_key)
                if value is not None:
                    self.stats['redis_hits'] += 1
                    return self._deserialize(value)
                else:
                    self.stats['redis_misses'] += 1
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при получении {full_key}: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Fallback на локальный кэш
        value = self.local_cache.get(full_key)
        if value is not None:
            self.stats['local_hits'] += 1
            return value
        else:
            self.stats['local_misses'] += 1
            return None
    
    async def set(self, prefix: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохраняет значение в кэш (Redis или локальный)."""
        full_key = self._get_key(prefix, key)
        serialized_value = self._serialize(value)
        
        # Сохраняем в Redis, если он доступен
        if self._redis_available:
            try:
                if ttl:
                    await self.redis_client.setex(full_key, ttl, serialized_value)
                else:
                    await self.redis_client.set(full_key, serialized_value)
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при сохранении {full_key}: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Сохраняем в локальный кэш
        self.local_cache.set(full_key, value, ttl)
    
    async def delete(self, prefix: str, key: str) -> bool:
        """Удаляет значение из кэша."""
        full_key = self._get_key(prefix, key)
        deleted = False
        
        # Удаляем из Redis
        if self._redis_available:
            try:
                result = await self.redis_client.delete(full_key)
                deleted = result > 0
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при удалении {full_key}: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Удаляем из локального кэша
        local_deleted = self.local_cache.delete(full_key)
        
        return deleted or local_deleted
    
    async def exists(self, prefix: str, key: str) -> bool:
        """Проверяет существование ключа в кэше."""
        full_key = self._get_key(prefix, key)
        
        if self._redis_available:
            try:
                result = await self.redis_client.exists(full_key)
                if result > 0:
                    return True
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при проверке существования {full_key}: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        return self.local_cache.get(full_key) is not None
    
    async def keys(self, prefix: str, pattern: str = "*") -> List[str]:
        """Получает список ключей по шаблону."""
        full_pattern = f"{self.prefixes.get(prefix, prefix)}{pattern}"
        keys = []
        
        if self._redis_available:
            try:
                redis_keys = await self.redis_client.keys(full_pattern)
                keys.extend(redis_keys)
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при получении ключей по шаблону {full_pattern}: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Добавляем ключи из локального кэша
        local_keys = [k for k in self.local_cache._cache.keys() if k.startswith(full_pattern[:-1])]
        keys.extend(local_keys)
        
        return list(set(keys))  # Удаляем дубликаты
    
    async def clear(self, prefix: Optional[str] = None) -> None:
        """Очищает кэш (всего или по префиксу)."""
        if prefix:
            pattern = f"{self.prefixes.get(prefix, prefix)}*"
        else:
            pattern = "*"
        
        # Очищаем Redis
        if self._redis_available:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при очистке кэша по шаблону {pattern}: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Очищаем локальный кэш
        if prefix:
            # Удаляем только ключи с указанным префиксом
            keys_to_delete = [k for k in self.local_cache._cache.keys() if k.startswith(self.prefixes.get(prefix, prefix))]
            for key in keys_to_delete:
                self.local_cache.delete(key)
        else:
            # Очищаем весь локальный кэш
            self.local_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования кэша."""
        return {
            **self.stats,
            'local_cache_size': self.local_cache.size(),
            'redis_available': self._redis_available,
            'total_hits': self.stats['redis_hits'] + self.stats['local_hits'],
            'total_misses': self.stats['redis_misses'] + self.stats['local_misses'],
            'hit_rate': self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Рассчитывает общий процент попаданий в кэш."""
        total_hits = self.stats['redis_hits'] + self.stats['local_hits']
        total_requests = total_hits + self.stats['redis_misses'] + self.stats['local_misses']
        
        if total_requests == 0:
            return 0.0
        
        return (total_hits / total_requests) * 100
    
    async def warmup_cache(self, data_loader_func, prefix: str, keys: List[str]) -> None:
        """Прогревает кэш, загружая данные из источника."""
        logger.info(f"🔥 Прогрев кэша для {prefix}, ключи: {len(keys)}")
        
        for key in keys:
            try:
                # Проверяем, есть ли уже в кэше
                if await self.exists(prefix, key):
                    continue
                
                # Загружаем данные из источника
                data = await data_loader_func(key)
                if data is not None:
                    await self.set(prefix, key, data, ttl=3600)  # TTL 1 час
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при прогреве кэша для {prefix}:{key}: {e}")
    
    async def batch_get(self, prefix: str, keys: List[str]) -> Dict[str, Optional[Any]]:
        """Пакетное получение значений из кэша."""
        results = {}
        
        if self._redis_available:
            try:
                full_keys = [self._get_key(prefix, key) for key in keys]
                values = await self.redis_client.mget(*full_keys)
                
                for key, value in zip(keys, values):
                    if value is not None:
                        results[key] = self._deserialize(value)
                        self.stats['redis_hits'] += 1
                    else:
                        self.stats['redis_misses'] += 1
                        
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при пакетном получении: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Fallback на локальный кэш для пропущенных ключей
        for key in keys:
            if key not in results:
                full_key = self._get_key(prefix, key)
                value = self.local_cache.get(full_key)
                if value is not None:
                    results[key] = value
                    self.stats['local_hits'] += 1
                else:
                    self.stats['local_misses'] += 1
        
        return results
    
    async def batch_set(self, prefix: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Пакетное сохранение значений в кэш."""
        # Сохраняем в Redis
        if self._redis_available:
            try:
                pipe = self.redis_client.pipeline()
                for key, value in data.items():
                    full_key = self._get_key(prefix, key)
                    serialized_value = self._serialize(value)
                    if ttl:
                        pipe.setex(full_key, ttl, serialized_value)
                    else:
                        pipe.set(full_key, serialized_value)
                await pipe.execute()
            except Exception as e:
                logger.error(f"❌ Ошибка Redis при пакетном сохранении: {e}")
                self.stats['redis_errors'] += 1
                self._redis_available = False
        
        # Сохраняем в локальный кэш
        for key, value in data.items():
            full_key = self._get_key(prefix, key)
            self.local_cache.set(full_key, value, ttl)

# Глобальный экземпляр менеджера кэша
_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """Возвращает глобальный экземпляр менеджера кэша."""
    global _cache_manager
    if _cache_manager is None:
        # Пытаемся получить URL Redis из конфигурации
        redis_url = None
        try:
            import config
            redis_url = getattr(config, 'REDIS_URL', None)
        except ImportError:
            pass
        
        _cache_manager = CacheManager(redis_url=redis_url)
    return _cache_manager

async def initialize_cache():
    """Инициализирует менеджер кэша."""
    cache_manager = get_cache_manager()
    await cache_manager.initialize()

async def close_cache():
    """Закрывает менеджер кэша."""
    cache_manager = get_cache_manager()
    await cache_manager.close()

# Функции для удобного использования кэша

async def cache_get(prefix: str, key: str) -> Optional[Any]:
    """Получает значение из кэша."""
    cache_manager = get_cache_manager()
    return await cache_manager.get(prefix, key)

async def cache_set(prefix: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Сохраняет значение в кэш."""
    cache_manager = get_cache_manager()
    await cache_manager.set(prefix, key, value, ttl)

async def cache_delete(prefix: str, key: str) -> bool:
    """Удаляет значение из кэша."""
    cache_manager = get_cache_manager()
    return await cache_manager.delete(prefix, key)

async def cache_exists(prefix: str, key: str) -> bool:
    """Проверяет существование ключа в кэше."""
    cache_manager = get_cache_manager()
    return await cache_manager.exists(prefix, key)

def get_cache_stats() -> Dict[str, Any]:
    """Возвращает статистику использования кэша."""
    cache_manager = get_cache_manager()
    return cache_manager.get_stats()

async def clear_cache(prefix: Optional[str] = None) -> None:
    """Очищает кэш."""
    cache_manager = get_cache_manager()
    await cache_manager.clear(prefix)

# Пример использования в db_manager.py
async def get_patsan_cached(user_id: int) -> Optional[Dict[str, Any]]:
    """Получает данные пользователя из кэша или базы данных."""
    # Сначала пробуем получить из кэша
    cached_data = await cache_get('user', str(user_id))
    if cached_data:
        return cached_data
    
    # Если нет в кэше, получаем из базы данных
    from db_manager import get_patsan
    db_data = await get_patsan(user_id)
    
    # Сохраняем в кэш на 5 минут
    if db_data:
        await cache_set('user', str(user_id), db_data, ttl=300)
    
    return db_data

async def save_patsan_cached(user_id: int, data: Dict[str, Any]) -> None:
    """Сохраняет данные пользователя в базу данных и кэш."""
    from db_manager import save_patsan
    await save_patsan(data)
    
    # Обновляем кэш
    await cache_set('user', str(user_id), data, ttl=300)

async def get_chat_stats_cached(chat_id: int) -> Optional[Dict[str, Any]]:
    """Получает статистику чата из кэша или базы данных."""
    cached_data = await cache_get('chat', str(chat_id))
    if cached_data:
        return cached_data
    
    from db_manager import ChatManager
    db_data = await ChatManager.get_chat_stats(chat_id)
    
    if db_data:
        await cache_set('chat', str(chat_id), db_data, ttl=600)  # 10 минут
    
    return db_data