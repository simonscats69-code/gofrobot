"""
Общие обработчики для чатов и дублирующиеся функции.
Вынесены из commands.py и callbacks.py для избежания дублирования.
"""

from aiogram import types
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
import time
import random
import logging
from db_manager import (
    get_patsan, davka_zmiy, get_gofra_info,
    format_length, ChatManager, calculate_atm_regen_time,
    can_fight_pvp, get_connection, calculate_davka_cooldown
)
from keyboards import (
    chat_menu_keyboard as get_chat_menu_keyboard,
)
from .shared import ft, validate_nickname

logger = logging.getLogger(__name__)

# Константы для игры
MIN_NICKNAME_LENGTH = 3
MAX_NICKNAME_LENGTH = 20
MAX_ATMOSPHERES = 12
PVP_CABLE_BONUS_PER_MM = 0.02
CABLE_GAIN_PVP_WIN = 0.2
CABLE_GAIN_PVP_LOSS = 0.1
GOFRA_BASE_GAIN = 5.0
GOFRA_MAX_GAIN = 12.0
GOFRA_GAIN_PER_LEVEL_DIFF = 0.08
ZMIY_TO_CABLE_RATIO = 2000  # 2кг змия = +0.2мм кабеля
PVP_HOURLY_LIMIT = 10
FORMATTED_ZMIY_AMOUNTS = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]

# FSM States for nickname changes
class NicknameChange(StatesGroup):
    waiting_for_nickname = State()


# ==================== CHAT UTILITY FUNCTIONS ====================

async def show_chat_top_message(chat_id, message_obj):
    """Show chat top leaderboard (used by both message and callback handlers)"""
    try:
        top_players = await ChatManager.get_chat_top(chat_id, limit=10)

        if not top_players:
            await message_obj.answer(
                "📊 ТОП ЧАТА ПУСТ!\n\n"
                "Пока никто не давил змия в этом чате.\n"
                "Будь первым!",
                reply_markup=get_chat_menu_keyboard()
            )
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        text = f"🏆 ТОП ЧАТА:\n\n"

        for i, player in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            nickname = player.get('nickname', f'Игрок_{player.get("user_id")}')
            if len(nickname) > 20:
                nickname = nickname[:17] + "..."

            total_kg = player['total_zmiy_grams'] / 1000

            text += f"{medal} {nickname}\n"
            text += f"   🐍 {total_kg:.1f} кг змия | #{player['rank']}\n\n"

        stats = await ChatManager.get_chat_stats(chat_id)
        text += f"📈 Статистика чата:\n"
        text += f"• Участников: {stats['total_players']}\n"
        text += f"• Всего змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• Всего давок: {stats['total_davki_all']}\n"
        text += f"• Активных: {stats['active_players']}"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error getting chat top: {e}")
        await message_obj.answer("❌ Ошибка загрузки топа чата.", reply_markup=get_chat_menu_keyboard())


async def show_chat_stats_message(chat_id, message_obj):
    """Show chat statistics (used by both message and callback handlers)"""
    try:
        stats = await ChatManager.get_chat_stats(chat_id)

        if stats['last_activity'] > 0:
            last_active = time.strftime('%d.%m.%Y %H:%M', time.localtime(stats['last_activity']))
        else:
            last_active = "никогда"

        text = f"📊 СТАТИСТИКА ЧАТА\n\n"
        text += f"👥 Участников: {stats['total_players']}\n"
        text += f"🔥 Активных: {stats['active_players']}\n\n"

        text += f"🐍 Змий добыто:\n"
        text += f"• Всего: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• На игрока: {stats['total_zmiy_all']/max(1, stats['total_players'])/1000:.1f} кг\n\n"

        text += f"⚡ Давок сделано:\n"
        text += f"• Всего: {stats['total_davki_all']}\n"
        text += f"• На игрока: {stats['total_davki_all']/max(1, stats['total_players']):.0f}\n\n"

        text += f"⏱️ Последняя активность: {last_active}"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        await message_obj.answer("❌ Ошибка загрузки статистики.", reply_markup=get_chat_menu_keyboard())


async def process_chat_davka_message(user_id, chat_id, message_obj):
    """Process chat davka command (used by both message and callback handlers)"""
    await ChatManager.register_chat(
        chat_id=chat_id,
        chat_title=message_obj.chat.title if hasattr(message_obj.chat, 'title') else "",
        chat_type=message_obj.chat.type
    )

    try:
        success, p, res = await davka_zmiy(user_id, chat_id)

        if not success:
            await message_obj.answer(res, reply_markup=get_chat_menu_keyboard())
            return

        await ChatManager.update_chat_activity(chat_id)

        user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)
        top_players = await ChatManager.get_chat_top(chat_id, limit=50)

        rank = None
        for i, player in enumerate(top_players, 1):
            if player['user_id'] == user_id:
                rank = i
                break

        davka_texts = [
            f"🐍 {message_obj.from_user.first_name} ЗАВАРВАРИЛ ДВАНАШКУ!\n\n",
            f"🐍 {message_obj.from_user.first_name} ВЫДАВИЛ КОРИЧНЕВАГА!\n\n",
            f"🐍 {message_obj.from_user.first_name} ОТЖАЛ ЗМИЯ!\n\n"
        ]

        text = random.choice(davka_texts)
        text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
        text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
        text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
        text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"

        text += f"📊 В этом чате:\n"
        text += f"• Всего змия: {user_total/1000:.1f} кг\n"
        if rank:
            text += f"• Место в топе: #{rank}\n"

        if rank == 1:
            text += "\n🏆 ЛИДЕР ЧАТА! 🏆\n"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error in group davka: {e}")
        await message_obj.answer("❌ Ошибка при давке змия.", reply_markup=get_chat_menu_keyboard())


async def show_user_chat_stats_message(user_id, chat_id, message_obj):
    """Show user chat stats (used by both message and callback handlers)"""
    try:
        user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)

        if user_total == 0:
            await message_obj.answer(
                f"📊 Твоя статистика в этом чате:\n\n"
                f"Пока ты не давил змия в этом чате.\n"
                f"Нажми кнопку 🐍 Давить в чате!",
                reply_markup=get_chat_menu_keyboard()
            )
            return

        top_players = await ChatManager.get_chat_top(chat_id, limit=50)
        rank = None
        total_in_chat = 0

        for i, player in enumerate(top_players, 1):
            total_in_chat += 1
            if player['user_id'] == user_id:
                rank = i

        stats = await ChatManager.get_chat_stats(chat_id)

        text = f"📊 ТВОЯ СТАТИСТИКА В ЧАТЕ\n\n"
        text += f"🐍 Всего змия: {user_total/1000:.1f} кг\n"

        if rank:
            text += f"🏆 Место в топе: #{rank} из {total_in_chat}\n"

            if rank > 1:
                prev_player = top_players[rank-2]
                diff = user_total - prev_player['total_zmiy_grams']
                text += f"📈 До #{rank-1}: +{diff/1000:.1f} кг\n"

            if rank < len(top_players):
                next_player = top_players[rank]
                diff = next_player['total_zmiy_grams'] - user_total
                text += f"📉 До #{rank+1}: -{diff/1000:.1f} кг\n"

        text += f"\n📊 Статистика чата:\n"
        text += f"• Всего участников: {stats['total_players']}\n"
        text += f"• Общий вес змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        total_all = stats['total_zmiy_all'] or 1  # Избегаем деления на 0
        text += f"• Твой вклад: {(user_total/total_all*100):.1f}%" if total_all > 0 else "• Твой вклад: 0%"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error getting user chat stats: {e}")
        await message_obj.answer("❌ Ошибка загрузки статистики.", reply_markup=get_chat_menu_keyboard())


# ==================== UNIFIED USER INFO FUNCTIONS ====================

async def show_user_gofra(callback: types.CallbackQuery, user_id: int, reply_markup=None):
    """Show user gofra info - unified function for both chat and personal context"""
    try:
        p = await get_patsan(user_id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🏗️ ТВОЯ ГОФРА\n\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"📏 Длина: {gofra_info['length_display']}\n\n"
        text += f"Характеристики:\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г\n\n"

        if gofra_info.get('next_threshold'):
            progress = gofra_info['progress']
            next_gofra = get_gofra_info(gofra_info['next_threshold'])
            text += f"Следующая гофрошка:\n"
            text += f"{gofra_info['emoji']} → {next_gofra['emoji']}\n"
            text += f"{next_gofra['name']}\n"
            text += f"📈 Прогресс: {progress*100:.1f}%"
        else:
            text += "🎉 Максимальный уровень гофрошки!"

        keyboard = reply_markup or get_chat_menu_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_user_gofra: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)


async def show_user_cable(callback: types.CallbackQuery, user_id: int, reply_markup=None):
    """Show user cable info - unified function for both chat and personal context"""
    try:
        p = await get_patsan(user_id)

        text = f"🔌 ТВОЙ КАБЕЛЬ\n\n"
        text += f"💪 Длина: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм\n"
        text += f"• Победы в радёмках дают +0.2 мм\n\n"
        text += f"📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г"

        keyboard = reply_markup or get_chat_menu_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_user_cable: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)


async def show_user_atm(callback: types.CallbackQuery, user_id: int, reply_markup=None):
    """Show user atm info - unified function for both chat and personal context"""
    try:
        p = await get_patsan(user_id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🌡️ ТВОИ АТМОСФЕРЫ\n\n"
        text += f"🌀 Текущий запас: {p.get('atm_count', 0)}/12\n\n"
        text += f"Точный таймер:\n"
        text += f"🕒 До следующей атмосферы: {ft(regen_info['time_to_one_atm'])}\n"
        text += f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
        text += f"Восстановление:\n"
        text += f"⏱️ 1 атмосфера: {ft(regen_info['time_to_one_atm'])}\n"
        text += f"📈 Нужно восстановить: {regen_info['needed']} атм.\n\n"
        text += f"Влияние гофрошки:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}"

        keyboard = reply_markup or get_chat_menu_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_user_atm: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)


async def show_user_profile(callback: types.CallbackQuery, user_id: int, reply_markup=None, show_timer=True):
    """Show user profile - unified function for both chat and personal context"""
    try:
        p = await get_patsan(user_id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"📊 ТВОЙ ПРОФИЛЬ\n\n"
        text += f"🏗️ Гофра: {gofra_info.get('width_display', gofra_info['length_display'])}\n"
        text += f"🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г\n\n"

        if show_timer:
            cooldown_info = await calculate_davka_cooldown(p)
            if cooldown_info.get('can_davka'):
                text += f"⏰ ДАВКА ГОТОВА! 🎉\n"
                text += f"Нажми кнопку 🐍 чтобы начать!\n\n"
            else:
                text += f"⏰ СЛЕДУЮЩАЯ ДАВКА ЧЕРЕЗ:\n"
                text += f"{ft(cooldown_info['time_until_next'])}\n\n"

        text += f"📈 Прогресс:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г"

        keyboard = reply_markup or get_chat_menu_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_user_profile: {e}")
        await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)


async def show_user_atm_regen(callback: types.CallbackQuery, user_id: int, reply_markup=None):
    """Show user atm regen info - unified function for both chat and personal context"""
    try:
        p = await get_patsan(user_id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        atm_count = p.get('atm_count', 0)
        max_atm = 12

        text = f"⏱️ ТОЧНЫЙ ТАЙМЕР ВОССТАНОВЛЕНИЯ\n\n"
        text += f"Текущее состояние:\n"
        text += f"🌀 Атмосферы: {atm_count}/{max_atm}\n"
        text += f"📈 Нужно восстановить: {regen_info['needed']} шт.\n\n"
        text += f"Точный таймер:\n"
        text += f"🕒 До следующей атмосферы: {ft(regen_info['time_to_next_atm'])}\n"
        text += f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
        text += f"Скорость восстановления:\n"
        text += f"• Базовая: 1 атм. за 2 часа (7200с)\n"
        text += f"• С учётом гофрошки ({gofra_info['name']}): x{gofra_info['atm_speed']:.2f}\n"
        text += f"• 1 атм. за: {ft(regen_info['time_to_one_atm'])}\n\n"
        text += f"Как ускорить:\n"
        text += f"• Повышай гофрошку - ускоряет восстановление\n"
        text += f"• Дави змия при полных 12 атмосферах\n"
        text += f"• Больше опыт → выше гофрошка → быстрее атмосферы"

        keyboard = reply_markup or get_chat_menu_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_user_atm_regen: {e}")
        await callback.answer("❌ Ошибка загрузки таймера", show_alert=True)


# ==================== CHAT CALLBACK UTILITY FUNCTIONS ====================

async def process_chat_davka_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    """Process chat davka callback"""
    await ChatManager.register_chat(
        chat_id=chat_id,
        chat_title=callback.message.chat.title if hasattr(callback.message.chat, 'title') else "",
        chat_type=callback.message.chat.type
    )

    success, p, res = await davka_zmiy(user_id, chat_id)

    if not success:
        error_msg = res.get('error', str(res)) if isinstance(res, dict) else str(res)
        await callback.answer(error_msg, show_alert=True)
        return

    await ChatManager.update_chat_activity(chat_id)

    user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)
    top_players = await ChatManager.get_chat_top(chat_id, limit=50)

    rank = None
    for i, player in enumerate(top_players, 1):
        if player['user_id'] == user_id:
            rank = i
            break

    davka_texts = [
        f"🐍 {callback.from_user.first_name} ЗАВАРВАРИЛ ДВАНАШКУ!\n\n",
        f"🐍 {callback.from_user.first_name} ВЫДАВИЛ КОРИЧНЕВАГА!\n\n",
        f"🐍 {callback.from_user.first_name} ОТЖАЛ ЗМИЯ!\n\n"
    ]

    text = random.choice(davka_texts)
    text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
    text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
    text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
    text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"

    text += f"📊 В этом чате:\n"
    text += f"• Всего змия: {user_total/1000:.1f} кг\n"
    if rank:
        text += f"• Место в топе: #{rank}\n"

    if rank == 1:
        text += "\n🏆 ЛИДЕР ЧАТА! 🏆\n"

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()


async def show_chat_top_callback(callback: types.CallbackQuery, chat_id: int):
    """Show chat top callback"""
    try:
        top_players = await ChatManager.get_chat_top(chat_id, limit=10)

        if not top_players:
            await callback.answer("📊 Топ чата пуст! Будь первым!", show_alert=True)
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        text = f"🏆 ТОП ЧАТА:\n\n"

        for i, player in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            nickname = player.get('nickname', f'Игрок_{player.get("user_id")}')
            if len(nickname) > 20:
                nickname = nickname[:17] + "..."

            total_kg = player['total_zmiy_grams'] / 1000

            text += f"{medal} {nickname}\n"
            text += f"   🐍 {total_kg:.1f} кг змия | #{player['rank']}\n\n"

        stats = await ChatManager.get_chat_stats(chat_id)
        text += f"📈 Статистика чата:\n"
        text += f"• Участников: {stats['total_players']}\n"
        text += f"• Всего змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• Всего давок: {stats['total_davki_all']}\n"
        text += f"• Активных: {stats['active_players']}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback top: {e}")
        await callback.answer("❌ Ошибка загрузки топа", show_alert=True)


async def show_chat_stats_callback(callback: types.CallbackQuery, chat_id: int):
    """Show chat stats callback"""
    try:
        stats = await ChatManager.get_chat_stats(chat_id)

        if stats['last_activity'] > 0:
            last_active = time.strftime('%d.%m.%Y %H:%M', time.localtime(stats['last_activity']))
        else:
            last_active = "никогда"

        text = f"📊 СТАТИСТИКА ЧАТА\n\n"
        text += f"👥 Участников: {stats['total_players']}\n"
        text += f"🔥 Активных: {stats['active_players']}\n\n"

        text += f"🐍 Змий добыто:\n"
        text += f"• Всего: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• На игрока: {stats['total_zmiy_all']/max(1, stats['total_players'])/1000:.1f} кг\n\n"

        text += f"⚡ Давок сделано:\n"
        text += f"• Всего: {stats['total_davki_all']}\n"
        text += f"• На игрока: {stats['total_davki_all']/max(1, stats['total_players']):.0f}\n\n"

        text += f"⏱️ Последняя активность: {last_active}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)


async def show_user_chat_stats_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    """Show user chat stats callback"""
    try:
        user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)

        if user_total == 0:
            text = f"📊 Твоя статистика в этом чате:\n\n"
            text += f"Пока ты не давил змия в этом чате.\n"
            text += f"Нажми кнопку 🐍 Давить в чате!"

            try:
                await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

            await callback.answer()
            return

        top_players = await ChatManager.get_chat_top(chat_id, limit=50)
        rank = None
        total_in_chat = 0

        for i, player in enumerate(top_players, 1):
            total_in_chat += 1
            if player['user_id'] == user_id:
                rank = i

        stats = await ChatManager.get_chat_stats(chat_id)

        text = f"📊 ТВОЯ СТАТИСТИКА В ЧАТЕ\n\n"
        text += f"🐍 Всего змия: {user_total/1000:.1f} кг\n"

        if rank:
            text += f"🏆 Место в топе: #{rank} из {total_in_chat}\n"

            if rank > 1:
                prev_player = top_players[rank-2]
                diff = user_total - prev_player['total_zmiy_grams']
                text += f"📈 До #{rank-1}: +{diff/1000:.1f} кг\n"

            if rank < len(top_players):
                next_player = top_players[rank]
                diff = next_player['total_zmiy_grams'] - user_total
                text += f"📉 До #{rank+1}: -{diff/1000:.1f} кг\n"

        text += f"\n📊 Статистика чата:\n"
        text += f"• Всего участников: {stats['total_players']}\n"
        text += f"• Общий вес змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        total_all = stats['total_zmiy_all'] or 1
        text += f"• Твой вклад: {(user_total/total_all*100):.1f}%" if total_all > 0 else "• Твой вклад: 0%"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback me: {e}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)


async def show_rademka_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    """Show rademka callback"""
    try:
        p = await get_patsan(user_id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        can_fight, fight_msg = await can_fight_pvp(user_id)
        fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"

        text = f"👊 РАДЁМКА (PvP)\n\n"
        text += f"{fight_status}\n\n"
        text += f"Выбери пацана из участников чата!\n"
        text += f"За победу: +0.2 мм к кабелю, +5-12 мм к гофрошке\n\n"

        try:
            chat_stats = await ChatManager.get_chat_stats(chat_id)
            if chat_stats['total_players'] > 1:
                top_players = await ChatManager.get_chat_top(chat_id, limit=20)
                opponents = [pl for pl in top_players if pl['user_id'] != user_id]

                if opponents:
                    text += f"🎯 Доступные цели ({len(opponents)}):\n"
                    for i, opp in enumerate(opponents[:5], 1):
                        nickname = opp.get('nickname', f'Игрок_{opp.get("user_id")}')
                        if len(nickname) > 15:
                            nickname = nickname[:12] + "..."
                        text += f"{i}. {nickname}\n"
                    text += f"\nНажми на игрока в ответном сообщении с командой /fight"
                else:
                    text += "😕 В чате нет других активных игроков!"
            else:
                text += "😕 В чате пока только ты один!\nПриведи друзей для радёмок!"
        except Exception as e:
            logger.error(f"Error getting chat players in callback: {e}")
            text += "\nОшибка загрузки списка игроков"

        text += f"\n\nТвои статы:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"🏗️ {format_length(p.get('gofra_mm', 10.0))} | 🔌 {format_length(p.get('cable_mm', 10.0))}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback rademka: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)


async def show_chat_help_callback(callback: types.CallbackQuery):
    """Show chat help callback"""
    text = (
        "🆘 ГОФРА-КОМАНДЫ ДЛЯ ЧАТОВ:\n\n"
        "👤 Личные команды:\n"
        "/start - Начать игру\n"
        "/davka - Давить коричневага\n"
        "/profile - Профиль\n"
        "/top - Топ игроков\n"
        "/rademka - Радёмка (PvP)\n\n"
        "👥 Команды чата:\n"
        "/gtop - Топ этого чата\n"
        "/gstats - Статистика чата\n"
        "/gme - Моя статистика в чате\n"
        "/gdavka - Давить змия в чате\n"
        "/grademka - Радёмка в чате\n"
        "/fight @игрок - Протащить игрока (ответом на сообщение)\n"
        "/gmenu - Меню для чата\n"
        "/ghelp - Эта справка\n\n"
        "📊 В чате сохраняется общая статистика!\n"
        "👊 Радёмки работают только между участниками чата!"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()


async def show_chat_menu_callback(callback: types.CallbackQuery):
    """Show chat menu callback"""
    text = "🏗️ ГОФРА-МЕНЮ ДЛЯ ЧАТА 🏗️\n\nВыбери действие:"

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()


# ==================== NICKNAME CHANGE FUNCTION ====================

async def do_change_nickname(user_id: int, new_nickname: str) -> tuple[bool, str]:
    """Change user nickname with validation"""
    try:
        # Validate nickname
        is_valid, error_msg = validate_nickname(new_nickname)
        if not is_valid:
            return False, error_msg

        # Check if nickname is already taken
        cn = await get_connection()
        cur = await cn.execute('SELECT user_id FROM users WHERE nickname=? AND user_id!=?', (new_nickname, user_id))
        existing = await cur.fetchone()

        if existing:
            await cn.close()
            return False, "Ник уже занят"

        # Update nickname
        await cn.execute('UPDATE users SET nickname=? WHERE user_id=?', (new_nickname, user_id))
        await cn.commit()
        await cn.close()

        return True, "OK"

    except Exception as e:
        logger.error(f"Error changing nickname: {e}")
        return False, "Ошибка базы данных"


# ==================== GROUP KEYWORDS RESPONSES ====================

GROUP_KEYWORD_RESPONSES = {
    "гофрошка": [
        "Гофрошка - это жизнь! 🏗️",
        "Чем больше гофрошка, тем тяжелее змий! 💪",
        "Моя гофрошка уже {length} см! А твоя? 🏗️",
        "Без гофрошки и змий не выдавишь! ⚡"
    ],
    "змий": [
        "Змий надо давить, а не обсуждать! 🐍",
        "У меня сегодня {weight}г змия вышло! 💩",
        "Коричневаг ждёт тебя! Нажми /davka 🐍"
    ],
    "давка": [
        "Давка - святое дело! 🐍",
        "Все 12 атмосфер готовы? Тогда /davka ⚡",
        "Лучшая давка - это утренняя давка! ☀️"
    ]
}


# ==================== EXPORTS ====================

__all__ = [
    # Constants
    'MIN_NICKNAME_LENGTH', 'MAX_NICKNAME_LENGTH', 'MAX_ATMOSPHERES',
    'PVP_CABLE_BONUS_PER_MM', 'CABLE_GAIN_PVP_WIN', 'CABLE_GAIN_PVP_LOSS',
    'GOFRA_BASE_GAIN', 'GOFRA_MAX_GAIN', 'GOFRA_GAIN_PER_LEVEL_DIFF',
    'ZMIY_TO_CABLE_RATIO', 'PVP_HOURLY_LIMIT', 'FORMATTED_ZMIY_AMOUNTS',
    # FSM
    'NicknameChange',
    # Unified functions (for both chat and personal callbacks)
    'show_user_gofra', 'show_user_cable', 'show_user_atm',
    'show_user_profile', 'show_user_atm_regen',
    # Chat message functions
    'show_chat_top_message', 'show_chat_stats_message',
    'process_chat_davka_message', 'show_user_chat_stats_message',
    # Chat-specific callback functions (using unified functions)
    'process_chat_davka_callback', 'show_chat_top_callback',
    'show_chat_stats_callback', 'show_user_chat_stats_callback',
    'show_rademka_callback', 'show_chat_help_callback', 'show_chat_menu_callback',
    # Nickname
    'do_change_nickname',
    # Keywords
    'GROUP_KEYWORD_RESPONSES',
]
