from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as Btn
from typing import List, Optional

MENUS = {
    "main": [
        ("🐍 Давить коричневага", "davka"), 
        ("💰 Сдать змия", "sdat"),
        ("📈 Прокачать", "pump"), 
        ("🌳 Специализации", "specializations"),
        ("🛒 Магазин", "shop"), 
        ("🔨 Крафт", "craft"),
        ("🎁 Ежедневная", "daily"), 
        ("👊 Радёмка", "rademka"), 
        ("🎒 Инвентарь", "inventory"),
        ("👤 Никнейм", "nickname_menu"),
        ("🏆 Топ", "top"), 
        ("📊 Профиль", "profile")
    ],
    
    "nickname": [
        ("📝 Изменить ник", "change_nickname"),
        ("⭐ Моя репутация", "my_reputation"),
        ("👑 Топ репутации", "top_reputation"),
        ("🔄 Обновить", "nickname_menu")
    ],
    
    "pump": [
        ("💪 Давка", "pump_davka"), 
        ("🛡️ Защита", "pump_zashita"), 
        ("🔍 Находка", "pump_nahodka")
    ],
    
    "shop": [
        ("🥛 Ряженка (300р)", "buy_ryazhenka"), 
        ("🍵 Чай (500р)", "buy_tea_slivoviy"),
        ("🧋 Бублэки (800р)", "buy_bubbleki"), 
        ("🥐 Курвасаны (1500р)", "buy_kuryasany")
    ],
    
    "shop_cat": [
        ("🥛 Нагнетатели", "shop"), 
        ("⚡ Бустеры", "shop_boosters"),
        ("🔧 Инструменты", "shop_tools"), 
        ("🎁 Наборы", "shop_random")
    ],
    
    "specs": [
        ("💪 Давила", "spec_info_davila"), 
        ("🔍 Охотник", "spec_info_ohotnik"),
        ("🛡️ Непробиваемый", "spec_info_neprobivaemy"), 
        ("❓ Инфо", "specialization_info")
    ],
    
    "craft": [
        ("🛠️ Крафт", "craft_items"), 
        ("📜 Рецепты", "craft_recipes"),
        ("📊 История", "craft_history")
    ],
    
    "rad": [
        ("🎯 Случайная цель", "rademka_random"), 
        ("📊 Статистика", "rademka_stats"), 
        ("👑 Топ", "rademka_top")
    ],
    
    "daily": [
        ("🔄 Проверить", "daily")
    ],
    
    "profile_ext": [
        ("📈 Уровни", "level_stats"),
        ("🌡️ Атмосферы", "atm_status")
    ],
    
    "top": [
        ("⭐ Авторитет", "top_avtoritet"), 
        ("💰 Деньги", "top_dengi"),
        ("🐍 Змий", "top_zmiy"), 
        ("💪 Скиллы", "top_total_skill"),
        ("📈 Уровень", "top_level"), 
        ("👊 Победы", "top_rademka_wins")
    ],
    
    "inv": [
        ("🛠️ Использовать", "inventory_use"), 
        ("🔨 Крафт", "craft"),
        ("📦 Сортировать", "inventory_sort"), 
        ("🗑️ Выбросить", "inventory_trash")
    ],
    
    "craft_items": [
        ("✨ Супер-двенашка", "craft_super_dvenashka"),
        ("⚡ Вечный двигатель", "craft_vechnyy_dvigatel"),
        ("👑 Царский обед", "craft_tarskiy_obed"),
        ("🌀 Бустер атмосфер", "craft_booster_atm")
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

def conf_kb(action: str, target: int = None, info: str = None) -> InlineKeyboardMarkup:
    btns = [[Btn(text="✅ ДА", callback_data=f"confirm_{action}_{target}" if target else f"confirm_{action}"),
             Btn(text="❌ НЕТ", callback_data=f"cancel_{action}")]]
    
    if info: btns.append([Btn(text="📋 Подробнее", callback_data=info)])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def rademka_fight_keyboard(target: int = None):
    if not target:
        return InlineKeyboardMarkup(inline_keyboard=[
            [Btn(text="🎯 Случайная цель", callback_data="rademka_random")],
            [Btn(text="⬅️ Назад", callback_data="rademka")]
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="✅ ДА, ПРОТАЩИТЬ!", callback_data=f"rademka_confirm_{target}")],
        [Btn(text="❌ Передумал", callback_data="rademka")]
    ])

def main_kb(): return mk("main")
def nickname_kb(): return mk("nickname", "back_main", 2)
def pump_kb(): return mk("pump", "back_main", 1)
def shop_kb(): return mk("shop", "back_main", 1)
def shop_cat_kb(): return mk("shop_cat", "shop", 1)
def specs_kb(): return mk("specs", "back_main")
def craft_kb(): return mk("craft", "back_main")
def rad_kb(): return mk("rad", "back_main")
def daily_kb(): return mk("daily", "back_main")
def profile_ext_kb(): return mk("profile_ext", "profile", 1)
def top_kb(): return mk("top", "back_main", 2)
def inv_kb(): return mk("inv", "inventory")
def craft_items_kb(): return mk("craft_items", "craft", 1)

def level_stats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="📈 Прогресс", callback_data="level_progress")],
        [Btn(text="🏆 Топ", callback_data="top_level")],
        [Btn(text="🎯 До след. уровня", callback_data="level_next")],
        [Btn(text="⬅️ В профиль", callback_data="profile")]
    ])

def atm_status_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="⏱️ Восстановление", callback_data="atm_regen_time")],
        [Btn(text="📊 Максимум", callback_data="atm_max_info")],
        [Btn(text="⚡ Бустеры", callback_data="atm_boosters")],
        [Btn(text="⬅️ В профиль", callback_data="profile")]
    ])

def craft_recipes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="✨ Супер-двенашка", callback_data="recipe_super_dvenashka")],
        [Btn(text="⚡ Вечный двигатель", callback_data="recipe_vechnyy_dvigatel")],
        [Btn(text="👑 Царский обед", callback_data="recipe_tarskiy_obed")],
        [Btn(text="🌀 Бустер атмосфер", callback_data="recipe_booster_atm")],
        [Btn(text="🛠️ К крафту", callback_data="craft_items")],
        [Btn(text="⬅️ Назад", callback_data="craft")]
    ])

def specs_info_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="💪 Давила - инфо", callback_data="spec_info_davila")],
        [Btn(text="🔍 Охотник - инфо", callback_data="spec_info_ohotnik")],
        [Btn(text="🛡️ Непробиваемый - инфо", callback_data="spec_info_neprobivaemy")],
        [Btn(text="💰 Купить", callback_data="specializations")],
        [Btn(text="⬅️ Назад", callback_data="back_main")]
    ])

def back_kb(to="back_main"): return InlineKeyboardMarkup(inline_keyboard=[[Btn(text="⬅️ Назад", callback_data=to)]])
def back_main(): return back_kb()
def back_craft(): return back_kb("craft")
def back_specs(): return back_kb("specializations")
def back_profile(): return back_kb("profile")
def back_rad(): return back_kb("rademka")
def back_inv(): return back_kb("inventory")

main_keyboard = main_kb
nickname_keyboard = nickname_kb
pump_keyboard = pump_kb
shop_keyboard = shop_kb
shop_categories_keyboard = shop_cat_kb
specializations_keyboard = specs_kb
craft_keyboard = craft_kb
rademka_keyboard = rad_kb
daily_keyboard = daily_kb
level_stats_keyboard = level_stats_kb
atm_status_keyboard = atm_status_kb
profile_extended_keyboard = profile_ext_kb
top_sort_keyboard = top_kb
top_menu_keyboard = top_kb
inventory_management_keyboard = inv_kb
craft_items_keyboard = craft_items_kb
craft_recipes_keyboard = craft_recipes_kb
specializations_info_keyboard = specs_info_kb
back_keyboard = back_main
back_to_main_keyboard = back_main
back_to_craft_keyboard = back_craft
back_to_specializations_keyboard = back_specs
back_to_profile_keyboard = back_profile
back_to_rademka_keyboard = back_rad
back_to_inventory_keyboard = back_inv
craft_confirmation_keyboard = lambda r_id: conf_kb(f"craft_execute_{r_id}", info=f"recipe_info_{r_id}")
specialization_confirmation_keyboard = lambda s_id: conf_kb(f"specialization_buy_{s_id}", info=f"specialization_info_{s_id}")
confirmation_keyboard = conf_kb
