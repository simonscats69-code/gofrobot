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


# ============ FORMATTER FUNCTIONS ============

def format_welcome(nickname: str, gofra_info: Dict, cable_mm: float, atm_count: int, zmiy_grams: float) -> str:
    div = Display.section_divider()
    return (
        f"🏗️ ДОБРО ПОЖАЛОВАТЬ В ГОФРОБОТ!\n\n"
        f"Ну чё, {nickname}? 👊\n\n"
        f"{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {gofra_info['length_display']} | 🔌 {format_length(cable_mm)}\n\n"
        f"🌀 Атмосферы: {atm_count}/12\n"
        f"🐍 Змий: {zmiy_grams:.0f}г\n\n"
        f"Доступные команды:\n"
        f"/start - Начать игру\n"
        f"/profile - Профиль\n"
        f"/davka - Давить змия\n"
        f"/rademka - Радёмка (PvP)\n"
        f"/top - Топ игроков\n"
        f"/timing - Таймеры\n"
        f"/help - Помощь\n"
        f"{div}"
    )


def format_profile(patsan: Dict, gofra_info: Dict) -> str:
    div = Display.section_divider()
    regen = 7200 / gofra_info['atm_speed']
    atm_pct = (patsan.get('atm_count', 0) / 12) * 100
    atm_str = f"{patsan.get('atm_count', 0)}/12"
    return (
        f"{Display.get_emoji('crown')} ПРОФИЛЬ: {patsan.get('nickname', 'Пацанчик')}\n"
        f"{div}\n"
        f"{gofra_info['emoji']} {gofra_info['name']}\n"
        f"🏗️ Гофра: {gofra_info['length_display']}\n"
        f"🔌 Кабель: {format_length(patsan.get('cable_mm', 10.0))}\n\n"
        f"{Display.stat_line('Атмосферы', atm_str, atm_pct, 'square')}\n"
        f"⏱️ Восстановление: {Display.format_time(regen)} за 1 атм.\n\n"
        f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n\n"
        f"📈 Статистика:\n"
        f"📊 Всего давок: {patsan.get('total_davki', 0)}\n"
        f"📈 Всего змия: {patsan.get('total_zmiy_grams', 0.0):.0f}г"
    )


def format_top_players(top_players: List[Dict], sort_by: str = 'gofra') -> str:
    if not top_players:
        return f"{Display.get_emoji('sad')} Топ пуст!\n\nБудь первым!"
    headers = ["#", "Ник", "Гофра", "Кабель", "Змий"]
    rows = []
    for i, player in enumerate(top_players[:10], 1):
        nick = player.get('nickname', f"Пацан_{player.get('user_id', '?')}")
        if len(nick) > 15:
            nick = nick[:12] + "..."
        rows.append([
            Display.player_rank(i),
            nick,
            format_length(player.get('gofra_mm', 10.0)),
            format_length(player.get('cable_mm', 10.0)),
            f"{player.get('zmiy_grams', 0):.0f}г"
        ])
    return f"🏆 ТОП ИГРОКОВ\n\n" + Display.table(headers, rows, 'left')


def format_gofra_info(gofra_mm: float, gofra_info: Dict) -> str:
    next_thr = gofra_info.get('next_threshold', 0)
    bar, pct = Display.level_progress(gofra_mm, next_thr)
    div = Display.section_divider()
    
    lines = [
        f"🏗️ ИНФОРМАЦИЯ О ГОФРОШКЕ\n\n",
        f"{gofra_info['emoji']} {gofra_info['name']}\n",
        f"📏 Длина: {gofra_info['length_display']}\n\n",
        f"📊 [{bar}] {pct:.1f}%\n\n",
        f"Характеристики:\n",
        f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n",
        f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г\n\n"
    ]
    
    if next_thr > 0:
        next_g = gofra_info['next_gofra']
        lines.extend([
            f"Следующая гофрошка:\n",
            f"{gofra_info['emoji']} → {next_g['emoji']}\n",
            f"{next_g['name']} (от {next_g['length_display']})\n",
            f"📈 Прогресс: {pct:.1f}%\n",
            f"⚡ Новая скорость: x{next_g['atm_speed']:.2f}"
        ])
    else:
        lines.append("🎉 Максимальный уровень гофрошки!")
    
    return ''.join(lines)


def format_cable_info(cable_mm: float) -> str:
    bar = Display.percentage_bar(cable_mm, 1000, 10)
    pct = (cable_mm / 1000) * 100
    return (
        f"🔌 ИНФОРМАЦИЯ О КАБЕЛЕ\n\n"
        f"💪 Длина: {format_length(cable_mm)}\n"
        f"📊 [{bar}] {pct:.1f}%\n\n"
        f"⚔️ Бонус в PvP: +{(cable_mm * 0.02):.1f}%\n\n"
        f"Прогресс:\n"
        f"📊 Всего змия: 0г\n"
        f"📈 Следующий +0.1 мм через: 2000г"
    )


def format_atm_status(atm_count: int, regen_info: Dict, gofra_info: Dict) -> str:
    bar = Display.atm_progress(atm_count)
    pct = (atm_count / 12) * 100
    return (
        f"🌡️ СОСТОЯНИЕ АТМОСФЕР\n\n"
        f"🌀 Текущий запас: {atm_count}/12\n"
        f"📊 [{bar}] {pct:.1f}%\n\n"
        f"Восстановление:\n"
        f"⏱️ 1 атмосфера: {regen_info['per_atm']:.0f}сек\n"
        f"🕐 До полного: {regen_info['total']:.0f}сек\n"
        f"📈 Осталось: {regen_info['needed']} атмосфер\n\n"
        f"Влияние гофрошки:\n"
        f"{gofra_info['emoji']} {gofra_info['name']}\n"
        f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}\n\n"
        f"Полные 12 атмосфер нужны для давки!"
    )
