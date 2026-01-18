import time
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FastUserCache:
    def __init__(self):
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._timestamps: Dict[int, float] = {}
        self._locks: Dict[int, asyncio.Lock] = {}
        self._ttl = 15  # Уменьшаем TTL для частых операций
    
    def _get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]
    
    async def get(self, user_id: int, getter_func) -> Dict[str, Any]:
        now = time.time()
        
        # Быстрая проверка без лока
        if user_id in self._cache and now - self._timestamps.get(user_id, 0) < self._ttl:
            return self._cache[user_id].copy()  # Возвращаем копию
        
        async with self._get_lock(user_id):
            # Повторная проверка после лока
            if user_id in self._cache and now - self._timestamps.get(user_id, 0) < self._ttl:
                return self._cache[user_id].copy()
            
            # Получаем данные
            data = await getter_func(user_id)
            
            # Кешируем
            self._cache[user_id] = data.copy()
            self._timestamps[user_id] = now
            
            # Очистка старых записей
            if len(self._cache) > 1000:
                self._cleanup()
            
            return data
    
    def update(self, user_id: int, updates: Dict[str, Any]):
        if user_id in self._cache:
            self._cache[user_id].update(updates)
            self._timestamps[user_id] = time.time()
    
    def invalidate(self, user_id: int):
        self._cache.pop(user_id, None)
        self._timestamps.pop(user_id, None)
    
    def _cleanup(self):
        now = time.time()
        to_delete = [uid for uid, ts in self._timestamps.items() 
                    if now - ts > self._ttl * 3]
        for uid in to_delete:
            self._cache.pop(uid, None)
            self._timestamps.pop(uid, None)

# Глобальный кеш
user_cache = FastUserCache()
