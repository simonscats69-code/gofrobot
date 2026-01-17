from aiogram import Router, types, F
from aiogram.filters import Command
from database.db_manager import (
    get_patsan_cached, get_available_specializations, 
    buy_specialization, get_specialization_bonuses
)
from keyboards.keyboards import main_keyboard, back_to_specializations_keyboard
from keyboards.new_keyboards import specializations_info_keyboard, specialization_confirmation_keyboard

router = Router()

@router.message(Command("spec"))
async def cmd_spec_short(message: types.Message):
    """Короткая команда для специализаций"""
    await cmd_specializations(message)

@router.callback_query(F.data == "specializations")
async def callback_specializations_menu(callback: types.CallbackQuery):
    """Меню специализаций через колбэк"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    current_spec = patsan.get("specialization", "")
    
    if current_spec:
        spec_bonuses = get_specialization_bonuses(current_spec)
        bonuses_text = "\n".join([f"• {k}: {v}" for k, v in spec_bonuses.items()])
        
        await callback.message.edit_text(
            f"<b>🌳 ТВОЯ СПЕЦИАЛИЗАЦИЯ</b>\n\n"
            f"<b>{current_spec.upper()}</b>\n\n"
            f"<b>🎁 Бонусы:</b>\n{bonuses_text}\n\n"
            f"<i>Сейчас у тебя может быть только одна специализация.</i>\n"
            f"<i>Чтобы сменить, нужно сначала сбросить текущую (стоимость: 2000р).</i>",
            reply_markup=back_to_specializations_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Если специализации нет, показываем доступные
    available_specs = await get_available_specializations(user_id)
    
    text = "<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n"
    text += "<i>Специализация даёт уникальные бонусы и открывает новые возможности.</i>\n"
    text += "<i>Можно выбрать только одну. Выбор бесплатен при выполнении требований.</i>\n\n"
    
    for spec in available_specs:
        status = "✅ Доступна" if spec["available"] else "❌ Недоступна"
        price_text = f" | Цена: {spec['price']}р" if spec['available'] else ""
        text += f"<b>{spec['name']}</b> {status}{price_text}\n"
        text += f"<i>{spec['description']}</i>\n"
        
        if not spec["available"] and spec["missing"]:
            text += f"<code>Требуется: {', '.join(spec['missing'])}</code>\n"
        
        text += "\n"
    
    text += "<i>Выбери специализацию для подробной информации:</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=specializations_info_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("spec_info_"))
async def callback_spec_info(callback: types.CallbackQuery):
    """Информация о конкретной специализации"""
    spec_type = callback.data.replace("spec_info_", "")
    
    spec_map = {
        "davila": {
            "name": "Давила",
            "description": "Мастер давления коричневага",
            "requirements": "💪 Давка змия: 5 ур.\n🐍 Накоплено змия: 50кг",
            "bonuses": "• +50% к выходу змия\n• -1 атмосфера на действие\n• Открывает: Гигантская давка",
            "price": 1500
        },
        "ohotnik": {
            "name": "Охотник за двенашками",
            "description": "Находит то, что другие не видят",
            "requirements": "🔍 Находка двенашек: 5 ур.\n🧱 Двенашка в инвентаре",
            "bonuses": "• +15% к шансу находок\n• 5% шанс на редкий предмет\n• Открывает: Детектор двенашек",
            "price": 1200
        },
        "neprobivaemy": {
            "name": "Непробиваемый",
            "description": "Железные кишки и стальные нервы",
            "requirements": "🛡️ Защита атмосфер: 5 ур.\n⭐ Авторитет: 20",
            "bonuses": "• -10% времени восстановления атмосфер\n• +15% защиты в радёмках\n• Открывает: Железный живот",
            "price": 2000
        }
    }
    
    if spec_type not in spec_map:
        await callback.answer("Неизвестная специализация", show_alert=True)
        return
    
    spec_data = spec_map[spec_type]
    
    await callback.message.edit_text(
        f"<b>🌳 {spec_data['name'].upper()}</b>\n\n"
        f"<i>{spec_data['description']}</i>\n\n"
        f"<b>💰 Цена:</b> {spec_data['price']}р\n\n"
        f"<b>📋 Требования:</b>\n{spec_data['requirements']}\n\n"
        f"<b>🎁 Бонусы:</b>\n{spec_data['bonuses']}\n\n"
        f"<i>Выбрать эту специализацию?</i>",
        reply_markup=specialization_confirmation_keyboard(spec_type),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("specialization_buy_"))
async def callback_specialization_buy(callback: types.CallbackQuery):
    """Покупка специализации"""
    spec_id = callback.data.replace("specialization_buy_", "")
    user_id = callback.from_user.id
    
    success, message = await buy_specialization(user_id, spec_id)
    
    if success:
        await callback.message.edit_text(
            f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n"
            f"{message}\n\n"
            f"Теперь ты обладатель уникальной специализации!\n"
            f"Используй её бонусы по максимуму.",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer(message, show_alert=True)
        await callback_specializations_menu(callback)

@router.callback_query(F.data.startswith("specialization_info_"))
async def callback_specialization_info(callback: types.CallbackQuery):
    """Информация о специализации для подтверждения"""
    spec_id = callback.data.replace("specialization_info_", "")
    
    # Просто перенаправляем на общую информацию
    await callback_spec_info(callback)
