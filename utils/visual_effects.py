"""
Система визуальных эффектов для Telegram-бота
Реализует красивые сообщения, прогресс-бары, анимации и другие визуальные улучшения
"""

import asyncio
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from aiogram import types
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

class VisualEffects:
    """Класс для визуальных эффектов"""
    
    # Цветовые коды через эмодзи
    COLORS = {
        'green': '🟢',
        'yellow': '🟡', 
        'red': '🔴',
        'blue': '🔵',
        'purple': '🟣',
        'orange': '🟠',
        'white': '⚪',
        'black': '⚫',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️',
        'star': '⭐',
        'crown': '👑',
        'fire': '🔥',
        'ice': '❄️',
        'lightning': '⚡',
        'clock': '⏰',
        'hourglass': '⏳',
        'rocket': '🚀',
        'gift': '🎁',
        'party': '🎉',
        'sad': '😢',
        'happy': '😊',
        'thinking': '🤔',
        'muscle': '💪',
        'construction': '🏗️',
        'snake': '🐍',
        'cable': '🔌',
        'atm': '🔋'
    }
    
    # Градиенты через эмодзи
    GRADIENTS = {
        'success': ['🟢', '🟡', '🟠', '🔴'],
        'progress': ['🔵', '🟢', '🟡', '🟠', '🔴'],
        'warning': ['🟡', '🟠', '🔴'],
        'cool': ['🔵', '🟣', '🟠', '🟡'],
        'fire': ['🟢', '🟡', '🟠', '🔴', '⚫']
    }
    
    @staticmethod
    def get_color_emoji(status: str) -> str:
        """Получить цветовой эмодзи по статусу"""
        color_map = {
            'ready': 'green',
            'active': 'green', 
            'success': 'success',
            'warning': 'warning',
            'error': 'error',
            'inactive': 'red',
            'waiting': 'yellow',
            'processing': 'blue',
            'completed': 'success',
            'failed': 'error'
        }
        return VisualEffects.COLORS.get(color_map.get(status, 'white'), '⚪')
    
    @staticmethod
    def create_progress_bar(percentage: float, length: int = 15, style: str = 'default') -> str:
        """Создать текстовый прогресс-бар"""
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
        
        filled = int(length * percentage / 100)
        empty = length - filled
        
        if style == 'default':
            return '█' * filled + '░' * empty
        elif style == 'rounded':
            return '●' * filled + '○' * empty
        elif style == 'square':
            return '■' * filled + '□' * empty
        elif style == 'block':
            return '▓' * filled + '░' * empty
        else:
            return '█' * filled + '░' * empty
    
    @staticmethod
    def create_circular_indicator(percentage: float, radius: int = 3) -> str:
        """Создать круговой индикатор"""
        # Простой круговой индикатор из символов
        symbols = ['●', '◐', '◒', '◑', '◒', '◐']
        index = int((percentage / 100) * len(symbols))
        return symbols[min(index, len(symbols) - 1)]
    
    @staticmethod
    def create_gradient_text(text: str, gradient_name: str = 'success') -> str:
        """Создать текст с градиентным эффектом"""
        gradient = VisualEffects.GRADIENTS.get(gradient_name, ['⚪'])
        result = ""
        for i, char in enumerate(text):
            color = gradient[i % len(gradient)]
            result += f"{color}{char}"
        return result
    
    @staticmethod
    def format_statistic_line(label: str, value: str, percentage: Optional[float] = None, 
                            style: str = 'default') -> str:
        """Форматировать строку статистики"""
        if percentage is not None:
            progress = VisualEffects.create_progress_bar(percentage, 12, style)
            return f"📊 {label}: {value} [{progress}] {percentage:.1f}%"
        else:
            return f"📈 {label}: {value}"
    
    @staticmethod
    def create_status_block(title: str, items: List[Tuple[str, str, str]], 
                           header_emoji: str = '📋') -> str:
        """Создать блок статуса"""
        result = f"{header_emoji} {title}\n\n"
        for emoji, label, value in items:
            result += f"{emoji} {label}: {value}\n"
        return result
    
    @staticmethod
    def create_divider(char: str = '─', length: int = 30, style: str = 'simple') -> str:
        """Создать визуальный разделитель"""
        if style == 'simple':
            return char * length
        elif style == 'double':
            return f"═{char * (length - 2)}═"
        elif style == 'arrow':
            return f"→{char * (length - 2)}→"
        elif style == 'star':
            return f"★{char * (length - 2)}★"
        else:
            return char * length
    
    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]], 
                    align: str = 'left') -> str:
        """Создать красивую таблицу"""
        # Вычисляем ширину колонок
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)
        
        # Формируем таблицу
        result = ""
        
        # Заголовок
        header_line = ""
        for i, header in enumerate(headers):
            if align == 'right':
                header_line += header.rjust(col_widths[i])
            elif align == 'center':
                header_line += header.center(col_widths[i])
            else:
                header_line += header.ljust(col_widths[i])
        result += f"📋 {header_line}\n"
        result += VisualEffects.create_divider('─', len(header_line), 'double') + "\n"
        
        # Данные
        for row in rows:
            row_line = ""
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    if align == 'right':
                        row_line += str(cell).rjust(col_widths[i])
                    elif align == 'center':
                        row_line += str(cell).center(col_widths[i])
                    else:
                        row_line += str(cell).ljust(col_widths[i])
            result += f"{row_line}\n"
        
        return result
    
    @staticmethod
    def create_animated_text(text: str, animation_type: str = 'blink') -> List[str]:
        """Создать анимированный текст"""
        if animation_type == 'blink':
            return [text, "   " + text[3:], text, "   " + text[3:]]
        elif animation_type == 'wave':
            return [text, text[::-1], text, text[::-1]]
        elif animation_type == 'color':
            colors = ['🔴', '🟡', '🟢', '🔵', '🟣']
            return [f"{color}{text[1:]}" for color in colors]
        else:
            return [text]
    
    @staticmethod
    def format_time_precise(seconds: float) -> str:
        """Форматировать время с миллисекундами"""
        if seconds < 1:
            return f"{seconds:.3f}с"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м {secs}с"
        elif hours > 0:
            return f"{hours}ч {minutes}м {secs}с"
        elif minutes > 0:
            return f"{minutes}м {secs}с"
        else:
            return f"{secs}с"

# Глобальный экземпляр для удобства
visual_effects = VisualEffects()