from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from database.db_manager import get_patsan_cached, change_nickname, get_connection
from keyboards.keyboards import main_keyboard
from keyboards.new_keyboards import nickname_keyboard, rademka_keyboard, rademka_fight_keyboard, back_to_rademka_keyboard

router = Router()

# Декоратор для обработки ошибки "message is not modified"
def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # Игнорируем эту ошибку - ничего страшного
                if len(args) > 0 and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise  # Пропускаем другие ошибки
    return wrapper

# ==================== СМЕНА НИКА (FSM) ====================

class NicknameChange(StatesGroup):
    waiting_for_nickname = State()

@router.message(Command("nickname"))
async def cmd_nickname(message: types.Message, state: FSMContext):
    """Команда /nickname - смена ника"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    if current_state == NicknameChange.waiting_for_nickname.state:
        await message.answer("Ты уже в процессе смены ника! Напиши новый ник или отмени командой /cancel")
        return
    
    nickname_changed = patsan.get("nickname_changed", False)
    cost = 0 if not nickname_changed else 5000
    
    if nickname_changed:
        message_text = (
            f"🏷️ <b>СМЕНА НИКА</b>\n\n"
            f"Твой текущий ник: <code>{patsan['nickname']}</code>\n"
            f"Ты уже менял ник ранее.\n"
            f"Стоимость смены: <b>{cost} руб.</b>\n\n"
            f"Напиши новый ник (3-20 символов, только буквы и цифры):"
        )
    else:
        message_text = (
            f"🏷️ <b>СМЕНА НИКА</b>\n\n"
            f"Твой текущий ник: <code>{patsan['nickname']}</code>\n"
            f"🎉 <b>Первая смена - БЕСПЛАТНО!</b>\n"
            f"Потом будет стоить 5000 руб.\n\n"
            f"Напиши новый ник (3-20 символов, только буквы и цифры):"
        )
    
    await message.answer(
        message_text,
        reply_markup=nickname_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(NicknameChange.waiting_for_nickname)

@router.callback_query(F.data == "change_nickname")
async def callback_change_nickname(callback: types.CallbackQuery, state: FSMContext):
    """Кнопка смены ника"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    # Проверяем текущее состояние - если уже в состоянии смены ника, не редактируем
    current_state = await state.get_state()
    if current_state == NicknameChange.waiting_for_nickname.state:
        await callback.answer("Ты уже в процессе смены ника! Напиши новый ник.")
        return
    
    nickname_changed = patsan.get("nickname_changed", False)
    cost = 0 if not nickname_changed else 5000
    
    if nickname_changed:
        message_text = (
            f"🏷️ <b>СМЕНА НИКА</b>\n\n"
            f"Твой текущий ник: <code>{patsan['nickname']}</code>\n"
            f"Ты уже менял ник ранее.\n"
            f"Стоимость смены: <b>{cost} руб.</b>\n\n"
            f"Напиши новый ник (3-20 символов, только буквы и цифры):"
        )
    else:
        message_text = (
            f"🏷️ <b>СМЕНА НИКА</b>\n\n"
            f"Твой текущий ник: <code>{patsan['nickname']}</code>\n"
            f"🎉 <b>Первая смена - БЕСПЛАТНО!</b>\n"
            f"Потом будет стоить 5000 руб.\n\n"
            f"Напиши новый ник (3-20 символов, только буквы и цифры):"
        )
    
    # Отправляем новое сообщение вместо редактирования старого
    await callback.message.answer(
        message_text,
        reply_markup=nickname_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(NicknameChange.waiting_for_nickname)
    await callback.answer("Введи новый ник в чат")

@router.message(NicknameChange.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    """Обработка нового ника"""
    user_id = message.from_user.id
    new_nickname = message.text.strip()
    
    # Валидация ника
    if len(new_nickname) < 3:
        await message.answer(
            "❌ Слишком короткий ник! Минимум 3 символа.\n"
            "Попробуй ещё раз:",
            reply_markup=nickname_keyboard()
        )
        return
    
    if len(new_nickname) > 20:
        await message.answer(
            "❌ Слишком длинный ник! Максимум 20 символов.\n"
            "Попробуй ещё раз:",
            reply_markup=nickname_keyboard()
        )
        return
    
    # Проверка на допустимые символы
    if not all(c.isalnum() or c in "_- " for c in new_nickname):
        await message.answer(
            "❌ Используй только буквы, цифры, пробелы, дефисы и подчёркивания!\n"
            "Попробуй ещё раз:",
            reply_markup=nickname_keyboard()
        )
        return
    
    # Пробуем сменить ник
    success, result_message = await change_nickname(user_id, new_nickname)
    
    if success:
        await message.answer(
            f"✅ {result_message}\n"
            f"Теперь ты известен как: <code>{new_nickname}</code>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ {result_message}\n"
            f"Попробуй снова:",
            reply_markup=nickname_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()

# Команда для отмены смены ника
@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена смены ника"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    
    await state.clear()
    await message.answer(
        "Смена ника отменена.",
        reply_markup=main_keyboard()
    )

# ==================== РАДЁМКА ====================

@router.message(Command("rademka"))
async def cmd_rademka(message: types.Message):
    """Команда /rademka - меню радёмки"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    message_text = (
        f"👊 <b>ПРОТАЩИТЬ КАК РАДЁМКУ!</b>\n\n"
        f"<i>ИДИ СЮДА РАДЁМКА БАЛЯ!</i>\n\n"
        f"Выбери пацана и протащи его по гофроцентралу!\n"
        f"За успешную радёмку получишь:\n"
        f"• +1 авторитет\n"
        f"• 10% его денег\n"
        f"• Шанс забрать двенашку\n\n"
        f"<b>Риски:</b>\n"
        f"• Можешь потерять 5% своих денег\n"
        f"• -1 авторитет при неудаче\n"
        f"• Отжатый пацан может отомстить\n\n"
        f"Твой авторитет: ⭐ {patsan['avtoritet']}\n"
        f"Твои деньги: 💰 {patsan['dengi']}р"
    )
    
    await message.answer(
        message_text,
        reply_markup=rademka_keyboard(),
        parse_mode="HTML"
    )

@ignore_not_modified_error
@router.callback_query(F.data == "rademka")
async def callback_rademka(callback: types.CallbackQuery):
    """Кнопка радёмки"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    message_text = (
        f"👊 <b>ПРОТАЩИТЬ КАК РАДЁМКУ!</b>\n\n"
        f"<i>ИДИ СЮДА РАДЁМКА БАЛЯ!</i>\n\n"
        f"Выбери пацана и протащи его по гофроцентралу!\n"
        f"За успешную радёмку получишь:\n"
        f"• +1 авторитет\n"
        f"• 10% его денег\n"
        f"• Шанс забрать двенашку\n\n"
        f"<b>Риски:</b>\n"
        f"• Можешь потерять 5% своих денег\n"
        f"• -1 авторитет при неудаче\n"
        f"• Отжатый пацан может отомстить\n\n"
        f"Твой авторитет: ⭐ {patsan['avtoritet']}\n"
        f"Твои деньги: 💰 {patsan['dengi']}р"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=rademka_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "rademka_random")
async def rademka_random(callback: types.CallbackQuery):
    """Случайный пацан для радёмки"""
    from database.db_manager import get_top_players
    import random
    
    user_id = callback.from_user.id
    
    # Получаем топ игроков (кроме себя)
    top_players = await get_top_players(limit=50, sort_by="avtoritet")
    
    # Фильтруем себя
    possible_targets = [p for p in top_players if p["user_id"] != user_id]
    
    if not possible_targets:
        await callback.message.edit_text(
            "😕 <b>НЕКОГО ПРОТАСКИВАТЬ!</b>\n\n"
            "На гофроцентрале кроме тебя никого нет...\n"
            "Приведи друзей, чтобы было кого радёмить!",
            reply_markup=back_to_rademka_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Выбираем случайную цель
    target = random.choice(possible_targets)
    target_id = target["user_id"]
    target_name = target["nickname"]
    target_avtoritet = target["avtoritet"]
    
    # Получаем данные атакующего
    patsan = await get_patsan_cached(user_id)
    attacker_avtoritet = patsan["avtoritet"]
    
    # Рассчитываем шансы
    chance = 50  # Базовый шанс 50%
    
    # Влияние авторитета
    if attacker_avtoritet > target_avtoritet:
        chance += min(30, (attacker_avtoritet - target_avtoritet) * 5)
    elif target_avtoritet > attacker_avtoritet:
        chance -= min(30, (target_avtoritet - attacker_avtoritet) * 5)
    
    chance = max(10, min(90, chance))  # Ограничиваем 10-90%
    
    message_text = (
        f"🎯 <b>НАШЁЛ ЦЕЛЬ ДЛЯ РАДЁМКИ!</b>\n\n"
        f"<i>ИДИ СЮДА РАДЁМКА БАЛЯ!</i>\n\n"
        f"🔴 <b>Цель:</b> {target_name}\n"
        f"⭐ <b>Его авторитет:</b> {target_avtoritet}\n"
        f"💰 <b>Его деньги:</b> {target['dengi_formatted']}\n\n"
        f"🟢 <b>Твой авторитет:</b> {attacker_avtoritet}\n"
        f"🎲 <b>Шанс успеха:</b> {chance}%\n\n"
        f"<b>Награда за успех:</b>\n"
        f"• +1 авторитет\n"
        f"• 10% его денег\n"
        f"• Шанс забрать двенашку\n\n"
        f"<b>Риск при провале:</b>\n"
        f"• -1 авторитет\n"
        f"• Потеря 5% своих денег\n\n"
        f"Протащить этого пацана?"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=rademka_fight_keyboard(target_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("rademka_confirm_"))
async def rademka_confirm(callback: types.CallbackQuery):
    """Подтверждение радёмки (С ИСПРАВЛЕНИЕМ: теперь сохраняет статистику)"""
    from database.db_manager import get_patsan, save_patsan, unlock_achievement
    import random
    
    user_id = callback.from_user.id
    target_id = int(callback.data.replace("rademka_confirm_", ""))
    
    # Получаем данные обоих пацанов
    attacker = await get_patsan(user_id)
    target = await get_patsan(target_id)
    
    if not attacker or not target:
        await callback.answer("Ошибка: один из пацанов не найден!", show_alert=True)
        return
    
    # Рассчитываем шансы
    base_chance = 50
    avtoritet_diff = attacker["avtoritet"] - target["avtoritet"]
    chance = base_chance + (avtoritet_diff * 5)
    chance = max(10, min(90, chance))
    
    # Случайный исход
    success = random.random() < (chance / 100)
    
    # Переменные для статистики
    money_taken = 0
    item_stolen = None
    
    if success:
        # УСПЕШНАЯ РАДЁМКА!
        
        # Награда: 10% денег цели
        money_taken = int(target["dengi"] * 0.1)
        attacker["dengi"] += money_taken
        target["dengi"] -= money_taken
        
        # Минимальная сумма у цели
        if target["dengi"] < 10:
            target["dengi"] = 10
        
        # +1 авторитет атакующему
        attacker["avtoritet"] += 1
        
        # Шанс забрать двенашку (30%)
        if target.get("inventory") and "двенашка" in target["inventory"] and random.random() < 0.3:
            target["inventory"].remove("двенашка")
            attacker["inventory"].append("двенашка")
            item_stolen = "двенашка"
            item_stolen_text = "\n🎒 <b>Забрал двенашку!</b>"
        else:
            item_stolen_text = ""
        
        result_text = (
            f"✅ <b>УСПЕШНАЯ РАДЁМКА!</b>\n\n"
            f"<i>ИДИ СЮДА РАДЁМКА БАЛЯ! ТЫ ПРОТАЩИЛ ЕГО!</i>\n\n"
            f"Ты унизил {target['nickname']} на глазах у всех!\n"
            f"⭐ <b>+1 авторитет</b> (теперь {attacker['avtoritet']})\n"
            f"💰 <b>+{money_taken}р</b> (отжал у пацана){item_stolen_text}\n\n"
            f"<i>Он теперь будет тебя бояться!</i>"
        )
        
        # Достижение за первую радёмку
        await unlock_achievement(user_id, "first_rademka", "Первая радёмка", 200)
        
    else:
        # ПРОВАЛ РАДЁМКИ
        
        # Штраф: 5% денег атакующего
        money_penalty = int(attacker["dengi"] * 0.05)
        attacker["dengi"] -= money_penalty
        
        # -1 авторитет
        attacker["avtoritet"] = max(1, attacker["avtoritet"] - 1)
        
        # Шанс получить ответку (20%)
        revenge_text = ""
        revenge_money = 0
        if random.random() < 0.2:
            revenge_money = int(attacker["dengi"] * 0.05)
            attacker["dengi"] -= revenge_money
            target["dengi"] += revenge_money
            revenge_text = f"\n💥 <b>Он отомстил и забрал {revenge_money}р!</b>"
        
        result_text = (
            f"❌ <b>ПРОВАЛ РАДЁМКИ!</b>\n\n"
            f"<i>Сам оказался радёмкой... Стыдоба!</i>\n\n"
            f"{target['nickname']} оказался круче тебя!\n"
            f"⭐ <b>-1 авторитет</b> (теперь {attacker['avtoritet']})\n"
            f"💰 <b>-{money_penalty}р</b> (потерял при позоре){revenge_text}\n\n"
            f"<i>Теперь над тобой смеются...</i>"
        )
    
    # Сохраняем изменения в пользователях
    await save_patsan(attacker)
    await save_patsan(target)
    
    # Сохраняем статистику боя
    await save_rademka_fight(
        winner_id=user_id if success else target_id,
        loser_id=target_id if success else user_id,
        money_taken=money_taken,
        item_stolen=item_stolen
    )
    
    await callback.message.edit_text(
        result_text,
        reply_markup=back_to_rademka_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

async def save_rademka_fight(winner_id: int, loser_id: int, money_taken: int = 0, item_stolen: str = None):
    """Сохранение статистики радёмки в базу"""
    try:
        conn = await get_connection()
        await conn.execute('''
            INSERT INTO rademka_fights (winner_id, loser_id, money_taken, item_stolen)
            VALUES (?, ?, ?, ?)
        ''', (winner_id, loser_id, money_taken, item_stolen))
        await conn.commit()
        await conn.close()
    except Exception as e:
        # Если таблицы нет - игнорируем, создадим позже
        pass

@router.callback_query(F.data == "rademka_stats")
async def rademka_stats(callback: types.CallbackQuery):
    """Статистика радёмок (РЕАЛЬНАЯ СТАТИСТИКА)"""
    user_id = callback.from_user.id
    
    try:
        conn = await get_connection()
        
        # Пробуем получить статистику из таблицы rademka_fights
        cursor = await conn.execute('''
            SELECT 
                COUNT(*) as total_fights,
                SUM(CASE WHEN winner_id = ? THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN loser_id = ? THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN winner_id = ? THEN money_taken ELSE 0 END) as total_money_taken
            FROM rademka_fights 
            WHERE winner_id = ? OR loser_id = ?
        ''', (user_id, user_id, user_id, user_id, user_id))
        
        stats = await cursor.fetchone()
        
        if stats and stats["total_fights"] and stats["total_fights"] > 0:
            total = stats["total_fights"]
            wins = stats["wins"] or 0
            losses = stats["losses"] or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            money_taken = stats["total_money_taken"] or 0
            
            message_text = (
                f"📊 <b>ТВОЯ СТАТИСТИКА РАДЁМОК</b>\n\n"
                f"🎮 <b>Всего радёмок:</b> {total}\n"
                f"✅ <b>Побед:</b> {wins}\n"
                f"❌ <b>Поражений:</b> {losses}\n"
                f"📈 <b>Винрейт:</b> {win_rate:.1f}%\n"
                f"💰 <b>Всего отжато:</b> {money_taken}р\n\n"
            )
            
            # Самые частые цели (если есть победы)
            if wins > 0:
                cursor = await conn.execute('''
                    SELECT loser_id, COUNT(*) as fights
                    FROM rademka_fights 
                    WHERE winner_id = ?
                    GROUP BY loser_id 
                    ORDER BY fights DESC 
                    LIMIT 3
                ''', (user_id,))
                
                top_targets = await cursor.fetchall()
                
                if top_targets:
                    message_text += "<b>Любимые цели:</b>\n"
                    for i, target in enumerate(top_targets, 1):
                        user_cursor = await conn.execute(
                            "SELECT nickname FROM users WHERE user_id = ?",
                            (target["loser_id"],)
                        )
                        target_user = await user_cursor.fetchone()
                        nickname = target_user["nickname"] if target_user else f"Пацан_{target['loser_id']}"
                        
                        # Обрезаем длинные ники
                        if len(nickname) > 20:
                            nickname = nickname[:17] + "..."
                        
                        message_text += f"{i}. {nickname} - {target['fights']} раз\n"
        
        else:
            # Нет статистики
            message_text = (
                f"📊 <b>СТАТИСТИКА РАДЁМОК</b>\n\n"
                f"У тебя ещё не было радёмок!\n"
                f"Выбери цель и протащи кого-нибудь!\n\n"
                f"<i>Пока все думают, что ты мирный пацан...</i>"
            )
        
        await conn.close()
        
    except Exception as e:
        # Если таблицы rademka_fights не существует
        message_text = (
            f"📊 <b>СТАТИСТИКА РАДЁМОК</b>\n\n"
            f"База данных статистики готовится...\n"
            f"Проведи первую радёмку - статистика появится автоматически!\n\n"
            f"<i>Система учится считать твои победы!</i>"
        )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_rademka_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "rademka_top")
async def rademka_top(callback: types.CallbackQuery):
    """Топ радёмщиков (РЕАЛЬНЫЙ ТОП)"""
    try:
        conn = await get_connection()
        
        # Пробуем получить топ из базы
        cursor = await conn.execute('''
            SELECT 
                u.nickname,
                u.user_id,
                COUNT(CASE WHEN rf.winner_id = u.user_id THEN 1 END) as wins,
                COUNT(CASE WHEN rf.loser_id = u.user_id THEN 1 END) as losses,
                SUM(CASE WHEN rf.winner_id = u.user_id THEN rf.money_taken ELSE 0 END) as total_money_taken
            FROM users u
            LEFT JOIN rademka_fights rf ON u.user_id = rf.winner_id OR u.user_id = rf.loser_id
            GROUP BY u.user_id, u.nickname
            HAVING wins > 0
            ORDER BY wins DESC, total_money_taken DESC
            LIMIT 10
        ''')
        
        top_players = await cursor.fetchall()
        
        if top_players:
            message_text = "👑 <b>ТОП РАДЁМЩИКОВ</b>\n\n"
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for i, player in enumerate(top_players):
                if i >= len(medals):
                    break
                    
                medal = medals[i]
                nickname = player["nickname"]
                wins = player["wins"] or 0
                losses = player["losses"] or 0
                total = wins + losses
                win_rate = (wins / total * 100) if total > 0 else 0
                money = player["total_money_taken"] or 0
                
                # Обрезаем длинные ники
                if len(nickname) > 15:
                    nickname = nickname[:12] + "..."
                
                message_text += (
                    f"{medal} <code>{nickname}</code>\n"
                    f"   ✅ {wins} побед | 📈 {win_rate:.0f}% | 💰 {money}р\n\n"
                )
            
            message_text += "<i>Топ по количеству побед в радёмках</i>"
            
        else:
            message_text = (
                f"👑 <b>ТОП РАДЁМЩИКОВ</b>\n\n"
                f"Пока никого нет в топе!\n"
                f"Будь первым - протащи кого-нибудь!\n\n"
                f"<i>Слава ждёт самого дерзкого пацана!</i>"
            )
            
        await conn.close()
        
    except Exception as e:
        # Если таблицы нет или ошибка
        message_text = (
            f"👑 <b>ТОП РАДЁМЩИКОВ</b>\n\n"
            f"Рейтинг формируется...\n\n"
            f"Чтобы попасть в топ, нужно:\n"
            f"1. Провести несколько радёмок\n"
            f"2. Побеждать чаще, чем проигрывать\n"
            f"3. Отжимать больше денег\n\n"
            f"<i>Первые места скоро будут заняты!</i>"
        )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_rademka_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    patsan = await get_patsan_cached(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер в кишке: {patsan['atm_count']}/12",
        reply_markup=main_keyboard()
    )
