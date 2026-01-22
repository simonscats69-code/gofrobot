from aiogram import Router, types, F
from db_manager import get_patsan, calculate_atm_regen_time, get_gofra_info
from keyboards import back_to_profile_keyboard
import time

router = Router()

@router.callback_query(F.data == "atm_regen_time")
async def atm_regen_time_info(callback: types.CallbackQuery):
    """Информация о времени восстановления атмосфер"""
    user_id = callback.from_user.id
    patsan = await get_patsan(user_id)
    
    atm_count = patsan['atm_count']
    max_atm = 12
    
    regen_info = calculate_atm_regen_time(patsan)
    gofra_info = get_gofra_info(patsan.get('gofra',1))
    
    text = (
        f"⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ АТМОСФЕР\n\n"
        f"Текущее состояние:\n"
        f"🌀 Атмосферы: {atm_count}/{max_atm}\n"
        f"🕐 Восстановить: {regen_info['needed']} шт.\n\n"
        f"Скорость восстановления:\n"
        f"• Базовая: 1 атм. за 24 часа\n"
        f"• С учётом гофры ({gofra_info['name']}): 1 атм. за {ft(regen_info['per_atm'])}\n"
        f"• Множитель скорости: x{gofra_info['atm_speed']:.1f}\n\n"
        f"Полное восстановление:\n"
        f"🕐 Примерное время: {ft(regen_info['total'])}\n\n"
        f"Как ускорить:\n"
        f"• Повышай гофру - ускоряет восстановление\n"
        f"• Жди полной зарядки (12/12)\n"
        f"• Тогда можно давить змия!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "atm_max_info")
async def atm_max_info(callback: types.CallbackQuery):
    """Информация о максимальном запасе атмосфер"""
    user_id = callback.from_user.id
    patsan = await get_patsan(user_id)
    
    current_max = 12
    atm_count = patsan['atm_count']
    
    gofra_info = get_gofra_info(patsan.get('gofra',1))
    
    text = (
        f"📊 МАКСИМАЛЬНЫЙ ЗАПАС АТМОСФЕР\n\n"
        f"Текущие показатели:\n"
        f"🌀 Текущий запас: {atm_count}/{current_max}\n"
        f"🎯 Максимум: {current_max} атм.\n\n"
        f"Особенности системы:\n"
        f"• Фиксированный максимум: 12 атмосфер\n"
        f"• Только при полных 12 можно давить змия\n"
        f"• Восстановление зависит от гофры\n\n"
        f"Твоя гофра:\n"
        f"{gofra_info['emoji']} {gofra_info['name']}\n"
        f"⚡ Скорость восстановления: x{gofra_info['atm_speed']:.1f}\n\n"
        f"Зачем ждать 12 атмосфер?\n"
        f"• Больше кабель свиснет при давке\n"
        f"• Больше опыт для гофры\n"
        f"• Больше денег при сдаче"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "atm_boosters")
async def atm_boosters_info(callback: types.CallbackQuery):
    """Информация о бустерах активности"""
    user_id = callback.from_user.id
    patsan = await get_patsan(user_id)
    gofra_info = get_gofra_info(patsan.get('gofra',1))
    
    text = (
        f"⚡ УСКОРЕНИЕ ВОССТАНОВЛЕНИЯ\n\n"
        f"В новой системе нет бустеров!\n\n"
        f"Вместо бустеров работает:\n"
        f"🏗️ СИСТЕМА ГОФРЫ\n\n"
        f"Твоя гофра:\n"
        f"{gofra_info['emoji']} {gofra_info['name']}\n"
        f"⚡ Множитель скорости: x{gofra_info['atm_speed']:.1f}\n\n"
        f"Как улучшить гофру?\n"
        f"1. Жди полных 12 атмосфер\n"
        f"2. Дави змия (кнопка 🐍)\n"
        f"3. Получай опыт\n"
        f"4. Повышай гофру\n\n"
        f"Следующие уровни гофры:\n"
    )
    
    # Показываем следующие 3 уровня
    thresholds = [1, 10, 25, 50, 100, 200, 500, 1000]
    current_gofra = patsan.get('gofra',1)
    
    for i, threshold in enumerate(thresholds):
        if current_gofra < threshold:
            next_info = get_gofra_info(threshold)
            text += f"• {next_info['emoji']} {next_info['name']}: x{next_info['atm_speed']:.1f}\n"
            if i >= 2:  # Показываем только 3 следующих
                break
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard()
    )
    await callback.answer()

# Вспомогательная функция для форматирования времени
def ft(s):
    """Форматирование времени"""
    if s < 60: return f"{s}с"
    m, h, d = s // 60, s // 3600, s // 86400
    if d > 0: return f"{d}д {h%24}ч {m%60}м"
    if h > 0: return f"{h}ч {m%60}м {s%60}с"
    return f"{m}м {s%60}с"
