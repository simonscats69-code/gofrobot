from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from db_manager import get_top_players, get_gofra_info
from keyboards import main_keyboard, top_sort_keyboard

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

@router.callback_query(F.data == "top")
async def callback_top_menu(callback: types.CallbackQuery):
    """Открыть меню выбора топа"""
    await callback.message.edit_text(
        "🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА\n\n"
        "Выбери, по какому показателю сортировать рейтинг:",
        reply_markup=top_sort_keyboard()
    )

@ignore_not_modified_error
@router.callback_query(F.data.startswith("top_"))
async def show_top(callback: types.CallbackQuery):
    """Показать топ по выбранному критерию"""
    sort_type = callback.data.replace("top_", "")
    
    sort_map = {
        "gofra": ("гофре", "🏗️", "gofra"),
        "zmiy": ("змию", "🐍", "zmiy_cm"),
        "dengi": ("деньгам", "💰", "dengi"),
        "atm": ("атмосферам", "🌀", "atm_count")
    }
    
    if sort_type not in sort_map:
        await callback.answer("Неизвестный тип топа", show_alert=True)
        return
    
    sort_name, emoji, db_key = sort_map[sort_type]
    
    try:
        top_players = await get_top_players(limit=10, sort_by=db_key)
    except Exception as e:
        await callback.answer(f"Ошибка при получении топа: {e}", show_alert=True)
        return
    
    if not top_players:
        await callback.message.edit_text(
            "😕 Топ пуст!\n\n"
            "Ещё никто не заслужил места в рейтинге.\n"
            "Будь первым!",
            reply_markup=top_sort_keyboard()
        )
        return
    
    top_text = f"{emoji} Топ пацанов по {sort_name}:\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, player in enumerate(top_players):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        
        if sort_type == "gofra":
            gofra_info = get_gofra_info(player['gofra'])
            value = f"🏗️ {player['gofra']} {gofra_info['emoji']}"
        elif sort_type == "dengi":
            value = f"💰 {player['dengi']}р"
        elif sort_type == "zmiy":
            value = f"🐍 {player['zmiy_cm']:.1f}см"
        else:  # atm
            value = f"🌀 {player['atm_count']}/12"
        
        nickname = player['nickname']
        if len(nickname) > 20:
            nickname = nickname[:17] + "..."
        
        top_text += f"{medal} {nickname} — {value}\n"
    
    top_text += f"\n📊 Всего пацанов в системе: {len(top_players)}"
    
    current_user_id = callback.from_user.id
    user_position = None
    
    for i, player in enumerate(top_players):
        if player.get('user_id') == current_user_id:
            user_position = i + 1
            break
    
    if user_position:
        user_medal = medals[user_position-1] if user_position-1 < len(medals) else str(user_position)
        top_text += f"\n\n🎯 Твоя позиция: {user_medal}"
    
    await callback.message.edit_text(
        top_text,
        reply_markup=top_sort_keyboard()
    )

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main_from_top(callback: types.CallbackQuery):
    """Возврат в главное меню из топа"""
    from db_manager import get_patsan
    
    patsan = await get_patsan(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер: {patsan['atm_count']}/12",
        reply_markup=main_keyboard()
    )
