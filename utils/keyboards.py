"""
Система красивых клавиатур для Telegram-бота
Реализует интерактивные клавиатуры с визуальными эффектами и анимациями
"""

import logging
from typing import List, Dict, Optional, Callable
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем visual_effects для использования в клавиатурах
try:
    from utils.visual_effects import visual_effects
except ImportError:
    # Заглушка для visual_effects если импорт не удался
    class MockVisualEffects:
        COLORS = {
            'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blue': '🔵',
            'success': '✅', 'warning': '⚠️', 'error': '❌', 'info': 'ℹ️'
        }
        GRADIENTS = {'success': ['🟢', '🟡', '🟠', '🔴']}
        
        @staticmethod
        def get_color_emoji(status: str) -> str:
            return '⚪'
        
        @staticmethod
        def create_progress_bar(percentage: float, length: int = 15, style: str = 'default') -> str:
            return "█" * int(length * percentage / 100) + "░" * (length - int(length * percentage / 100))
        
        @staticmethod
        def create_divider(char: str = '─', length: int = 30, style: str = 'simple') -> str:
            return char * length
    
    visual_effects = MockVisualEffects()

logger = logging.getLogger(__name__)

class BeautifulKeyboards:
    """Красивые клавиатуры с визуальными эффектами"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Главная менюшка с красивыми кнопками"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏗️ Гофрошка", callback_data="gofra_info"),
                InlineKeyboardButton(text="🔌 Кабель", callback_data="cable_info")
            ],
            [
                InlineKeyboardButton(text="🔋 Атмосферы", callback_data="atm_status"),
                InlineKeyboardButton(text="🐍 Давка", callback_data="davka")
            ],
            [
                InlineKeyboardButton(text="🏆 Радёмка", callback_data="rademka"),
                InlineKeyboardButton(text="📊 Профиль", callback_data="profile")
            ],
            [
                InlineKeyboardButton(text="⏰ Таймеры", callback_data="timing"),
                InlineKeyboardButton(text="🏆 Топ", callback_data="top")
            ]
        ])
    
    @staticmethod
    def get_gofra_menu() -> InlineKeyboardMarkup:
        """Меню гофрошки"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📏 Инфо", callback_data="gofra_info"),
                InlineKeyboardButton(text="⚡ Скорость", callback_data="gofra_speed")
            ],
            [
                InlineKeyboardButton(text="🎯 Цель", callback_data="gofra_target"),
                InlineKeyboardButton(text="📈 Прогресс", callback_data="gofra_progress")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_cable_menu() -> InlineKeyboardMarkup:
        """Меню кабеля"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📏 Инфо", callback_data="cable_info"),
                InlineKeyboardButton(text="💪 Сила", callback_data="cable_power")
            ],
            [
                InlineKeyboardButton(text="⚔️ PvP", callback_data="cable_pvp"),
                InlineKeyboardButton(text="⬆️ Улучшения", callback_data="cable_upgrade")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_atm_menu() -> InlineKeyboardMarkup:
        """Меню атмосфер"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔋 Статус", callback_data="atm_status"),
                InlineKeyboardButton(text="🕐 Время", callback_data="atm_regen_time")
            ],
            [
                InlineKeyboardButton(text="⚡ Максимум", callback_data="atm_max_info"),
                InlineKeyboardButton(text="⚡ Бустеры", callback_data="atm_boosters")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_davka_menu() -> InlineKeyboardMarkup:
        """Меню давки"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🐍 Давить", callback_data="davka"),
                InlineKeyboardButton(text="🚀 Улететь", callback_data="uletet")
            ],
            [
                InlineKeyboardButton(text="⏰ Таймер", callback_data="davka_timer"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="davka_stats")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_rademka_menu() -> InlineKeyboardMarkup:
        """Меню радёмки"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⚔️ Сражаться", callback_data="rademka_fight"),
                InlineKeyboardButton(text="🏆 Рейтинг", callback_data="rademka_rating")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="rademka_stats"),
                InlineKeyboardButton(text="🎯 Противники", callback_data="rademka_opponents")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_timing_menu() -> InlineKeyboardMarkup:
        """Меню таймеров"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏰ Все таймеры", callback_data="timing_all"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="timing_refresh")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="timing_stats"),
                InlineKeyboardButton(text="❌ Стоп", callback_data="timing_stop")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_top_menu() -> InlineKeyboardMarkup:
        """Меню топов"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Игроки", callback_data="top_players"),
                InlineKeyboardButton(text="🏆 Чаты", callback_data="top_chats")
            ],
            [
                InlineKeyboardButton(text="🐍 Змий", callback_data="top_zmiy"),
                InlineKeyboardButton(text="🏗️ Гофрошка", callback_data="top_gofra")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_profile_menu() -> InlineKeyboardMarkup:
        """Меню профиля"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Инфо", callback_data="profile_info"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")
            ],
            [
                InlineKeyboardButton(text="🏆 Достижения", callback_data="profile_achievements"),
                InlineKeyboardButton(text="🎯 Цели", callback_data="profile_goals")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
            ]
        ])
    
    @staticmethod
    def get_confirmation_keyboard(action: str, confirm_text: str = "Да", 
                                 cancel_text: str = "Нет") -> InlineKeyboardMarkup:
        """Клавиатура подтверждения действия"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"✅ {confirm_text}", callback_data=f"confirm_{action}"),
                InlineKeyboardButton(text=f"❌ {cancel_text}", callback_data=f"cancel_{action}")
            ]
        ])
    
    @staticmethod
    def get_action_keyboard(actions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Создать клавиатуру из списка действий"""
        buttons = []
        row = []
        
        for action in actions:
            button = InlineKeyboardButton(
                text=action.get('text', 'Кнопка'),
                callback_data=action.get('callback_data', 'action')
            )
            row.append(button)
            
            # Делаем по 2 кнопки в ряду
            if len(row) == 2:
                buttons.append(row)
                row = []
        
        # Добавляем оставшиеся кнопки
        if row:
            buttons.append(row)
        
        # Добавляем кнопку назад
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def get_gradient_keyboard(buttons: List[Dict[str, str]], gradient_name: str = 'success') -> InlineKeyboardMarkup:
        """Создать клавиатуру с градиентными кнопками"""
        gradient = visual_effects.GRADIENTS.get(gradient_name, ['⚪'])
        
        keyboard_buttons = []
        row = []
        
        for i, button in enumerate(buttons):
            # Берём цвет из градиента
            color = gradient[i % len(gradient)]
            text = f"{color} {button.get('text', 'Кнопка')}"
            
            row_button = InlineKeyboardButton(
                text=text,
                callback_data=button.get('callback_data', f'action_{i}')
            )
            row.append(row_button)
            
            # Делаем по 2 кнопки в ряду
            if len(row) == 2:
                keyboard_buttons.append(row)
                row = []
        
        # Добавляем оставшиеся кнопки
        if row:
            keyboard_buttons.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    @staticmethod
    def get_animated_keyboard(base_buttons: List[Dict[str, str]], animation_type: str = 'blink') -> List[InlineKeyboardMarkup]:
        """Создать серию клавиатур для анимации"""
        animations = visual_effects.create_animated_text("Анимация", animation_type)
        keyboard_variants = []
        
        for animation in animations:
            buttons = []
            for button in base_buttons:
                animated_text = f"{animation} {button.get('text', 'Кнопка')}"
                buttons.append(InlineKeyboardButton(
                    text=animated_text,
                    callback_data=button.get('callback_data', 'action')
                ))
            
            keyboard_variants.append(InlineKeyboardMarkup(inline_keyboard=[buttons]))
        
        return keyboard_variants
    
    @staticmethod
    def get_status_keyboard(status: str, actions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Создать клавиатуру с статусом"""
        status_emoji = visual_effects.get_color_emoji(status)
        
        buttons = []
        for action in actions:
            buttons.append(InlineKeyboardButton(
                text=f"{status_emoji} {action.get('text', 'Кнопка')}",
                callback_data=action.get('callback_data', 'action')
            ))
        
        return InlineKeyboardMarkup(inline_keyboard=[buttons])
    
    @staticmethod
    def get_progress_keyboard(current_step: int, total_steps: int, actions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Создать клавиатуру с прогрессом"""
        progress = (current_step / total_steps) * 100
        progress_bar = visual_effects.create_progress_bar(progress, 10, 'rounded')
        
        # Заголовок с прогрессом
        header_button = InlineKeyboardButton(
            text=f"Прогресс: [{progress_bar}] {progress:.0f}%",
            callback_data="progress_info"
        )
        
        buttons = [[header_button]]
        
        # Основные действия
        row = []
        for action in actions:
            row.append(InlineKeyboardButton(
                text=action.get('text', 'Кнопка'),
                callback_data=action.get('callback_data', 'action')
            ))
            
            if len(row) == 2:
                buttons.append(row)
                row = []
        
        if row:
            buttons.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def get_menu_with_divider(menu_type: str, divider_char: str = '─') -> InlineKeyboardMarkup:
        """Создать меню с визуальным разделителем"""
        divider = visual_effects.create_divider(divider_char, 20, 'double')
        
        if menu_type == 'main':
            return InlineKeyboardMarkup(inline_keyboard=[
                [[InlineKeyboardButton(text=divider, callback_data="divider")]],
                [
                    InlineKeyboardButton(text="🏗️ Гофрошка", callback_data="gofra_info"),
                    InlineKeyboardButton(text="🔌 Кабель", callback_data="cable_info")
                ],
                [
                    InlineKeyboardButton(text="🔋 Атмосферы", callback_data="atm_status"),
                    InlineKeyboardButton(text="🐍 Давка", callback_data="davka")
                ],
                [
                    InlineKeyboardButton(text="🏆 Радёмка", callback_data="rademka"),
                    InlineKeyboardButton(text="📊 Профиль", callback_data="profile")
                ]
            ])
        else:
            return BeautifulKeyboards.get_main_menu()

# Глобальный экземпляр
beautiful_keyboards = BeautifulKeyboards()