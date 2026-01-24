from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from db_manager import get_patsan, calculate_atm_regen_time, get_gofra_info
from keyboards import back_to_profile_keyboard
from handlers.utils import ignore_not_modified_error, ft
import time

router = Router()

def pb(c, t, l=10):
    """Create a progress bar string"""
    f = int((c / t) * l) if t > 0 else 0
    return "█" * f + "░" * (l - f)

@router.callback_query(F.data == "atm_regen_time")
@ignore_not_modified_error
async def atm_regen_time_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)
        
        atm_count = patsan.get('atm_count', 0)
        max_atm = 12
        
        regen_info = calculate_atm_regen_time(patsan)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
        
        text = (
            f"⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ АТМОСФЕР\n\n"
            f"Текущее состояние:\n"
            f"🌀 Атмосферы: [{pb(atm_count, max_atm)}] {atm_count}/{max_atm}\n"
            f"📈 Восстановить: {regen_info['needed']} шт.\n\n"
            f"Скорость восстановления:\n"
            f"• Базовая: 1 атм. за 2 часа (7200с)\n"
            f"• С учётом гофрошки ({gofra_info['name']}): x{gofra_info['atm_speed']:.2f}\n"
            f"• 1 атм. за: {ft(regen_info['per_atm'])}\n\n"
            f"Полное восстановление:\n"
            f"🕐 Примерное время: {ft(regen_info['total'])}\n\n"
            f"Как ускорить:\n"
            f"• Повышай гофрошку - ускоряет восстановление\n"
            f"• Дави змия при полных 12 атмосферах\n"
            f"• Больше опыт → выше гофрошка → быстрее атмосферы"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "atm_max_info")
async def atm_max_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)
        
        current_max = 12
        atm_count = patsan.get('atm_count', 0)
        
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
        
        text = (
            f"📊 МАКСИМАЛЬНЫЙ ЗАПАС АТМОСФЕР\n\n"
            f"Текущие показатели:\n"
            f"🌀 Атмосферы: [{pb(atm_count, current_max)}] {atm_count}/{current_max}\n"
            f"🎯 Максимум: {current_max} атм.\n\n"
            f"Особенности системы:\n"
            f"• Фиксированный максимум: 12 атмосфер\n"
            f"• Только при полных 12 можно давить змия\n"
            f"• Восстановление зависит от гофрошки\n\n"
            f"Твоя гофрошка:\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"⚡ Скорость восстановления: x{gofra_info['atm_speed']:.2f}\n\n"
            f"Зачем ждать 12 атмосфер?\n"
            f"• Более тяжёлый змий при давке\n"
            f"• Больше опыт для гофрошки\n"
            f"• Укрепление кабеля (+0.1 мм за 1кг змия)"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "atm_boosters")
async def atm_boosters_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
        
        text = (
            f"⚡ УСКОРЕНИЕ ВОССТАНОВЛЕНИЯ\n\n"
            f"В новой системе нет платных бустеров!\n\n"
            f"Вместо них работает:\n"
            f"🏗️ СИСТЕМА ГОФРЫ\n\n"
            f"Твоя гофрошка:\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"⚡ Множитель скорости: x{gofra_info['atm_speed']:.2f}\n\n"
            f"Как улучшить гофрошку?\n"
            f"1. Дождись 12 атмосфер (кнопка 🌡️)\n"
            f"2. Дави змия (кнопка 🐍)\n"
            f"3. Получай опыт (0.02 мм/г змия)\n"
            f"4. Повышай гофрошку\n\n"
            f"Следующие уровни гофрошки:\n"
        )
        
        thresholds = [10.0, 50.0, 150.0, 300.0, 600.0, 1200.0, 2500.0, 5000.0, 10000.0, 20000.0]
        current_gofra = patsan.get('gofra_mm', 10.0)
        
        for i, threshold in enumerate(thresholds):
            if current_gofra < threshold:
                next_info = get_gofra_info(threshold)
                text += f"• {next_info['emoji']} {next_info['name']}: x{next_info['atm_speed']:.2f}\n"
                if i >= 2:
                    break
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)
