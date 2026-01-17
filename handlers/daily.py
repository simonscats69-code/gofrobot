from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from database.db_manager import get_patsan_cached, get_daily_reward
from keyboards.keyboards import main_keyboard
from keyboards.new_keyboards import daily_keyboard, achievements_keyboard

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
    result = await get_daily_reward(user_id)
    
    if result["success"]:
        # Успешное получение награды
        reward_text = (
            f"🎁 <b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n"
            f"💰 +{result['money']} руб. ({result['base']} + {result['random_bonus']} бонус)\n"
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
            f"Следующая награда через: {result['wait_time']}\n\n"
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
    result = await get_daily_reward(user_id)
    
    if result["success"]:
        reward_text = (
            f"🎁 <b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n"
            f"💰 +{result['money']} руб. ({result['base']} + {result['random_bonus']} бонус)\n"
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
            f"Следующая награда через: {result['wait_time']}\n\n"
            f"<i>Приходи позже, не торопись!</i>"
        )
        
        await callback.message.edit_text(
            wait_text,
            reply_markup=daily_keyboard(),
            parse_mode="HTML"
        )

@router.message(Command("achievements"))
async def cmd_achievements(message: types.Message):
    """Команда /achievements - список достижений"""
    from database.db_manager import get_user_achievements
    
    user_id = message.from_user.id
    achievements = await get_user_achievements(user_id)
    
    if not achievements:
        await message.answer(
            "📜 <b>Твои достижения:</b>\n\n"
            "Пока пусто... Действуй, пацан!\n"
            "Заработай первое достижение!",
            reply_markup=achievements_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Формируем список достижений
    achievements_text = "📜 <b>ТВОИ ДОСТИЖЕНИЯ:</b>\n\n"
    
    for i, ach in enumerate(achievements[:20], 1):  # Ограничиваем 20 достижениями
        name = ach.get("name", "Неизвестное")
        reward = ach.get("reward", 0)
        unlocked_at = ach.get("unlocked_at", 0)
        
        # Форматируем дату
        if unlocked_at:
            from datetime import datetime
            date_str = datetime.fromtimestamp(unlocked_at).strftime("%d.%m.%Y")
        else:
            date_str = "давно"
        
        reward_text = f" (+{reward}р)" if reward > 0 else ""
        
        achievements_text += f"{i}. <b>{name}</b>{reward_text}\n   📅 {date_str}\n\n"
    
    # Добавляем статистику
    total_rewards = sum(ach.get("reward", 0) for ach in achievements)
    achievements_text += f"💰 <i>Всего получено с достижений: {total_rewards}р</i>"
    
    await message.answer(
        achievements_text,
        reply_markup=achievements_keyboard(),
        parse_mode="HTML"
    )

@ignore_not_modified_error
@router.callback_query(F.data == "achievements")
async def callback_achievements(callback: types.CallbackQuery):
    """Кнопка достижений"""
    from database.db_manager import get_user_achievements
    
    user_id = callback.from_user.id
    achievements = await get_user_achievements(user_id)
    
    if not achievements:
        await callback.message.edit_text(
            "📜 <b>Твои достижения:</b>\n\n"
            "Пока пусто... Действуй, пацан!\n"
            "Заработай первое достижение!",
            reply_markup=achievements_keyboard(),
            parse_mode="HTML"
        )
        return
    
    achievements_text = "📜 <b>ТВОИ ДОСТИЖЕНИЯ:</b>\n\n"
    
    for i, ach in enumerate(achievements[:20], 1):
        name = ach.get("name", "Неизвестное")
        reward = ach.get("reward", 0)
        unlocked_at = ach.get("unlocked_at", 0)
        
        if unlocked_at:
            from datetime import datetime
            date_str = datetime.fromtimestamp(unlocked_at).strftime("%d.%m.%Y")
        else:
            date_str = "давно"
        
        reward_text = f" (+{reward}р)" if reward > 0 else ""
        
        achievements_text += f"{i}. <b>{name}</b>{reward_text}\n   📅 {date_str}\n\n"
    
    total_rewards = sum(ach.get("reward", 0) for ach in achievements)
    achievements_text += f"💰 <i>Всего получено с достижений: {total_rewards}р</i>"
    
    await callback.message.edit_text(
        achievements_text,
        reply_markup=achievements_keyboard(),
        parse_mode="HTML"
    )
