from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as Btn
from typing import List, Optional

MENUS = {
    "main": [
        ("🐍 Давить коричневага", "davka"), 
        ("💰 Сдать змия", "sdat"),
        ("🏗️ Моя гофра", "gofra_info"), 
        ("🌡️ Атмосферы", "atm_status"),
        ("👊 Радёмка", "rademka"), 
        ("🏆 Топ", "top"), 
        ("📊 Профиль", "profile"),
        ("👤 Никнейм", "nickname_menu")
    ],
    
    "nickname": [
        ("📝 Изменить ник", "change_nickname"),
        ("🔄 Обновить", "nickname_menu")
    ],
    
    "rad": [
        ("🎯 Случайная цель", "rademka_random"), 
        ("📊 Статистика", "rademka_stats"), 
        ("👑 Топ", "rademka_top")
    ],
    
    "gofra": [
        ("📈 Прогресс гофры", "gofra_progress"),
        ("⚡ Скорость атмосфер", "gofra_speed"),
        ("📊 Следующая гофра", "gofra_next"),
        ("⬅️ Назад", "back_main")
    ],
    
    "top": [
        ("🏗️ По гофре", "top_gofra"), 
        ("🐍 По змию", "top_zmiy"),
        ("💰 По деньгам", "top_dengi"),
        ("🌡️ По атмосферам", "top_atm")
    ]
}

def mk(menu: str, back: str = None, cols: int = 2) -> InlineKeyboardMarkup:
    if menu not in MENUS: return main_kb()
    
    items = MENUS[menu]
    btns, row = [], []
    
    for i, (text, cb) in enumerate(items, 1):
        row.append(Btn(text=text, callback_data=cb))
        if i % cols == 0:
            btns.append(row)
            row = []
    if row: btns.append(row)
    
    if back: btns.append([Btn(text="⬅️ Назад", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def main_kb(): return mk("main")
def nickname_kb(): return mk("nickname", "back_main", 2)
def rad_kb(): return mk("rad", "back_main")
def gofra_kb(): return mk("gofra", "profile", 1)
def top_kb(): return mk("top", "back_main", 2)

def back_kb(to="back_main"): 
    return InlineKeyboardMarkup(inline_keyboard=[[Btn(text="⬅️ Назад", callback_data=to)]])

# Алиасы для совместимости
main_keyboard = main_kb
nickname_keyboard = nickname_kb
rademka_keyboard = rad_kb
top_sort_keyboard = top_kb
back_to_main_keyboard = lambda: back_kb("back_main")
back_to_profile_keyboard = lambda: back_kb("profile")
back_to_rademka_keyboard = lambda: back_kb("rademka")
profile_extended_keyboard = lambda: mk("gofra", "profile", 1)

# Специальные клавиатуры
def atm_status_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="⏱️ Время восстановления", callback_data="atm_regen_time")],
        [Btn(text="⚡ Скорость гофры", callback_data="gofra_speed")],
        [Btn(text="⬅️ В профиль", callback_data="profile")]
    ])

def gofra_info_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="📈 Прогресс", callback_data="gofra_progress")],
        [Btn(text="⚡ Скорость", callback_data="gofra_speed")],
        [Btn(text="🎯 Следующая", callback_data="gofra_next")],
        [Btn(text="⬅️ В главное", callback_data="back_main")]
    ])

# Обновлённые алиасы
level_stats_keyboard = gofra_info_kb
atm_status_keyboard = atm_status_kb
