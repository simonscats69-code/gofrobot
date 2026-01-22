from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
import time
import random
import logging
from db_manager import (
    get_patsan, davka_zmiy, uletet_zmiy, get_gofra_info, 
    format_length, ChatManager, calculate_atm_regen_time
)
from keyboards import main_keyboard, back_kb

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def group_start(message: types.Message):
    chat = message.chat
    
    await ChatManager.register_chat(
        chat_id=chat.id,
        chat_title=chat.title if hasattr(chat, 'title') else "",
        chat_type=chat.type
    )
    
    await message.answer(
        f"👋 Приветствуем в гофроцентрале, {chat.title if hasattr(chat, 'title') else 'чатик'}!\n\n"
        f"Я бот для давки коричневага и прокачки гофры.\n"
        f"Работаю как в личке, так и в группах!\n\n"
        f"📊 В группе ведётся общая статистика\n"
        f"🏆 Есть топ участников чата\n"
        f"👊 Можно устраивать радёмки\n\n"
        f"Используй /help для списка команд",
        reply_markup=main_keyboard()
    )

@router.message(Command("help"))
async def group_help(message: types.Message):
    help_text = (
        "🆘 КОМАНДЫ ДЛЯ ГРУПП:\n\n"
        "👤 Личные команды (работают в любом месте):\n"
        "/start - Начать игру\n"
        "/davka - Давить коричневага\n"
        "/uletet - Отправить змия\n"
        "/profile - Профиль\n"
        "/top - Топ игроков\n\n"
        "👥 Групповые команды:\n"
        "/chat_top - Топ этого чата\n"
        "/chat_stats - Статистика чата\n"
        "/my_chat_stats - Моя статистика в чате\n"
        "/chat_help - Эта справка\n\n"
        "🎮 Быстрые действия (кнопками):\n"
        "🐍 Давить коричневага\n"
        "✈️ Отправить змия\n"
        "🏆 Смотреть топы\n"
        "👊 Радёмка (PvP)\n\n"
        "📊 В группе сохраняется общая статистика!"
    )
    
    await message.answer(help_text)

@router.message(Command("chat_top"))
async def chat_top_command(message: types.Message):
    chat_id = message.chat.id
    
    try:
        top_players = await ChatManager.get_chat_top(chat_id, limit=15)
        
        if not top_players:
            await message.answer(
                "📊 ТОП ЧАТА ПУСТ!\n\n"
                "Пока никто не давил змия в этом чате.\n"
                "Будь первым - нажми кнопку 🐍!",
                reply_markup=main_keyboard()
            )
            return
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", 
                 "🅰️", "🅱️", "🆎", "🆑", "🅾️"]
        
        text = f"🏆 ТОП ЧАТА: {message.chat.title if hasattr(message.chat, 'title') else 'Этого чата'}\n\n"
        
        for i, player in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            nickname = player.get('nickname', f'Игрок_{player.get("user_id")}')
            if len(nickname) > 20:
                nickname = nickname[:17] + "..."
            
            total_kg = player['total_zmiy_grams'] / 1000
            
            text += f"{medal} {nickname}\n"
            text += f"   🐍 {total_kg:.1f} кг змия | 📊 {player['rank']} место\n\n"
        
        stats = await ChatManager.get_chat_stats(chat_id)
        text += f"📈 Статистика чата:\n"
        text += f"• Участников: {stats['total_players']}\n"
        text += f"• Всего змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• Всего давок: {stats['total_davki_all']}\n"
        text += f"• Активных за неделю: {stats['active_players']}"
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error getting chat top: {e}")
        await message.answer("❌ Ошибка загрузки топа чата. Попробуй позже.")

@router.message(Command("chat_stats"))
async def chat_stats_command(message: types.Message):
    chat_id = message.chat.id
    
    try:
        stats = await ChatManager.get_chat_stats(chat_id)
        
        if stats['last_activity'] > 0:
            last_active = time.strftime('%d.%m.%Y %H:%M', time.localtime(stats['last_activity']))
        else:
            last_active = "никогда"
        
        text = f"📊 СТАТИСТИКА ЧАТА\n\n"
        text += f"📝 Название: {message.chat.title if hasattr(message.chat, 'title') else 'Без названия'}\n"
        text += f"👥 Всего участников: {stats['total_players']}\n"
        text += f"🔥 Активных за неделю: {stats['active_players']}\n\n"
        
        text += f"🐍 Змий добыто:\n"
        text += f"• Всего: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• На игрока: {stats['total_zmiy_all']/max(1, stats['total_players'])/1000:.1f} кг\n\n"
        
        text += f"⚡ Давок сделано:\n"
        text += f"• Всего: {stats['total_davki_all']}\n"
        text += f"• На игрока: {stats['total_davki_all']/max(1, stats['total_players']):.0f}\n\n"
        
        text += f"⏱️ Последняя активность: {last_active}"
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        await message.answer("❌ Ошибка загрузки статистики чата.")

@router.message(Command("davka"))
async def group_davka_command(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await ChatManager.register_chat(
        chat_id=chat_id,
        chat_title=message.chat.title if hasattr(message.chat, 'title') else "",
        chat_type=message.chat.type
    )
    
    try:
        success, p, res = await davka_zmiy(user_id, chat_id)
        
        if not success:
            await message.answer(res)
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
            f"🐍 {message.from_user.first_name} ЗАВАРВАРИЛ ДВАНАШКУ!\n\n",
            f"🐍 {message.from_user.first_name} ВЫДАВИЛ КОРИЧНЕВАГА!\n\n",
            f"🐍 {message.from_user.first_name} ОТЖАЛ ЗМИЯ!\n\n"
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
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error in group davka: {e}")
        await message.answer("❌ Ошибка при давке змия. Попробуй позже.")

@router.message(Command("my_chat_stats"))
async def my_chat_stats_command(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)
        
        if user_total == 0:
            await message.answer(
                f"📊 Твоя статистика в этом чате:\n\n"
                f"Пока ты не давил змия в этом чате.\n"
                f"Нажми /davka чтобы начать!"
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
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error getting user chat stats: {e}")
        await message.answer("❌ Ошибка загрузки статистики.")

@router.message(F.text.contains("гофра") | F.text.contains("змий") | F.text.contains("давка"))
async def group_keywords(message: types.Message):
    text_lower = message.text.lower()
    
    responses = []
    
    if "гофра" in text_lower:
        responses.extend([
            "Гофра - это жизнь! 🏗️",
            "Чем больше гофра, тем тяжелее змий! 💪",
            "Моя гофра уже {length} см! А твоя? 🏗️",
            "Без гофры и змий не выдавишь! ⚡"
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
