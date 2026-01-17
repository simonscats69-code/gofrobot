from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_manager import get_patsan_cached, change_nickname
from keyboards.keyboards import main_keyboard
from keyboards.new_keyboards import nickname_keyboard, rademka_keyboard, rademka_fight_keyboard, back_to_rademka_keyboard

router = Router()

# ==================== СМЕНА НИКА (FSM) ====================

class NicknameChange(StatesGroup):
    waiting_for_nickname = State()

@router.message(Command("nickname"))
async def cmd_nickname(message: types.Message, state: FSMContext):
    """Команда /nickname - смена ника"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
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
    
    await callback.message.edit_text(
        message_text,
        reply_markup=nickname_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(NicknameChange.waiting_for_nickname)
    await callback.answer()

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
    """Подтверждение радёмки"""
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
    
    if success:
        # УСПЕШНАЯ РАДЁМКА!
        
        # Награда: 10% денег цели
        money_reward = int(target["dengi"] * 0.1)
        attacker["dengi"] += money_reward
        target["dengi"] -= money_reward
        
        # Минимальная сумма у цели
        if target["dengi"] < 10:
            target["dengi"] = 10
        
        # +1 авторитет атакующему
        attacker["avtoritet"] += 1
        
        # Шанс забрать двенашку (30%)
        item_stolen = ""
        if target.get("inventory") and "двенашка" in target["inventory"] and random.random() < 0.3:
            target["inventory"].remove("двенашка")
            attacker["inventory"].append("двенашка")
            item_stolen = "\n🎒 <b>Забрал двенашку!</b>"
        
        result_text = (
            f"✅ <b>УСПЕШНАЯ РАДЁМКА!</b>\n\n"
            f"<i>ИДИ СЮДА РАДЁМКА БАЛЯ! ТЫ ПРОТАЩИЛ ЕГО!</i>\n\n"
            f"Ты унизил {target['nickname']} на глазах у всех!\n"
            f"⭐ <b>+1 авторитет</b> (теперь {attacker['avtoritet']})\n"
            f"💰 <b>+{money_reward}р</b> (отжал у пацана){item_stolen}\n\n"
            f"<i>Он теперь будет тебя бояться!</i>"
        )
        
        # Достижение за первую радёмку
        await unlock_achievement(user_id, "first_rademka", "Первая радёмка", 200)
        
        # Достижение за 10 радёмок (нужно будет добавить счётчик)
        
    else:
        # ПРОВАЛ РАДЁМКИ
        
        # Штраф: 5% денег атакующего
        money_penalty = int(attacker["dengi"] * 0.05)
        attacker["dengi"] -= money_penalty
        
        # -1 авторитет
        attacker["avtoritet"] = max(1, attacker["avtoritet"] - 1)
        
        # Шанс получить ответку (20%)
        revenge_text = ""
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
    
    # Сохраняем изменения
    await save_patsan(attacker)
    await save_patsan(target)
    
    await callback.message.edit_text(
        result_text,
        reply_markup=back_to_rademka_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "rademka_stats")
async def rademka_stats(callback: types.CallbackQuery):
    """Статистика радёмок"""
    # Пока заглушка - можно добавить реальную статистику
    message_text = (
        f"📊 <b>СТАТИСТИКА РАДЁМОК</b>\n\n"
        f"<i>В разработке...</i>\n\n"
        f"Скоро здесь появится:\n"
        f"• Твои победы/поражения\n"
        f"• Заработано на радёмках\n"
        f"• Самые частые цели\n"
        f"• Общая статистика по всем пацанам"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_rademka_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "rademka_top")
async def rademka_top(callback: types.CallbackQuery):
    """Топ радёмщиков"""
    # Пока заглушка - можно добавить реальный топ
    message_text = (
        f"👑 <b>ТОП РАДЁМЩИКОВ</b>\n\n"
        f"<i>В разработке...</i>\n\n"
        f"Скоро здесь появится рейтинг пацанов:\n"
        f"🥇 Кто больше всех протащил\n"
        f"🥈 Кто заработал больше всех\n"
        f"🥉 У кого лучший процент побед\n"
        f"💀 Самый отжимаемый пацан"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_rademka_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    patsan = await get_patsan_cached(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер в кишке: {patsan['atm_count']}/12",
        reply_markup=main_keyboard()
    )
