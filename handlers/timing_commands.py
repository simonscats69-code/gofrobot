"""
Команды для управления системой точного тайминга
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from keyboards import main_keyboard
from timing_system import timing_manager
from db_manager import get_patsan, get_gofra_info
from config import TIMING_CONFIG

# Утилиты для форматирования
def get_atm_info(atm_count: int) -> dict:
    """Информация об атмосферах"""
    return {
        'atm_count': atm_count,
        'regen_time': '1 атм. = 2 часа',
        'max_atm': 12
    }

def get_cable_info(cable_mm: float) -> dict:
    """Информация о кабеле"""
    return {
        'length': cable_mm,
        'strength': cable_mm / 10.0
    }

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("timing"))
async def cmd_timing(message: Message):
    """Показать все таймеры"""
    try:
        user_id = message.from_user.id
        
        # Получаем информацию о давке
        davka_info = await timing_manager.calculate_precise_davka_time(user_id)
        if 'error' in davka_info:
            await message.answer("❌ Ошибка получения данных о давке")
            return
        
        # Получаем информацию об атмосферах
        atm_info = await timing_manager.get_realtime_atm_status(user_id)
        if 'error' in atm_info:
            await message.answer("❌ Ошибка получения данных об атмосферах")
            return
        
        # Формируем сообщение
        message_text = await _format_timing_message(davka_info, atm_info)
        
        # Отправляем сообщение с клавиатурой
        await message.answer(
            message_text,
            reply_markup=timing_manager._get_countdown_keyboard()
        )
        
        # Запускаем обратный отсчёт
        await timing_manager.start_countdown(user_id, message.chat.id, message.message_id + 1, message.bot)
        
    except Exception as e:
        logger.error(f"Error in cmd_timing: {e}")
        await message.answer("❌ Произошла ошибка при получении таймеров")

@router.message(Command("stats", "statistics"))
async def cmd_stats(message: Message):
    """Показать статистику"""
    try:
        user_id = message.from_user.id
        command_args = message.text.split()
        
        if len(command_args) > 1 and command_args[1] == "timing":
            # Статистика по времени
            stats = await timing_manager.get_timing_statistics(user_id)
            if 'error' in stats:
                await message.answer("❌ Ошибка получения статистики по времени")
                return
            
            message_text = await _format_timing_stats_message(stats)
            await message.answer(message_text, reply_markup=main_keyboard())
        else:
            # Общая статистика (оставляем существующую логику)
            patsan = await get_patsan(user_id)
            gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
            cable_info = get_cable_info(patsan.get('cable_mm', 10.0))
            atm_info = get_atm_info(patsan.get('atm_count', 0))
            
            message_text = (
                f"📊 СТАТИСТИКА ПАЦАНА {patsan['nickname']}\n\n"
                f"🏗️ Гофрошка: {patsan['gofra_mm']:.1f}мм\n"
                f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}\n"
                f"🔋 Атмосферы: {patsan['atm_count']}/12\n"
                f"🕐 Время восстановления: {atm_info['regen_time']}\n"
                f"🔌 Кабель: {patsan['cable_mm']:.1f}мм\n"
                f"💪 Сила: x{cable_info['strength']:.2f}\n"
                f"🐍 Змий: {patsan['zmiy_grams']:.1f}г\n"
                f"🏆 Радёмка: {patsan['rademka_wins']}/{patsan['rademka_losses']}\n"
                f"📅 Регистрация: {datetime.fromtimestamp(patsan['registration_time']).strftime('%d.%m.%Y')}"
            )
            
            await message.answer(message_text, reply_markup=main_keyboard())
        
    except Exception as e:
        logger.error(f"Error in cmd_stats: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики")

@router.message(Command("countdown"))
async def cmd_countdown(message: Message):
    """Показать обратный отсчёт до давки"""
    try:
        user_id = message.from_user.id
        
        # Получаем информацию о давке
        davka_info = await timing_manager.calculate_precise_davka_time(user_id)
        if 'error' in davka_info:
            await message.answer("❌ Ошибка получения данных о давке")
            return
        
        # Формируем сообщение с обратным отсчётом
        message_text = await _format_countdown_message(davka_info)
        
        # Отправляем сообщение с клавиатурой
        await message.answer(
            message_text,
            reply_markup=timing_manager._get_countdown_keyboard()
        )
        
        # Запускаем обратный отсчёт
        await timing_manager.start_countdown(user_id, message.chat.id, message.message_id + 1, message.bot)
        
    except Exception as e:
        logger.error(f"Error in cmd_countdown: {e}")
        await message.answer("❌ Произошла ошибка при получении обратного отсчёта")

@router.callback_query(F.data == "timing_refresh")
async def callback_timing_refresh(callback: CallbackQuery):
    """Обновить таймеры"""
    try:
        user_id = callback.from_user.id
        
        # Получаем информацию о давке
        davka_info = await timing_manager.calculate_precise_davka_time(user_id)
        if 'error' in davka_info:
            await callback.answer("❌ Ошибка получения данных о давке")
            return
        
        # Получаем информацию об атмосферах
        atm_info = await timing_manager.get_realtime_atm_status(user_id)
        if 'error' in atm_info:
            await callback.answer("❌ Ошибка получения данных об атмосферах")
            return
        
        # Формируем сообщение
        message_text = await _format_timing_message(davka_info, atm_info)
        
        # Обновляем сообщение
        await callback.message.edit_text(
            text=message_text,
            reply_markup=timing_manager._get_countdown_keyboard()
        )
        
        await callback.answer("✅ Таймеры обновлены")
        
    except TelegramBadRequest:
        # Сообщение не изменилось
        await callback.answer("⏳ Таймеры уже обновлены")
    except Exception as e:
        logger.error(f"Error in callback_timing_refresh: {e}")
        await callback.answer("❌ Ошибка обновления таймеров")

@router.callback_query(F.data == "timing_stats")
async def callback_timing_stats(callback: CallbackQuery):
    """Показать статистику по времени"""
    try:
        user_id = callback.from_user.id
        
        # Получаем статистику
        stats = await timing_manager.get_timing_statistics(user_id)
        if 'error' in stats:
            await callback.answer("❌ Ошибка получения статистики")
            return
        
        # Формируем сообщение
        message_text = await _format_timing_stats_message(stats)
        
        # Обновляем сообщение
        await callback.message.edit_text(
            text=message_text,
            reply_markup=main_keyboard()
        )
        
        await callback.answer("📊 Статистика загружена")
        
    except Exception as e:
        logger.error(f"Error in callback_timing_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики")

@router.callback_query(F.data == "timing_stop")
async def callback_timing_stop(callback: CallbackQuery):
    """Остановить обратный отсчёт"""
    try:
        user_id = callback.from_user.id
        
        # Останавливаем обратный отсчёт
        await timing_manager.stop_countdown(user_id)
        
        # Формируем сообщение без таймеров
        message_text = "⏰ Таймеры остановлены\n\nНажми /timing чтобы снова запустить таймеры"
        
        # Обновляем сообщение
        await callback.message.edit_text(
            text=message_text,
            reply_markup=main_keyboard()
        )
        
        await callback.answer("✅ Таймеры остановлены")
        
    except Exception as e:
        logger.error(f"Error in callback_timing_stop: {e}")
        await callback.answer("❌ Ошибка остановки таймеров")

async def _format_timing_message(davka_info: dict, atm_info: dict) -> str:
    """Форматировать сообщение с таймерами"""
    current_time = davka_info['current_time']
    
    # Информация о давке
    time_until_davka = davka_info['time_until']
    can_davka = davka_info['can_davka']
    davka_color = timing_manager.get_time_color(time_until_davka)
    
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
        message += f"{davka_color} ДАВКА: {await timing_manager.format_precise_time(time_until_davka)}\n"
        message += f"📊 [{timing_manager.create_progress_bar(davka_progress, 100)}] {davka_progress:.1f}%\n\n"
    
    # Таймер атмосфер
    message += f"🌀 АТМОСФЕРЫ: {atm_count}/12\n"
    if needed_atm > 0:
        message += f"⏱️ Следующая: {await timing_manager.format_precise_time(time_to_next_atm)}\n"
        message += f"🕐 Полностью: {await timing_manager.format_precise_time(full_regen_time)}\n"
        message += f"📊 [{timing_manager.create_progress_bar(atm_progress, 100)}] {atm_progress:.1f}%\n"
    
    # Модификаторы
    message += f"\n⚡ МОДИФИКАТОРЫ:\n"
    message += f"🏗️ Гофрошка: x{davka_info['speed_multiplier']:.2f}\n"
    message += f"🎯 Активность: x{davka_info['activity_bonus']:.2f}\n"
    
    # Текущее время
    message += f"\n🕒 Серверное время: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}"
    
    return message

async def _format_countdown_message(davka_info: dict) -> str:
    """Форматировать сообщение с обратным отсчётом"""
    time_until_davka = davka_info['time_until']
    can_davka = davka_info['can_davka']
    davka_color = timing_manager.get_time_color(time_until_davka)
    
    message = f"⏰ ОБРАТНЫЙ ОТСЧЁТ ДО ДАВКИ\n\n"
    
    if can_davka:
        message += f"{davka_color} ДАВКА ГОТОВА! 🎉\n"
        message += f"🚀 Нажми /davka и дави змия!\n\n"
    else:
        message += f"{davka_color} ДО СЛЕДУЮЩЕЙ ДАВКИ:\n"
        message += f"{await timing_manager.format_precise_time(time_until_davka)}\n\n"
        message += f"📊 [{timing_manager.create_progress_bar(100 - (time_until_davka / TIMING_CONFIG['base_davka_cooldown']) * 100, 100)}]\n"
    
    # Модификаторы
    message += f"\n⚡ МОДИФИКАТОРЫ:\n"
    message += f"🏗️ Гофрошка: x{davka_info['speed_multiplier']:.2f}\n"
    message += f"🎯 Активность: x{davka_info['activity_bonus']:.2f}\n"
    
    return message

async def _format_timing_stats_message(stats: dict) -> str:
    """Форматировать сообщение со статистикой по времени"""
    total_davki = stats['total_davki']
    avg_wait_time = stats['avg_wait_time']
    longest_wait = stats['longest_wait']
    shortest_wait = stats['shortest_wait']
    efficiency = stats['efficiency']
    
    message = f"📊 СТАТИСТИКА ПО ВРЕМЕНИ\n\n"
    
    if total_davki == 0:
        message += "🐍 Пока не было давок\n"
    else:
        message += f"🐍 Всего давок: {total_davki}\n"
        message += f"⏱️ Среднее время ожидания: {await timing_manager.format_precise_time(avg_wait_time)}\n"
        message += f"🕐 Самое долгое ожидание: {await timing_manager.format_precise_time(longest_wait)}\n"
        message += f"⚡ Самое короткое ожидание: {await timing_manager.format_precise_time(shortest_wait)}\n"
        message += f"🎯 Эффективность использования: {efficiency:.1f}%\n"
    
    return message