from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def top_menu_keyboard():
    """Меню выбора типа топа"""
    kb = [
        [InlineKeyboardButton(text="⭐ По авторитету", callback_data="top_avtoritet")],
        [InlineKeyboardButton(text="💰 По деньгам", callback_data="top_dengi")],
        [InlineKeyboardButton(text="🐍 По змию", callback_data="top_zmiy")],
        [InlineKeyboardButton(text="💪 По сумме скиллов", callback_data="top_total_skill")],
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
