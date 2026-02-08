from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import time
import random
import logging
import re
from db_manager import (
    get_patsan, davka_zmiy, uletet_zmiy, get_gofra_info,
    format_length, ChatManager, calculate_atm_regen_time,
    calculate_pvp_chance, can_fight_pvp, save_patsan, save_rademka_fight,
    calculate_davka_cooldown, get_top_players, change_nickname
)
from keyboards import main_keyboard, back_kb, gofra_info_kb, cable_info_kb, atm_status_kb, rademka_keyboard, nickname_keyboard, chat_menu_keyboard as get_chat_menu_keyboard, top_sort_keyboard, back_to_profile_keyboard, mk, rademka_fight_keyboard

# Импорты для визуальных эффектов (если доступны)
try:
    from utils import visual_effects, formatters, animation_manager, notification_effects
    VISUAL_EFFECTS_AVAILABLE = True
except ImportError:
    VISUAL_EFFECTS_AVAILABLE = False

router = Router()
logger = logging.getLogger(__name__)

# ========== UTILITIES FROM utils.py ==========
def ft(s):
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

def pb(c, t, l=10):
    """Create a progress bar string"""
    f = int((c / t) * l) if t > 0 else 0
    return "█" * f + "░" * (l - f)
# ========== END OF UTILITIES ==========

@router.message(Command("start", "gofra", "gofrastart"))
async def group_start(message: types.Message):
    chat = message.chat

    await ChatManager.register_chat(
        chat_id=chat.id,
        chat_title=chat.title if hasattr(chat, 'title') else "",
        chat_type=chat.type
    )

    await message.answer(
        f"👋 Саламчик пополамчик родные! Приветствуем в гофроцентрале, {chat.title if hasattr(chat, 'title') else 'чатик'}!\n\n"
        f"Я бот для давки коричневага и прокачки гофрошки.\n\n"
        f"В чате доступно:\n"
        f"🐍 Общая статистика\n"
        f"🏆 Топ участников\n"
        f"👊 Радёмки между участниками\n\n"
        f"Используй /ghelp или кнопки ниже:",
        reply_markup=get_chat_menu_keyboard()
    )

@router.message(Command("ghelp", "g_help", "chathelp"))
async def group_help(message: types.Message):
    await message.answer(
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
        "👊 Радёмки работают только между участниками чата!",
        reply_markup=get_chat_menu_keyboard()
    )

@router.message(Command("gmenu", "chatmenu"))
async def group_menu_command(message: types.Message):
    await message.answer(
        "🏗️ ГОФРА-МЕНЮ ДЛЯ ЧАТА 🏗️\n\n"
        "Выбери действие:",
        reply_markup=get_chat_menu_keyboard()
    )

@router.message(Command("gtop", "g_top", "chattop"))
async def chat_top_command(message: types.Message):
    await show_chat_top_message(message.chat.id, message)

@router.message(Command("gstats", "g_stats", "chatstats"))
async def chat_stats_command(message: types.Message):
    await show_chat_stats_message(message.chat.id, message)

@router.message(Command("gdavka", "g_davka", "chatdavka"))
async def group_davka_command(message: types.Message):
    await process_chat_davka_message(message.from_user.id, message.chat.id, message)

@router.message(Command("grademka", "g_rademka", "chatrademka"))
async def group_rademka_command(message: types.Message):
    chat = message.chat

    await ChatManager.register_chat(
        chat_id=chat.id,
        chat_title=chat.title if hasattr(chat, 'title') else "",
        chat_type=chat.type
    )

    p = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

    can_fight, fight_msg = await can_fight_pvp(message.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"

    text = f"👊 РАДЁМКА В ЧАТЕ\n\n"
    text += f"{fight_status}\n\n"
    text += f"Выбери пацана из участников чата!\n"
    text += f"За победу: +5-10 мм к кабелю, +2 мм к гофрошке\n\n"

    try:
        chat_stats = await ChatManager.get_chat_stats(message.chat.id)
        if chat_stats['total_players'] > 1:
            top_players = await ChatManager.get_chat_top(message.chat.id, limit=20)
            opponents = [p for p in top_players if p['user_id'] != message.from_user.id]

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
        logger.error(f"Error getting chat players: {e}")
        text += "\nОшибка загрузки списка игроков"

    await message.answer(text, reply_markup=get_chat_menu_keyboard())

@router.message(Command("fight", "протащить", "радёмка"))
async def fight_command(message: types.Message, command: CommandObject):
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение игрока, которого хочешь протащить!")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id == message.from_user.id:
        await message.answer("❌ Нельзя драться с самим собой!")
        return

    target_data = await get_patsan(target_user.id)
    attacker_data = await get_patsan(message.from_user.id)

    if not target_data:
        await message.answer(f"❌ {target_user.first_name} ещё не зарегистрирован в боте!")
        return

    can_fight, fight_msg = await can_fight_pvp(message.from_user.id)
    if not can_fight:
        await message.answer(f"❌ {fight_msg}")
        return

    can_target_fight, target_fight_msg = await can_fight_pvp(target_user.id)
    if not can_target_fight:
        await message.answer(f"❌ {target_user.first_name} превысил лимит боёв на сегодня!")
        return

    chance = await calculate_pvp_chance(attacker_data, target_data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Протащить!", callback_data=f"chat_fight_{target_user.id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="chat_menu")
        ]
    ])

    gofra_info_att = get_gofra_info(attacker_data.get('gofra_mm', 10.0))
    gofra_info_tar = get_gofra_info(target_data.get('gofra_mm', 10.0))

    text = f"👊 ЗАПРОС НА РАДЁМКУ!\n\n"
    text += f"🗡️ Атакующий: {message.from_user.first_name}\n"
    text += f"{gofra_info_att['emoji']} {gofra_info_att['name']}\n"
    text += f"🏗️ {format_length(attacker_data.get('gofra_mm', 10.0))} | 🔌 {format_length(attacker_data.get('cable_mm', 10.0))}\n\n"

    text += f"🛡️ Цель: {target_user.first_name}\n"
    text += f"{gofra_info_tar['emoji']} {gofra_info_tar['name']}\n"
    text += f"🏗️ {format_length(target_data.get('gofra_mm', 10.0))} | 🔌 {format_length(target_data.get('cable_mm', 10.0))}\n\n"

    text += f"🎯 Шанс успеха: {chance}%\n"
    text += f"🏆 Награда за победу: +5-10 мм к кабелю, +2 мм к гофрошке\n"
    text += f"💀 Риск: публичный позор при проигрыше\n\n"

    text += f"Подтверждаешь радёмку?"

    await message.answer(text, reply_markup=keyboard)

@router.message(Command("gme", "g_me", "chatme"))
async def my_chat_stats_command(message: types.Message):
    await show_user_chat_stats_message(message.from_user.id, message.chat.id, message)

async def show_chat_top_message(chat_id, message_obj):
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

@router.callback_query(F.data == "davka")
async def handle_davka_callback(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        success, p, res = await davka_zmiy(user_id)

        if not success:
            error_msg = res.get('error', 'Ошибка при давке змия')
            await callback.answer(error_msg, show_alert=True)
            return

        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        # Calculate cooldown for next davka
        cooldown_info = await calculate_davka_cooldown(p)

        text = f"🐍 ДАВКА КОРИЧНЕВАГА!\n\n"
        text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
        text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
        text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
        text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г\n\n"

        # Add precise timer information
        text += f"⏱️ ТОЧНЫЙ ТАЙМЕР ДО СЛЕДУЮЩЕЙ ДАВКИ:\n"
        text += f"🕒 Следующая давка через: {cooldown_info['formatted_time']}\n"
        text += f"📅 Точное время: {cooldown_info['time_until_next']} секунд"

        try:
            await callback.message.edit_text(text, reply_markup=main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=main_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in davka callback: {e}")
        await callback.answer("❌ Ошибка при давке змия", show_alert=True)

@router.callback_query(F.data == "uletet")
async def handle_uletet_callback(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        success, p, res = await uletet_zmiy(user_id)

        if not success:
            error_msg = res.get('error', 'Ошибка при отправке змия')
            await callback.answer(error_msg, show_alert=True)
            return

        text = f"✈️ ЗМИЙ ОТПРАВЛЕН!\n\n"
        text += f"🐍 Отправлено: {res['zmiy_grams']:.0f}г коричневага!\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г"

        try:
            await callback.message.edit_text(text, reply_markup=main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=main_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in uletet callback: {e}")
        await callback.answer("❌ Ошибка при отправке змия", show_alert=True)

@router.callback_query(F.data == "gofra_info")
async def handle_gofra_info_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
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

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra info callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о гофрошке", show_alert=True)

@router.callback_query(F.data == "cable_info")
async def handle_cable_info_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"🔌 ТВОЙ КАБЕЛЬ\n\n"
        text += f"💪 Длина: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"А у тебя пацанчик с гофроцентрала кишка как кабель силовой висит на {format_length(p.get('cable_mm', 10.0))}!\n\n"
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм\n"
        text += f"• Победы в радёмках дают +0.2 мм\n\n"
        text += f"📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable info callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о кабеле", show_alert=True)

@router.callback_query(F.data == "atm_status")
async def handle_atm_status_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🌡️ ТВОИ АТМОСФЕРЫ\n\n"
        text += f"🌀 Текущий запас: {p.get('atm_count', 0)}/12\n\n"
        text += f"Точный таймер:\n"
        text += f"🕒 До следующей атмосферы: {ft(regen_info['time_to_next_atm'])}\n"
        text += f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
        text += f"Восстановление:\n"
        text += f"⏱️ 1 атмосфера: {ft(regen_info['time_to_one_atm'])}\n"
        text += f"📈 Нужно восстановить: {regen_info['needed']} атм.\n\n"
        text += f"Влияние гофрошки:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}"

        try:
            await callback.message.edit_text(text, reply_markup=atm_status_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=atm_status_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in atm status callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации об атмосферах", show_alert=True)

@router.callback_query(F.data == "profile")
async def handle_profile_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"📊 ТВОЙ ПРОФИЛЬ\n\n"
        text += f"🏗️ Гофра: {format_length(p.get('gofra_mm', 10.0))}\n"
        text += f"🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г\n\n"
        text += f"📈 Прогресс:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г"

        try:
            await callback.message.edit_text(text, reply_markup=main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=main_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in profile callback: {e}")
        await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)

@router.callback_query(F.data == "gofra_progress")
async def handle_gofra_progress_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"📈 ПРОГРЕСС ГОФРЫ\n\n"
        text += f"🏗️ Текущая гофрошка: {gofra_info['length_display']}\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n\n"

        if gofra_info.get('next_threshold'):
            current_gofra = p.get('gofra_mm', 10.0)
            next_threshold = gofra_info['next_threshold']
            progress = (current_gofra - gofra_info['threshold']) / (next_threshold - gofra_info['threshold'])
            progress_percent = progress * 100

            next_gofra = get_gofra_info(next_threshold)

            text += f"🎯 Следующая гофрошка:\n"
            text += f"{next_gofra['emoji']} {next_gofra['name']}\n"
            text += f"📏 Требуется: {next_gofra['length_display']}\n"
            text += f"📊 Прогресс: [{'█' * int(progress_percent/10)}{'░' * (10 - int(progress_percent/10))}] {progress_percent:.1f}%\n\n"
            text += f"💪 Осталось: {next_threshold - current_gofra:.1f} мм"
        else:
            text += "🎉 Ты достиг максимального уровня гофрошки!\n"
            text += "🏆 Коричневый бог - это ты!"

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra progress callback: {e}")
        await callback.answer("❌ Ошибка загрузки прогресса гофрошки", show_alert=True)

@router.callback_query(F.data == "gofra_speed")
async def handle_gofra_speed_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"⚡ СКОРОСТЬ ВОССТАНОВЛЕНИЯ АТМОСФЕР\n\n"
        text += f"🏗️ Твоя гофрошка: {gofra_info['length_display']}\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n\n"
        text += f"📊 Скорость восстановления:\n"
        text += f"• Базовая: 1 атмосфера за 2 часа\n"
        text += f"• Твой множитель: x{gofra_info['atm_speed']:.2f}\n"
        text += f"• Фактическая: 1 атмосфера за {ft(7200 / gofra_info['atm_speed'])}\n\n"
        text += f"💡 Как ускорить:\n"
        text += f"• Повышай гофрошку (дави змия при 12 атмосферах)\n"
        text += f"• Чем выше гофрошка, тем быстрее восстанавливаются атмосферы\n"
        text += f"• Максимальный множитель: x2.0 (Коричневый бог)"

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra speed callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о скорости", show_alert=True)

@router.callback_query(F.data == "gofra_next")
async def handle_gofra_next_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🎯 СЛЕДУЮЩАЯ ГОФРА\n\n"

        if gofra_info.get('next_threshold'):
            current_gofra = p.get('gofra_mm', 10.0)
            next_threshold = gofra_info['next_threshold']
            next_gofra = get_gofra_info(next_threshold)

            text += f"🏗️ Текущая гофрошка: {gofra_info['length_display']}\n"
            text += f"{gofra_info['emoji']} {gofra_info['name']}\n\n"
            text += f"📈 Следующая гофрошка:\n"
            text += f"{next_gofra['emoji']} {next_gofra['name']}\n"
            text += f"📏 Требуется: {next_gofra['length_display']}\n\n"
            text += f"📊 Преимущества:\n"
            text += f"• Скорость атмосфер: x{next_gofra['atm_speed']:.2f} (текущая: x{gofra_info['atm_speed']:.2f})\n"
            text += f"• Вес змия: {next_gofra['min_grams']}-{next_gofra['max_grams']}г (текущий: {gofra_info['min_grams']}-{gofra_info['max_grams']}г)\n\n"
            text += f"💪 Как получить:\n"
            text += f"• Дави змия при 12 атмосферах\n"
            text += f"• Получай опыт: 0.02 мм за 1 грамм змия\n"
            text += f"• Нужно ещё: {next_threshold - current_gofra:.1f} мм"
        else:
            text += "🎉 Ты достиг максимального уровня!\n"
            text += "🏆 Коричневый бог - это ты!\n"
            text += "📊 Больше нет уровней гофрошки"

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra next callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о следующей гофрошке", show_alert=True)

@router.callback_query(F.data == "cable_power_info")
async def handle_cable_power_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"💪 СИЛА КАБЕЛЯ\n\n"
        text += f"🔌 Длина кабеля: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"📊 Как влияет на PvP:\n"
        text += f"• Каждый 1 мм кабеля = +0.02% к шансу победы\n"
        text += f"• Твой бонус: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n"
        text += f"• Максимальный бонус: +20% (1000 мм кабеля)\n\n"
        text += f"💡 Как прокачать:\n"
        text += f"• Дави змия: +0.2 мм за 1 кг змия\n"
        text += f"• Побеждай в радёмках: +0.2 мм за победу\n"
        text += f"• Участвуй в PvP боях"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable power callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о силе кабеля", show_alert=True)

@router.callback_query(F.data == "cable_pvp_info")
async def handle_cable_pvp_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"⚔️ КАБЕЛЬ В PVP\n\n"
        text += f"🔌 Твой кабель: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"💪 Бонус к шансу победы: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"📊 Формула PvP:\n"
        text += f"• Базовый шанс: 50%\n"
        text += f"• Бонус от гофрошки: +2% за каждые 10 мм разницы\n"
        text += f"• Бонус от кабеля: +0.2% за каждый 1 мм разницы\n"
        text += f"• Общий шанс: от 10% до 90%\n\n"
        text += f"💡 Стратегия:\n"
        text += f"• Прокачивай кабель для увеличения шанса\n"
        text += f"• Выбирай противников с меньшим кабелем\n"
        text += f"• Победы дают +0.2 мм к кабелю"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable pvp callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о PvP", show_alert=True)

@router.callback_query(F.data == "cable_upgrade_info")
async def handle_cable_upgrade_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"📈 ПРОКАЧКА КАБЕЛЯ\n\n"
        text += f"🔌 Текущая длина: {format_length(p.get('cable_mm', 10.0))}\n\n"
        text += f"📊 Способы прокачки:\n"
        text += f"1️⃣ Давка змия:\n"
        text += f"   • +0.2 мм за 1 кг змия\n"
        text += f"   • Твой прогресс: {p.get('total_zmiy_grams', 0)/1000:.1f} кг\n"
        text += f"   • Кабель от давки: +{(p.get('total_zmiy_grams', 0)/1000 * 0.2):.1f} мм\n\n"
        text += f"2️⃣ Победы в PvP:\n"
        text += f"   • +0.2 мм за каждую победу\n"
        text += f"   • Участвуй в радёмках\n"
        text += f"   • Выбирай слабых противников\n\n"
        text += f"💡 Советы:\n"
        text += f"• Дави больше змия для быстрой прокачки\n"
        text += f"• Участвуй в PvP для дополнительного бонуса\n"
        text += f"• Следи за прогрессом в профиле"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable upgrade callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о прокачке", show_alert=True)


async def process_chat_davka_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    await ChatManager.register_chat(
        chat_id=chat_id,
        chat_title=callback.message.chat.title if hasattr(callback.message.chat, 'title') else "",
        chat_type=callback.message.chat.type
    )

    success, p, res = await davka_zmiy(user_id, chat_id)

    if not success:
        await callback.answer(res, show_alert=True)
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
        logger.error(f"Error in chat callback stats: {e}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

async def show_user_chat_stats_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
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
        text += f"• Твой вклад: {(user_total/stats['total_zmiy_all']*100):.1f}%"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback me: {e}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

async def show_user_gofra_callback(callback: types.CallbackQuery, user_id: int):
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

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback gofra: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_user_cable_callback(callback: types.CallbackQuery, user_id: int):
    try:
        p = await get_patsan(user_id)

        text = f"🔌 ТВОЙ КАБЕЛЬ\n\n"
        text += f"💪 Длина: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм\n"
        text += f"• Победы в радёмках дают +0.2 мм\n\n"
        text += f"📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback cable: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_user_atm_callback(callback: types.CallbackQuery, user_id: int):
    try:
        p = await get_patsan(user_id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🌡️ ТВОИ АТМОСФЕРЫ\n\n"
        text += f"🌀 Текущий запас: {p.get('atm_count', 0)}/12\n\n"
        text += f"Восстановление:\n"
        text += f"⏱️ 1 атмосфера: {ft(regen_info['per_atm'])}\n"
        text += f"🕐 До полного: {ft(regen_info['total'])}\n"
        text += f"📈 Осталось: {regen_info['needed']} атм.\n\n"
        text += f"Влияние гофрошки:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback atm: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_rademka_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
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
                opponents = [p for p in top_players if p['user_id'] != user_id]

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
    text = "🏗️ ГОФРА-МЕНЮ ДЛЯ ЧАТА 🏗️\n\nВыбери действие:"

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()

@router.message(F.text.contains("гофрошка") | F.text.contains("змий") | F.text.contains("давка"))
async def group_keywords(message: types.Message):
    text_lower = message.text.lower()

    responses = []

    if "гофрошка" in text_lower:
        responses.extend([
            "Гофрошка - это жизнь! 🏗️",
            "Чем больше гофрошка, тем тяжелее змий! 💪",
            "Моя гофрошка уже {length} см! А твоя? 🏗️",
            "Без гофрошки и змий не выдавишь! ⚡"
        ])

    if "змий" in text_lower or "зме" in text_lower:
        responses.extend([
            "Змий надо давить, а не обсуждать! 🐍",
            "У меня сегодня {weight}г змия вышло! 💩",
            "Коричневаг ждёт тебя! Нажми /davka 🐍"
        ])

    if "давка" in text_lower:
        responses.extend([
            "Давка - святое дело! 🐍",
            "Все 12 атмосфер готовы? Тогда /davka ⚡",
            "Лучшая давка - это утренняя давка! ☀️"
        ])

    if responses:
        response = random.choice(responses)

        if "{length}" in response:
            try:
                user = await get_patsan(message.from_user.id)
                length = format_length(user.get('gofra_mm', 10.0))
                response = response.format(length=length)
            except Exception as e:
                logger.error(f"Error getting user gofra length: {e}")
                response = response.format(length="1.5")

        if "{weight}" in response:
            weight = random.randint(50, 500)
            response = response.format(weight=weight)

        await message.reply(response)

# ========== TOP HANDLERS FROM top.py ==========
@router.callback_query(F.data == "top")
@ignore_not_modified_error
async def callback_top_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА\n\n"
        "Выбери, по какому показателю сортировать рейтинг:",
        reply_markup=top_sort_keyboard()
    )

@ignore_not_modified_error
@router.callback_query(F.data.startswith("top_"))
async def show_top(callback: types.CallbackQuery):
    sort_type = callback.data.replace("top_", "")

    sort_map = {
        "gofra": ("гофрошке", "🏗️", "gofra"),
        "cable": ("кабелю", "🔌", "cable_power"),
        "zmiy": ("змию", "🐍", "zmiy_grams"),
        "atm": ("атмосферам", "🌀", "atm_count")
    }

    if sort_type not in sort_map:
        await callback.answer("Неизвестный тип топа", show_alert=True)
        return

    sort_name, emoji, db_key = sort_map[sort_type]

    try:
        top_players = await get_top_players(limit=10, sort_by=db_key)
    except Exception as e:
        await callback.answer(f"Ошибка при получении топа: {e}", show_alert=True)
        return

    if not top_players:
        await callback.message.edit_text(
            "😕 Топ пуст!\n\n"
            "Ещё никто не заслужил места в рейтинге.\n"
            "Будь первым!",
            reply_markup=top_sort_keyboard()
        )
        return

    top_text = f"{emoji} Топ пацанов по {sort_name}:\n\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, player in enumerate(top_players):
        medal = medals[i] if i < len(medals) else f"{i+1}."

        if sort_type == "gofra":
            gofra_info = get_gofra_info(player.get('gofra_mm', 10.0))
            value = f"🏗️ {gofra_info['length_display']} {gofra_info['emoji']}"
        elif sort_type == "cable":
            value = f"🔌 {format_length(player.get('cable_mm', 10.0))}"
        elif sort_type == "zmiy":
            value = f"🐍 {player['zmiy_grams']:.0f}г"
        else:
            value = f"🌀 {player['atm_count']}/12"

        nickname = player['nickname']
        if len(nickname) > 20:
            nickname = nickname[:17] + "..."

        top_text += f"{medal} {nickname} — {value}\n"

    top_text += f"\n📊 Всего пацанов в системе: {len(top_players)}"

    current_user_id = callback.from_user.id
    user_position = None

    for i, player in enumerate(top_players):
        if player.get('user_id') == current_user_id:
            user_position = i + 1
            break

    if user_position:
        user_medal = medals[user_position-1] if user_position-1 < len(medals) else str(user_position)
        top_text += f"\n\n🎯 Твоя позиция: {user_medal}"

    await callback.message.edit_text(
        top_text,
        reply_markup=top_sort_keyboard()
    )

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main_from_top(callback: types.CallbackQuery):
    from db_manager import get_patsan, get_gofra_info, format_length

    patsan = await get_patsan(callback.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
    await callback.message.edit_text(
        f"Главное меню. Атмосфер: {patsan['atm_count']}/12\n"
        f"{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {gofra_info['length_display']}",
        reply_markup=main_keyboard()
    )
# ========== END OF TOP HANDLERS ==========

# ========== NICKNAME AND RADEMKA HANDLERS FROM nickname_and_rademka.py ==========
class NicknameChange(StatesGroup):
    waiting_for_nickname = State()

def validate_nickname(nickname):
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

@router.message(Command("nickname"))
async def cmd_nickname_handler(m: types.Message, state: FSMContext):
    p = await get_patsan(m.from_user.id)
    await m.answer(f"🏷️ НИКНЕЙМ И РЕПУТАЦИЯ\n\n🔤 Твой ник: {p.get('nickname','Неизвестно')}\n🏗️ Гофра: {format_length(p.get('gofra_mm', 10.0))}\n🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n\nВыбери действие:", reply_markup=nickname_keyboard())

@router.callback_query(F.data == "nickname_menu")
@ignore_not_modified_error
async def nickname_menu(c: types.CallbackQuery):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    await c.message.edit_text(f"🏷️ НИКНЕЙМ И РЕПУТАЦИЯ\n\n🔤 Твой ник: {p.get('nickname','Неизвестно')}\n🏗️ Гофра: {format_length(p.get('gofra_mm', 10.0))}\n🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n\nВыбери действие:", reply_markup=nickname_keyboard())

@ignore_not_modified_error
@router.callback_query(F.data == "my_reputation")
async def my_reputation(c: types.CallbackQuery):
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
    await c.message.edit_text(f"⭐ МОЯ РЕПУТАЦИЯ\n\n{gofra_info['emoji']} Звание: {gofra_info['name']}\n🏗️ Гофрошка: {format_length(p.get('gofra_mm', 10.0))}\n🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n🐍 Змий: {p.get('zmiy_grams',0):.0f}г\n\nКак повысить?\n• Дави змия при полных атмосферах\n• Отправляй змия в коричневую страну\n• Участвуй в радёмках\n\nЧем больше гофрошка, тем больше уважения!", reply_markup=nickname_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "top_reputation")
async def top_reputation(c: types.CallbackQuery):
    tp = await get_top_players(limit=10, sort_by="gofra")
    if not tp: 
        await c.message.edit_text("🥇 ТОП ГОФРЫ\n\nПока никого нет в топе!\nБудь первым!\n\nСлава ждёт!", reply_markup=nickname_keyboard())
    else:
        mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 ТОП ГОФРЫ\n\n"
        for i, p in enumerate(tp):
            md = mds[i] if i<len(mds) else f"{i+1}."
            nn = p.get("nickname", f"Пацан_{p.get('user_id','?')}")[:12]+("..." if len(p.get('nickname',''))>15 else "")
            gi = get_gofra_info(p.get('gofra_mm', 10.0))
            txt += f"{md} {nn} - {gi['emoji']} {gi['name']} ({gi['length_display']})\n"
        uid = c.from_user.id
        for i, p in enumerate(tp):
            if p.get('user_id')==uid: 
                txt+=f"\n🎯 Твоя позиция: {mds[i] if i<len(mds) else str(i+1)}"
                break
        txt+=f"\n👥 Всего пацанов: {len(tp)}"
        await c.message.edit_text(txt, reply_markup=nickname_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "change_nickname")
async def callback_change_nickname(c: types.CallbackQuery, state: FSMContext):
    p = await get_patsan(c.from_user.id)

    current_state = await state.get_state()
    if current_state == NicknameChange.waiting_for_nickname:
        await c.answer("Ты уже в процессе смены ника!", show_alert=True)
        return

    txt = f"✏️ СМЕНА НИКА\n\nТвой текущий ник: {p.get('nickname','Неизвестно')}\n"
    txt += f"Правила ника:\n"
    txt += f"• 3-20 символов\n"
    txt += f"• Буквы, цифры, пробелы, дефисы, подчёркивания\n"
    txt += f"• Без запрещённых слов (admin, бот и т.д.)\n"
    txt += f"• Без лишних пробелов\n\n"
    txt += f"Напиши новый ник в чат:"

    await c.message.edit_text(txt, reply_markup=back_kb("nickname_menu"))
    await state.set_state(NicknameChange.waiting_for_nickname)
    await c.answer("Введи новый ник в чат")

# ОБРАБОТЧИК ВВОДА НИКА
@router.message(NicknameChange.waiting_for_nickname)
async def process_nickname_input(message: types.Message, state: FSMContext):
    nn = message.text.strip()

    is_valid, error_msg = validate_nickname(nn)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nПопробуй другой ник:", reply_markup=back_kb("nickname_menu"))
        return

    ok, msg = await change_nickname(message.from_user.id, nn)
    if ok:
        await message.answer(f"✅ Ник изменён!\nТеперь ты: {nn}", reply_markup=main_keyboard())
    else:
        await message.answer(f"❌ {msg}\nПопробуй другой:", reply_markup=main_keyboard())

    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(m: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        return await m.answer("Нечего отменять.", reply_markup=main_keyboard())
    
    if current_state == NicknameChange.waiting_for_nickname:
        await state.clear()
        await m.answer("Смена ника отменена.", reply_markup=main_keyboard())
    else:
        await m.answer("Нет активного процесса для отмены.", reply_markup=main_keyboard())

async def cmd_rademka(m: types.Message):
    p = await get_patsan(m.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
    
    can_fight, fight_msg = await can_fight_pvp(m.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"
    
    txt = f"👊 ПРОТАЩИТЬ КАК РАДЁМКУ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ!\n\n{fight_status}\n\nВыбери пацана и протащи его по гофроцентралу!\nЗа успешную радёмку получишь:\n• +0.2 мм к кабелю\n• +5-12 мм к гофрошке\n• Шанс унизить публично\n\nРиски:\n• Можешь опозориться перед всеми\n• Потеряешь уважение\n\nТвои статы:\n{gofra_info['emoji']} {gofra_info['name']}\n🏗️ {format_length(p.get('gofra_mm', 10.0))}\n🔌 {format_length(p.get('cable_mm', 10.0))}"
    await m.answer(txt, reply_markup=rademka_keyboard())

@router.message(Command("rademka"))
async def cmd_rademka_handler(m: types.Message):
    await cmd_rademka(m)

@ignore_not_modified_error
@router.callback_query(F.data == "rademka")
async def callback_rademka(c: types.CallbackQuery):
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
    
    can_fight, fight_msg = await can_fight_pvp(c.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"
    
    await c.message.edit_text(f"👊 ПРОТАЩИТЬ КАК РАДЁМКУ!\n\n{fight_status}\n\nВыбери пацана!\nЗа успех: +0.2 мм к кабелю, +5-12 мм к гофрошке, публичное унижение\n\nРиски: публичный позор\n\nТвои статы:\n{gofra_info['emoji']} {gofra_info['name']}\n🏗️ {format_length(p.get('gofra_mm', 10.0))} | 🔌 {format_length(p.get('cable_mm', 10.0))}", reply_markup=rademka_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "rademka_random")
async def rademka_random(c: types.CallbackQuery):
    can_fight, fight_msg = await can_fight_pvp(c.from_user.id)
    if not can_fight:
        await c.answer(f"❌ {fight_msg}", show_alert=True)
        return
    
    tp = await get_top_players(limit=50, sort_by="gofra")
    tg = [p for p in tp if p.get("user_id")!=c.from_user.id]
    if not tg: 
        return await c.message.edit_text("😕 НЕКОГО ПРОТАЩИВАТЬ!\n\nПриведи друзей!", reply_markup=back_kb("rademka"))
    
    t = random.choice(tg)
    pid, tn = t.get("user_id"), t.get("nickname","Неизвестно")
    tgofra_info = get_gofra_info(t.get("gofra_mm", 10.0))
    tcable = format_length(t.get("cable_mm", 10.0))
    
    p = await get_patsan(c.from_user.id)
    mgofra_info = get_gofra_info(p.get("gofra_mm", 10.0))
    mcable = format_length(p.get("cable_mm", 10.0))
    
    chance = await calculate_pvp_chance(p, t)

    await c.message.edit_text(f"🎯 НАШЁЛ ЦЕЛЬ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ!\n\n👤 Цель: {tn}\n{tgofra_info['emoji']} {tgofra_info['name']}\n🏗️ {tgofra_info['length_display']} | 🔌 {tcable}\n\n👤 Ты: {mgofra_info['emoji']} {mgofra_info['name']}\n🏗️ {mgofra_info['length_display']} | 🔌 {mcable}\n🎯 Шанс: {chance}%\n\nНаграда: +0.2 мм к кабелю, +5-12 мм к гофрошке\nРиск: позор\n\nПротащить?", reply_markup=rademka_fight_keyboard(pid))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data.startswith("rademka_confirm_"))
async def rademka_confirm(c: types.CallbackQuery):
    uid = c.from_user.id
    tid = int(c.data.replace("rademka_confirm_", ""))
    
    can_fight, fight_msg = await can_fight_pvp(uid)
    if not can_fight:
        await c.answer(f"❌ {fight_msg}", show_alert=True)
        return
    
    a = await get_patsan(uid)
    t = await get_patsan(tid)
    
    if not a or not t: 
        return await c.answer("Ошибка: пацан не найден!", show_alert=True)
    
    chance = await calculate_pvp_chance(a, t)
    suc = random.random() < (chance/100)
    
    if suc:
        cable_gain_mm = 0.2
        a["cable_mm"] = a.get("cable_mm", 10.0) + cable_gain_mm
        
        level_diff = t.get("gofra_mm", 10.0) - a.get("gofra_mm", 10.0)
        if level_diff > 0:
            gofra_gain_mm = 12.0 + min(level_diff / 100, 8.0)
        else:
            gofra_gain_mm = max(5.0, 12.0 + level_diff / 200)
        
        gofra_gain_mm = round(gofra_gain_mm, 2)
        a["gofra_mm"] = a.get("gofra_mm", 10.0) + gofra_gain_mm
        
        a["cable_power"] = int(a["cable_mm"] / 5)
        a["gofra"] = int(a["gofra_mm"] / 10)
        
        txt = f"✅ УСПЕХ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ! ТЫ ПРОТАЩИЛ!\n\n"
        txt += f"Ты унизил {t.get('nickname','Неизвестно')}!\n"
        txt += f"🔌 Кабель: +{cable_gain_mm:.1f} мм (теперь {format_length(a['cable_mm'])})\n"
        txt += f"🏗️ Гофрошка: +{gofra_gain_mm:.1f} мм (теперь {format_length(a['gofra_mm'])})\n"
        txt += f"🎯 Шанс был: {chance}%\n"
        txt += "Он теперь боится!"
    else:
        txt = f"❌ ПРОВАЛ!\n\nСам оказался радёмкой...\n\n"
        txt += f"{t.get('nickname','Неизвестно')} круче!\n"
        txt += f"🎯 Шанс был: {chance}%\n"
        txt += "Теперь смеются..."
    
    await save_patsan(a)
    await save_patsan(t)
    await save_rademka_fight(winner_id=uid if suc else tid, loser_id=tid if suc else uid)
    
    await c.message.edit_text(txt, reply_markup=back_kb("rademka"))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "rademka_stats")
async def rademka_stats(c: types.CallbackQuery):
    try:
        from db_manager import get_connection
        cn = await get_connection()
        cur = await cn.execute('SELECT COUNT(*) as tf, SUM(CASE WHEN winner_id=? THEN 1 ELSE 0 END) as w, SUM(CASE WHEN loser_id=? THEN 1 ELSE 0 END) as l FROM rademka_fights WHERE winner_id=? OR loser_id=?', (c.from_user.id,)*4)
        s = await cur.fetchone()
        if s and s[0] and s[0] > 0:
            t, w, l = s[0], s[1] or 0, s[2] or 0
            wr = (w / t * 100) if t > 0 else 0
            
            cur2 = await cn.execute('SELECT COUNT(*) as hour_fights FROM rademka_fights WHERE (winner_id=? OR loser_id=?) AND created_at > ?',
                                   (c.from_user.id, c.from_user.id, int(time.time()) - 3600))
            hour_row = await cur2.fetchone()
            hour_fights = hour_row[0] if hour_row else 0
            
            txt = f"📊 СТАТИСТИКА РАДЁМОК\n\n"
            txt += f"🎲 Всего: {t}\n"
            txt += f"✅ Побед: {w}\n"
            txt += f"❌ Поражений: {l}\n"
            txt += f"📈 Винрейт: {wr:.1f}%\n"
            txt += f"⏱️ За час: {hour_fights}/10 боёв\n\n"
            txt += f"Лимит: 10 боёв в час"
        else: 
            txt = f"📊 СТАТИСТИКА РАДёмОК\n\nНет радёмок!\nВыбери цель!\n\nПока мирный пацан..."
        await cn.close()
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        txt = f"📊 СТАТИСТИКА РАДёмОК\n\nБаза готовится...\n\nСистема учится считать!"
    await c.message.edit_text(txt, reply_markup=back_kb("rademka"))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "rademka_top")
async def rademka_top(c: types.CallbackQuery):
    try:
        from db_manager import get_connection
        cn = await get_connection()
        cur = await cn.execute('SELECT u.nickname, u.user_id, u.gofra_mm, u.cable_mm, COUNT(CASE WHEN rf.winner_id=u.user_id THEN 1 END) as w, COUNT(CASE WHEN rf.loser_id=u.user_id THEN 1 END) as l FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id OR u.user_id=rf.loser_id GROUP BY u.user_id, u.nickname, u.gofra_mm, u.cable_mm HAVING w>0 ORDER BY w DESC LIMIT 10')
        tp = await cur.fetchall()
        if tp:
            mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 ТОП РАДёМЩИКОВ\n\n"
            for i, p in enumerate(tp):
                if i>=len(mds): 
                    break
                md, nn, w, l, gofra_mm, cable_mm = mds[i], p.get("nickname","Неизвестно"), p.get("w",0) or 0, p.get("l",0) or 0, p.get("gofra_mm",10.0), p.get("cable_mm",10.0)
                gofra_info = get_gofra_info(gofra_mm)
                if len(nn)>15:
                    nn=nn[:12]+"..."
                win_rate = 0 if w+l==0 else (w/(w+l)*100)
                txt+=f"{md} {nn} {gofra_info['emoji']}\n   🏗️ {format_length(gofra_mm)} | 🔌 {format_length(cable_mm)} | ✅ {w} ({win_rate:.0f}%)\n\n"
            txt+="Топ по победам"
        else: 
            txt = f"🥇 ТОП РАДёмЩИКОВ\n\nПока никого!\nБудь первым!\n\nСлава ждёт!"
        await cn.close()
    except Exception as e:
        logger.error(f"Ошибка топа: {e}")
        txt = f"🥇 ТОП РАДёмЩИКОВ\n\nРейтинг формируется...\n\nМеста скоро будут!"
    await c.message.edit_text(txt, reply_markup=back_kb("rademka"))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(c: types.CallbackQuery):
    try:
        p = await get_patsan(c.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
        await c.message.edit_text(f"Главное меню\n{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {gofra_info['length_display']} | 🔌 {format_length(p.get('cable_mm', 10.0))}\n\n🌀 Атмосферы: {p.get('atm_count',0)}/12\n🐍 Змий: {p.get('zmiy_grams',0):.0f}г\n\nВыбери действие:", reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка главного: {e}")
        await c.message.edit_text("Главное меню\n\nБот работает!", reply_markup=main_keyboard())

# ========== END OF NICKNAME AND RADEMKA HANDLERS ==========

# ========== ATM HANDLERS FROM atm_handlers.py ==========
@router.callback_query(F.data == "atm_regen_time")
@ignore_not_modified_error
async def atm_regen_time_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)

        atm_count = patsan.get('atm_count', 0)
        max_atm = 12

        regen_info = await calculate_atm_regen_time(patsan)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        text = (
            f"⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ АТМОСФЕР\n\n"
            f"Текущее состояние:\n"
            f"🌀 Атмосферы: [{pb(atm_count, max_atm)}] {atm_count}/{max_atm}\n"
            f"📈 Нужно восстановить: {regen_info['needed']} шт.\n\n"
            f"Точный таймер:\n"
            f"🕒 До следующей атмосферы: {ft(regen_info['time_to_next_atm'])}\n"
            f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
            f"Скорость восстановления:\n"
            f"• Базовая: 1 атм. за 2 часа (7200с)\n"
            f"• С учётом гофрошки ({gofra_info['name']}): x{gofra_info['atm_speed']:.2f}\n"
            f"• 1 атм. за: {ft(regen_info['time_to_one_atm'])}\n\n"
            f"Как ускорить:\n"
            f"• Повышай гофрошку - ускоряет восстановление\n"
            f"• Дави змия при полных 12 атмосферах\n"
            f"• Больше опыт → выше гофрошка → быстрее атмосферы"
        )

        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "atm_max_info")
async def atm_max_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)

        current_max = 12
        atm_count = patsan.get('atm_count', 0)

        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        text = (
            f"📊 МАКСИМАЛЬНЫЙ ЗАПАС АТМОСФЕР\n\n"
            f"Текущие показатели:\n"
            f"🌀 Атмосферы: [{pb(atm_count, current_max)}] {atm_count}/{current_max}\n"
            f"🎯 Максимум: {current_max} атм.\n\n"
            f"Особенности системы:\n"
            f"• Фиксированный максимум: 12 атмосфер\n"
            f"• Только при полных 12 можно давить змия\n"
            f"• Восстановление зависит от гофрошки\n\n"
            f"Твоя гофрошка:\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"⚡ Скорость восстановления: x{gofra_info['atm_speed']:.2f}\n\n"
            f"Зачем ждать 12 атмосфер?\n"
            f"• Более тяжёлый змий при давке\n"
            f"• Больше опыт для гофрошки\n"
            f"• Укрепление кабеля (+0.1 мм за 1кг змия)"
        )

        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "atm_boosters")
async def atm_boosters_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        text = (
            f"⚡ УСКОРЕНИЕ ВОССТАНОВЛЕНИЯ\n\n"
            f"В новой системе нет платных бустеров!\n\n"
            f"Вместо них работает:\n"
            f"🏗️ СИСТЕМА ГОФРЫ\n\n"
            f"Твоя гофрошка:\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"⚡ Множитель скорости: x{gofra_info['atm_speed']:.2f}\n\n"
            f"Как улучшить гофрошку?\n"
            f"1. Дождись 12 атмосфер (кнопка 🌡️)\n"
            f"2. Дави змия (кнопка 🐍)\n"
            f"3. Получай опыт (0.02 мм/г змия)\n"
            f"4. Повышай гофрошку\n\n"
            f"Следующие уровни гофрошки:\n"
        )

        thresholds = [10.0, 50.0, 150.0, 300.0, 600.0, 1200.0, 2500.0, 5000.0, 10000.0, 20000.0]
        current_gofra = patsan.get('gofra_mm', 10.0)

        for i, threshold in enumerate(thresholds):
            if current_gofra < threshold:
                next_info = get_gofra_info(threshold)
                text += f"• {next_info['emoji']} {next_info['name']}: x{next_info['atm_speed']:.2f}\n"
                if i >= 2:
                    break

        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)
# ========== END OF ATM HANDLERS ==========
