"""
Test cases for cache system
"""
import pytest
import asyncio
import time
from cache_manager import get_gofra_info_optimized, get_cache_stats, clear_local_cache
from config import GOFRY_MM

@pytest.mark.asyncio
async def test_gofra_info_caching():
    """Test that gofra info caching works correctly"""
    # Clear cache before test
    clear_local_cache()

    # First call should be cache miss
    start_time = time.time()
    info1 = await get_gofra_info_optimized(150.0)
    duration1 = time.time() - start_time

    # Second call should be cache hit
    start_time = time.time()
    info2 = await get_gofra_info_optimized(150.0)
    duration2 = time.time() - start_time

    # Verify results are identical
    assert info1 == info2

    # Verify caching worked (second call should be faster)
    assert duration2 < duration1

    # Verify cache stats
    stats = get_cache_stats()
    assert stats["local_cache_hits"] >= 1
    assert stats["local_cache_misses"] >= 1

    # Test different gofra level
    info3 = await get_gofra_info_optimized(50.0)
    assert info3 != info1  # Different gofra level
    assert info3["threshold"] == 50.0

    # Test cosmic gofra level
    info4 = await get_gofra_info_optimized(150000.0)
    assert "КОСМИЧЕСКАЯ ГОФРА" in info4["name"]
    assert info4["emoji"] == "🚀"

def test_cache_stats():
    """Test cache statistics tracking"""
    clear_local_cache()

    # Initial stats should be zero
    stats = get_cache_stats()
    assert stats["local_cache_hits"] == 0
    assert stats["local_cache_misses"] == 0
    assert stats["local_cache_size"] == 0

    # Hit rate should be 0 initially
    assert stats["local_cache_hit_rate"] == 0.0

@pytest.mark.asyncio
async def test_gofra_info_values():
    """Test that gofra info contains expected values"""
    info = await get_gofra_info_optimized(300.0)

    # Verify all expected fields are present
    expected_fields = [
        "name", "emoji", "min_grams", "max_grams",
        "threshold", "next_threshold", "progress",
        "length_mm", "length_display", "atm_speed"
    ]

    for field in expected_fields:
        assert field in info, f"Missing field: {field}"

    # Verify values are reasonable
    assert info["threshold"] == 300.0
    assert info["atm_speed"] > 1.0
    assert info["min_grams"] < info["max_grams"]
    assert 0 <= info["progress"] <= 1.0

def test_gofra_levels():
    """Test all gofra levels from configuration"""
    for threshold, expected_info in GOFRY_MM.items():
        info = asyncio.run(get_gofra_info_optimized(threshold))

        # Should match the level info
        assert info["name"] == expected_info["name"]
        assert info["emoji"] == expected_info["emoji"]
        assert info["threshold"] == threshold
        assert info["atm_speed"] == expected_info["atm_speed"]

@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test that cache properly handles different inputs"""
    clear_local_cache()

    # Cache one value
    await get_gofra_info_optimized(150.0)

    # Different value should not hit cache
    stats_before = get_cache_stats()
    await get_gofra_info_optimized(300.0)
    stats_after = get_cache_stats()

    assert stats_after["local_cache_misses"] > stats_before["local_cache_misses"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])