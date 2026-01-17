from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def daily_keyboard():
    """Клавиатура для ежедневных наград (ОБНОВЛЁННАЯ)"""
    kb = [
        [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="daily")],
        [InlineKeyboardButton(text="📜 Мои достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="📈 Прогресс достижений", callback_data="achievements_progress")],  # НОВОЕ
        [InlineKeyboardButton(text="🏷️ Сменить ник", callback_data="change_nickname")],
        [InlineKeyboardButton(text="👊 Протащить радёмку", callback_data="rademka")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def achievements_keyboard():
    """Клавиатура для достижений (ОБНОВЛЁННАЯ)"""
    kb = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="achievements")],
        [InlineKeyboardButton(text="📊 Прогресс по уровням", callback_data="achievements_progress")],  # НОВОЕ
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
    """Клавиатура для радёмки (ОБНОВЛЁННАЯ)"""
    kb = [
        [InlineKeyboardButton(text="🎯 Выбрать случайную цель", callback_data="rademka_random")],
        [InlineKeyboardButton(text="🕵️ Разведка цели", callback_data="rademka_scout_menu")],  # НОВОЕ
        [InlineKeyboardButton(text="📊 Статистика радёмок", callback_data="rademka_stats")],
        [InlineKeyboardButton(text="👑 Топ радёмщиков", callback_data="rademka_top")],
        [InlineKeyboardButton(text="🤝 Пакты и союзы", callback_data="rademka_pacts")],  # НОВОЕ (будет в будущем)
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def rademka_fight_keyboard(target_id: int = None, scouted: bool = False):
    """Клавиатура для выбора цели радёмки (ОБНОВЛЁННАЯ)"""
    if target_id:
        kb = [
            [InlineKeyboardButton(text="✅ ДА, ПРОТАЩИТЬ ЕГО!", callback_data=f"rademka_confirm_{target_id}")],
        ]
        
        # Если была разведка, показываем точный шанс
        if scouted:
            kb.insert(0, [InlineKeyboardButton(text="🎯 Шанс известен (разведано)", callback_data="no_action")])
        
        kb.append([InlineKeyboardButton(text="🕵️ Сначала разведка", callback_data=f"rademka_scout_{target_id}")])
        kb.append([InlineKeyboardButton(text="❌ Нет, передумал", callback_data="rademka")])
    else:
        kb = [
            [InlineKeyboardButton(text="🎯 Выбрать случайную цель", callback_data="rademka_random")],
            [InlineKeyboardButton(text="🕵️ Сначала разведка", callback_data="rademka_scout_choose")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="rademka")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_rademka_keyboard():
    """Кнопка назад в меню радёмки"""
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад к радёмке", callback_data="rademka")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== НОВАЯ ФУНКЦИЯ ДЛЯ РАЗВЕДКИ ====================

def rademka_scout_keyboard():
    """Клавиатура для меню разведки радёмки"""
    kb = [
        [InlineKeyboardButton(text="🎯 Случайная цель", callback_data="rademka_scout_random")],
        [InlineKeyboardButton(text="📊 Статистика разведок", callback_data="rademka_scout_stats")],
        [
            InlineKeyboardButton(text="👊 К радёмке", callback_data="rademka"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== КОНЕЦ НОВОЙ ФУНКЦИИ ====================

def achievements_progress_keyboard():
    """Клавиатура для прогресса уровневих достижений"""
    kb = [
        [InlineKeyboardButton(text="🐍 Коллекционер змия", callback_data="achievement_zmiy_collector")],
        [InlineKeyboardButton(text="💰 Денежный мешок", callback_data="achievement_money_maker")],
        [InlineKeyboardButton(text="👊 Король радёмок", callback_data="achievement_rademka_king")],
        [InlineKeyboardButton(text="📊 Все достижения", callback_data="achievements_progress_all")],
        [InlineKeyboardButton(text="⬅️ Назад к достижениям", callback_data="achievements")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def level_stats_keyboard():
    """Клавиатура статистики уровней"""
    kb = [
        [InlineKeyboardButton(text="📈 Мой прогресс", callback_data="level_progress")],
        [InlineKeyboardButton(text="🏆 Топ по уровням", callback_data="top_level")],
        [InlineKeyboardButton(text="🎯 До следующего уровня", callback_data="level_next")],
        [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def atm_status_keyboard():
    """Клавиатура состояния атмосфер"""
    kb = [
        [InlineKeyboardButton(text="⏱️ Время восстановления", callback_data="atm_regen_time")],
        [InlineKeyboardButton(text="📊 Максимальный запас", callback_data="atm_max_info")],
        [InlineKeyboardButton(text="⚡ Бустеры активности", callback_data="atm_boosters")],
        [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def specializations_info_keyboard():
    """Клавиатура информации о специализациях"""
    kb = [
        [InlineKeyboardButton(text="💪 Давила - информация", callback_data="spec_info_davila")],
        [InlineKeyboardButton(text="🔍 Охотник - информация", callback_data="spec_info_ohotnik")],
        [InlineKeyboardButton(text="🛡️ Непробиваемый - информация", callback_data="spec_info_neprobivaemy")],
        [InlineKeyboardButton(text="💰 Купить специализацию", callback_data="specializations")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def craft_recipes_keyboard():
    """Клавиатура рецептов крафта"""
    kb = [
        [InlineKeyboardButton(text="✨ Супер-двенашка", callback_data="recipe_super_dvenashka")],
        [InlineKeyboardButton(text="⚡ Вечный двигатель", callback_data="recipe_vechnyy_dvigatel")],
        [InlineKeyboardButton(text="👑 Царский обед", callback_data="recipe_tarskiy_obed")],
        [InlineKeyboardButton(text="🌀 Бустер атмосфер", callback_data="recipe_booster_atm")],
        [InlineKeyboardButton(text="🛠️ Перейти к крафту", callback_data="craft_items")],
        [InlineKeyboardButton(text="⬅️ Назад к крафту", callback_data="craft")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def craft_confirmation_keyboard(recipe_id: str):
    """Клавиатура подтверждения крафта"""
    kb = [
        [
            InlineKeyboardButton(text="✅ Скрафтить", callback_data=f"craft_execute_{recipe_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="craft")
        ],
        [InlineKeyboardButton(text="📋 Посмотреть рецепт", callback_data=f"recipe_info_{recipe_id}")]
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

def top_sort_keyboard():
    """Клавиатура сортировки топа (расширенная)"""
    kb = [
        [InlineKeyboardButton(text="⭐ По авторитету", callback_data="top_avtoritet")],
        [InlineKeyboardButton(text="💰 По деньгам", callback_data="top_dengi")],
        [InlineKeyboardButton(text="🐍 По змию", callback_data="top_zmiy")],
        [InlineKeyboardButton(text="💪 По сумме скиллов", callback_data="top_total_skill")],
        [InlineKeyboardButton(text="📈 По уровню", callback_data="top_level")],  # НОВОЕ
        [InlineKeyboardButton(text="👊 По победам в радёмках", callback_data="top_rademka_wins")],  # НОВОЕ
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="back_main")]
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

def shop_categories_keyboard():
    """Клавиатура категорий магазина"""
    kb = [
        [InlineKeyboardButton(text="🥛 Нагнетатели", callback_data="shop_upgrades")],
        [InlineKeyboardButton(text="⚡ Бустеры", callback_data="shop_boosters")],  # НОВАЯ КАТЕГОРИЯ
        [InlineKeyboardButton(text="🔧 Инструменты", callback_data="shop_tools")],  # НОВАЯ КАТЕГОРИЯ
        [InlineKeyboardButton(text="🎁 Случайный набор", callback_data="shop_random")],  # НОВАЯ КАТЕГОРИЯ
        [InlineKeyboardButton(text="⬅️ Назад в магазин", callback_data="shop")]
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

def back_to_profile_keyboard():
    """Кнопка назад в профиль"""
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== КЛАВИАТУРЫ ДЛЯ АДМИНИСТРАТИВНЫХ ФУНКЦИЙ (на будущее) ====================

def admin_keyboard():
    """Клавиатура администратора"""
    kb = [
        [InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎁 Выдать награду", callback_data="admin_give_reward")],
        [InlineKeyboardButton(text="⚙️ Настройки баланса", callback_data="admin_balance")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def event_management_keyboard():
    """Клавиатура управления ивентами"""
    kb = [
        [InlineKeyboardButton(text="🎪 Запустить ивент", callback_data="event_start")],
        [InlineKeyboardButton(text="📅 Запланировать ивент", callback_data="event_schedule")],
        [InlineKeyboardButton(text="📊 Активные ивенты", callback_data="event_active")],
        [InlineKeyboardButton(text="📋 История ивентов", callback_data="event_history")],
        [InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
