"""
Тест для прогнозирования роста гофрошки и кабеля за месяц игры.
"""

import asyncio
from db_manager import davka_zmiy, get_patsan, save_patsan, get_gofra_info

async def simulate_monthly_growth():
    """Симулируем рост гофрошки и кабеля за месяц игры (30 дней)."""

    # Создаем тестового пользователя
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

    # Сохраняем начальные данные
    await save_patsan(initial_data)

    print("📊 Симуляция роста гофрошки и кабеля за 30 дней")
    print("=" * 60)

    # Параметры симуляции
    days_to_simulate = 30
    davki_per_day = 5  # Предполагаем 5 давок в день

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
            # Симулируем давку змия
            success, patsan, result = await davka_zmiy(test_user_id)

            if success:
                total_davki += 1
                day_zmiy += result['zmiy_grams']
                total_zmiy += result['zmiy_grams']

                # Обновляем данные пользователя для следующей давки
                await save_patsan(patsan)
            else:
                # Если не удалось сделать давку, восстанавливаем атмосферы
                current_patsan = await get_patsan(test_user_id)
                current_patsan['atm_count'] = 12
                await save_patsan(current_patsan)

        # Выводим прогресс каждые 5 дней
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

    # Финальная статистика
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

    # Показываем текущий уровень гофрошки
    gofra_info = get_gofra_info(final_gofra)
    print(f"🏆 Текущий уровень гофрошки: {gofra_info['emoji']} {gofra_info['name']}")
    print(f"   📊 Длина: {gofra_info['length_display']}")
    print(f"   ⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}")
    print(f"   ⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']} г")

if __name__ == "__main__":
    asyncio.run(simulate_monthly_growth())