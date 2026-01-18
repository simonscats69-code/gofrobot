from aiogram import Router, types, F
from database.db_manager import get_patsan_cached
from keyboards.new_keyboards import back_to_profile_keyboard
import time

router = Router()

@router.callback_query(F.data == "atm_regen_time")
async def atm_regen_time_info(callback: types.CallbackQuery):
    """Информация о времени восстановления атмосфер"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    
    base_regen_time = 30
    
    skill_zashita = patsan.get("skill_zashita", 0)
    reduced_time = base_regen_time * (1 - skill_zashita * 0.05)
    
    active_boosters = patsan.get("active_boosters", {})
    if "regen" in active_boosters:
        reduced_time *= 0.7
    
    atm_to_regen = max_atm - atm_count
    total_time_minutes = atm_to_regen * reduced_time
    
    hours = int(total_time_minutes // 60)
    minutes = int(total_time_minutes % 60)
    
    time_text = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
    
    text = (
        f"⏱️ <b>ВРЕМЯ ВОССТАНОВЛЕНИЯ АТМОСФЕР</b>\n\n"
        f"<b>Текущее состояние:</b>\n"
        f"🌀 Атмосферы: {atm_count}/{max_atm}\n"
        f"🕐 Восстановить осталось: {atm_to_regen} шт.\n\n"
        f"<b>Скорость восстановления:</b>\n"
        f"• Базовая: 1 атм. за {base_regen_time} мин.\n"
        f"• С учётом навыка ({skill_zashita} ур.): 1 атм. за {reduced_time:.1f} мин.\n"
    )
    
    if "regen" in active_boosters:
        text += f"• ⚡ <b>Бустер активности:</b> ускорение на 30%\n"
    
    text += (
        f"\n<b>Полное восстановление:</b>\n"
        f"🕐 Примерное время: {time_text}\n\n"
        f"<b>Как ускорить:</b>\n"
        f"• Прокачать навык 'Защита атмосфер'\n"
        f"• Использовать бустеры активности\n"
        f"• Купить улучшения в магазине\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "atm_max_info")
async def atm_max_info(callback: types.CallbackQuery):
    """Информация о максимальном запасе атмосфер"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    current_max = patsan.get('max_atm', 12)
    atm_count = patsan['atm_count']
    
    skill_zashita = patsan.get("skill_zashita", 0)
    max_increase_from_skill = skill_zashita * 2
    
    active_boosters = patsan.get("active_boosters", {})
    max_increase_from_boosters = 0
    
    if "capacity" in active_boosters:
        max_increase_from_boosters = active_boosters.get("capacity_amount", 5)
    
    total_max_possible = 12 + max_increase_from_skill + max_increase_from_boosters
    
    text = (
        f"📊 <b>МАКСИМАЛЬНЫЙ ЗАПАС АТМОСФЕР</b>\n\n"
        f"<b>Текущие показатели:</b>\n"
        f"🌀 Текущий запас: {atm_count}/{current_max}\n"
        f"🎯 Максимум сейчас: {current_max} атм.\n\n"
        f"<b>Из чего состоит максимум:</b>\n"
        f"• База: 12 атм.\n"
        f"• От навыка ({skill_zashita} ур.): +{max_increase_from_skill} атм.\n"
    )
    
    if max_increase_from_boosters > 0:
        text += f"• От бустеров: +{max_increase_from_boosters} атм.\n"
    
    text += (
        f"\n<b>Теоретический максимум:</b>\n"
        f"🎖️ Всего возможно: {total_max_possible} атм.\n\n"
        f"<b>Как увеличить запас:</b>\n"
        f"• Прокачать навык 'Защита атмосфер' (макс. +20 атм.)\n"
        f"• Использовать бустеры ёмкости\n"
        f"• Купить улучшения в магазине\n\n"
        f"<i>Больше атмосфер = больше давок за раз!</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "atm_boosters")
async def atm_boosters_info(callback: types.CallbackQuery):
    """Информация о бустерах активности"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    inventory = patsan.get("inventory", [])
    active_boosters = patsan.get("active_boosters", {})
    
    regen_boosters = inventory.count("бустер_активности") if inventory else 0
    capacity_boosters = inventory.count("бустер_ёмкости") if inventory else 0
    
    text = (
        f"⚡ <b>БУСТЕРЫ АКТИВНОСТИ АТМОСФЕР</b>\n\n"
        f"<b>Доступные бустеры:</b>\n"
        f"• ⏱️ Бустер времени: {regen_boosters} шт. (ускоряет восстановление на 30%)\n"
        f"• 📊 Бустер ёмкости: {capacity_boosters} шт. (+5 к максимальному запасу)\n\n"
    )
    
    if active_boosters:
        text += "<b>Активные бустеры:</b>\n"
        
        if "regen" in active_boosters:
            expires_at = active_boosters.get("regen_expires", 0)
            time_left = max(0, expires_at - time.time())
            hours_left = int(time_left // 3600)
            minutes_left = int((time_left % 3600) // 60)
            
            text += f"• ⏱️ Ускорение восстановления: {hours_left}ч {minutes_left}мин\n"
        
        if "capacity" in active_boosters:
            text += f"• 📊 Увеличение запаса: +{active_boosters.get('capacity_amount', 5)} атм.\n"
    else:
        text += "<i>Активных бустеров нет</i>\n\n"
    
    text += (
        f"\n<b>Эффекты бустеров:</b>\n"
        f"• ⏱️ <b>Бустер времени:</b>\n"
        f"  - Сокращает время восстановления на 30%\n"
        f"  - Длительность: 4 часа\n"
        f"  - Можно использовать несколько\n"
        f"  - Эффекты суммируются\n\n"
        f"• 📊 <b>Бустер ёмкости:</b>\n"
        f"  - Увеличивает максимальный запас на 5\n"
        f"  - Длительность: 6 часов\n"
        f"  - Можно использовать несколько\n\n"
        f"<b>Как использовать:</b>\n"
        f"1. Перейдите в 🎒 Инвентарь\n"
        f"2. Выберите '🛠️ Использовать предмет'\n"
        f"3. Выберите нужный бустер\n\n"
        f"<b>Как получить:</b>\n"
        f"• Крафт в меню 🔨 Крафт\n"
        f"• Покупка в 🛒 Нагнетательной столовой\n"
        f"• Награды за достижения\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
