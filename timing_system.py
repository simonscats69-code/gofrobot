"""
Система точного тайминга для гофроцентрала
Реализует точные таймеры, обратный отсчёт и визуализацию времени
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from db_manager import get_patsan, save_patsan, get_gofra_info
from config import TIMING_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class TimingStatus:
    """Статус таймера"""
    current_time: float
    next_davka_time: float
    atm_regen_time: float
    atm_count: int
    gofra_level: float
    can_davka: bool
    time_until_davka: float
    time_until_full_atm: float
    progress_davka: float
    progress_atm: float

@dataclass
class TimingStats:
    """Статистика по времени"""
    total_davki: int
    avg_wait_time: float
    last_davka_time: float
    longest_wait: float
    shortest_wait: float
    efficiency: float

class PreciseTimingManager:
    """Менеджер точного тайминга"""
    
    def __init__(self):
        self.countdown_tasks: Dict[int, asyncio.Task] = {}
        self.last_update_times: Dict[int, float] = {}
        
    async def calculate_precise_davka_time(self, user_id: int) -> Dict[str, Any]:
        """Точный расчёт времени до следующей давки"""
        try:
            patsan = await get_patsan(user_id)
            gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
            
            current_time = time.time()
            last_davka = patsan.get('last_davka_time', 0)
            
            # Базовое время восстановления (2 часа)
            base_cooldown = TIMING_CONFIG["base_davka_cooldown"]
            
            # Модификатор от гофрошки
            speed_multiplier = gofra_info['atm_speed']
            
            # Модификатор активности
            activity_bonus = await self._calculate_activity_bonus(user_id, current_time)
            
            # Финальное время восстановления
            final_cooldown = base_cooldown / (speed_multiplier * activity_bonus)
            
            next_davka_time = last_davka + final_cooldown
            time_until = max(0, next_davka_time - current_time)
            
            return {
                'current_time': current_time,
                'last_davka_time': last_davka,
                'next_davka_time': next_davka_time,
                'time_until': time_until,
                'can_davka': time_until == 0,
                'cooldown': final_cooldown,
                'speed_multiplier': speed_multiplier,
                'activity_bonus': activity_bonus
            }
            
        except Exception as e:
            logger.error(f"Error calculating precise davka time: {e}")
            return {'error': str(e)}
    
    async def get_realtime_atm_status(self, user_id: int) -> Dict[str, Any]:
        """Реальное время восстановления атмосфер"""
        try:
            patsan = await get_patsan(user_id)
            gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
            
            current_time = time.time()
            last_atm_update = patsan.get('last_atm_update', current_time)
            atm_count = patsan.get('atm_count', 0)
            
            # Базовое время восстановления 1 атмосферы (2 часа)
            base_atm_time = TIMING_CONFIG["base_atm_regen_time"]
            
            # Модификатор от гофрошки
            speed_multiplier = gofra_info['atm_speed']
            
            # Модификатор активности
            activity_bonus = await self._calculate_activity_bonus(user_id, current_time)
            
            # Финальное время восстановления
            final_atm_time = base_atm_time / (speed_multiplier * activity_bonus)
            
            # Сколько атмосфер нужно восстановить
            needed_atm = 12 - atm_count
            
            # Время до полного восстановления
            full_regen_time = needed_atm * final_atm_time
            
            # Время до следующей атмосферы
            time_to_next_atm = final_atm_time - (current_time - last_atm_update) % final_atm_time
            
            return {
                'current_time': current_time,
                'last_atm_update': last_atm_update,
                'atm_count': atm_count,
                'needed_atm': needed_atm,
                'time_to_next_atm': max(0, time_to_next_atm),
                'full_regen_time': full_regen_time,
                'atm_regen_rate': final_atm_time,
                'speed_multiplier': speed_multiplier,
                'activity_bonus': activity_bonus
            }
            
        except Exception as e:
            logger.error(f"Error getting realtime atm status: {e}")
            return {'error': str(e)}
    
    async def _calculate_activity_bonus(self, user_id: int, current_time: float) -> float:
        """Рассчитать бонус за активность"""
        try:
            patsan = await get_patsan(user_id)
            
            last_activity = patsan.get('last_activity', 0)
            days_inactive = (current_time - last_activity) / 86400  # в днях
            
            # Базовый бонус за активность
            if days_inactive < 1:
                return 1.2  # 20% бонус за активность
            elif days_inactive < 3:
                return 1.0  # Нормальное время
            elif days_inactive < 7:
                return 0.9  # 10% штраф за неактивность
            else:
                return 0.8  # 20% штраф за долгую неактивность
                
        except Exception as e:
            logger.error(f"Error calculating activity bonus: {e}")
            return 1.0
    
    async def get_timing_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику по времени"""
        try:
            patsan = await get_patsan(user_id)
            
            davki_history = patsan.get('davki_history', [])
            if not davki_history:
                return {
                    'total_davki': 0,
                    'avg_wait_time': 0,
                    'last_davka_time': 0,
                    'longest_wait': 0,
                    'shortest_wait': 0,
                    'efficiency': 0
                }
            
            # Рассчитываем временные интервалы
            wait_times = []
            for i in range(1, len(davki_history)):
                wait_time = davki_history[i] - davki_history[i-1]
                wait_times.append(wait_time)
            
            if wait_times:
                avg_wait = sum(wait_times) / len(wait_times)
                longest_wait = max(wait_times)
                shortest_wait = min(wait_times)
            else:
                avg_wait = 0
                longest_wait = 0
                shortest_wait = 0
            
            # Эффективность использования времени (сколько процентов времени можно было давить)
            current_time = time.time()
            total_possible_davki = (current_time - davki_history[0]) / TIMING_CONFIG["base_davka_cooldown"]
            actual_davki = len(davki_history)
            efficiency = min(100, (actual_davki / total_possible_davki) * 100) if total_possible_davki > 0 else 0
            
            return {
                'total_davki': len(davki_history),
                'avg_wait_time': avg_wait,
                'last_davka_time': davki_history[-1] if davki_history else 0,
                'longest_wait': longest_wait,
                'shortest_wait': shortest_wait,
                'efficiency': efficiency
            }
            
        except Exception as e:
            logger.error(f"Error getting timing statistics: {e}")
            return {'error': str(e)}
    
    async def format_precise_time(self, seconds: float) -> str:
        """Форматировать время с миллисекундами и анимацией"""
        if seconds < 1:
            return f"⏱️ {seconds:.3f}с"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"📅 {days}д {hours}ч {minutes}м {secs}с"
        elif hours > 0:
            return f"⏰ {hours}ч {minutes}м {secs}с"
        elif minutes > 0:
            return f"⏱️ {minutes}м {secs}с"
        else:
            return f"⚡ {secs}с"
    
    def create_progress_bar(self, current: float, total: float, length: int = 15) -> str:
        """Создать прогресс-бар с анимацией"""
        if total <= 0:
            return "█" * length
        
        progress = min(1.0, max(0.0, current / total))
        filled = int(length * progress)
        empty = length - filled
        
        # Добавляем анимацию для готового состояния
        if filled == length:
            return "█" * filled + " 🎉"
        elif filled >= length * 0.8:
            return "█" * filled + "🔥" * empty
        elif filled >= length * 0.5:
            return "█" * filled + "⚡" * empty
        else:
            return "█" * filled + "░" * empty
    
    def get_time_color(self, time_until: float, threshold_fast: float = 300, threshold_medium: float = 1800) -> str:
        """Получить цветовую индикацию времени с улучшенной системой"""
        if time_until <= 0:
            return "🟢"  # Можно давить
        elif time_until <= 60:  # 1 минута
            return "🟡"  # Скоро можно (1 минута)
        elif time_until <= 300:  # 5 минут
            return "🟠"  # Скоро можно (5 минут)
        elif time_until <= 900:  # 15 минут
            return "🔴"  # Среднее время (15 минут)
        elif time_until <= 1800:  # 30 минут
            return "🟣"  # Долго ждать (30 минут)
        elif time_until <= 3600:  # 1 час
            return "⚫"  # Очень долго (1 час)
        else:
            return "💀"  # Смертельно долго (1+ час)
    
    async def start_countdown(self, user_id: int, chat_id: int, message_id: int, bot):
        """Запустить обратный отсчёт"""
        if user_id in self.countdown_tasks:
            self.countdown_tasks[user_id].cancel()
        
        task = asyncio.create_task(self._countdown_loop(user_id, chat_id, message_id, bot))
        self.countdown_tasks[user_id] = task
        self.last_update_times[user_id] = time.time()
    
    async def stop_countdown(self, user_id: int):
        """Остановить обратный отсчёт"""
        if user_id in self.countdown_tasks:
            self.countdown_tasks[user_id].cancel()
            del self.countdown_tasks[user_id]
    
    async def _countdown_loop(self, user_id: int, chat_id: int, message_id: int, bot):
        """Цикл обратного отсчёта с улучшенной логикой"""
        try:
            while True:
                await asyncio.sleep(5)  # Обновляем каждые 5 секунд для более плавной анимации
                
                # Проверяем, не прошло ли слишком много времени с последнего обновления
                if time.time() - self.last_update_times.get(user_id, 0) > 600:  # 10 минут
                    await self.stop_countdown(user_id)
                    break
                
                # Получаем актуальную информацию
                davka_info = await self.calculate_precise_davka_time(user_id)
                atm_info = await self.get_realtime_atm_status(user_id)
                
                if 'error' in davka_info or 'error' in atm_info:
                    continue
                
                # Проверяем, изменилось ли что-то существенно
                current_time = time.time()
                last_update = self.last_update_times.get(user_id, 0)
                
                # Если прошло меньше 2 секунд и время не изменилось существенно, пропускаем обновление
                if current_time - last_update < 2:
                    continue
                
                # Формируем сообщение с таймерами
                message_text = await self._format_countdown_message(davka_info, atm_info)
                
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=message_text,
                        reply_markup=self._get_countdown_keyboard()
                    )
                    self.last_update_times[user_id] = current_time
                except TelegramBadRequest:
                    # Сообщение не изменилось, пропускаем
                    pass
                except Exception as e:
                    logger.error(f"Error updating countdown message: {e}")
                    await self.stop_countdown(user_id)
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in countdown loop: {e}")
    
    async def _format_countdown_message(self, davka_info: Dict, atm_info: Dict) -> str:
        """Форматировать сообщение с таймерами с улучшенной визуализацией"""
        current_time = davka_info['current_time']
        
        # Информация о давке
        time_until_davka = davka_info['time_until']
        can_davka = davka_info['can_davka']
        davka_color = self.get_time_color(time_until_davka)
        
        # Информация об атмосферах
        atm_count = atm_info['atm_count']
        needed_atm = atm_info['needed_atm']
        time_to_next_atm = atm_info['time_to_next_atm']
        full_regen_time = atm_info['full_regen_time']
        
        atm_progress = ((12 - needed_atm) / 12) * 100 if needed_atm < 12 else 100
        davka_progress = ((TIMING_CONFIG["base_davka_cooldown"] - time_until_davka) / TIMING_CONFIG["base_davka_cooldown"]) * 100 if time_until_davka > 0 else 100
        
        message = f"⏰ ТОЧНЫЕ ТАЙМЕРЫ\n\n"
        
        # Таймер давки
        if can_davka:
            message += f"{davka_color} ДАВКА ГОТОВА! 🎉\n"
            message += f"🚀 Нажми /davka и дави змия!\n\n"
        else:
            message += f"{davka_color} ДАВКА: {await self.format_precise_time(time_until_davka)}\n"
            message += f"📊 [{self.create_progress_bar(davka_progress, 100)}] {davka_progress:.1f}%\n\n"
        
        # Таймер атмосфер
        message += f"🌀 АТМОСФЕРЫ: {atm_count}/12\n"
        if needed_atm > 0:
            message += f"⏱️ Следующая: {await self.format_precise_time(time_to_next_atm)}\n"
            message += f"🕐 Полностью: {await self.format_precise_time(full_regen_time)}\n"
            message += f"📊 [{self.create_progress_bar(atm_progress, 100)}] {atm_progress:.1f}%\n"
        
        # Модификаторы
        message += f"\n⚡ МОДИФИКАТОРЫ:\n"
        message += f"🏗️ Гофрошка: x{davka_info['speed_multiplier']:.2f}\n"
        message += f"🎯 Активность: x{davka_info['activity_bonus']:.2f}\n"
        
        # Текущее время
        message += f"\n🕒 Серверное время: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}"
        
        # Добавляем анимационные эффекты для готовых таймеров
        if can_davka:
            message += f"\n🎉 ДАВКА ГОТОВА! БЫСТРЕЕ ДАВИ ЗМИЯ!"
        
        return message
    
    def _get_countdown_keyboard(self) -> InlineKeyboardMarkup:
        """Получить клавиатуру для таймеров"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🐍 Давить", callback_data="davka"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="timing_refresh")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="timing_stats"),
                InlineKeyboardButton(text="❌ Стоп", callback_data="timing_stop")
            ]
        ])

# Глобальный экземпляр менеджера тайминга
timing_manager = PreciseTimingManager()

# Конфигурация по умолчанию (если нет в config.py)
if not hasattr(TIMING_CONFIG, 'base_davka_cooldown'):
    TIMING_CONFIG = {
        'base_davka_cooldown': 7200,  # 2 часа в секундах
        'base_atm_regen_time': 7200,  # 2 часа в секундах
        'countdown_update_interval': 10,  # Обновление каждые 10 секунд
        'max_countdown_duration': 300  # Максимальное время отсчёта 5 минут
    }