"""
Система анимационных эффектов для Telegram-бота
Реализует мерцание, плавные переходы и другие анимационные эффекты
"""

import asyncio
import logging
from typing import List, Optional, Callable
from aiogram import types
from aiogram.exceptions import TelegramBadRequest

# Импортируем visual_effects для использования в анимациях
try:
    from utils import visual_effects
except ImportError:
    # Заглушка для visual_effects если импорт не удался
    class MockVisualEffects:
        @staticmethod
        def create_progress_bar(percentage: float, length: int = 15, style: str = 'default') -> str:
            return "█" * int(length * percentage / 100) + "░" * (length - int(length * percentage / 100))
    
    visual_effects = MockVisualEffects()

logger = logging.getLogger(__name__)

class AnimationManager:
    """Менеджер анимационных эффектов"""
    
    def __init__(self):
        self.active_animations: dict = {}
    
    async def start_blinking(self, bot, chat_id: int, message_id: int, 
                           text: str, duration: int = 10, interval: float = 0.5):
        """Запустить мерцание текста"""
        animation_key = f"{chat_id}_{message_id}_blink"
        
        if animation_key in self.active_animations:
            await self.stop_animation(animation_key)
        
        task = asyncio.create_task(self._blink_task(
            bot, chat_id, message_id, text, duration, interval
        ))
        self.active_animations[animation_key] = task
    
    async def start_color_cycle(self, bot, chat_id: int, message_id: int,
                              text: str, duration: int = 10, interval: float = 1.0):
        """Запустить смену цветов текста"""
        animation_key = f"{chat_id}_{message_id}_color"
        
        if animation_key in self.active_animations:
            await self.stop_animation(animation_key)
        
        task = asyncio.create_task(self._color_cycle_task(
            bot, chat_id, message_id, text, duration, interval
        ))
        self.active_animations[animation_key] = task
    
    async def start_wave_animation(self, bot, chat_id: int, message_id: int,
                                 text: str, duration: int = 5, interval: float = 0.3):
        """Запустить волновую анимацию текста"""
        animation_key = f"{chat_id}_{message_id}_wave"
        
        if animation_key in self.active_animations:
            await self.stop_animation(animation_key)
        
        task = asyncio.create_task(self._wave_task(
            bot, chat_id, message_id, text, duration, interval
        ))
        self.active_animations[animation_key] = task
    
    async def start_progress_animation(self, bot, chat_id: int, message_id: int,
                                     start_value: float, end_value: float,
                                     duration: int = 5, interval: float = 0.1):
        """Запустить анимацию прогресс-бара"""
        animation_key = f"{chat_id}_{message_id}_progress"
        
        if animation_key in self.active_animations:
            await self.stop_animation(animation_key)
        
        task = asyncio.create_task(self._progress_task(
            bot, chat_id, message_id, start_value, end_value, duration, interval
        ))
        self.active_animations[animation_key] = task
    
    async def stop_animation(self, animation_key: str):
        """Остановить анимацию"""
        if animation_key in self.active_animations:
            self.active_animations[animation_key].cancel()
            del self.active_animations[animation_key]
    
    async def stop_all_animations(self):
        """Остановить все анимации"""
        for task in self.active_animations.values():
            task.cancel()
        self.active_animations.clear()
    
    async def _blink_task(self, bot, chat_id: int, message_id: int,
                         text: str, duration: int, interval: float):
        """Задача мерцания текста"""
        try:
            start_time = asyncio.get_event_loop().time()
            original_text = text
            
            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > duration:
                    break
                
                # Мерцаем текстом
                await self._safe_edit_message(bot, chat_id, message_id, original_text)
                await asyncio.sleep(interval)
                
                # Делаем текст прозрачным (заменяем символы на пробелы)
                hidden_text = original_text.replace('🚨', '   ').replace('⚠️', '   ')
                await self._safe_edit_message(bot, chat_id, message_id, hidden_text)
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in blink animation: {e}")
    
    async def _color_cycle_task(self, bot, chat_id: int, message_id: int,
                              text: str, duration: int, interval: float):
        """Задача смены цветов"""
        try:
            start_time = asyncio.get_event_loop().time()
            colors = ['🔴', '🟡', '🟢', '🔵', '🟣', '🟠']
            
            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > duration:
                    break
                
                # Меняем цвет
                color_index = int((current_time - start_time) / interval) % len(colors)
                color = colors[color_index]
                
                # Заменяем первый эмодзи на текущий цвет
                if text.startswith(('🚨', '⚠️', '✅', '❌')):
                    animated_text = color + text[1:]
                else:
                    animated_text = color + text
                
                await self._safe_edit_message(bot, chat_id, message_id, animated_text)
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in color cycle animation: {e}")
    
    async def _wave_task(self, bot, chat_id: int, message_id: int,
                       text: str, duration: int, interval: float):
        """Задача волновой анимации"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > duration:
                    break
                
                # Создаём волновой эффект
                wave_text = self._create_wave_text(text, current_time - start_time)
                await self._safe_edit_message(bot, chat_id, message_id, wave_text)
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in wave animation: {e}")
    
    async def _progress_task(self, bot, chat_id: int, message_id: int,
                           start_value: float, end_value: float,
                           duration: int, interval: float):
        """Задача анимации прогресс-бара"""
        try:
            start_time = asyncio.get_event_loop().time()
            current_value = start_value
            
            while True:
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time
                
                if elapsed >= duration:
                    current_value = end_value
                else:
                    # Плавное изменение значения
                    progress = elapsed / duration
                    current_value = start_value + (end_value - start_value) * progress
                
                # Создаём анимированный прогресс-бар
                progress_bar = visual_effects.create_progress_bar(current_value, 20, 'default')
                animated_text = f"📊 Загрузка: {current_value:.1f}%\n[{progress_bar}]"
                
                await self._safe_edit_message(bot, chat_id, message_id, animated_text)
                
                if elapsed >= duration:
                    break
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in progress animation: {e}")
    
    async def _safe_edit_message(self, bot, chat_id: int, message_id: int, text: str):
        """Безопасное редактирование сообщения"""
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, пропускаем
            pass
        except Exception as e:
            logger.error(f"Error editing message: {e}")
    
    def _create_wave_text(self, text: str, time_offset: float) -> str:
        """Создать волновой эффект для текста"""
        result = ""
        for i, char in enumerate(text):
            # Создаём волновой эффект через изменение регистра
            if i % 2 == 0:
                result += char.upper()
            else:
                result += char.lower()
        return result

class NotificationEffects:
    """Эффекты для уведомлений"""
    
    @staticmethod
    async def important_notification(bot, chat_id: int, text: str, duration: int = 5):
        """Показать важное уведомление с мерцанием"""
        animation_manager = AnimationManager()
        
        # Отправляем сообщение
        message = await bot.send_message(chat_id, text)
        
        # Запускаем мерцание
        await animation_manager.start_blinking(
            bot, chat_id, message.message_id, text, duration, 0.5
        )
        
        # Ждём окончания анимации
        await asyncio.sleep(duration)
        
        # Останавливаем анимацию
        await animation_manager.stop_animation(f"{chat_id}_{message.message_id}_blink")
    
    @staticmethod
    async def success_notification(bot, chat_id: int, text: str, duration: int = 3):
        """Показать уведомление об успехе с цветовой анимацией"""
        animation_manager = AnimationManager()
        
        # Отправляем сообщение
        message = await bot.send_message(chat_id, f"✅ {text}")
        
        # Запускаем цветовую анимацию
        await animation_manager.start_color_cycle(
            bot, chat_id, message.message_id, f"✅ {text}", duration, 0.5
        )
        
        # Ждём окончания анимации
        await asyncio.sleep(duration)
        
        # Останавливаем анимацию
        await animation_manager.stop_animation(f"{chat_id}_{message.message_id}_color")
    
    @staticmethod
    async def progress_notification(bot, chat_id: int, start: float, end: float, duration: int = 5):
        """Показать прогресс с анимацией"""
        animation_manager = AnimationManager()
        
        # Отправляем сообщение
        message = await bot.send_message(chat_id, "📊 Загрузка: 0%")
        
        # Запускаем анимацию прогресса
        await animation_manager.start_progress_animation(
            bot, chat_id, message.message_id, start, end, duration, 0.1
        )
        
        # Ждём окончания анимации
        await asyncio.sleep(duration)
        
        # Останавливаем анимацию
        await animation_manager.stop_animation(f"{chat_id}_{message.message_id}_progress")

# Глобальные экземпляры
animation_manager = AnimationManager()
notification_effects = NotificationEffects()