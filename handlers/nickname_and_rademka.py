from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
import time
import random
import re
from db_manager import get_patsan, change_nickname, get_connection, save_patsan, save_rademka_fight, get_top_players, get_gofra_info, calculate_pvp_chance, can_fight_pvp
from keyboards import main_keyboard, nickname_keyboard, rademka_keyboard, rademka_fight_keyboard, back_to_rademka_keyboard

router = Router()

class NicknameChange(StatesGroup):
    waiting_for_nickname = State()

def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try: 
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                if args and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise
    return wrapper

def validate_nickname(nickname):
    """Валидация ника"""
    if len(nickname) < 3 or len(nickname) > 20:
        return False, "Длина ника должна быть от 3 до 20 символов"
    
    banned_words = ["admin", "root", "support", "бот", "admin", "модератор", 
                    "админ", "support", "help", "техподдержка"]
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
async def cmd_nickname(m: types.Message, state: FSMContext):
    p = await get_patsan(m.from_user.id)
    c = 'Бесплатно (первый раз)' if not p.get('nickname_changed', False) else 'Больше нельзя'
    await m.answer(f"🏷️ НИКНЕЙМ И РЕПУТАЦИЯ\n\n🔤 Твой ник: {p.get('nickname','Неизвестно')}\n🏗️ Гофра: {p.get('gofra',1)}\n🔌 Кабель: {p.get('cable_power',1)}\n💸 Смена ника: {c}\n\nВыбери действие:", reply_markup=nickname_keyboard())

@router.callback_query(F.data == "nickname_menu")
async def nickname_menu(c: types.CallbackQuery):
    p = await get_patsan(c.from_user.id)
    cst = 'Бесплатно (первый раз)' if not p.get('nickname_changed', False) else 'Больше нельзя'
    await c.message.edit_text(f"🏷️ НИКНЕЙМ И РЕПУТАЦИЯ\n\n🔤 Твой ник: {p.get('nickname','Неизвестно')}\n🏗️ Гофра: {p.get('gofra',1)}\n🔌 Кабель: {p.get('cable_power',1)}\n💸 Смена ника: {cst}\n\nВыбери действие:", reply_markup=nickname_keyboard())
    await c.answer()

@router.callback_query(F.data == "my_reputation")
async def my_reputation(c: types.CallbackQuery):
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra',1))
    await c.message.edit_text(f"⭐ МОЯ РЕПУТАЦИЯ\n\n{gofra_info['emoji']} Звание: {gofra_info['name']}\n🏗️ Гофра: {p.get('gofra',1)}\n🔌 Кабель: {p.get('cable_power',1)}\n🐍 Змий: {p.get('zmiy_grams',0):.0f}г\n\nКак повысить?\n• Дави змия при полных атмосферах\n• Отправляй змия в коричневую страну\n• Участвуй в радёмках\n\nЧем выше гофра, тем больше уважения!", reply_markup=nickname_keyboard())
    await c.answer()

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
            gi = get_gofra_info(p.get('gofra',1))
            txt += f"{md} {nn} - {gi['emoji']} {gi['name']} ({p.get('gofra',0)})\n"
        uid = c.from_user.id
        for i, p in enumerate(tp):
            if p.get('user_id')==uid: 
                txt+=f"\n🎯 Твоя позиция: {mds[i] if i<len(mds) else str(i+1)}"
                break
        txt+=f"\n👥 Всего пацанов: {len(tp)}"
        await c.message.edit_text(txt, reply_markup=nickname_keyboard())
    await c.answer()

@router.callback_query(F.data == "change_nickname")
async def callback_change_nickname(c: types.CallbackQuery, state: FSMContext):
    p = await get_patsan(c.from_user.id)
    if await state.get_state() == NicknameChange.waiting_for_nickname.state:
        return await c.answer("Ты уже в процессе смены ника!", show_alert=True)
    
    nc = p.get("nickname_changed", False)
    txt = f"✏️ СМЕНА НИКА\n\nТвой текущий ник: {p.get('nickname','Неизвестно')}\n"
    
    if nc:
        txt += f"❌ Ты уже менял ник.\nБольше нельзя сменить ник.\n"
        await c.answer(txt, show_alert=True)
        return
    else:
        txt += f"🎁 Первая смена - БЕСПЛАТНО!\n\n"
        txt += f"Правила ника:\n"
        txt += f"• 3-20 символов\n"
        txt += f"• Буквы, цифры, пробелы, дефисы, подчёркивания\n"
        txt += f"• Без запрещённых слов (admin, бот и т.д.)\n"
        txt += f"• Без лишних пробелов\n\n"
        txt += f"Напиши новый ник:"
    
    await c.message.answer(txt, reply_markup=nickname_keyboard())
    await state.set_state(NicknameChange.waiting_for_nickname)
    await c.answer("Введи новый ник")

@router.message(NicknameChange.waiting_for_nickname)
async def process_nickname(m: types.Message, state: FSMContext):
    nn = m.text.strip()
    
    is_valid, error_msg = validate_nickname(nn)
    if not is_valid:
        await m.answer(f"❌ {error_msg}\n\nПопробуй другой ник:")
        return
    
    ok, msg = await change_nickname(m.from_user.id, nn)
    if ok:
        await m.answer(f"✅ {msg}\nТеперь ты: {nn}", reply_markup=main_keyboard())
    else:
        await m.answer(f"❌ {msg}\nПопробуй другой:", reply_markup=main_keyboard())
    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(m: types.Message, state: FSMContext):
    if await state.get_state() is None: 
        return await m.answer("Нечего отменять.")
    await state.clear()
    await m.answer("Смена ника отменена.", reply_markup=main_keyboard())

@router.message(Command("rademka"))
async def cmd_rademka(m: types.Message):
    p = await get_patsan(m.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra',1))
    
    can_fight, fight_msg = await can_fight_pvp(m.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"
    
    txt = f"👊 ПРОТАЩИТЬ КАК РАДЁМКУ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ!\n\n{fight_status}\n\nВыбери пацана и протащи его по гофроцентралу!\nЗа успешную радёмку получишь:\n• +1 к силе кабеля\n• +50 к гофре\n• Шанс унизить публично\n\nРиски:\n• Можешь опозориться перед всеми\n• Потеряешь уважение\n\nТвои статы:\n{gofra_info['emoji']} {gofra_info['name']}\n🏗️ {p.get('gofra',1)}\n🔌 {p.get('cable_power',1)}"
    await m.answer(txt, reply_markup=rademka_keyboard())

@ignore_not_modified_error
@router.callback_query(F.data == "rademka")
async def callback_rademka(c: types.CallbackQuery):
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra',1))
    
    can_fight, fight_msg = await can_fight_pvp(c.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"
    
    await c.message.edit_text(f"👊 ПРОТАЩИТЬ КАК РАДЁМКУ!\n\n{fight_status}\n\nВыбери пацана!\nЗа успех: +1 к кабелю, +50 к гофре, публичное унижение\n\nРиски: публичный позор\n\nТвои статы:\n{gofra_info['emoji']} {gofra_info['name']}\n🏗️ {p.get('gofra',1)} | 🔌 {p.get('cable_power',1)}", reply_markup=rademka_keyboard())
    await c.answer()

@router.callback_query(F.data == "rademka_random")
async def rademka_random(c: types.CallbackQuery):
    can_fight, fight_msg = await can_fight_pvp(c.from_user.id)
    if not can_fight:
        await c.answer(f"❌ {fight_msg}", show_alert=True)
        return
    
    tp = await get_top_players(limit=50, sort_by="gofra")
    tg = [p for p in tp if p.get("user_id")!=c.from_user.id]
    if not tg: 
        return await c.message.edit_text("😕 НЕКОГО ПРОТАЩИВАТЬ!\n\nПриведи друзей!", reply_markup=back_to_rademka_keyboard())
    
    t = random.choice(tg)
    pid, tn = t.get("user_id"), t.get("nickname","Неизвестно")
    tgofra = t.get("gofra",1)
    tcable = t.get("cable_power",1)
    
    p = await get_patsan(c.from_user.id)
    mgofra = p.get("gofra",1)
    mcable = p.get("cable_power",1)
    
    chance = calculate_pvp_chance(p, t)
    
    tgofra_info = get_gofra_info(tgofra)
    mgofra_info = get_gofra_info(mgofra)
    
    await c.message.edit_text(f"🎯 НАШЁЛ ЦЕЛЬ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ!\n\n👤 Цель: {tn}\n{tgofra_info['emoji']} {tgofra_info['name']}\n🏗️ {tgofra} | 🔌 {tcable}\n\n👤 Ты: {mgofra_info['emoji']} {mgofra_info['name']}\n🏗️ {mgofra} | 🔌 {mcable}\n🎯 Шанс: {chance}%\n\nНаграда: +1 к кабелю, +50 к гофре\nРиск: позор\n\nПротащить?", reply_markup=rademka_fight_keyboard(pid))
    await c.answer()

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
    
    chance = calculate_pvp_chance(a, t)
    suc = random.random() < (chance/100)
    
    if suc:
        a["cable_power"] = a.get("cable_power",1) + 1
        exp_gain = 50
        a["gofra"] = a.get("gofra",1) + exp_gain
        
        txt = f"✅ УСПЕХ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ! ТЫ ПРОТАЩИЛ!\n\nТы унизил {t.get('nickname','Неизвестно')}!\n🔌 +1 к кабелю (теперь {a.get('cable_power',1)})\n🏗️ +{exp_gain} к гофре (теперь {a.get('gofra',1)})\n🎯 Шанс был: {chance}%\nОн теперь боится!"
    else:
        txt = f"❌ ПРОВАЛ!\n\nСам оказался радёмкой...\n\n{t.get('nickname','Неизвестно')} круче!\n🎯 Шанс был: {chance}%\nТеперь смеются..."
    
    await save_patsan(a)
    await save_patsan(t)
    await save_rademka_fight(winner_id=uid if suc else tid, loser_id=tid if suc else uid, money_taken=0)
    
    await c.message.edit_text(txt, reply_markup=back_to_rademka_keyboard())
    await c.answer()

@router.callback_query(F.data == "rademka_stats")
async def rademka_stats(c: types.CallbackQuery):
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT COUNT(*) as tf, SUM(CASE WHEN winner_id=? THEN 1 ELSE 0 END) as w, SUM(CASE WHEN loser_id=? THEN 1 ELSE 0 END) as l FROM rademka_fights WHERE winner_id=? OR loser_id=?', (c.from_user.id,)*4)
        s = await cur.fetchone()
        if s and s.get("tf") and s["tf"]>0:
            t, w, l = s["tf"], s.get("w",0) or 0, s.get("l",0) or 0
            wr = (s.get("w",0)/s["tf"]*100) if s["tf"]>0 else 0
            
            cur2 = await cn.execute('SELECT COUNT(*) as hour_fights FROM rademka_fights WHERE (winner_id=? OR loser_id=?) AND created_at > ?', 
                                   (c.from_user.id, c.from_user.id, int(time.time()) - 3600))
            hour_row = await cur2.fetchone()
            hour_fights = hour_row['hour_fights'] if hour_row else 0
            
            txt = f"📊 СТАТИСТИКА РАДЁМОК\n\n"
            txt += f"🎲 Всего: {t}\n"
            txt += f"✅ Побед: {w}\n"
            txt += f"❌ Поражений: {l}\n"
            txt += f"📈 Винрейт: {wr:.1f}%\n"
            txt += f"⏱️ За час: {hour_fights}/10 боёв\n\n"
            txt += f"Лимит: 10 боёв в час"
        else: 
            txt = f"📊 СТАТИСТИКА РАДЁМОК\n\nНет радёмок!\nВыбери цель!\n\nПока мирный пацан..."
        await cn.close()
    except Exception as e:
        print(f"Ошибка статистики: {e}")
        txt = f"📊 СТАТИСТИКА РАДЁМОК\n\nБаза готовится...\n\nСистема учится считать!"
    await c.message.edit_text(txt, reply_markup=back_to_rademka_keyboard())
    await c.answer()

@router.callback_query(F.data == "rademka_top")
async def rademka_top(c: types.CallbackQuery):
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT u.nickname, u.user_id, u.gofra, u.cable_power, COUNT(CASE WHEN rf.winner_id=u.user_id THEN 1 END) as w, COUNT(CASE WHEN rf.loser_id=u.user_id THEN 1 END) as l FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id OR u.user_id=rf.loser_id GROUP BY u.user_id, u.nickname, u.gofra, u.cable_power HAVING w>0 ORDER BY w DESC LIMIT 10')
        tp = await cur.fetchall()
        if tp:
            mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 ТОП РАДЁМЩИКОВ\n\n"
            for i, p in enumerate(tp):
                if i>=len(mds): 
                    break
                md, nn, w, l, gofra, cable = mds[i], p.get("nickname","Неизвестно"), p.get("w",0) or 0, p.get("l",0) or 0, p.get("gofra",1), p.get("cable_power",1)
                gofra_info = get_gofra_info(gofra)
                if len(nn)>15: 
                    nn=nn[:12]+"..."
                win_rate = 0 if w+l==0 else (w/(w+l)*100)
                txt+=f"{md} {nn} {gofra_info['emoji']}\n   🏗️ {gofra} | 🔌 {cable} | ✅ {w} ({win_rate:.0f}%)\n\n"
            txt+="Топ по победам"
        else: 
            txt = f"🥇 ТОП РАДЁМЩИКОВ\n\nПока никого!\nБудь первым!\n\nСлава ждёт!"
        await cn.close()
    except Exception as e:
        print(f"Ошибка топа: {e}")
        txt = f"🥇 ТОП РАДЁМЩИКОВ\n\nРейтинг формируется...\n\nМеста скоро будут!"
    await c.message.edit_text(txt, reply_markup=back_to_rademka_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(c: types.CallbackQuery):
    try:
        p = await get_patsan(c.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra',1))
        await c.message.edit_text(f"Главное меню\n{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {p.get('gofra',1)} | 🔌 {p.get('cable_power',1)}\n\n🌀 Атмосферы: {p.get('atm_count',0)}/12\n🐍 Змий: {p.get('zmiy_grams',0):.0f}г\n\nВыбери действие:", reply_markup=main_keyboard())
    except Exception as e: 
        print(f"Ошибка главного: {e}")
        await c.message.edit_text("Главное меню\n\nБот работает!", reply_markup=main_keyboard())

__all__ = ["router", "process_nickname"]
