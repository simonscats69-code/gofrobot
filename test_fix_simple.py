#!/usr/bin/env python3
"""
Простой тест для проверки, что исправленный код импортируется и работает без синтаксических ошибок
"""

import sys
import traceback

def test_imports():
    """Тест: проверка импорта модулей"""
    print("🧪 Тестирование импорта модулей...")

    try:
        # Пробуем импортировать модули с исправлениями
        from handlers import callbacks, nickname_and_rademka
        print("✅ Успешно импортированы handlers.callbacks и handlers.nickname_and_rademka")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        traceback.print_exc()
        return False

def test_syntax():
    """Тест: проверка синтаксиса ключевых функций"""
    print("\n🧪 Тестирование синтаксиса ключевых функций...")

    try:
        from handlers.callbacks import (
            handle_davka_callback,
            handle_uletet_callback,
            handle_atm_status_callback,
            handle_profile_callback
        )
        from handlers.nickname_and_rademka import rademka_stats

        # Проверяем, что функции существуют и являются корутинами
        assert callable(handle_davka_callback), "handle_davka_callback не является callable"
        assert callable(handle_uletet_callback), "handle_uletet_callback не является callable"
        assert callable(handle_atm_status_callback), "handle_atm_status_callback не является callable"
        assert callable(handle_profile_callback), "handle_profile_callback не является callable"
        assert callable(rademka_stats), "rademka_stats не является callable"

        print("✅ Все функции существуют и являются callable")
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки функций: {e}")
        traceback.print_exc()
        return False

def test_code_structure():
    """Тест: проверка структуры кода на наличие исправлений"""
    print("\n🧪 Тестирование структуры кода...")

    try:
        import inspect
        from handlers.callbacks import handle_davka_callback, handle_uletet_callback, handle_atm_status_callback

        # Проверяем, что в handle_davka_callback есть обработка ошибки с извлечением строки
        source = inspect.getsource(handle_davka_callback)
        if "error_msg = res.get('error'" in source:
            print("✅ handle_davka_callback правильно извлекает сообщение об ошибке")
        else:
            print("❌ handle_davka_callback не извлекает сообщение об ошибке правильно")
            return False

        # Проверяем, что в handle_uletet_callback есть обработка ошибки с извлечением строки
        source = inspect.getsource(handle_uletet_callback)
        if "error_msg = res.get('error'" in source:
            print("✅ handle_uletet_callback правильно извлекает сообщение об ошибке")
        else:
            print("❌ handle_uletet_callback не извлекает сообщение об ошибке правильно")
            return False

        # Проверяем, что в handle_atm_status_callback есть await для calculate_atm_regen_time
        source = inspect.getsource(handle_atm_status_callback)
        if "await calculate_atm_regen_time" in source:
            print("✅ handle_atm_status_callback правильно использует await")
        else:
            print("❌ handle_atm_status_callback не использует await")
            return False

        # Проверяем, что в handle_profile_callback используется main_keyboard
        # Импортируем функцию прямо здесь
        from handlers.callbacks import handle_profile_callback
        source = inspect.getsource(handle_profile_callback)
        if "reply_markup=main_keyboard()" in source:
            print("✅ handle_profile_callback использует main_keyboard")
        else:
            print("❌ handle_profile_callback не использует main_keyboard")
            return False

        return True
    except Exception as e:
        print(f"❌ Ошибка проверки структуры кода: {e}")
        traceback.print_exc()
        return False

def test_rademka_stats_structure():
    """Тест: проверка структуры rademka_stats"""
    print("\n🧪 Тестирование структуры rademka_stats...")

    try:
        # Читаем файл напрямую, так как inspect.getsource возвращает код декоратора
        with open('/workspaces/gofrobot/handlers/nickname_and_rademka.py', 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Ищем функцию rademka_stats в файле
        lines = file_content.split('\n')
        in_function = False
        function_lines = []
        indent_level = None

        for i, line in enumerate(lines):
            if 'async def rademka_stats' in line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                function_lines.append(line)
                continue

            if in_function:
                current_indent = len(line) - len(line.lstrip())
                # Продолжаем, если строка не пустая и имеет правильный отступ
                if line.strip() and current_indent > indent_level:
                    function_lines.append(line)
                elif line.strip() and current_indent <= indent_level and 'async def' not in line:
                    # Конец функции
                    break
                elif not line.strip():
                    function_lines.append(line)

        source = '\n'.join(function_lines)
        print(f"🔍 Найдено {len(function_lines)} строк в функции rademka_stats")
        if len(function_lines) < 10:
            print("❌ Функция слишком короткая, возможно не найдена")
            return False

        # Проверяем, что обращение к результату запроса идет через индексы, а не через .get()
        if "s[0]" in source and "s[1]" in source and "s[2]" in source:
            print("✅ rademka_stats правильно обращается к кортежу по индексам")
        else:
            print("❌ rademka_stats не обращается к кортежу по индексам")
            # Ищем вхождения s[ в источнике
            s_bracket_matches = [i for i, line in enumerate(source.split('\n')) if 's[' in line]
            if s_bracket_matches:
                print(f"🔍 Найдены обращения s[ в строках: {s_bracket_matches}")
                for line_num in s_bracket_matches[:3]:  # Показать первые 3 вхождения
                    line = source.split('\n')[line_num]
                    print(f"   Строка {line_num}: {line.strip()}")
            else:
                print("🔍 В источнике нет обращений s[")
            return False

        # Проверяем, что нет обращений через .get() для переменной s
        # Разрешаем .get() для других объектов, но не для s
        lines = source.split('\n')
        bad_lines = []
        for i, line in enumerate(lines):
            if 's.get(' in line and 's[' not in line:
                bad_lines.append((i+1, line.strip()))

        if not bad_lines:
            print("✅ rademka_stats не использует .get() для кортежа s")
        else:
            print("❌ rademka_stats использует .get() для кортежа s в строках:")
            for line_num, line_content in bad_lines:
                print(f"   Строка {line_num}: {line_content}")
            return False

        return True
    except Exception as e:
        print(f"❌ Ошибка проверки rademka_stats: {e}")
        traceback.print_exc()
        return False

def main():
    """Запуск всех тестов"""
    print("🚀 Запуск простых тестов для проверки исправлений...\n")

    tests = [
        test_imports,
        test_syntax,
        test_code_structure,
        test_rademka_stats_structure
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Тест {test.__name__} упал с ошибкой: {e}")
            results.append(False)

    print(f"\n📊 Результаты тестов:")
    print(f"   Пройдено: {sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 Все тесты пройдены! Исправления применены успешно.")
        print("\n📋 Что было исправлено:")
        print("   1. handle_davka_callback: извлечение строки из словаря ошибки")
        print("   2. handle_uletet_callback: извлечение строки из словаря ошибки")
        print("   3. handle_atm_status_callback: добавлен await для корутины")
        print("   4. handle_profile_callback: заменена несуществующая клавиатура")
        print("   5. rademka_stats: исправлено обращение к кортежу вместо словаря")
        return 0
    else:
        print("\n❌ Некоторые тесты не прошли. Проверьте исправления.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)