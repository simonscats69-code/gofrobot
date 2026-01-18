from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Tuple, Optional, Union

# ========== КОНФИГУРАЦИИ КЛАВИАТУР ==========

MENUS = {
    # Главное меню (используется в back_main, start, profile)
    "main": [
        [("🐍 Давить коричневага", "davka")],
        [("💰 Сдать змия на металл", "sdat")],
        [("📈 Прокачать скиллы", "pump")],
        [("🌳 Специализации", "specializations")],
        [("🛒 Нагнетательная столовая", "shop"), ("🔨 Крафт", "craft")],
        [("🎁 Ежедневная награда", "daily"), ("📜 Достижения", "achievements")],
        [("👊 Протащить радёмку", "rademka"), ("🕵️ Разведка", "rademka_scout_menu")],
        [("🎒 Инвентарь", "inventory"), ("🏆 Топ пацанов", "top")],
        [("📊 Профиль", "profile")]
    ],
    
    # Прокачка скиллов (pump)
    "pump": [
        [("💪 Давка змия", "pump_davka")],
        [("🛡️ Защита атмосфер", "pump_zashita")],
        [("🔍 Находка двенашек", "pump_nahodka")]
    ],
    
    # Магазин (shop)
    "shop": [
        [("🥛 Ряженка (300р)", "buy_ryazhenka")],
        [("🍵 Чай сливовый (500р)", "buy_tea_slivoviy")],
        [("🧋 Бублэки (800р)", "buy_bubbleki")],
        [("🥐 Курвасаны (1500р)", "buy_kuryasany")]
    ],
    
    # Специализации (specializations)
    "specializations": [
        [("💪 Давила", "spec_info_davila")],
        [("🔍 Охотник за двенашками", "spec_info_ohotnik")],
        [("🛡️ Непробиваемый", "spec_info_neprobivaemy")],
        [("❓ Информация", "specialization_info")]
    ],
    
    # Крафт (craft)
    "craft": [
        [("🛠️ Крафт предметов", "craft_items")],
        [("📜 Доступные рецепты", "craft_recipes")],
        [("📊 История крафта", "craft_history")]
    ],
    
    # Радёмка (rademka)
    "rademka": [
        [("🎯 Выбрать случайную цель", "rademka_random")],
        [("🕵️ Разведка цели", "rademka_scout_menu")],
        [("📊 Статистика радёмок", "rademka_stats")],
        [("👑 Топ радёмщиков", "rademka_top")]
    ],
    
    # Разведка радёмки (rademka_scout_menu)
    "rademka_scout": [
        [("🎯 Разведать случайную цель", "rademka_scout_random")],
        [("🔍 Выбрать цель для разведки", "rademka_scout_choose")],
        [("📊 Мои разведки", "rademka_scout_stats")]
    ],
    
    # Достижения (achievements)
    "achievements": [
        [("🔄 Обновить", "achievements")],
        [("📊 Прогресс по уровням", "achievements_progress")],
        [("🎁 Ежедневная награда", "daily")]
    ],
    
    # Ежедневные награды (daily)
    "daily": [
        [("🔄 Проверить снова", "daily")],
        [("📜 Мои достижения", "achievements")],
        [("📈 Прогресс достижений", "achievements_progress")]
    ],
    
    # Профиль (profile)
    "profile_extended": [
        [("⭐ Прогресс достижений", "achievements_progress")],
        [("📈 Статистика по уровням", "level_stats")],
        [("🌡️ Состояние атмосфер", "atm_status")]
    ],
    
    # Топ (top)
    "top_sort": [
        [("⭐ По авторитету", "top_avtoritet")],
        [("💰 По деньгам", "top_dengi")],
        [("🐍 По змию", "top_zmiy")],
        [("💪 По сумме скиллов", "top_total_skill")],
        [("📈 По уровню", "top_level")],
        [("👊 По победам в радёмках", "top_rademka_wins")]
    ],
    
    # Инвентарь (inventory)
    "inventory": [
        [("🛠️ Использовать предмет", "inventory_use")],
        [("🔨 Перейти к крафту", "craft")],
        [("📦 Сортировать", "inventory_sort")],
        [("🗑️ Выбросить мусор", "inventory_trash")]
    ],
    
    # Крафт предметов (craft_items)
    "craft_items": [
        [("✨ Супер-двенашка", "craft_super_dvenashka")],
        [("⚡ Вечный двигатель", "craft_vechnyy_dvigatel")],
        [("👑 Царский обед", "craft_tarskiy_obed")],
        [("🌀 Бустер атмосфер", "craft_booster_atm")]
    ]
}

# ========== УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ==========

def create_keyboard(menu_name: str, back_to: str = None, extra_rows: List = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру из конфигурации.
    
    Args:
        menu_name: имя меню из MENUS
        back_to: callback_data для кнопки "Назад" (если нужна)
        extra_rows: дополнительные строки кнопок
    """
    if menu_name not in MENUS:
        return main_keyboard()
    
    buttons = []
    
    # Добавляем основные кнопки из конфигурации
    for row in MENUS[menu_name]:
        row_buttons = []
        for btn_text, callback_data in row:
            row_buttons.append(InlineKeyboardButton(text=btn_text, callback_data=callback_data))
        if row_buttons:
            buttons.append(row_buttons)
    
    # Добавляем дополнительные строки
    if extra_rows:
        for row in extra_rows:
            if isinstance(row[0], tuple):  # Список кортежей
                row_buttons = [InlineKeyboardButton(text=t, callback_data=d) for t, d in row]
            else:  # Один кортеж
                row_buttons = [InlineKeyboardButton(text=row[0], callback_data=row[1])]
            buttons.append(row_buttons)
    
    # Добавляем кнопку "Назад" если указано куда
    if back_to:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_to)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== СПЕЦИАЛЬНЫЕ КЛАВИАТУРЫ ==========

def rademka_fight_keyboard(target_id: Optional[int] = None, scouted: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для радёмки с выбором цели"""
    buttons = []
    
    if target_id:
        if scouted:
            buttons.append([InlineKeyboardButton(text="🎯 Шанс известен (разведано)", callback_data="no_action")])
        
        buttons.append([InlineKeyboardButton(text="✅ ДА, ПРОТАЩИТЬ ЕГО!", callback_data=f"rademka_confirm_{target_id}")])
        buttons.append([InlineKeyboardButton(text="🕵️ Сначала разведка", callback_data=f"rademka_scout_{target_id}")])
        buttons.append([InlineKeyboardButton(text="❌ Нет, передумал", callback_data="rademka")])
    else:
        buttons = [
            [InlineKeyboardButton(text="🎯 Выбрать случайную цель", callback_data="rademka_random")],
            [InlineKeyboardButton(text="🕵️ Сначала разведка", callback_data="rademka_scout_choose")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="rademka")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirmation_keyboard(action: str, target_id: Optional[int] = None, show_info: bool = False, info_data: str = None) -> InlineKeyboardMarkup:
    """Универсальная клавиатура подтверждения"""
    confirm_data = f"confirm_{action}_{target_id}" if target_id else f"confirm_{action}"
    cancel_data = f"cancel_{action}"
    
    buttons = [[
        InlineKeyboardButton(text="✅ ДА", callback_data=confirm_data),
        InlineKeyboardButton(text="❌ НЕТ", callback_data=cancel_data)
    ]]
    
    if show_info and info_data:
        buttons.append([InlineKeyboardButton(text="📋 Подробнее", callback_data=info_data)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def craft_confirmation_keyboard(recipe_id: str) -> InlineKeyboardMarkup:
    """Подтверждение крафта"""
    return confirmation_keyboard(
        action=f"craft_execute_{recipe_id}",
        show_info=True,
        info_data=f"recipe_info_{recipe_id}"
    )

def specialization_confirmation_keyboard(spec_id: str) -> InlineKeyboardMarkup:
    """Подтверждение покупки специализации"""
    return confirmation_keyboard(
        action=f"specialization_buy_{spec_id}",
        show_info=True,
        info_data=f"specialization_info_{spec_id}"
    )

# ========== ГОТОВЫЕ КЛАВИАТУРЫ (для удобства) ==========

def main_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("main")

def pump_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("pump", "back_main")

def shop_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("shop", "back_main")

def specializations_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("specializations", "back_main")

def craft_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("craft", "back_main")

def rademka_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("rademka", "back_main")

def rademka_scout_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("rademka_scout", "rademka")

def daily_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("daily", "back_main")

def achievements_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("achievements", "back_main")

def achievements_progress_keyboard() -> InlineKeyboardMarkup:
    # Создаем динамически, так как есть доп кнопка
    buttons = [
        [InlineKeyboardButton(text="🐍 Коллекционер змия", callback_data="achievement_zmiy_collector")],
        [InlineKeyboardButton(text="💰 Денежный мешок", callback_data="achievement_money_maker")],
        [InlineKeyboardButton(text="👊 Король радёмок", callback_data="achievement_rademka_king")],
        [InlineKeyboardButton(text="📊 Все достижения", callback_data="achievements_progress_all")],
        [InlineKeyboardButton(text="⬅️ Назад к достижениям", callback_data="achievements")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def level_stats_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📈 Мой прогресс", callback_data="level_progress")],
        [InlineKeyboardButton(text="🏆 Топ по уровням", callback_data="top_level")],
        [InlineKeyboardButton(text="🎯 До следующего уровня", callback_data="level_next")],
        [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def atm_status_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="⏱️ Время восстановления", callback_data="atm_regen_time")],
        [InlineKeyboardButton(text="📊 Максимальный запас", callback_data="atm_max_info")],
        [InlineKeyboardButton(text="⚡ Бустеры активности", callback_data="atm_boosters")],
        [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_extended_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("profile_extended", "profile")

def top_sort_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("top_sort", "back_main")

def inventory_management_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("inventory", "inventory")

def craft_items_keyboard() -> InlineKeyboardMarkup:
    return create_keyboard("craft_items", "craft")

def craft_recipes_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✨ Супер-двенашка", callback_data="recipe_super_dvenashka")],
        [InlineKeyboardButton(text="⚡ Вечный двигатель", callback_data="recipe_vechnyy_dvigatel")],
        [InlineKeyboardButton(text="👑 Царский обед", callback_data="recipe_tarskiy_obed")],
        [InlineKeyboardButton(text="🌀 Бустер атмосфер", callback_data="recipe_booster_atm")],
        [InlineKeyboardButton(text="🛠️ Перейти к крафту", callback_data="craft_items")],
        [InlineKeyboardButton(text="⬅️ Назад к крафту", callback_data="craft")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def specializations_info_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💪 Давила - информация", callback_data="spec_info_davila")],
        [InlineKeyboardButton(text="🔍 Охотник - информация", callback_data="spec_info_ohotnik")],
        [InlineKeyboardButton(text="🛡️ Непробиваемый - информация", callback_data="spec_info_neprobivaemy")],
        [InlineKeyboardButton(text="💰 Купить специализацию", callback_data="specializations")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== ПРОСТЫЕ КЛАВИАТУРЫ (одна кнопка) ==========

def back_keyboard(back_to: str = "back_main") -> InlineKeyboardMarkup:
    """Кнопка назад в указанное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад", callback_data=back_to)
    ]])

def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return back_keyboard("back_main")

def back_to_craft_keyboard() -> InlineKeyboardMarkup:
    return back_keyboard("craft")

def back_to_specializations_keyboard() -> InlineKeyboardMarkup:
    return back_keyboard("specializations")

def back_to_profile_keyboard() -> InlineKeyboardMarkup:
    return back_keyboard("profile")

def back_to_rademka_keyboard() -> InlineKeyboardMarkup:
    return back_keyboard("rademka")

def back_to_inventory_keyboard() -> InlineKeyboardMarkup:
    return back_keyboard("inventory")

# ========== УДОБНЫЕ АЛИАСЫ (для обратной совместимости) ==========

back_keyboard = back_to_main_keyboard  # для старого кода
