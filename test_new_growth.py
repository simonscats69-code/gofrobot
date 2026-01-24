"""
Тест для проверки новых коэффициентов роста гофрошки и кабеля.
"""

import asyncio
from db_manager import davka_zmiy, get_patsan, save_patsan, get_gofra_info

async def test_new_growth():
    """Тестируем новые коэффициенты роста за 30 дней (30 давок)."""

    # Создаем тестового пользователя
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

    print("🧪 Тестирование новых коэффициентов роста")
    print("=" * 50)
    print("📅 Период: 30 дней (30 давок)")
    print("🎯 Цели:")
    print("   🏗️ Гофра: 70-100 мм (7-10 см)")
    print("   🔌 Кабель: 300-500 мм (30-50 см)")
    print()

    initial_gofra = initial_data['gofra_mm']
    initial_cable = initial_data['cable_mm']
    total_zmiy = 0
    kilogram_count = 0

    for day in range(1, 31):
        # Симулируем давку змия
        success, patsan, result = await davka_zmiy(test_user_id)

        if success:
            total_zmiy += result['zmiy_grams']
            if result['zmiy_grams'] > 1000:
                kilogram_count += 1

            # Восстанавливаем атмосферы для следующей давки
            patsan['atm_count'] = 12
            await save_patsan(patsan)

            # Показываем прогресс каждые 5 дней
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

        # Пауза для восстановления атмосфер (24 часа)
        await asyncio.sleep(0.01)

    # Финальная статистика
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

    # Показываем текущий уровень гофрошки
    gofra_info = get_gofra_info(final_gofra)
    print(f"🏆 Текущий уровень гофрошки: {gofra_info['emoji']} {gofra_info['name']}")
    print(f"   📊 Длина: {gofra_info['length_display']}")
    print(f"   ⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}")
    print(f"   ⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']} г")

    # Проверка целей
    gofra_goal_achieved = 70 <= gofra_growth <= 100
    cable_goal_achieved = 300 <= cable_growth <= 500

    print()
    print("🎯 ОБЩИЙ РЕЗУЛЬТАТ:")
    if gofra_goal_achieved and cable_goal_achieved:
        print("   🎉 ВСЕ ЦЕЛИ ДОСТИГНУТЫ! НОВЫЕ КОЭФФИЦИЕНТЫ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print("   ⚠️ Цели не достигнуты. Требуется корректировка коэффициентов.")

if __name__ == "__main__":
    asyncio.run(test_new_growth())