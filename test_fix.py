#!/usr/bin/env python3
"""
Тест для проверки исправленных ошибок в обработчиках колбэков
"""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message
from handlers.callbacks import (
    handle_davka_callback,
    handle_uletet_callback,
    handle_atm_status_callback,
    handle_profile_callback
)
from handlers.nickname_and_rademka import rademka_stats

async def test_davka_callback_error_handling():
    """Тест: davka callback должен возвращать строку, а не словарь"""
    print("🧪 Тестирование handle_davka_callback...")

    # Создаем mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()

    # Мокаем функцию davka_zmiy, чтобы она возвращала ошибку
    with patch('handlers.callbacks.davka_zmiy', new_callable=AsyncMock) as mock_davka:
        mock_davka.return_value = (False, {}, {'error': 'Нужно 12 атмосфер для давки змия!'})

        try:
            await handle_davka_callback(callback)
            # Проверяем, что callback.answer был вызван с строкой, а не со словарем
            call_args = callback.answer.call_args
            if call_args:
                actual_text = call_args[0][0]
                print(f"✅ Callback answer вызван с текстом: {actual_text}")
                print(f"✅ Тип текста: {type(actual_text)}")
                assert isinstance(actual_text, str), f"Ожидалась строка, получено {type(actual_text)}"
                print("✅ Тест пройден: davka callback возвращает строку")
            else:
                print("❌ Ошибка: callback.answer не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

    return True

async def test_uletet_callback_error_handling():
    """Тест: uletet callback должен возвращать строку, а не словарь"""
    print("\n🧪 Тестирование handle_uletet_callback...")

    # Создаем mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()

    # Мокаем функцию uletet_zmiy, чтобы она возвращала ошибку
    with patch('handlers.callbacks.uletet_zmiy', new_callable=AsyncMock) as mock_uletet:
        mock_uletet.return_value = (False, {}, {'error': 'Нет змия для отправки!'})

        try:
            await handle_uletet_callback(callback)
            # Проверяем, что callback.answer был вызван с строкой, а не со словарем
            call_args = callback.answer.call_args
            if call_args:
                actual_text = call_args[0][0]
                print(f"✅ Callback answer вызван с текстом: {actual_text}")
                print(f"✅ Тип текста: {type(actual_text)}")
                assert isinstance(actual_text, str), f"Ожидалась строка, получено {type(actual_text)}"
                print("✅ Тест пройден: uletet callback возвращает строку")
            else:
                print("❌ Ошибка: callback.answer не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

    return True

async def test_atm_status_callback_await():
    """Тест: atm status callback должен использовать await для корутины"""
    print("\n🧪 Тестирование handle_atm_status_callback...")

    # Создаем mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    # Мокаем функции
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
            # Проверяем, что calculate_atm_regen_time был вызван с await
            assert mock_calculate.await_count > 0, "calculate_atm_regen_time не был await-нут"
            print("✅ Тест пройден: calculate_atm_regen_time используется с await")
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

    return True

async def test_profile_callback_keyboard():
    """Тест: profile callback должен использовать существующую клавиатуру"""
    print("\n🧪 Тестирование handle_profile_callback...")

    # Создаем mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    # Мокаем функции
    mock_patsan = {'atm_count': 5, 'gofra_mm': 15.0, 'cable_mm': 10.0, 'zmiy_grams': 1000.0, 'total_zmiy_grams': 0}
    mock_gofra_info = {
        'emoji': '🐍',
        'name': 'Коричневый бог',
        'atm_speed': 2.0,
        'min_grams': 100,
        'max_grams': 500,
        'length_display': '15.0 мм'
    }

    # Прямое тестирование без сложных моков
    try:
        # Импортируем функции напрямую
        from handlers.callbacks import handle_profile_callback
        from db_manager import get_patsan, get_gofra_info, format_length
        from keyboards import main_keyboard

        # Мокаем только необходимые части
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
                # Проверяем, что edit_text был вызван с правильной клавиатурой
                call_args = callback.message.edit_text.call_args
                if call_args:
                    kwargs = call_args[1]
                    keyboard = kwargs.get('reply_markup')
                    print(f"✅ Используемая клавиатура: {keyboard}")
                    # Проверяем, что это не profile_extended_kb (которая не существует)
                    assert keyboard == "main_keyboard_mock", f"Ожидалась main_keyboard, получено {keyboard}"
                    print("✅ Тест пройден: profile callback использует существующую клавиатуру")
                else:
                    print("❌ Ошибка: edit_text не был вызван")
                    return False
            except Exception as e:
                print(f"❌ Ошибка в тесте: {e}")
                return False

    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        return False

    return True

async def test_rademka_stats_tuple_handling():
    """Тест: rademka_stats должен правильно обрабатывать кортеж из SQL-запроса"""
    print("\n🧪 Тестирование rademka_stats...")

    # Создаем mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    # Мокаем функции
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = (10, 7, 3)  # (total_fights, wins, losses) как кортеж

    mock_cursor2 = AsyncMock()
    mock_cursor2.fetchone.return_value = (2,)  # (hour_fights,) как кортеж

    with patch('db_manager.get_connection', new_callable=AsyncMock) as mock_get_conn, \
         patch('handlers.nickname_and_rademka.back_kb') as mock_back_kb:

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        mock_back_kb.return_value = "back_kb_mock"

        try:
            await rademka_stats(callback)
            # Проверяем, что edit_text был вызван
            call_args = callback.message.edit_text.call_args
            if call_args:
                text = call_args[0][0]
                print(f"✅ Статистика радёмок сгенерирована: {text[:100]}...")
                # Проверяем, что в тексте есть ожидаемые данные
                assert "10" in text, "Общее количество боёв не найдено"
                assert "7" in text, "Количество побед не найдено"
                assert "3" in text, "Количество поражений не найдено"
                assert "70.0%" in text, "Винрейт не рассчитан правильно"
                print("✅ Тест пройден: rademka_stats правильно обрабатывает кортеж из SQL")
            else:
                print("❌ Ошибка: edit_text не был вызван")
                return False
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return False

    return True

async def main():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов для исправленных ошибок...\n")

    tests = [
        test_davka_callback_error_handling,
        test_uletet_callback_error_handling,
        test_atm_status_callback_await,
        test_profile_callback_keyboard,
        test_rademka_stats_tuple_handling
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Тест {test.__name__} упал с ошибкой: {e}")
            results.append(False)

    print(f"\n📊 Результаты тестов:")
    print(f"   Пройдено: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 Все тесты пройдены! Ошибки исправлены успешно.")
        return 0
    else:
        print("❌ Некоторые тесты не прошли. Проверьте исправления.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)