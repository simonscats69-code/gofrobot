"""
Advanced caching system with Redis support
"""
import time
import json
from typing import Optional, Any, Dict
import logging
from config import REDIS_CONFIG, DB_CONFIG

logger = logging.getLogger(__name__)

# Local cache storage
_local_cache = {}
_local_cache_hits = 0
_local_cache_misses = 0

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
    Get cached value or compute and cache if not found

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
            return cached_data

    # Try Redis cache if available
    if redis_client:
        try:
            cached_data = await redis_client.get(key)
            if cached_data:
                _local_cache_hits += 1
                # Update local cache
                _local_cache[key] = (json.loads(cached_data), time.time())
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")

    # Cache miss - compute value
    _local_cache_misses += 1
    result = await fallback_func()

    # Update local cache
    _local_cache[key] = (result, time.time())

    # Update Redis cache if available
    if redis_client:
        try:
            await redis_client.setex(key, ttl, json.dumps(result))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    return result

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
            }

        # Find current gofra level
        sorted_thresholds = sorted(GOFRY_MM.items())
        current_info = None

        for threshold_mm, info in sorted_thresholds:
            if gofra_value_mm >= threshold_mm:
                current_info = info.copy()
                current_info["threshold"] = threshold_mm
            else:
                break

        if not current_info:
            current_info = GOFRY_MM[10.0].copy()
            current_info["threshold"] = 10.0

        # Set up thresholds and progress
        thresholds = list(GOFRY_MM.keys())
        current_index = thresholds.index(current_info["threshold"])

        if current_index < len(thresholds) - 1:
            next_threshold = thresholds[current_index + 1]
            current_info["next_threshold"] = next_threshold
            current_info["progress"] = (gofra_value_mm - current_info["threshold"]) / (next_threshold - current_info["threshold"]) if (next_threshold - current_info["threshold"]) > 0 else 0
        else:
            current_info["next_threshold"] = 100000.0
            current_info["progress"] = (gofra_value_mm - current_info["threshold"]) / (100000.0 - current_info["threshold"]) if (100000.0 - current_info["threshold"]) > 0 else 0

        current_info["length_mm"] = gofra_value_mm
        current_info["length_display"] = f"{gofra_value_mm / BALANCE['UNIT_SCALE']:.{BALANCE['DISPLAY_DECIMALS']}f} см"

        if "atm_speed" not in current_info:
            current_info["atm_speed"] = 1.0

        return current_info

    return await get_cached(cache_key, compute_gofra_info, REDIS_CONFIG["cache_ttl"])

def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics"""
    hit_rate = _local_cache_hits / max(1, _local_cache_hits + _local_cache_misses)
    return {
        "local_cache_size": len(_local_cache),
        "local_cache_hits": _local_cache_hits,
        "local_cache_misses": _local_cache_misses,
        "local_cache_hit_rate": hit_rate,
        "redis_enabled": REDIS_CONFIG["enabled"],
        "redis_connected": redis_client is not None
    }

def clear_local_cache():
    """Clear local cache"""
    global _local_cache, _local_cache_hits, _local_cache_misses
    _local_cache = {}
    _local_cache_hits = 0
    _local_cache_misses = 0

async def clear_redis_cache():
    """Clear Redis cache (be careful!)"""
    if redis_client:
        try:
            await redis_client.flushdb()
            logger.info("Redis cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear Redis cache: {e}")