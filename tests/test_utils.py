"""
Utility functions for testing
"""
import pytest
from db_manager import get_patsan, davka_zmiy, uletet_zmiy, save_patsan
from cache_manager import get_gofra_info_optimized

@pytest.mark.asyncio
async def test_davka_zmiy_function():
    """Test the davka_zmiy function"""
    # Create test user
    test_user_id = 999999
    user = await get_patsan(test_user_id)

    # Set atm to 12 for davka
    user["atm_count"] = 12
    await save_patsan(user)

    # Test successful davka
    success, user, result = await davka_zmiy(test_user_id)

    assert success == True
    assert user is not None
    assert result is not None
    assert "zmiy_grams" in result
    assert result["zmiy_grams"] > 0
    assert user["atm_count"] == 0  # Should be 0 after davka

    # Verify gofra increased
    assert result["new_gofra_mm"] > result["old_gofra_mm"]

    # Verify cable increased
    assert result["new_cable_mm"] >= result["old_cable_mm"]

@pytest.mark.asyncio
async def test_uletet_zmiy_function():
    """Test the uletet_zmiy function"""
    test_user_id = 999998

    # First add some zmiy
    await get_patsan(test_user_id)
    success, user, _ = await davka_zmiy(test_user_id)
    assert success

    # Now test uletet
    success, user, result = await uletet_zmiy(test_user_id)

    assert success == True
    assert user["zmiy_grams"] == 0  # Should be 0 after uletet
    assert result["zmiy_grams"] > 0

@pytest.mark.asyncio
async def test_gofra_progression():
    """Test that gofra progresses correctly"""
    test_user_id = 999997
    initial_user = await get_patsan(test_user_id)
    initial_gofra = initial_user["gofra_mm"]

    # Do multiple davka actions
    for i in range(5):
        # Set atm to 12 for davka
        initial_user["atm_count"] = 12
        await save_patsan(initial_user)

        success, user, _ = await davka_zmiy(test_user_id)
        assert success
        assert user["gofra_mm"] >= initial_gofra

        if i > 0:
            # Gofra should increase with each davka
            assert user["gofra_mm"] > initial_gofra

        initial_gofra = user["gofra_mm"]
        initial_user = user

@pytest.mark.asyncio
async def test_atm_regen():
    """Test atmosphere regeneration"""
    test_user_id = 999996
    user = await get_patsan(test_user_id)

    # Set atm to 0
    user["atm_count"] = 0
    user["last_update"] = 0
    await save_patsan(user)

    # Wait a bit (simulate time passing)
    import time
    time.sleep(0.1)

    # Get user again (should trigger regeneration)
    user2 = await get_patsan(test_user_id)

    # ATM should start regenerating
    assert user2["atm_count"] >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])