from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from database.db_manager import get_top_players
from keyboards.keyboards import main_keyboard
from keyboards.keyboards import top_sort_keyboard  # ИЗМЕНЕНО

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

@router.callback_query(F.data == "top")
async def callback_top_menu(callback: types.CallbackQuery):
    """Открыть меню выбора топа (обработчик кнопки '🏆 Топ пацанов')"""
    await callback.message.edit_text(
        "🏆 <b>Топ пацанов с гофроцентрала</b>\n\n"
        "Выбери, по какому показателю сортировать рейтинг:",
        reply_markup=top_sort_keyboard(),  # ИЗМЕНЕНО
        parse_mode="HTML"
    )

@ignore_not_modified_error
@router.callback_query(F.data.startswith("top_"))
async def show_top(callback: types.CallbackQuery):
    """Показать топ по выбранному критерию"""
    sort_type = callback.data.replace("top_", "")
    
    # Маппинг callback -> (русское название, эмодзи, ключ для сортировки)
    sort_map = {
        "avtoritet": ("авторитету", "⭐", "avtoritet"),
        "dengi": ("деньгам", "💰", "dengi"),
        "zmiy": ("змию", "🐍", "zmiy"),
        "total_skill": ("сумме скиллов", "💪", "total_skill")
    }
    
    if sort_type not in sort_map:
        await callback.answer("Неизвестный тип топа", show_alert=True)
        return
    
    sort_name, emoji, db_key = sort_map[sort_type]
    
    # Получаем топ из базы данных
    try:
        top_players = await get_top_players(limit=10, sort_by=db_key)
    except Exception as e:
        await callback.answer(f"Ошибка при получении топа: {e}", show_alert=True)
        return
    
    if not top_players:
        await callback.message.edit_text(
            "😕 <b>Топ пуст!</b>\n\n"
            "Ещё никто не заслужил места в рейтинге.\n"
            "Будь первым!",
            reply_markup=top_sort_keyboard(),  # ИЗМЕНЕНО
            parse_mode="HTML"
        )
        return
    
    # Формируем красивый топ
    top_text = f"{emoji} <b>Топ пацанов по {sort_name}:</b>\n\n"
    
    # Медальки для первых трёх мест
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, player in enumerate(top_players):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        
        # Форматируем значение в зависимости от типа топа
        if sort_type == "avtoritet":
            value = f"⭐ {player['avtoritet']}"
        elif sort_type == "dengi":
            value = f"💰 {player['dengi_formatted']}"
        elif sort_type == "zmiy":
            value = f"🐍 {player['zmiy_formatted']}"
        else:  # total_skill
            value = f"💪 {player['total_skill']} ур."
        
        # Обрезаем слишком длинные ники
        nickname = player['nickname']
        if len(nickname) > 20:
            nickname = nickname[:17] + "..."
        
        top_text += f"{medal} <code>{nickname}</code> — {value}\n"
    
    # Добавляем статистику
    top_text += f"\n📊 <i>Всего пацанов в системе: {len(top_players)}</i>"
    
    # Показываем пользователю его позицию, если он есть в топе
    current_user_id = callback.from_user.id
    user_position = None
    
    for i, player in enumerate(top_players):
        if player.get('user_id') == current_user_id:
            user_position = i + 1
            break
    
    if user_position:
        user_medal = medals[user_position-1] if user_position-1 < len(medals) else str(user_position)
        top_text += f"\n\n🎯 <b>Твоя позиция:</b> {user_medal}"
    
    await callback.message.edit_text(
        top_text,
        reply_markup=top_sort_keyboard(),  # ИЗМЕНЕНО
        parse_mode="HTML"
    )

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main_from_top(callback: types.CallbackQuery):
    """Возврат в главное меню из топа"""
    from database.db_manager import get_patsan_cached
    
    patsan = await get_patsan_cached(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер в кишке: {patsan['atm_count']}/12",
        reply_markup=main_keyboard()
    )
