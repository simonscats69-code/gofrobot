from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as Btn
from typing import List, Optional

MENUS = {
    "main": [
        ("🐍 Давить коричневага", "davka"), 
        ("💰 Сдать змия", "sdat"),
        ("🏗️ Моя гофра", "gofra_info"), 
        ("🔌 Мой кабель", "cable_info"),
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
    
    "cable": [
        ("💪 Сила кабеля", "cable_power_info"),
        ("⚔️ Урон в PvP", "cable_pvp_info"),
        ("📈 Прокачка", "cable_upgrade_info"),
        ("⬅️ Назад", "back_main")
    ],
    
    "top": [
        ("🏗️ По гофре", "top_gofra"), 
        ("🔌 По кабелю", "top_cable"),
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
def cable_kb(): return mk("cable", "profile", 1)
def top_kb(): return mk("top", "back_main", 2)

def back_kb(to="back_main"): 
    return InlineKeyboardMarkup(inline_keyboard=[[Btn(text="⬅️ Назад", callback_data=to)]])

main_keyboard = main_kb
nickname_keyboard = nickname_kb
rademka_keyboard = rad_kb
top_sort_keyboard = top_kb
back_to_main_keyboard = lambda: back_kb("back_main")
back_to_profile_keyboard = lambda: back_kb("profile")
back_to_rademka_keyboard = lambda: back_kb("rademka")
profile_extended_keyboard = lambda: mk("gofra", "profile", 1)

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

def cable_info_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="💪 Сила кабеля", callback_data="cable_power_info")],
        [Btn(text="⚔️ Урон в PvP", callback_data="cable_pvp_info")],
        [Btn(text="📈 Прокачка", callback_data="cable_upgrade_info")],
        [Btn(text="⬅️ В главное", callback_data="back_main")]
    ])

def profile_extended_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="🏗️ Гофра", callback_data="gofra_info")],
        [Btn(text="🔌 Кабель", callback_data="cable_info")],
        [Btn(text="🌡️ Атмосферы", callback_data="atm_status")],
        [Btn(text="⬅️ Главное меню", callback_data="back_main")]
    ])

def rademka_fight_keyboard(target_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            Btn(text="✅ Протащить!", callback_data=f"rademka_confirm_{target_id}"),
            Btn(text="❌ Отмена", callback_data="rademka")
        ]
    ])

def back_to_rademka_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="⬅️ Назад к радёмке", callback_data="rademka")]
    ])

level_stats_keyboard = gofra_info_kb
atm_status_keyboard = atm_status_kb
cable_stats_keyboard = cable_info_kb
