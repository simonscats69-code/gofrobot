"""
Общие утилиты для всех обработчиков
"""

from typing import Any
from aiogram.exceptions import TelegramBadRequest
import logging

logger = logging.getLogger(__name__)

# Импортируем функции форматирования из utils.display
from utils.display import Display

# Алиас для форматирования времени
ft = Display.format_time

# Алиас для прогрессбара (использует Display.progress_bar)
def pb(c: float, t: float, l: int = 10) -> str:
    """
    Create a progress bar string (using Display.progress_bar internally)
    """
    pct = (c / t * 100) if t > 0 else 0
    return Display.progress_bar(pct, l, 'default')


def ignore_not_modified_error(func):
    """
    Decorator to ignore TelegramBadRequest errors when message is not modified

    Args:
        func: function to wrap

    Returns:
        wrapper function
    """
    async def wrapper(*args, **kwargs):
        try:
            # Only pass kwargs that the function can actually accept
            import inspect
            sig = inspect.signature(func)
            filtered_kwargs = {
                k: v for k, v in kwargs.items()
                if k in sig.parameters
            }
            return await func(*args, **filtered_kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                if len(args) > 0 and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise
    return wrapper


# ============ VALIDATION FUNCTIONS ============

def validate_nickname(nickname: str) -> tuple[bool, str]:
    """
    Validate nickname format and content

    Args:
        nickname: nickname to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    import re

    if len(nickname) < 3 or len(nickname) > 20:
        return False, "Длина ника должна быть от 3 до 20 символов"

    banned_words = ["admin", "root", "support", "бот", "модератор",
                    "админ", "help", "техподдержка"]
    nickname_lower = nickname.lower()
    if any(word in nickname_lower for word in banned_words):
        return False, "Запрещённый ник"

    pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9_\- ]+$'
    if not re.match(pattern, nickname):
        return False, "Только буквы, цифры, пробелы, дефисы и подчёркивания"

    if nickname.strip() != nickname:
        return False, "Убери пробелы в начале или конце"

    if nickname.count('  ') > 0:
        return False, "Слишком много пробелов подряд"

    return True, "OK"

# Экспорт
__all__ = ['ft', 'pb', 'ignore_not_modified_error', 'validate_nickname']
