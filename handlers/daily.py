from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from database.db_manager import get_patsan_cached, get_daily
from keyboards.keyboards import main_keyboard
from keyboards.keyboards import daily_keyboard

router = Router()

# Декоратор для обработки ошибки "message is not modified"
def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # Игнорируем эту ошибку - ничего страшного
                if len(args) > 0 and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise  # Пропускаем другие ошибки
    return wrapper

@router.message(Command("daily"))
async def cmd_daily(message: types.Message):
    """Команда /daily - ежедневная награда"""
    user_id = message.from_user.id
    
    # Получаем награду
    result = await get_daily(user_id)
    
    if result["ok"]:
        # Успешное получение награды
        reward_text = (
            f"🎁 <b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n"
            f"💰 +{result['money']} руб. ({result['base']} + {result['bonus']} бонус)\n"
            f"🎒 +1 {result['item']}\n"
            f"🔥 Стрик: {result['streak']} дней{result.get('streak_bonus', '')}\n\n"
            f"<i>Приходи завтра за новой наградой!</i>"
        )
        
        await message.answer(
            reward_text,
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Нужно подождать
        wait_text = (
            f"⏰ <b>РАНО, ПАЦАН!</b>\n\n"
            f"Ты уже получал сегодняшнюю награду.\n"
            f"Следующая награда через: {result['wait']}\n\n"
            f"<i>Приходи позже, не торопись!</i>"
        )
        
        await message.answer(
            wait_text,
            reply_markup=daily_keyboard(),
            parse_mode="HTML"
        )

@ignore_not_modified_error
@router.callback_query(F.data == "daily")
async def callback_daily(callback: types.CallbackQuery):
    """Кнопка ежедневной награды"""
    user_id = callback.from_user.id
    
    # Получаем награду
    result = await get_daily(user_id)
    
    if result["ok"]:
        reward_text = (
            f"🎁 <b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n"
            f"💰 +{result['money']} руб. ({result['base']} + {result['bonus']} бонус)\n"
            f"🎒 +1 {result['item']}\n"
            f"🔥 Стрик: {result['streak']} дней{result.get('streak_bonus', '')}\n\n"
            f"<i>Приходи завтра за новой наградой!</i>"
        )
        
        await callback.message.edit_text(
            reward_text,
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        wait_text = (
            f"⏰ <b>РАНО, ПАЦАН!</b>\n\n"
            f"Ты уже получал сегодняшнюю награду.\n"
            f"Следующая награда через: {result['wait']}\n\n"
            f"<i>Приходи позже, не торопись!</i>"
        )
        
        await callback.message.edit_text(
            wait_text,
            reply_markup=daily_keyboard(),
            parse_mode="HTML"
        )
