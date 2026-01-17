from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    """Главное меню пацана"""
    kb = [
        [InlineKeyboardButton(text="🐍 Давить коричневага", callback_data="davka")],
        [InlineKeyboardButton(text="💰 Сдать змия на металл", callback_data="sdat")],
        [InlineKeyboardButton(text="📈 Прокачать скиллы", callback_data="pump")],
        [InlineKeyboardButton(text="🛒 Нагнетательная столовая", callback_data="shop")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton(text="🏆 Топ пацанов", callback_data="top")],  # НОВАЯ КНОПКА
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def pump_keyboard():
    """Клавиатура прокачки скиллов"""
    kb = [
        [InlineKeyboardButton(text="💪 Давка змия", callback_data="pump_davka")],
        [InlineKeyboardButton(text="🛡️ Защита атмосфер", callback_data="pump_zashita")],
        [InlineKeyboardButton(text="🔍 Находка двенашек", callback_data="pump_nahodka")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def shop_keyboard():
    """Клавиатура нагнетательной столовой"""
    kb = [
        [InlineKeyboardButton(text="🥛 Ряженка (500р)", callback_data="buy_ryazhenka")],
        [InlineKeyboardButton(text="🍵 Чай сливовый (700р)", callback_data="buy_tea_slivoviy")],
        [InlineKeyboardButton(text="🧋 Бублэки (600р)", callback_data="buy_bubbleki")],
        [InlineKeyboardButton(text="🥐 Курвасаны (1000р)", callback_data="buy_kuryasany")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_keyboard():
    """Простая кнопка назад"""
    kb = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)
