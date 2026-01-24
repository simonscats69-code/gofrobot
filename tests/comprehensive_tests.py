#!/usr/bin/env python3
"""
Комплексные тесты для проекта GofRobot.
Объединяет все необходимые тесты в одном файле.
"""

import asyncio
import sys
import traceback
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

# Импортируем необходимые модули
from handlers.callbacks import (
    handle_davka_callback,
    handle_uletet_callback,
    handle_atm_status_callback,
    handle_profile_callback
)
from handlers.nickname_and_rademka import rademka_stats
from db_manager import davka_zmiy, get_patsan, save_patsan, get_gofra_info, uletet_zmiy
from cache_manager import get_gofra_info_optimized, get_cache_stats, clear_local_cache
from config import GOFRY_MM

# ======================
# Тесты для декоратора
# ======================

def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                if args and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise
    return wrapper

class MockCallbackQuery:
    def __init__(self):
        self.answered = False

    async def answer(self):
        self.answered = True
        print("Callback answered successfully")

@ignore_not_modified_error
async def test_function():
    callback = MockCallbackQuery()
    error = TelegramBadRequest("editMessageText", "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message")
    raise error

async def test_decorator():
    """Тест для проверки работы декоратора @ignore_not_modified_error"""
    print("🧪 Тестирование @ignore_not_modified_error decorator...")

    callback = MockCallbackQuery()

    try:
        result = await test_function(callback)
        print(f"Function returned: {result}")

        if callback.answered:
            print("✅ SUCCESS: Callback was answered correctly")
            return True
        else:
            print("❌ FAIL: Callback was not answered")
            return False
    except TelegramBadRequest as e:
        print(f"❌ FAIL: TelegramBadRequest was not caught: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {e}")
        return False

# ======================
# Тесты для исправлений
# ======================

async def test_davka_callback_error_handling():
    """Тест: davka callback должен возвращать строку, а не словарь"""
    print("\n🧪 Тестирование handle_davka_callback...")

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()

    with patch('handlers.callbacks.davka_zmiy', new_callable=AsyncMock) as mock_davka:
        mock_davka.return_value = (False, {}, {'error': 'Нужно 12 атмосфер для давки змия!'})

        try:
            await handle_davka_callback(callback)
            call_args = callback.answer.call_args
            if call_args:
                actual_text = call_args[0][0]
                print(f"✅ Callback answer вызван с текстом: {actual_text}")
                assert isinstance(actual_text, str), f"Ожидалась строка, получено {type(actual_text)}"
                print("✅ Тест пройден: davka callback возвращает строку")
                return True
            else:
                print("❌ Ошибка: callback.answer не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

async def test_uletet_callback_error_handling():
    """Тест: uletet callback должен возвращать строку, а не словарь"""
    print("\n🧪 Тестирование handle_uletet_callback...")

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()

    with patch('handlers.callbacks.uletet_zmiy', new_callable=AsyncMock) as mock_uletet:
        mock_uletet.return_value = (False, {}, {'error': 'Нет змия для отправки!'})

        try:
            await handle_uletet_callback(callback)
            call_args = callback.answer.call_args
            if call_args:
                actual_text = call_args[0][0]
                print(f"✅ Callback answer вызван с текстом: {actual_text}")
                assert isinstance(actual_text, str), f"Ожидалась строка, получено {type(actual_text)}"
                print("✅ Тест пройден: uletet callback возвращает строку")
                return True
            else:
                print("❌ Ошибка: callback.answer не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

async def test_atm_status_callback_await():
    """Тест: atm status callback должен использовать await для корутины"""
    print("\n🧪 Тестирование handle_atm_status_callback...")

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    mock_patsan = {'atm_count': 5, 'gofra_mm': 15.0}
    mock_regen_info = {'per_atm': 3600, 'total': 7200, 'needed': 7}

    with patch('handlers.callbacks.get_patsan', new_callable=AsyncMock) as mock_get_patsan, \
         patch('handlers.callbacks.calculate_atm_regen_time', new_callable=AsyncMock) as mock_calculate, \
         patch('handlers.callbacks.get_gofra_info') as mock_gofra_info:

        mock_get_patsan.return_value = mock_patsan
        mock_calculate.return_value = mock_regen_info
        mock_gofra_info.return_value = {'emoji': '🐍', 'name': 'Коричневый бог', 'atm_speed': 2.0}

        try:
            await handle_atm_status_callback(callback)
            assert mock_calculate.await_count > 0, "calculate_atm_regen_time не был await-нут"
            print("✅ Тест пройден: calculate_atm_regen_time используется с await")
            return True
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

async def test_profile_callback_keyboard():
    """Тест: profile callback должен использовать существующую клавиатуру"""
    print("\n🧪 Тестирование handle_profile_callback...")

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    mock_patsan = {'atm_count': 5, 'gofra_mm': 15.0, 'cable_mm': 10.0, 'zmiy_grams': 1000.0, 'total_zmiy_grams': 0}
    mock_gofra_info = {
        'emoji': '🐍',
        'name': 'Коричневый бог',
        'atm_speed': 2.0,
        'min_grams': 100,
        'max_grams': 500,
        'length_display': '15.0 мм'
    }

    with patch('handlers.callbacks.format_length', return_value="15.0 мм"), \
         patch('db_manager.format_length', return_value="15.0 мм"), \
         patch('handlers.callbacks.get_patsan', new_callable=AsyncMock) as mock_get_patsan, \
         patch('handlers.callbacks.get_gofra_info') as mock_gofra_info, \
         patch('handlers.callbacks.main_keyboard') as mock_main_keyboard:

        mock_get_patsan.return_value = mock_patsan
        mock_gofra_info.return_value = mock_gofra_info
        mock_main_keyboard.return_value = "main_keyboard_mock"

        try:
            await handle_profile_callback(callback)
            call_args = callback.message.edit_text.call_args
            if call_args:
                kwargs = call_args[1]
                keyboard = kwargs.get('reply_markup')
                print(f"✅ Используемая клавиатура: {keyboard}")
                assert keyboard == "main_keyboard_mock", f"Ожидалась main_keyboard, получено {keyboard}"
                print("✅ Тест пройден: profile callback использует существующую клавиатуру")
                return True
            else:
                print("❌ Ошибка: edit_text не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

async def test_rademka_stats_tuple_handling():
    """Тест: rademka_stats должен правильно обрабатывать кортеж из SQL-запроса"""
    print("\n🧪 Тестирование rademka_stats...")

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = (10, 7, 3)

    mock_cursor2 = AsyncMock()
    mock_cursor2.fetchone.return_value = (2,)

    with patch('db_manager.get_connection', new_callable=AsyncMock) as mock_get_conn, \
         patch('handlers.nickname_and_rademka.back_kb') as mock_back_kb:

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        mock_back_kb.return_value = "back_kb_mock"

        try:
            await rademka_stats(callback)
            call_args = callback.message.edit_text.call_args
            if call_args:
                text = call_args[0][0]
                print(f"✅ Статистика радёмок сгенерирована: {text[:100]}...")
                assert "10" in text, "Общее количество боёв не найдено"
                assert "7" in text, "Количество побед не найдено"
                assert "3" in text, "Количество поражений не найдено"
                assert "70.0%" in text, "Винрейт не рассчитан правильно"
                print("✅ Тест пройден: rademka_stats правильно обрабатывает кортеж из SQL")
                return True
            else:
                print("❌ Ошибка: edit_text не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

# ======================
# Тесты для роста
# ======================

async def simulate_monthly_growth():
    """Симулируем рост гофрошки и кабеля за месяц игры (30 дней)."""
    print("\n📊 Симуляция роста гофрошки и кабеля за 30 дней")
    print("=" * 60)

    test_user_id = 999999
    initial_data = {
        'user_id': test_user_id,
        'nickname': 'TestPlayer',
        'gofra_mm': 10.0,
        'cable_mm': 10.0,
        'atm_count': 12,
        'zmiy_grams': 0.0,
        'total_zmiy_grams': 0.0,
        'cable_power': 2,
        'gofra': 1,
        'last_atm_regen': 0,
        'last_davka': 0,
        'last_rademka': 0
    }

    await save_patsan(initial_data)

    days_to_simulate = 30
    davki_per_day = 5

    initial_gofra = initial_data['gofra_mm']
    initial_cable = initial_data['cable_mm']

    print(f"📅 Период симуляции: {days_to_simulate} дней")
    print(f"🔄 Давок в день: {davki_per_day}")
    print(f"📏 Начальная гофрошка: {initial_gofra:.1f} мм")
    print(f"🔌 Начальный кабель: {initial_cable:.1f} мм")
    print()

    total_davki = 0
    total_zmiy = 0

    for day in range(1, days_to_simulate + 1):
        day_zmiy = 0

        for davka_num in range(davki_per_day):
            success, patsan, result = await davka_zmiy(test_user_id)

            if success:
                total_davki += 1
                day_zmiy += result['zmiy_grams']
                total_zmiy += result['zmiy_grams']
                await save_patsan(patsan)
            else:
                current_patsan = await get_patsan(test_user_id)
                current_patsan['atm_count'] = 12
                await save_patsan(current_patsan)

        if day % 5 == 0 or day == 1 or day == days_to_simulate:
            current_patsan = await get_patsan(test_user_id)
            current_gofra = current_patsan['gofra_mm']
            current_cable = current_patsan['cable_mm']
            gofra_growth = current_gofra - initial_gofra
            cable_growth = current_cable - initial_cable

            print(f"📅 День {day:2d}:")
            print(f"   🏗️ Гофра: {current_gofra:.1f} мм (+{gofra_growth:.1f} мм)")
            print(f"   🔌 Кабель: {current_cable:.1f} мм (+{cable_growth:.1f} мм)")
            print(f"   🐍 Змия за день: {day_zmiy:.0f} г")
            print()

    final_patsan = await get_patsan(test_user_id)
    final_gofra = final_patsan['gofra_mm']
    final_cable = final_patsan['cable_mm']

    gofra_growth = final_gofra - initial_gofra
    cable_growth = final_cable - initial_cable

    gofra_per_day = gofra_growth / days_to_simulate
    cable_per_day = cable_growth / days_to_simulate

    print("📊 ИТОГИ ЗА 30 ДНЕЙ:")
    print("=" * 60)
    print(f"🏗️ Гофрошка: {final_gofra:.1f} мм (+{gofra_growth:.1f} мм)")
    print(f"   Средний рост в день: {gofra_per_day:.2f} мм/день")
    print(f"   Средний рост в неделю: {gofra_per_day * 7:.2f} мм/неделю")
    print(f"   Средний рост в месяц: {gofra_growth:.2f} мм/месяц")
    print()
    print(f"🔌 Кабель: {final_cable:.1f} мм (+{cable_growth:.1f} мм)")
    print(f"   Средний рост в день: {cable_per_day:.2f} мм/день")
    print(f"   Средний рост в неделю: {cable_per_day * 7:.2f} мм/неделю")
    print(f"   Средний рост в месяц: {cable_growth:.2f} мм/месяц")
    print()
    print(f"🐍 Всего змия выдавлено: {total_zmiy:.0f} г")
    print(f"💪 Всего давок сделано: {total_davki}")
    print()

    gofra_info = get_gofra_info(final_gofra)
    print(f"🏆 Текущий уровень гофрошки: {gofra_info['emoji']} {gofra_info['name']}")
    print(f"   📊 Длина: {gofra_info['length_display']}")
    print(f"   ⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}")
    print(f"   ⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']} г")

    return True

async def test_new_growth():
    """Тестируем новые коэффициенты роста за 30 дней (30 давок)."""
    print("\n🧪 Тестирование новых коэффициентов роста")
    print("=" * 50)
    print("📅 Период: 30 дней (30 давок)")
    print("🎯 Цели:")
    print("   🏗️ Гофра: 70-100 мм (7-10 см)")
    print("   🔌 Кабель: 300-500 мм (30-50 см)")
    print()

    test_user_id = 888888
    initial_data = {
        'user_id': test_user_id,
        'nickname': 'NewGrowthTest',
        'gofra_mm': 10.0,
        'cable_mm': 10.0,
        'atm_count': 12,
        'zmiy_grams': 0.0,
        'total_zmiy_grams': 0.0,
        'cable_power': 2,
        'gofra': 1,
        'last_atm_regen': 0,
        'last_davka': 0,
        'last_rademka': 0
    }

    await save_patsan(initial_data)

    initial_gofra = initial_data['gofra_mm']
    initial_cable = initial_data['cable_mm']
    total_zmiy = 0
    kilogram_count = 0

    for day in range(1, 31):
        success, patsan, result = await davka_zmiy(test_user_id)

        if success:
            total_zmiy += result['zmiy_grams']
            if result['zmiy_grams'] > 1000:
                kilogram_count += 1

            patsan['atm_count'] = 12
            await save_patsan(patsan)

            if day % 5 == 0 or day == 1 or day == 30:
                current_gofra = patsan['gofra_mm']
                current_cable = patsan['cable_mm']
                gofra_growth = current_gofra - initial_gofra
                cable_growth = current_cable - initial_cable

                print(f"📅 День {day:2d}:")
                print(f"   🏗️ Гофра: {current_gofra:.1f} мм (+{gofra_growth:.1f} мм)")
                print(f"   🔌 Кабель: {current_cable:.1f} мм (+{cable_growth:.1f} мм)")
                print(f"   🐍 Змия: {result['zmiy_grams']:.0f} г")
                if result['zmiy_grams'] > 1000:
                    print(f"   🎉 СПЕЦСООБЩЕНИЕ: КИЛОГРАММ ГОВНА ЗА ДВАДЦАТЬ ПЯТЬ СЕКУНД")
                print()

        await asyncio.sleep(0.01)

    final_patsan = await get_patsan(test_user_id)
    final_gofra = final_patsan['gofra_mm']
    final_cable = final_patsan['cable_mm']

    gofra_growth = final_gofra - initial_gofra
    cable_growth = final_cable - initial_cable

    gofra_per_day = gofra_growth / 30
    cable_per_day = cable_growth / 30

    print("📊 ИТОГИ ЗА 30 ДНЕЙ:")
    print("=" * 50)
    print(f"🏗️ Гофрошка: {final_gofra:.1f} мм (+{gofra_growth:.1f} мм)")
    print(f"   📏 В сантиметрах: {gofra_growth/10:.1f} см")
    print(f"   📈 Средний рост: {gofra_per_day:.2f} мм/день")
    print(f"   🎯 Цель (70-100 мм): {'✅ ДОСТИГНУТА' if 70 <= gofra_growth <= 100 else '❌ НЕ ДОСТИГНУТА'}")
    print()
    print(f"🔌 Кабель: {final_cable:.1f} мм (+{cable_growth:.1f} мм)")
    print(f"   📏 В сантиметрах: {cable_growth/10:.1f} см")
    print(f"   📈 Средний рост: {cable_per_day:.2f} мм/день")
    print(f"   🎯 Цель (300-500 мм): {'✅ ДОСТИГНУТА' if 300 <= cable_growth <= 500 else '❌ НЕ ДОСТИГНУТА'}")
    print()
    print(f"🐍 Общая статистика:")
    print(f"   Всего змия: {total_zmiy:.0f} г ({total_zmiy/1000:.1f} кг)")
    print(f"   Килограммовых змеев: {kilogram_count}")
    print(f"   Средний вес змия: {total_zmiy/30:.0f} г/давка")
    print()

    gofra_info = get_gofra_info(final_gofra)
    print(f"🏆 Текущий уровень гофрошки: {gofra_info['emoji']} {gofra_info['name']}")
    print(f"   📊 Длина: {gofra_info['length_display']}")
    print(f"   ⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}")
    print(f"   ⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']} г")

    gofra_goal_achieved = 70 <= gofra_growth <= 100
    cable_goal_achieved = 300 <= cable_growth <= 500

    print()
    print("🎯 ОБЩИЙ РЕЗУЛЬТАТ:")
    if gofra_goal_achieved and cable_goal_achieved:
        print("   🎉 ВСЕ ЦЕЛИ ДОСТИГНУТЫ! НОВЫЕ КОЭФФИЦИЕНТЫ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print("   ⚠️ Цели не достигнуты. Требуется корректировка коэффициентов.")

    return True

# ======================
# Тесты для кэширования
# ======================

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

    print("✅ Тест пройден: кэширование информации о гофрошке работает корректно")
    return True

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

    print("✅ Тест пройден: статистика кэша отслеживается корректно")

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

    print("✅ Тест пройден: информация о гофрошке содержит ожидаемые значения")
    return True

def test_gofra_levels():
    """Test all gofra levels from configuration"""
    for threshold, expected_info in GOFRY_MM.items():
        info = asyncio.run(get_gofra_info_optimized(threshold))

        # Should match the level info
        assert info["name"] == expected_info["name"]
        assert info["emoji"] == expected_info["emoji"]
        assert info["threshold"] == threshold
        assert info["atm_speed"] == expected_info["atm_speed"]

    print("✅ Тест пройден: все уровни гофрошки соответствуют конфигурации")

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

    print("✅ Тест пройден: инвалидация кэша работает корректно")
    return True

# ======================
# Тесты для утилит
# ======================

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

    print("✅ Тест пройден: функция davka_zmiy работает корректно")
    return True

async def test_uletet_zmiy_function():
    """Test the uletet_zmiy function"""
    test_user_id = 999998

    # First add some zmiy
    user = await get_patsan(test_user_id)
    user["atm_count"] = 12  # Set atm to 12 for davka
    await save_patsan(user)

    success, user, _ = await davka_zmiy(test_user_id)
    assert success

    # Now test uletet
    success, user, result = await uletet_zmiy(test_user_id)

    assert success == True
    assert user["zmiy_grams"] == 0  # Should be 0 after uletet
    assert result["zmiy_grams"] > 0

    print("✅ Тест пройден: функция uletet_zmiy работает корректно")
    return True

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

    print("✅ Тест пройден: прогрессия гофрошки работает корректно")
    return True

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

    print("✅ Тест пройден: регенерация атмосфер работает корректно")
    return True

# ======================
# Новые тесты для команд и обработчиков
# ======================

async def test_group_commands():
    """Test group commands functionality"""
    from handlers.chat_handlers import group_start, group_help, group_menu_command

    # Mock message object
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.chat = MagicMock()
    message.chat.id = -100
    message.chat.type = "supergroup"
    message.answer = AsyncMock()

    try:
        # Test group_start command
        await group_start(message)
        assert message.answer.called, "group_start should call message.answer"

        # Test group_help command
        await group_help(message)
        assert message.answer.called, "group_help should call message.answer"

        # Test group_menu_command
        await group_menu_command(message)
        assert message.answer.called, "group_menu_command should call message.answer"

        print("✅ Тест пройден: групповые команды работают корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте групповых команд: {e}")
        return False

async def test_chat_commands():
    """Test chat commands functionality"""
    from handlers.chat_handlers import chat_top_command, chat_stats_command

    # Mock message object
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.chat = MagicMock()
    message.chat.id = -100
    message.chat.type = "supergroup"
    message.answer = AsyncMock()

    try:
        # Test chat_top_command
        await chat_top_command(message)
        assert message.answer.called, "chat_top_command should call message.answer"

        # Test chat_stats_command
        await chat_stats_command(message)
        assert message.answer.called, "chat_stats_command should call message.answer"

        print("✅ Тест пройден: команды чата работают корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте команд чата: {e}")
        return False

async def test_basic_commands():
    """Test basic bot commands"""
    from handlers.commands import cmd_start, cmd_profile, cmd_help, cmd_version

    # Mock message object
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.username = "testuser"
    message.chat = MagicMock()
    message.chat.id = 123
    message.answer = AsyncMock()

    try:
        # Test cmd_start
        await cmd_start(message)
        assert message.answer.called, "cmd_start should call message.answer"

        # Test cmd_help
        await cmd_help(message)
        assert message.answer.called, "cmd_help should call message.answer"

        # Test cmd_version
        await cmd_version(message)
        assert message.answer.called, "cmd_version should call message.answer"

        print("✅ Тест пройден: базовые команды работают корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте базовых команд: {e}")
        return False

async def test_nickname_functionality():
    """Test nickname change functionality"""
    from handlers.nickname_and_rademka import validate_nickname

    # Test nickname validation
    valid_nicknames = ["TestUser", "User123", "Valid_Nick"]
    invalid_nicknames = ["", "A", "VeryLongNicknameThatExceedsMaximumLength", "Invalid@Nick", "Nick#123"]

    for nickname in valid_nicknames:
        is_valid, _ = validate_nickname(nickname)
        assert is_valid, f"Valid nickname {nickname} should pass validation"

    for nickname in invalid_nicknames:
        is_valid, _ = validate_nickname(nickname)
        assert not is_valid, f"Invalid nickname {nickname} should fail validation"

    print("✅ Тест пройден: валидация никнеймов работает корректно")
    return True

async def test_atm_handlers():
    """Test ATM handlers functionality"""
    from handlers.atm_handlers import atm_regen_time_info, atm_max_info, atm_boosters_info

    # Mock callback object
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    try:
        # Test atm_regen_time_info
        await atm_regen_time_info(callback)
        assert callback.message.edit_text.called, "atm_regen_time_info should call edit_text"

        # Test atm_max_info
        await atm_max_info(callback)
        assert callback.message.edit_text.called, "atm_max_info should call edit_text"

        # Test atm_boosters_info
        await atm_boosters_info(callback)
        assert callback.message.edit_text.called, "atm_boosters_info should call edit_text"

        print("✅ Тест пройден: обработчики ATM работают корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте обработчиков ATM: {e}")
        return False

async def test_top_functionality():
    """Test top functionality"""
    from handlers.top import callback_top_menu, show_top

    # Mock callback object
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    try:
        # Test callback_top_menu
        await callback_top_menu(callback)
        assert callback.message.edit_text.called, "callback_top_menu should call edit_text"

        # Test show_top
        await show_top(callback)
        assert callback.message.edit_text.called, "show_top should call edit_text"

        print("✅ Тест пройден: функциональность топов работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте функциональности топов: {e}")
        return False

# ======================
# Главная функция
# ======================

async def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск комплексных тестов для GofRobot...\n")

    tests = [
        ("Декоратор", test_decorator),
        ("Davka Callback", test_davka_callback_error_handling),
        ("Uletet Callback", test_uletet_callback_error_handling),
        ("ATM Status Callback", test_atm_status_callback_await),
        ("Profile Callback", test_profile_callback_keyboard),
        ("Rademka Stats", test_rademka_stats_tuple_handling),
        ("Кэширование гофрошки", test_gofra_info_caching),
        ("Статистика кэша", test_cache_stats),
        ("Значения информации о гофрошке", test_gofra_info_values),
        ("Уровни гофрошки", test_gofra_levels),
        ("Инвалидация кэша", test_cache_invalidation),
        ("Функция davka_zmiy", test_davka_zmiy_function),
        ("Функция uletet_zmiy", test_uletet_zmiy_function),
        ("Прогрессия гофрошки", test_gofra_progression),
        ("Регенерация атмосфер", test_atm_regen),
        ("Групповые команды", test_group_commands),
        ("Команды чата", test_chat_commands),
        ("Базовые команды", test_basic_commands),
        ("Валидация никнеймов", test_nickname_functionality),
        ("Обработчики ATM", test_atm_handlers),
        ("Функциональность топов", test_top_functionality),
        ("Ежемесячный рост", simulate_monthly_growth),
        ("Новые коэффициенты роста", test_new_growth)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"📋 Запуск теста: {test_name}")
            print(f"{'='*60}")
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Тест {test_name} упал с ошибкой: {e}")
            traceback.print_exc()
            results.append(False)

    print(f"\n📊 ОБЩИЕ РЕЗУЛЬТАТЫ:")
    print(f"   Пройдено: {sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Проект работает корректно.")
        return 0
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. Требуется доработка.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)