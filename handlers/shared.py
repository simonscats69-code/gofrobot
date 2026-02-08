"""
Общие утилиты для всех обработчиков
"""

from typing import Any
from aiogram.exceptions import TelegramBadRequest
import logging

logger = logging.getLogger(__name__)


def ft(s: int) -> str:
    """
    Format time duration in seconds to human-readable format

    Args:
        s: seconds

    Returns:
        str: formatted time string
    """
    if s < 60:
        return f"{s}с"
    m, h, d = s // 60, s // 3600, s // 86400
    if d > 0:
        return f"{d}д {h%24}ч {m%60}м"
    if h > 0:
        return f"{h}ч {m%60}м {s%60}с"
    return f"{m}м {s%60}с"


def pb(c: float, t: float, l: int = 10) -> str:
    """
    Create a progress bar string

    Args:
        c: current value
        t: total value
        l: length of bar

    Returns:
        str: progress bar
    """
    f = int((c / t) * l) if t > 0 else 0
    return "█" * f + "░" * (l - f)


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


# Экспорт
__all__ = ['ft', 'pb', 'ignore_not_modified_error']
