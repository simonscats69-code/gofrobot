"""
Форматтеры сообщений для Telegram-бота
Создаёт красивые и информативные сообщения с использованием визуальных эффектов
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Импорты для визуальных эффектов (если доступны)
try:
    from utils import visual_effects
    VISUAL_EFFECTS_AVAILABLE = True
except ImportError:
    VISUAL_EFFECTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Импорты для совместимости - будут добавлены позже
def get_gofra_info(gofra_mm: float) -> Dict:
    """Заглушка для совместимости"""
    return {'atm_speed': 1.0}

def get_cable_info(cable_mm: float) -> Dict:
    """Заглушка для совместимости"""
    return {'strength': 1.0, 'pvp_bonus': 0.0}

def get_atm_info(atm_count: int) -> Dict:
    """Заглушка для совместимости"""
    return {'regen_time': '2 часа', 'max_atm': 12}

class MessageFormatters:
    """Форматтеры сообщений"""
    
    @staticmethod
    def format_welcome(nickname: str = "Пацанчик", gofra_emoji: str = "🏗️", 
                      gofra_name: str = "Гофрошка", gofra_length: str = "10.0мм",
                      cable_length: str = "10.0мм", atm_count: int = 0, 
                      atm_max: int = 12, zmiy_grams: float = 0.0) -> str:
        """Форматировать приветственное сообщение"""
        return (
            f"🏗️ ДОБРО ПОЖАЛОВАТЬ В ГОФРОБОТ!\n\n"
            f"Ну чё, {nickname}? 👊\n\n"
            f"{gofra_emoji} {gofra_name} | 🏗️ {gofra_length} | 🔌 {cable_length}\n\n"
            f"🌀 Атмосферы: {atm_count}/{atm_max}\n"
            f"🐍 Змий: {zmiy_grams:.0f}г\n\n"
            f"Доступные команды:\n"
            f"/start - Начать игру\n"
            f"/profile - Показать профиль\n"
            f"/davka - Давить змия\n"
            f"/uletet - Отправить змия в коричневую страну\n"
            f"/rademka - Радёмка с другим игроком\n"
            f"/top - Таблица лидеров\n"
            f"/timing - Точные таймеры\n"
            f"/help - Помощь\n"
            f"{visual_effects.create_divider('─', 30, 'double')}"
        )
    
    @staticmethod
    def format_gofra_info(gofra_mm: float, gofra_info: Dict) -> str:
        """Форматировать информацию о гофрошке"""
        percentage = min(100, (gofra_mm / 2000.0) * 100)  # Максимум 2000мм
        progress = visual_effects.create_progress_bar(percentage, 15, 'default')
        
        return (
            f"🏗️ ТВОЯ ГОФРОШКА\n\n"
            f"📏 Размер: {gofra_mm:.1f}мм\n"
            f"📊 [{progress}] {percentage:.1f}%\n"
            f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}\n"
            f"🎯 Цель: 2000мм (осталось {max(0, 2000 - gofra_mm):.1f}мм)\n"
            f"{visual_effects.create_divider('─', 30, 'double')}"
        )
    
    @staticmethod
    def format_cable_info(cable_mm: float, cable_info: Dict) -> str:
        """Форматировать информацию о кабеле"""
        percentage = min(100, (cable_mm / 5000.0) * 100)  # Максимум 5000мм
        progress = visual_effects.create_progress_bar(percentage, 15, 'rounded')
        
        return (
            f"🔌 ТВОЙ КАБЕЛЬ\n\n"
            f"📏 Длина: {cable_mm:.1f}мм\n"
            f"📊 [{progress}] {percentage:.1f}%\n"
            f"💪 Сила: x{cable_info['strength']:.2f}\n"
            f"🎯 Цель: 5000мм (осталось {max(0, 5000 - cable_mm):.1f}мм)\n"
            f"⚔️ PvP бонус: +{cable_info['pvp_bonus']:.1f}%\n"
            f"{visual_effects.create_divider('─', 30, 'double')}"
        )
    
    @staticmethod
    def format_atm_info(atm_count: int, atm_info: Dict) -> str:
        """Форматировать информацию об атмосферах"""
        percentage = (atm_count / 12.0) * 100
        progress = visual_effects.create_progress_bar(percentage, 12, 'square')
        
        status_emoji = visual_effects.get_color_emoji('active' if atm_count > 0 else 'inactive')
        
        return (
            f"🔋 АТМОСФЕРЫ\n\n"
            f"{status_emoji} Заряд: {atm_count}/12\n"
            f"📊 [{progress}] {percentage:.1f}%\n"
            f"🕐 Время восстановления: {atm_info['regen_time']}\n"
            f"⚡ Максимум: {atm_info['max_atm']}\n"
            f"{visual_effects.create_divider('─', 30, 'double')}"
        )
    
    @staticmethod
    def format_profile(patsan: Dict) -> str:
        """Форматировать профиль игрока"""
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
        cable_info = get_cable_info(patsan.get('cable_mm', 10.0))
        atm_info = get_atm_info(patsan.get('atm_count', 0))
        
        # Определяем статус
        status = 'active'
        if patsan.get('atm_count', 0) == 0:
            status = 'inactive'
        
        status_emoji = visual_effects.get_color_emoji(status)
        
        return (
            f"{status_emoji} ПРОФИЛЬ ПАЦАНА {patsan['nickname']}\n\n"
            f"🏗️ Гофрошка: {patsan['gofra_mm']:.1f}мм\n"
            f"🔌 Кабель: {patsan['cable_mm']:.1f}мм\n"
            f"🔋 Атмосферы: {patsan['atm_count']}/12\n"
            f"🐍 Змий: {patsan['zmiy_grams']:.1f}г\n"
            f"🏆 Радёмка: {patsan['rademka_wins']}/{patsan['rademka_losses']}\n"
            f"📅 Регистрация: {datetime.fromtimestamp(patsan['registration_time']).strftime('%d.%m.%Y')}\n"
            f"{visual_effects.create_divider('─', 30, 'double')}"
        )
    
    @staticmethod
    def format_davka_result(success: bool, zmiy_grams: float, new_atm_count: int, 
                           patsan: Dict, message_type: str = 'standard') -> str:
        """Форматировать результат давки"""
        if success:
            if message_type == 'animated':
                return (
                    f"🎉 УСПЕШНАЯ ДАВКА!\n\n"
                    f"🐍 Змий: +{zmiy_grams:.1f}г\n"
                    f"🔋 Атмосферы: {new_atm_count}/12\n"
                    f"🏗️ Гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                    f"{visual_effects.create_divider('─', 30, 'star')}"
                )
            else:
                return (
                    f"✅ ДАВКА УСПЕШНА!\n\n"
                    f"🐍 Змий: +{zmiy_grams:.1f}г\n"
                    f"🔋 Атмосферы: {new_atm_count}/12\n"
                    f"🏗️ Гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                    f"{visual_effects.create_divider('─', 30, 'double')}"
                )
        else:
            return (
                f"❌ ДАВКА НЕ УДАЛАСЬ!\n\n"
                f"🔋 Атмосферы: {new_atm_count}/12\n"
                f"⏰ Подождите: {patsan.get('next_davka_time', 0)}\n"
                f"{visual_effects.create_divider('─', 30, 'double')}"
            )
    
    @staticmethod
    def format_uletet_result(success: bool, zmiy_grams: float, patsan: Dict) -> str:
        """Форматировать результат отправки змия в коричневую страну"""
        if success:
            return (
                f"🚀 ЗМИЙ УЛЕТЕЛ!\n\n"
                f"🐍 Змий: {zmiy_grams:.1f}г\n"
                f"🏗️ Гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                f"🎉 Поздравляем!\n"
                f"{visual_effects.create_divider('─', 30, 'party')}"
            )
        else:
            return (
                f"❌ ЗМИЙ НЕ УЛЕТЕЛ!\n\n"
                f"🐍 Змий: {zmiy_grams:.1f}г\n"
                f"🏗️ Гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                f"⏰ Подождите: {patsan.get('next_uletet_time', 0)}\n"
                f"{visual_effects.create_divider('─', 30, 'double')}"
            )
    
    @staticmethod
    def format_rademka_result(winner: bool, opponent_nickname: str, 
                            damage: float, patsan: Dict) -> str:
        """Форматировать результат радёмки"""
        if winner:
            return (
                f"🏆 ПОБЕДА В РАДЁМКЕ!\n\n"
                f"💥 Нанесено урона: {damage:.1f}\n"
                f"🎯 Противник: {opponent_nickname}\n"
                f"🏗️ Твоя гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                f"{visual_effects.create_divider('─', 30, 'fire')}"
            )
        else:
            return (
                f"💀 ПОРАЖЕНИЕ В РАДЁМКЕ!\n\n"
                f"💥 Получено урона: {damage:.1f}\n"
                f"🎯 Противник: {opponent_nickname}\n"
                f"🏗️ Твоя гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                f"{visual_effects.create_divider('─', 30, 'double')}"
            )
    
    @staticmethod
    def format_top_players(top_players: List[Dict], limit: int = 10) -> str:
        """Форматировать таблицу лидеров"""
        headers = ["Место", "Ник", "Гофрошка", "Кабель", "Змий"]
        rows = []
        
        for i, player in enumerate(top_players[:limit], 1):
            place_emoji = visual_effects.COLORS.get('crown' if i == 1 else 'star', '⭐')
            rows.append([
                f"{place_emoji} {i}",
                player['nickname'],
                f"{player['gofra_mm']:.1f}мм",
                f"{player['cable_mm']:.1f}мм", 
                f"{player['zmiy_grams']:.1f}г"
            ])
        
        return f"🏆 ТОП {limit} ИГРОКОВ\n\n" + visual_effects.format_table(headers, rows, 'left')
    
    @staticmethod
    def format_chat_top(chat_stats: List[Dict], limit: int = 10) -> str:
        """Форматировать топ чата"""
        headers = ["Место", "Ник", "Давки", "Змий"]
        rows = []
        
        for i, player in enumerate(chat_stats[:limit], 1):
            place_emoji = visual_effects.COLORS.get('crown' if i == 1 else 'star', '⭐')
            rows.append([
                f"{place_emoji} {i}",
                player['nickname'],
                str(player['davki_count']),
                f"{player['total_zmiy']:.1f}г"
            ])
        
        return f"🏆 ТОП ЧАТА\n\n" + visual_effects.format_table(headers, rows, 'left')
    
    @staticmethod
    def format_timing_info(davka_info: Dict, atm_info: Dict) -> str:
        """Форматировать информацию о таймерах"""
        # Информация о давке
        time_until_davka = davka_info['time_until']
        can_davka = davka_info['can_davka']
        davka_color = visual_effects.get_color_emoji('ready' if can_davka else 'waiting')
        
        # Информация об атмосферах
        atm_count = atm_info['atm_count']
        needed_atm = atm_info['needed_atm']
        time_to_next_atm = atm_info['time_to_next_atm']
        full_regen_time = atm_info['full_regen_time']
        
        atm_progress = ((12 - needed_atm) / 12) * 100 if needed_atm < 12 else 100
        davka_progress = ((7200 - time_until_davka) / 7200) * 100 if time_until_davka > 0 else 100
        
        message = f"⏰ ТОЧНЫЕ ТАЙМЕРЫ\n\n"
        
        # Таймер давки
        if can_davka:
            message += f"{davka_color} ДАВКА ГОТОВА! 🎉\n"
            message += f"🚀 Нажми /davka и дави змия!\n\n"
        else:
            precise_time = visual_effects.format_time_precise(time_until_davka)
            message += f"{davka_color} ДАВКА: {precise_time}\n"
            message += f"📊 [{visual_effects.create_progress_bar(davka_progress, 12)}] {davka_progress:.1f}%\n\n"
        
        # Таймер атмосфер
        message += f"🌀 АТМОСФЕРЫ: {atm_count}/12\n"
        if needed_atm > 0:
            next_atm_time = visual_effects.format_time_precise(time_to_next_atm)
            full_time = visual_effects.format_time_precise(full_regen_time)
            message += f"⏱️ Следующая: {next_atm_time}\n"
            message += f"🕐 Полностью: {full_time}\n"
            message += f"📊 [{visual_effects.create_progress_bar(atm_progress, 12)}] {atm_progress:.1f}%\n"
        
        # Модификаторы
        message += f"\n⚡ МОДИФИКАТОРЫ:\n"
        message += f"🏗️ Гофрошка: x{davka_info['speed_multiplier']:.2f}\n"
        message += f"🎯 Активность: x{davka_info['activity_bonus']:.2f}\n"
        
        return message
    
    @staticmethod
    def format_error(message: str, error_type: str = 'error') -> str:
        """Форматировать сообщение об ошибке"""
        emoji = visual_effects.get_color_emoji(error_type)
        return f"{emoji} ОШИБКА\n\n{message}\n{visual_effects.create_divider('─', 30, 'double')}"
    
    @staticmethod
    def format_success(message: str) -> str:
        """Форматировать сообщение об успехе"""
        return f"✅ УСПЕШНО\n\n{message}\n{visual_effects.create_divider('─', 30, 'star')}"
    
    @staticmethod
    def format_info(message: str) -> str:
        """Форматировать информационное сообщение"""
        return f"ℹ️ ИНФОРМАЦИЯ\n\n{message}\n{visual_effects.create_divider('─', 30, 'simple')}"
    
    @staticmethod
    def format_warning(message: str) -> str:
        """Форматировать предупреждение"""
        return f"⚠️ ВНИМАНИЕ\n\n{message}\n{visual_effects.create_divider('─', 30, 'double')}"

    @staticmethod
    def format_atm_status(atm_count: int = 0, atm_max: int = 12,
                         per_atm: float = 0.0, total: float = 0.0,
                         needed: int = 0, gofra_emoji: str = "🏗️",
                         gofra_name: str = "Гофрошка", atm_speed: float = 1.0) -> str:
        """Форматировать информацию об атмосферах"""
        return (
            f"🌡️ СОСТОЯНИЕ АТМОСФЕР\n\n"
            f"🌀 Текущий запас: {atm_count}/{atm_max}\n\n"
            f"Восстановление:\n"
            f"⏱️ 1 атмосфера: {per_atm:.0f}сек\n"
            f"🕐 До полного: {total:.0f}сек\n"
            f"📈 Осталось: {needed} атмосфер\n\n"
            f"Влияние гофрошки:\n"
            f"{gofra_emoji} {gofra_name}\n"
            f"⚡ Скорость: x{atm_speed:.2f}\n\n"
            f"Полные 12 атмосфер нужны для давки!"
        )

    @staticmethod
    def format_main_menu(gofra_emoji: str = "🏗️", gofra_name: str = "Гофрошка",
                        gofra_length: str = "10.0мм", cable_length: str = "10.0мм",
                        atm_count: int = 0, atm_max: int = 12,
                        zmiy_grams: float = 0.0) -> str:
        """Форматировать главное меню"""
        return (
            f"Главное меню\n"
            f"{gofra_emoji} {gofra_name} | 🏗️ {gofra_length} | 🔌 {cable_length}\n\n"
            f"🌀 Атмосферы: {atm_count}/{atm_max}\n"
            f"🐍 Змий: {zmiy_grams:.0f}г\n\n"
            f"Выбери действие, пацан:"
        )

    @staticmethod
    def format_help() -> str:
        """Форматировать помощь"""
        return (
            "🆘 ПОМОЩЬ ПО БОТУ\n\n"
            "📋 Основные команды:\n"
            "/start - Запуск бота\n"
            "/profile - Профиль игрока\n"
            "/gofra - Информация о гофрошке\n"
            "/cable - Информация о кабеле\n"
            "/atm - Состояние атмосфер\n"
            "/top - Топ игроков\n"
            "/menu - Главное меню\n\n"
            "🎮 Игровые действия:\n"
            "• 🐍 Давка коричневага - при 12 атмосферах\n"
            "• ✈️ Отправить змия - в коричневую страну\n"
            "• 👊 Радёмка (PvP)\n"
            "• 👤 Никнейм и репутация\n\n"
            "🏗️ Система гофрошки (в мм/см):\n"
            "• Чем длиннее гофрошка, тем тяжелее змий\n"
            "• Быстрее атмосферы\n"
            "• Медленная прогрессия (0.02 мм/г змия)\n\n"
            "🔌 Силовой кабель (в мм/см):\n"
            "• Увеличивает шанс в PvP (+0.02%/мм)\n"
            "• Прокачивается медленно (0.2 мм/кг змия)\n\n"
            "⏱️ Атмосферы:\n"
            "• Восстанавливаются автоматически\n"
            "• Нужны все 12 для давки\n"
            "• Скорость зависит от гофрошки"
        )

    @staticmethod
    def format_version_info() -> str:
        """Форматировать информацию о версии"""
        return (
            "🔄 ВЕРСИЯ БОТА\n\n"
            "📊 Информация о системе:\n"
            "• 🏗️ Гофра измеряется в мм\n"
            "• 🔌 Кабель измеряется в мм\n"
            "• 🐍 Вес змия зависит от гофрошки\n\n"
            "👥 Функции:\n"
            "• /chat_top - топ участников чата\n"
            "• /chat_stats - статистика чата\n"
            "• Сохранение прогресса в каждом чате"
        )


# Глобальный экземпляр для удобства
formatters = MessageFormatters()

# Импорты для совместимости (будут добавлены позже)
def get_gofra_info(gofra_mm: float) -> Dict:
    """Заглушка для совместимости"""
    return {'atm_speed': 1.0}

def get_cable_info(cable_mm: float) -> Dict:
    """Заглушка для совместимости"""
    return {'strength': 1.0, 'pvp_bonus': 0.0}

def get_atm_info(atm_count: int) -> Dict:
    """Заглушка для совместимости"""
    return {'regen_time': '2 часа', 'max_atm': 12}