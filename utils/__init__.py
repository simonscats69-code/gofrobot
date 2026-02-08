"""
Утилиты для Telegram-бота гофроцентра
"""

# Импорты для визуальных эффектов
try:
    from .visual_effects import visual_effects
except ImportError:
    visual_effects = None

# Импорты для анимаций
try:
    from .animations import animation_manager, notification_effects
except ImportError:
    animation_manager = None
    notification_effects = None

__all__ = [
    'visual_effects',
    'animation_manager',
    'notification_effects',
]
