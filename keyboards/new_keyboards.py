from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def daily_keyboard():
    """Клавиатура для ежедневных наград"""
    kb = [
        [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="daily")],
        [InlineKeyboardButton(text="📜 Мои достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="🏷️ Сменить ник", callback_data="change_nickname")],
        [InlineKeyboardButton(text="👊 Протащить радёмку", callback_data="rademka")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def achievements_keyboard():
    """Клавиатура для достижений"""
    kb = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="achievements")],
        [InlineKeyboardButton(text="🎁 Ежедневная награда", callback_data="daily")],
        [InlineKeyboardButton(text="🏷️ Сменить ник", callback_data="change_nickname")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def nickname_keyboard():
    """Клавиатура для смены ника"""
    kb = [
        [InlineKeyboardButton(text="🔄 Попробовать другой ник", callback_data="change_nickname")],
        [InlineKeyboardButton(text="🎁 Ежедневная награда", callback_data="daily")],
        [InlineKeyboardButton(text="📜 Достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def rademka_keyboard():
    """Клавиатура для радёмки"""
    kb = [
        [InlineKeyboardButton(text="👊 ПРОТАЩИТЬ КОГО-ТО", callback_data="rademka_fight")],
        [InlineKeyboardButton(text="📊 Статистика радёмок", callback_data="rademka_stats")],
        [InlineKeyboardButton(text="👑 Топ радёмщиков", callback_data="rademka_top")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def rademka_fight_keyboard(target_id: int = None):
    """Клавиатура для выбора цели радёмки"""
    if target_id:
        kb = [
            [InlineKeyboardButton(text="✅ ДА, ПРОТАЩИТЬ ЕГО!", callback_data=f"rademka_confirm_{target_id}")],
            [InlineKeyboardButton(text="❌ Нет, передумал", callback_data="rademka")]
        ]
    else:
        kb = [
            [InlineKeyboardButton(text="🎯 Выбрать случайную цель", callback_data="rademka_random")],
            [InlineKeyboardButton(text="👥 Посмотреть всех пацанов", callback_data="rademka_list")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="rademka")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_rademka_keyboard():
    """Кнопка назад в меню радёмки"""
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад к радёмке", callback_data="rademka")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
