from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    """Главное меню пацана (ОБНОВЛЁННОЕ)"""
    kb = [
        [InlineKeyboardButton(text="🐍 Давить коричневага", callback_data="davka")],
        [InlineKeyboardButton(text="💰 Сдать змия на металл", callback_data="sdat")],
        [InlineKeyboardButton(text="📈 Прокачать скиллы", callback_data="pump")],
        [InlineKeyboardButton(text="🌳 Специализации", callback_data="specializations")],  # НОВОЕ
        [
            InlineKeyboardButton(text="🛒 Нагнетательная столовая", callback_data="shop"),
            InlineKeyboardButton(text="🔨 Крафт", callback_data="craft")  # НОВОЕ
        ],
        [
            InlineKeyboardButton(text="🎁 Ежедневная награда", callback_data="daily"),
            InlineKeyboardButton(text="📜 Достижения", callback_data="achievements")
        ],
        [
            InlineKeyboardButton(text="👊 Протащить радёмку", callback_data="rademka"),
            InlineKeyboardButton(text="🕵️ Разведка", callback_data="rademka_scout_menu")  # НОВОЕ
        ],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"),
            InlineKeyboardButton(text="🏆 Топ пацанов", callback_data="top")
        ],
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
    """Клавиатура нагнетательной столовой (ОБНОВЛЁННЫЕ ЦЕНЫ)"""
    kb = [
        [InlineKeyboardButton(text="🥛 Ряженка (300р)", callback_data="buy_ryazhenka")],
        [InlineKeyboardButton(text="🍵 Чай сливовый (500р)", callback_data="buy_tea_slivoviy")],
        [InlineKeyboardButton(text="🧋 Бублэки (800р)", callback_data="buy_bubbleki")],
        [InlineKeyboardButton(text="🥐 Курвасаны (1500р)", callback_data="buy_kuryasany")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_keyboard():
    """Простая кнопка назад"""
    kb = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== НОВЫЕ КЛАВИАТУРЫ ====================

def specializations_keyboard():
    """Клавиатура выбора специализации"""
    kb = [
        [InlineKeyboardButton(text="💪 Давила", callback_data="specialization_davila")],
        [InlineKeyboardButton(text="🔍 Охотник за двенашками", callback_data="specialization_ohotnik")],
        [InlineKeyboardButton(text="🛡️ Непробиваемый", callback_data="specialization_neprobivaemy")],
        [InlineKeyboardButton(text="❓ Информация о специализациях", callback_data="specializations_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def craft_keyboard():
    """Клавиатура крафта"""
    kb = [
        [InlineKeyboardButton(text="🛠️ Крафт предметов", callback_data="craft_items")],
        [InlineKeyboardButton(text="📜 Доступные рецепты", callback_data="craft_recipes")],
        [InlineKeyboardButton(text="📊 История крафта", callback_data="craft_history")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def craft_items_keyboard():
    """Клавиатура для крафта конкретных предметов"""
    kb = [
        [InlineKeyboardButton(text="✨ Супер-двенашка", callback_data="craft_super_dvenashka")],
        [InlineKeyboardButton(text="⚡ Вечный двигатель", callback_data="craft_vechnyy_dvigatel")],
        [InlineKeyboardButton(text="👑 Царский обед", callback_data="craft_tarskiy_obed")],
        [InlineKeyboardButton(text="🌀 Бустер атмосфер", callback_data="craft_booster_atm")],
        [InlineKeyboardButton(text="⬅️ Назад к крафту", callback_data="craft")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def rademka_scout_keyboard():
    """Клавиатура разведки радёмки"""
    kb = [
        [InlineKeyboardButton(text="🎯 Разведать случайную цель", callback_data="rademka_scout_random")],
        [InlineKeyboardButton(text="🔍 Выбрать цель для разведки", callback_data="rademka_scout_choose")],
        [InlineKeyboardButton(text="📊 Мои разведки", callback_data="rademka_scout_stats")],
        [InlineKeyboardButton(text="⬅️ Назад к радёмке", callback_data="rademka")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def profile_extended_keyboard():
    """Расширенная клавиатура профиля"""
    kb = [
        [InlineKeyboardButton(text="⭐ Прогресс достижений", callback_data="achievements_progress")],
        [InlineKeyboardButton(text="📈 Статистика по уровням", callback_data="level_stats")],
        [InlineKeyboardButton(text="🌡️ Состояние атмосфер", callback_data="atm_status")],
        [InlineKeyboardButton(text="⬅️ Основной профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirmation_keyboard(action: str, target_id: int = None):
    """Клавиатура подтверждения действий"""
    if target_id:
        kb = [
            [
                InlineKeyboardButton(text="✅ ДА", callback_data=f"confirm_{action}_{target_id}"),
                InlineKeyboardButton(text="❌ НЕТ", callback_data=f"cancel_{action}")
            ]
        ]
    else:
        kb = [
            [
                InlineKeyboardButton(text="✅ ДА", callback_data=f"confirm_{action}"),
                InlineKeyboardButton(text="❌ НЕТ", callback_data=f"cancel_{action}")
            ]
        ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def specialization_confirmation_keyboard(spec_id: str):
    """Клавиатура подтверждения покупки специализации"""
    kb = [
        [
            InlineKeyboardButton(text="✅ Купить", callback_data=f"specialization_buy_{spec_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="specializations")
        ],
        [InlineKeyboardButton(text="📋 Подробнее", callback_data=f"specialization_info_{spec_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def inventory_management_keyboard():
    """Клавиатура управления инвентарём"""
    kb = [
        [InlineKeyboardButton(text="🛠️ Использовать предмет", callback_data="inventory_use")],
        [InlineKeyboardButton(text="🔨 Перейти к крафту", callback_data="craft")],
        [InlineKeyboardButton(text="📦 Сортировать", callback_data="inventory_sort")],
        [InlineKeyboardButton(text="🗑️ Выбросить мусор", callback_data="inventory_trash")],
        [InlineKeyboardButton(text="⬅️ Назад к инвентарю", callback_data="inventory")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_craft_keyboard():
    """Кнопка назад в меню крафта"""
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад к крафту", callback_data="craft")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_specializations_keyboard():
    """Кнопка назад в меню специализаций"""
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад к специализациям", callback_data="specializations")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
