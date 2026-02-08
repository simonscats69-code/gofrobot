"""
Утилиты для Telegram-бота гофроцентра
"""

# Импорты для визуальных эффектов
try:
    from .visual_effects import visual_effects
except ImportError:
    visual_effects = None

# Импорты для форматтеров
try:
    from .formatters import formatters
except ImportError:
    formatters = None

# Импорты для клавиатур
try:
    from .keyboards import beautiful_keyboards
except ImportError:
    beautiful_keyboards = None

# Импорты для анимаций
try:
    from .animations import animation_manager, notification_effects
except ImportError:
    animation_manager = None
    notification_effects = None

# Импорты вспомогательных функций
try:
    from .formatters import ft, pb, ignore_not_modified_error
except ImportError:
    ft = None
    pb = None
    ignore_not_modified_error = None

# Импорты функций для работы с гофрошкой
try:
    from .formatters import get_gofra_info, get_cable_info, get_atm_info, format_length
except ImportError:
    get_gofra_info = None
    get_cable_info = None
    get_atm_info = None
    format_length = None

# Импорты функций для клавиатур
try:
    from .keyboards import mk, main_keyboard, nickname_keyboard, rademka_keyboard, top_sort_keyboard, back_kb, back_to_main_keyboard, back_to_profile_keyboard, back_to_rademka_keyboard, profile_extended_keyboard, atm_status_kb, gofra_info_kb, cable_info_kb, profile_extended_kb, rademka_fight_keyboard, chat_menu_keyboard
except ImportError:
    mk = None
    main_keyboard = None
    nickname_keyboard = None
    rademka_keyboard = None
    top_sort_keyboard = None
    back_kb = None
    back_to_main_keyboard = None
    back_to_profile_keyboard = None
    back_to_rademka_keyboard = None
    profile_extended_keyboard = None
    atm_status_kb = None
    gofra_info_kb = None
    cable_info_kb = None
    profile_extended_kb = None
    rademka_fight_keyboard = None
    chat_menu_keyboard = None

__all__ = [
    'visual_effects', 'formatters', 'beautiful_keyboards', 
    'animation_manager', 'notification_effects', 'ft', 'pb', 
    'ignore_not_modified_error', 'get_gofra_info', 'get_cable_info', 
    'get_atm_info', 'format_length', 'mk', 'main_keyboard', 
    'nickname_keyboard', 'rademka_keyboard', 'top_sort_keyboard', 
    'back_kb', 'back_to_main_keyboard', 'back_to_profile_keyboard', 
    'back_to_rademka_keyboard', 'profile_extended_keyboard', 
    'atm_status_kb', 'gofra_info_kb', 'cable_info_kb', 
    'profile_extended_kb', 'rademka_fight_keyboard', 'chat_menu_keyboard'
]