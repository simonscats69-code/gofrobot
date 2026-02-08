"""
Модуль визуального отображения для Telegram-бота гофроцентра
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============ UTILITY FUNCTIONS ============

def format_length(mm: float) -> str:
    """Форматировать длину в мм/см"""
    if mm >= 1000:
        return f"{mm / 1000:.1f}м"
    elif mm >= 10:
        return f"{mm / 10:.1f}см"
    return f"{mm:.1f}мм"


# ============ VISUAL EFFECTS ============

class Display:
    """Класс для визуальных эффектов"""
    
    EMOJI = {
        'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blue': '🔵',
        'purple': '🟣', 'orange': '🟠', 'white': '⚪', 'black': '⚫',
        'success': '✅', 'warning': '⚠️', 'error': '❌', 'info': 'ℹ️',
        'star': '⭐', 'crown': '👑', 'fire': '🔥', 'ice': '❄️',
        'lightning': '⚡', 'clock': '⏰', 'hourglass': '⏳', 'rocket': '🚀',
        'gift': '🎁', 'party': '🎉', 'sad': '😢', 'happy': '😊',
        'muscle': '💪', 'construction': '🏗️', 'snake': '🐍', 'cable': '🔌',
        'atm': '🔋', 'davka': '🐍', 'check': '✓', 'cross': '✗'
    }
    
    PROGRESS_STYLES = {
        'default': ('█', '░'),
        'rounded': ('●', '○'),
        'square': ('■', '□'),
        'block': ('▓', '░'),
        'arrow': ('►', '░'),
        'star': ('★', '☆'),
    }
    
    @staticmethod
    def get_emoji(key: str) -> str:
        return Display.EMOJI.get(key, '⚪')
    
    @staticmethod
    def get_status_emoji(status: str) -> str:
        color_map = {
            'ready': 'green', 'active': 'green', 'success': 'success',
            'warning': 'warning', 'error': 'error', 'inactive': 'red',
            'waiting': 'yellow', 'processing': 'blue', 'completed': 'success',
            'failed': 'error'
        }
        return Display.EMOJI.get(color_map.get(status, 'white'), '⚪')
    
    # Progress bars
    @staticmethod
    def progress_bar(percentage: float, length: int = 15, style: str = 'default') -> str:
        percentage = max(0, min(100, percentage))
        filled = int(length * percentage / 100)
        empty = length - filled
        chars = Display.PROGRESS_STYLES.get(style, ('█', '░'))
        return chars[0] * filled + chars[1] * empty
    
    @staticmethod
    def atm_progress(atm_count: int, max_atm: int = 12) -> str:
        pct = (atm_count / max_atm) * 100
        return Display.progress_bar(pct, 12, 'square')
    
    @staticmethod
    def davka_progress(current: float, total: float) -> str:
        pct = 0 if total == 0 else (current / total) * 100
        return Display.progress_bar(pct, 10, 'default')
    
    # Dividers
    @staticmethod
    def divider(length: int = 30, style: str = 'simple') -> str:
        chars = {'simple': '─', 'double': '═', 'star': '★',
                 'arrow': '→', 'block': '▓', 'dot': '·'}
        char = chars.get(style, '─')
        if style == 'double':
            return f"╔{char * (length - 2)}╗"
        elif style == 'star':
            return f"★{char * (length - 2)}★"
        elif style == 'arrow':
            return f"➜{char * (length - 2)}➜"
        elif style == 'block':
            return f"▓{char * (length - 2)}▓"
        return char * length
    
    @staticmethod
    def section_divider() -> str:
        return Display.divider(25, 'double')
    
    # Time formatting
    @staticmethod
    def format_time(seconds: float) -> str:
        if seconds < 1:
            return f"{seconds:.1f}с"
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м {secs}с"
        elif minutes > 0:
            return f"{minutes}м {secs}с"
        return f"{secs}с"
    
    @staticmethod
    def format_time_short(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}с"
        elif seconds < 3600:
            return f"{int(seconds // 60)}м"
        elif seconds < 86400:
            return f"{int(seconds // 3600)}ч"
        return f"{int(seconds // 86400)}д"
    
    # Tables
    @staticmethod
    def table(headers: List[str], rows: List[List[str]], align: str = 'left') -> str:
        if not headers or not rows:
            return ""
        col_widths = []
        for i, header in enumerate(headers):
            max_w = len(header)
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(str(row[i])))
            col_widths.append(max_w + 2)
        result = ""
        header_line = ""
        for i, header in enumerate(headers):
            if align == 'right':
                header_line += header.rjust(col_widths[i])
            elif align == 'center':
                header_line += header.center(col_widths[i])
            else:
                header_line += header.ljust(col_widths[i])
        result += f"📋 {header_line}\n"
        result += Display.divider(len(header_line), 'double') + "\n"
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
    
    # Player displays
    @staticmethod
    def player_rank(i: int) -> str:
        medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        return medals[i - 1] if i <= len(medals) else f"{i}."
    
    @staticmethod
    def stat_line(label: str, value: str, percentage: Optional[float] = None, style: str = 'default') -> str:
        if percentage is not None:
            bar = Display.progress_bar(percentage, 12, style)
            return f"📊 {label}: {value} [{bar}] {percentage:.1f}%"
        return f"📈 {label}: {value}"
    
    @staticmethod
    def level_progress(current: float, next_level: float) -> Tuple[str, float]:
        if next_level <= 0:
            return "MAX", 100.0
        pct = min(100, (current / next_level) * 100)
        bar = Display.progress_bar(pct, 10, 'star')
        return bar, pct
    
    @staticmethod
    def percentage_bar(current: float, total: float, length: int = 10) -> str:
        if total == 0:
            return '░' * length
        pct = (current / total) * 100
        return Display.progress_bar(pct, length, 'default')
