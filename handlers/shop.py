from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from db_manager import get_patsan
from keyboards import main_keyboard

router = Router()

def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                if len(args) > 0 and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise
    return wrapper

@router.callback_query(F.data == "shop")
async def callback_shop(callback: types.CallbackQuery):
    """Заглушка для магазина - в новой системе его нет"""
    patsan = await get_patsan(callback.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra',1))
    
    await callback.message.edit_text(
        f"🛒 МАГАЗИН УБРАН\n\n"
        f"В новой системе гофроцентрала магазин заменён на:\n\n"
        f"🏗️ Систему гофры:\n"
        f"• Чем больше гофра, тем быстрее атмосферы\n"
        f"• Длиннее кабель при давке\n"
        f"• Больше бонус при сдаче змия\n\n"
        f"Твоя гофра:\n"
        f"{gofra_info['emoji']} {gofra_info['name']}\n"
        f"⚡ Скорость: x{gofra_info['atm_speed']:.1f}\n"
        f"📏 Кабель: {gofra_info['min_cm']:.1f}-{gofra_info['max_cm']:.1f}см",
        reply_markup=main_keyboard()
    )

@router.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: types.CallbackQuery):
    """Заглушка для покупки"""
    await callback.answer("В новой системе магазин убран!", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    patsan = await get_patsan(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер: {patsan['atm_count']}/12",
        reply_markup=main_keyboard()
    )
