"""
Единая система клавиатур для Telegram-бота
Все клавиатуры в едином красивом стиле
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# УНИФИЦИРОВАННЫЕ КЛАВИАТУРЫ
# ============================================

def _btn(text: str, callback_data: str) -> InlineKeyboardButton:
    """Создать кнопку"""
    return InlineKeyboardButton(text=text, callback_data=callback_data)

def _row(*buttons: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    """Создать ряд кнопок"""
    return list(buttons)

def _mk(*rows: List[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    """Создать клавиатуру из рядов"""
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


# ========== ГЛАВНОЕ МЕНЮ ==========
def main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню - все действия"""
    return _mk(
        _row(_btn("🐍 Давить коричневага", "davka"), _btn("✈️ Отправить змия", "uletet")),
        _row(_btn("👊 Радёмка (PvP)", "rademka"), _btn("🏆 Топ игроков", "top")),
        _row(_btn("📊 Профиль", "profile"), _btn("👤 Никнейм", "nickname_menu"))
    )


# ========== МЕНЮ НИКНЕЙМА ==========
def nickname_keyboard() -> InlineKeyboardMarkup:
    """Меню никнейма"""
    return _mk(
        _row(_btn("📝 Изменить ник", "change_nickname"), _btn("⭐ Моя репутация", "my_reputation")),
        _row(_btn("🥇 Топ репутации", "top_reputation"), _btn("⬅️ Назад", "back_main"))
    )


# ========== МЕНЮ РАДЁМКИ ==========
def rademka_keyboard() -> InlineKeyboardMarkup:
    """Меню радёмки"""
    return _mk(
        _row(_btn("🎯 Случайная цель", "rademka_random"), _btn("📊 Моя статистика", "rademka_stats")),
        _row(_btn("🥇 Топ радёмщиков", "rademka_top"), _btn("⬅️ Назад", "back_main"))
    )


# ========== МЕНЮ ГОФРЫ ==========
def gofra_info_keyboard() -> InlineKeyboardMarkup:
    """Меню информации о гофрошке"""
    return _mk(
        _row(_btn("📈 Прогресс", "gofra_progress"), _btn("⚡ Скорость ATM", "gofra_speed")),
        _row(_btn("🎯 Следующая гофра", "gofra_next"), _btn("⬅️ В профиль", "profile"))
    )


# ========== МЕНЮ КАБЕЛЯ ==========
def cable_info_keyboard() -> InlineKeyboardMarkup:
    """Меню информации о кабеле"""
    return _mk(
        _row(_btn("💪 Сила кабеля", "cable_power_info"), _btn("⚔️ PvP бонус", "cable_pvp_info")),
        _row(_btn("📈 Прокачка", "cable_upgrade_info"), _btn("⬅️ В профиль", "profile"))
    )


# ========== МЕНЮ АТМОСФЕР ==========
def atm_status_keyboard() -> InlineKeyboardMarkup:
    """Меню атмосфер"""
    return _mk(
        _row(_btn("⏱️ Время восстановления", "atm_regen_time"), _btn("📊 Максимум ATM", "atm_max_info")),
        _row(_btn("⚡ Ускорение", "atm_boosters"), _btn("⬅️ В профиль", "profile"))
    )


# ========== МЕНЮ ТОПА ==========
def top_sort_keyboard() -> InlineKeyboardMarkup:
    """Меню выбора сортировки топа"""
    return _mk(
        _row(_btn("🏗️ По гофрошке", "top_gofra"), _btn("🔌 По кабелю", "top_cable")),
        _row(_btn("🐍 По змию", "top_zmiy"), _btn("🌡️ По атмосферам", "top_atm")),
        _row(_btn("⬅️ Назад", "back_main"))
    )


# ========== МЕНЮ ЧАТА ==========
def chat_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню для чата"""
    return _mk(
        _row(_btn("🐍 Давить в чате", "chat_davka"), _btn("👊 Радёмка", "chat_rademka")),
        _row(_btn("🏆 Топ чата", "chat_top"), _btn("📊 Стата чата", "chat_stats")),
        _row(_btn("👤 Мой вклад", "chat_me"), _btn("📊 Профиль", "chat_profile")),
        _row(_btn("🌡️ Атмосферы", "chat_atm"), _btn("⏱️ Таймер", "chat_atm_regen")),
        _row(_btn("🆘 Помощь", "chat_help"), _btn("📱 Меню", "chat_menu"))
    )


# ========== КЛАВИАТУРЫ ПОДТВЕРЖДЕНИЯ ==========
def rademka_fight_keyboard(target_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения радёмки"""
    return _mk(
        _row(
            _btn("✅ Протащить!", f"rademka_confirm_{target_id}"),
            _btn("❌ Отмена", "rademka")
        )
    )


def chat_fight_keyboard(target_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения радёмки в чате"""
    return _mk(
        _row(
            _btn("✅ Протащить!", f"chat_fight_{target_id}"),
            _btn("❌ Отмена", "chat_menu")
        )
    )


def confirmation_keyboard(action: str, confirm_text: str = "Да", cancel_text: str = "Нет") -> InlineKeyboardMarkup:
    """Универсальная клавиатура подтверждения"""
    return _mk(
        _row(
            _btn(f"✅ {confirm_text}", f"confirm_{action}"),
            _btn(f"❌ {cancel_text}", f"cancel_{action}")
        )
    )


# ========== КНОПКА НАЗАД ==========
def back_keyboard(to: str = "back_main") -> InlineKeyboardMarkup:
    """Клавиатура только с кнопкой назад"""
    return _mk(
        _row(_btn("⬅️ Назад", to))
    )


# ========== АЛИАСЫ ==========
back_kb = back_keyboard
atm_status_kb = atm_status_keyboard
gofra_info_kb = gofra_info_keyboard
cable_info_kb = cable_info_keyboard
profile_extended_kb = main_keyboard
chat_menu_kb = chat_menu_keyboard
top_sort_kb = top_sort_keyboard

back_to_main_keyboard = lambda: back_keyboard("back_main")
back_to_profile_keyboard = lambda: back_keyboard("profile")
back_to_rademka_keyboard = lambda: back_keyboard("rademka")


# ========== ЭКСПОРТ ==========
__all__ = [
    # Основные клавиатуры
    'main_keyboard',
    'nickname_keyboard', 
    'rademka_keyboard',
    'gofra_info_keyboard',
    'cable_info_keyboard',
    'atm_status_keyboard',
    'top_sort_keyboard',
    'chat_menu_keyboard',
    
    # Подтверждения
    'rademka_fight_keyboard',
    'chat_fight_keyboard',
    'confirmation_keyboard',
    
    # Назад
    'back_keyboard',
    
    # Алиасы
    'back_kb',
    'atm_status_kb', 'gofra_info_kb', 'cable_info_kb', 'profile_extended_kb',
    'chat_menu_kb', 'top_sort_kb',
    'back_to_main_keyboard', 'back_to_profile_keyboard', 'back_to_rademka_keyboard',
]
