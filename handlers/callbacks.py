from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import time
import random
import logging
from db_manager import (
    get_patsan, davka_zmiy, uletet_zmiy, get_gofra_info, 
    format_length, ChatManager, calculate_atm_regen_time,
    calculate_pvp_chance, can_fight_pvp, save_patsan, save_rademka_fight
)
from keyboards import main_keyboard, back_kb, gofra_info_kb, cable_info_kb, atm_status_kb, rademka_keyboard, nickname_keyboard, chat_menu_keyboard as get_chat_menu_keyboard
from handlers.utils import ft

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start", "gofra", "gofrastart"))
async def group_start(message: types.Message):
    chat = message.chat
    
    await ChatManager.register_chat(
        chat_id=chat.id,
        chat_title=chat.title if hasattr(chat, 'title') else "",
        chat_type=chat.type
    )
    
    await message.answer(
        f"👋 Приветствуем в гофроцентрале, {chat.title if hasattr(chat, 'title') else 'чатик'}!\n\n"
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
    text += f"За победу: +0.2 мм к кабелю, +5-12 мм к гофрошке\n\n"
    
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
    
    chance = calculate_pvp_chance(attacker_data, target_data)
    
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
    text += f"🏆 Награда за победу: +0.2 мм к кабелю, +5-12 мм к гофрошке\n"
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
        text += f"• Твой вклад: {(user_total/stats['total_zmiy_all']*100):.1f}%"
        
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
            await callback.answer(res, show_alert=True)
            return

        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
        text = f"🐍 ДАВКА КОРИЧНЕВАГА!\n\n"
        text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
        text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
        text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
        text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г"

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
            await callback.answer(res, show_alert=True)
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
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм\n"
        text += f"• Победы в радёмках = +0.2 мм\n\n"
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
        regen_info = calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        def ft(s):
            if s < 60: return f"{s}с"
            m, h, d = s // 60, s // 3600, s // 86400
            if d > 0: return f"{d}д {h%24}ч {m%60}м"
            if h > 0: return f"{h}ч {m%60}м {s%60}с"
            return f"{m}м {s%60}с"

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
            await callback.message.edit_text(text, reply_markup=profile_extended_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=profile_extended_kb())

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

@router.callback_query(F.data.startswith("chat_"))
async def handle_chat_callbacks(callback: types.CallbackQuery):
    action = callback.data.replace("chat_", "")
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    try:
        if action == "davka":
            await process_chat_davka_callback(callback, user_id, chat_id)
        elif action == "top":
            await show_chat_top_callback(callback, chat_id)
        elif action == "stats":
            await show_chat_stats_callback(callback, chat_id)
        elif action == "me":
            await show_user_chat_stats_callback(callback, user_id, chat_id)
        elif action == "gofra":
            await show_user_gofra_callback(callback, user_id)
        elif action == "cable":
            await show_user_cable_callback(callback, user_id)
        elif action == "atm":
            await show_user_atm_callback(callback, user_id)
        elif action == "rademka":
            await show_rademka_callback(callback, user_id, chat_id)
        elif action == "help":
            await show_chat_help_callback(callback)
        elif action == "menu":
            await show_chat_menu_callback(callback)
        elif action == "fight":
            await callback.answer("Используй команду /fight в ответ на сообщение игрока", show_alert=True)
        else:
            await callback.answer("❌ Неизвестное действие", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error in chat callback {action}: {e}")
        await callback.answer("❌ Ошибка, попробуй позже", show_alert=True)

@router.callback_query(F.data.startswith("chat_fight_"))
async def handle_chat_fight(callback: types.CallbackQuery):
    try:
        target_id = int(callback.data.replace("chat_fight_", ""))
        attacker_id = callback.from_user.id
        
        if attacker_id == target_id:
            await callback.answer("❌ Нельзя драться с самим собой!", show_alert=True)
            return
        
        can_fight, fight_msg = await can_fight_pvp(attacker_id)
        if not can_fight:
            await callback.answer(f"❌ {fight_msg}", show_alert=True)
            return
        
        attacker = await get_patsan(attacker_id)
        target = await get_patsan(target_id)
        
        if not attacker or not target:
            await callback.answer("❌ Ошибка: игрок не найден!", show_alert=True)
            return
        
        chance = calculate_pvp_chance(attacker, target)
        success = random.random() < (chance / 100)
        
        winner_id = attacker_id if success else target_id
        loser_id = target_id if success else attacker_id
        
        winner = await get_patsan(winner_id)
        loser = await get_patsan(loser_id)
        
        if success:
            cable_gain_mm = 0.2
            attacker["cable_mm"] = attacker.get("cable_mm", 10.0) + cable_gain_mm
            
            level_diff = target.get("gofra_mm", 10.0) - attacker.get("gofra_mm", 10.0)
            if level_diff > 0:
                gofra_gain_mm = 12.0 + min(level_diff / 100, 8.0)
            else:
                gofra_gain_mm = max(5.0, 12.0 + level_diff / 200)
            
            gofra_gain_mm = round(gofra_gain_mm, 2)
            attacker["gofra_mm"] = attacker.get("gofra_mm", 10.0) + gofra_gain_mm
            
            attacker["cable_power"] = int(attacker["cable_mm"] / 5)
            attacker["gofra"] = int(attacker["gofra_mm"] / 10)
            
            await save_patsan(attacker)
            winner_nick = attacker.get('nickname', callback.from_user.first_name)
            loser_nick = target.get('nickname', 'Неизвестно')
        else:
            cable_gain_mm = 0.1
            target["cable_mm"] = target.get("cable_mm", 10.0) + cable_gain_mm
            
            level_diff = attacker.get("gofra_mm", 10.0) - target.get("gofra_mm", 10.0)
            if level_diff > 0:
                gofra_gain_mm = 6.0 + min(level_diff / 200, 4.0)
            else:
                gofra_gain_mm = max(2.5, 6.0 + level_diff / 400)
            
            gofra_gain_mm = round(gofra_gain_mm, 2)
            target["gofra_mm"] = target.get("gofra_mm", 10.0) + gofra_gain_mm
            
            target["cable_power"] = int(target["cable_mm"] / 5)
            target["gofra"] = int(target["gofra_mm"] / 10)
            
            await save_patsan(target)
            winner_nick = target.get('nickname', 'Неизвестно')
            loser_nick = attacker.get('nickname', callback.from_user.first_name)
        
        await save_rademka_fight(winner_id=winner_id, loser_id=loser_id, money_taken=0)
        
        if success:
            result_text = f"🎉 РАДЁМКА ЗАВЕРШЕНА!\n\n"
            result_text += f"🏆 ПОБЕДИТЕЛЬ: {callback.from_user.first_name}\n"
            result_text += f"💀 ПРОИГРАВШИЙ: {target.get('nickname', 'Неизвестно')}\n\n"
            result_text += f"Награды победителю:\n"
            result_text += f"🔌 Кабель: +{cable_gain_mm:.1f} мм\n"
            result_text += f"🏗️ Гофра: +{gofra_gain_mm:.1f} мм\n"
            result_text += f"🎯 Шанс был: {chance}%\n\n"
            result_text += f"{target.get('nickname', 'Неизвестно')} теперь будет носить твои кроссовки!"
        else:
            result_text = f"💀 РАДЁМКА ЗАВЕРШЕНА!\n\n"
            result_text += f"🏆 ПОБЕДИТЕЛЬ: {target.get('nickname', 'Неизвестно')}\n"
            result_text += f"😭 ПРОИГРАВШИЙ: {callback.from_user.first_name}\n\n"
            result_text += f"{callback.from_user.first_name} был унижен публично!\n"
            result_text += f"🎯 Шанс был: {chance}%\n\n"
            result_text += f"Теперь {callback.from_user.first_name} моет туалеты на гофроцентрале!"
        
        try:
            await callback.message.edit_text(result_text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(result_text, reply_markup=get_chat_menu_keyboard())
        
        await callback.answer()
        
        try:
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=f"👊 Результат радёмки: {winner_nick} протащил {loser_nick}!"
            )
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error in chat fight: {e}", exc_info=True)
        await callback.answer("❌ Ошибка в радёмке!", show_alert=True)

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
    text += f"🏗️ Гофra: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
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
        text += f"• Победы в радёмках = +0.2 мм\n\n"
        text += f"📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г"
        
        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in chat callback cable: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_user_atm_callback(callback: types.CallbackQuery, user_id: int):
    try:
        p = await get_patsan(user_id)
        regen_info = calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
        
        def ft(s):
            if s < 60: return f"{s}с"
            m, h, d = s // 60, s // 3600, s // 86400
            if d > 0: return f"{d}д {h%24}ч {m%60}м"
            if h > 0: return f"{h}ч {m%60}м {s%60}с"
            return f"{m}м {s%60}с"
        
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
            except:
                response = response.format(length="1.5")
        
        if "{weight}" in response:
            weight = random.randint(50, 500)
            response = response.format(weight=weight)
        
        await message.reply(response)
