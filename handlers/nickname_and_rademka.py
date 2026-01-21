from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
import time
import random
from database.db_manager import (get_patsan_cached, change_nickname, get_connection, 
                                get_patsan, save_patsan, save_rademka_fight, 
                                get_top_players, get_specialization_bonuses, 
                                check_level_up, get_rank)
from keyboards.keyboards import (main_keyboard, nickname_keyboard, rademka_keyboard, 
                                rademka_fight_keyboard, back_to_rademka_keyboard, 
                                daily_keyboard)

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

@router.message(Command("nickname"))
async def cmd_nickname(m: types.Message, state: FSMContext):
    p = await get_patsan_cached(m.from_user.id)
    c = 'Бесплатно (первый раз)' if not p.get('nickname_changed', False) else '5000 руб.'
    await m.answer(f"🏷️ <b>НИКНЕЙМ И РЕПУТАЦИЯ</b>\n\n🔤 <b>Твой ник:</b> <code>{p.get('nickname','Неизвестно')}</code>\n⭐ <b>Авторитет:</b> {p.get('avtoritet',1)}\n💸 <b>Стоимость смены ника:</b> {c}\n\n<i>Выбери действие:</i>", reply_markup=nickname_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "nickname_menu")
async def nickname_menu(c: types.CallbackQuery):
    p = await get_patsan_cached(c.from_user.id)
    cst = 'Бесплатно (первый раз)' if not p.get('nickname_changed', False) else '5000 руб.'
    await c.message.edit_text(f"🏷️ <b>НИКНЕЙМ И РЕПУТАЦИЯ</b>\n\n🔤 <b>Твой ник:</b> <code>{p.get('nickname','Неизвестно')}</code>\n⭐ <b>Авторитет:</b> {p.get('avtoritet',1)}\n💸 <b>Стоимость смены ника:</b> {cst}\n\n<i>Выбери действие:</i>", reply_markup=nickname_keyboard(), parse_mode="HTML")
    await c.answer()

@router.callback_query(F.data == "my_reputation")
async def my_reputation(c: types.CallbackQuery):
    p = await get_patsan_cached(c.from_user.id)
    rn, re = get_rank(p.get('avtoritet',1))
    await c.message.edit_text(f"⭐ <b>МОЯ РЕПУТАЦИЯ</b>\n\n{re} <b>Звание:</b> {rn}\n🏆 <b>Авторитет:</b> {p.get('avtoritet',1)}\n\n<b>Как повысить?</b>\n• Побеждай в радёмках (+1)\n• Покупай курвасаны (+2)\n• Выполняй достижения\n\n<i>Чем выше авторитет, тем больше уважения!</i>", reply_markup=nickname_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "top_reputation")
async def top_reputation(c: types.CallbackQuery):
    tp = await get_top_players(limit=10, sort_by="avtoritet")
    if not tp: 
        await c.message.edit_text("🥇 <b>ТОП АВТОРИТЕТА</b>\n\nПока никого нет в топе!\nБудь первым!\n\n<i>Слава ждёт!</i>", reply_markup=nickname_keyboard(), parse_mode="HTML")
    else:
        mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 <b>ТОП АВТОРИТЕТА</b>\n\n"
        for i, p in enumerate(tp):
            md = mds[i] if i<len(mds) else f"{i+1}."
            nn = p.get("nickname", f"Пацан_{p.get('user_id','?')}")[:12]+("..." if len(p.get('nickname',''))>15 else "")
            txt += f"{md} <code>{nn}</code> - ⭐ {p.get('avtoritet',0)}\n"
        uid = c.from_user.id
        for i, p in enumerate(tp):
            if p.get('user_id')==uid: 
                txt+=f"\n🎯 <b>Твоя позиция:</b> {mds[i] if i<len(mds) else str(i+1)}"
                break
        txt+=f"\n👥 <i>Всего пацанов: {len(tp)}</i>"
        await c.message.edit_text(txt, reply_markup=nickname_keyboard(), parse_mode="HTML")
    await c.answer()

@router.callback_query(F.data == "change_nickname")
async def callback_change_nickname(c: types.CallbackQuery, state: FSMContext):
    p = await get_patsan_cached(c.from_user.id)
    if await state.get_state() == NicknameChange.waiting_for_nickname.state:
        return await c.answer("Ты уже в процессе смены ника!", show_alert=True)
    nc, cost = p.get("nickname_changed", False), 0 if not p.get("nickname_changed", False) else 5000
    txt = (f"✏️ <b>СМЕНА НИКА</b>\n\nТвой текущий ник: <code>{p.get('nickname','Неизвестно')}</code>\n" +
           (f"Ты уже менял ник.\nСтоимость: <b>{cost} руб.</b>\n" if nc else f"🎁 <b>Первая смена - БЕСПЛАТНО!</b>\nПотом 5000 руб.\n") +
           f"\nНапиши новый ник (3-20 символов, буквы и цифры):")
    await c.message.answer(txt, reply_markup=nickname_keyboard(), parse_mode="HTML")
    await state.set_state(NicknameChange.waiting_for_nickname)
    await c.answer("Введи новый ник")

@router.message(NicknameChange.waiting_for_nickname)
async def process_nickname(m: types.Message, state: FSMContext):
    nn = m.text.strip()
    if len(nn)<3: 
        return await m.answer("❌ Слишком короткий! Минимум 3 символа.\nПопробуй:")
    if len(nn)>20: 
        return await m.answer("❌ Слишком длинный! Максимум 20 символов.\nПопробуй:")
    if not all(c.isalnum() or c in "_- " for c in nn): 
        return await m.answer("❌ Только буквы, цифры, пробелы, дефисы, подчёркивания!\nПопробуй:")
    ok, msg = await change_nickname(m.from_user.id, nn)
    if ok:
        await m.answer(f"✅ {msg}\nТеперь ты: <code>{nn}</code>", reply_markup=main_keyboard(), parse_mode="HTML")
    else:
        await m.answer(f"❌ {msg}\nПопробуй:", reply_markup=main_keyboard(), parse_mode="HTML")
    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(m: types.Message, state: FSMContext):
    if await state.get_state() is None: 
        return await m.answer("Нечего отменять.")
    await state.clear()
    await m.answer("Смена ника отменена.", reply_markup=main_keyboard())

@router.message(Command("rademka"))
async def cmd_rademka(m: types.Message):
    p = await get_patsan_cached(m.from_user.id)
    txt = (f"👊 <b>ПРОТАЩИТЬ КАК РАДЁМКУ!</b>\n\n<i>ИДИ СЮДА РАДЁМКУ БАЛЯ!</i>\n\nВыбери пацана и протащи его по гофроцентралу!\nЗа успешную радёмку получишь:\n• +1 авторитет\n• 10% его денег\n• Шанс забрать двенашку\n\n<b>Риски:</b>\n• Можешь потерять 5% своих денег\n• -1 авторитет при неудаче\n• Отжатый пацан может отомстить\n\n<b>Твои статы:</b>\n⭐ {p.get('avtoritet',1)}\n💰 {p.get('dengi',0)}р\n📈 {p.get('level',1)}")
    await m.answer(txt, reply_markup=rademka_keyboard(), parse_mode="HTML")

@ignore_not_modified_error
@router.callback_query(F.data == "rademka")
async def callback_rademka(c: types.CallbackQuery):
    p = await get_patsan_cached(c.from_user.id)
    await c.message.edit_text(f"👊 <b>ПРОТАЩИТЬ КАК РАДЁМКУ!</b>\n\n<i>ИДИ СЮДА РАДЁМКУ БАЛЯ!</i>\n\nВыбери пацана!\nЗа успех: +1 авторитет, 10% его денег, шанс на двенашку\n\nРиски: -5% денег, -1 авторитет\n\n<b>Твои статы:</b>\n⭐ {p.get('avtoritet',1)} | 💰 {p.get('dengi',0)}р | 📈 {p.get('level',1)}", reply_markup=rademka_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "rademka_random")
async def rademka_random(c: types.CallbackQuery):
    tp = await get_top_players(limit=50, sort_by="avtoritet")
    tg = [p for p in tp if p.get("user_id")!=c.from_user.id]
    if not tg: 
        return await c.message.edit_text("😕 <b>НЕКОГО ПРОТАЩИВАТЬ!</b>\n\nПриведи друзей!", reply_markup=back_to_rademka_keyboard(), parse_mode="HTML")
    t = random.choice(tg)
    pid, tn, tav = t.get("user_id"), t.get("nickname","Неизвестно"), t.get("avtoritet",1)
    p = await get_patsan_cached(c.from_user.id)
    av, ch = p.get("avtoritet",1), 50
    if av > tav: 
        ch += min(30, (av-tav)*5)
    elif tav > av: 
        ch += 20-min(30, (tav-av)*5)
    if p.get("specialization")=="neprobivaemy": 
        ch += 5
    td = await get_patsan(pid)
    if td and time.time()-td.get("last_update", time.time())>86400: 
        ch += 15
    ch = max(10, min(95, ch))
    ar, ae = get_rank(av); tr, te = get_rank(tav)
    tm = t.get('dengi_formatted', t.get('dengi',0))
    await c.message.edit_text(f"🎯 <b>НАШЁЛ ЦЕЛЬ!</b>\n\n<i>ИДИ СЮДА РАДЁМКУ БАЛЯ!</i>\n\n👤 <b>Цель:</b> {tn}\n{te} <b>Звание:</b> {tr}\n⭐ {tav} | 💰 {tm}р | 📈 {t.get('level',1)}\n\n👤 <b>Ты:</b> {ae} {ar}\n⭐ {av}\n🎯 <b>Шанс:</b> {ch}%\n\n<b>Награда:</b> +1 авторитет, 10% его денег\n<b>Риск:</b> -1 авторитет, -5% денег\n\nПротащить?", reply_markup=rademka_fight_keyboard(pid), parse_mode="HTML")

@router.callback_query(F.data.startswith("rademka_confirm_"))
async def rademka_confirm(c: types.CallbackQuery):
    uid, tid = c.from_user.id, int(c.data.replace("rademka_confirm_", ""))
    a, t = await get_patsan(uid), await get_patsan(tid)
    if not a or not t: 
        return await c.answer("Ошибка: пацан не найден!", show_alert=True)
    ch = 50 + (a.get("avtoritet",1)-t.get("avtoritet",1))*5
    if a.get("avtoritet",1)<t.get("avtoritet",1): 
        ch+=20
    if a.get("specialization")=="neprobivaemy": 
        ch+=5
    if t.get("level",1)>a.get("level",1): 
        ch-=min(15, (t.get("level",1)-a.get("level",1))*3)
    if time.time()-t.get("last_update", time.time())>86400: 
        ch+=15
    ch = max(10, min(95, ch))
    suc = random.random() < (ch/100)
    mt, it, eg = 0, None, 0
    
    if suc:
        mt = int(t.get("dengi",0)*0.1)
        a["dengi"] = a.get("dengi",0) + mt
        t["dengi"] = max(10, t.get("dengi",0) - mt)
        a["avtoritet"] = a.get("avtoritet",1) + 1
        if t.get("inventory") and "двенашка" in t["inventory"] and random.random()<0.3:
            t["inventory"].remove("двенашка")
            a["inventory"].append("двенашка")
            it="двенашка"
        eg = 25+(t.get("avtoritet",1)//10)
        a["experience"] = a.get("experience",0) + eg
        if t.get("avtoritet",1) > a.get("avtoritet",1):
            be = (t.get("avtoritet",1) - a.get("avtoritet",1)) * 2
            a["experience"] += be
            eg += be
        
        item_text = '\n🎁 <b>Забрал двенашку!</b>' if it else ''
        txt = f"✅ <b>УСПЕХ!</b>\n\n<i>ИДИ СЮДА РАДЁМКУ БАЛЯ! ТЫ ПРОТАЩИЛ!</i>\n\nТы унизил {t.get('nickname','Неизвестно')}!\n⭐ <b>+1 авторитет</b> (теперь {a.get('avtoritet',1)})\n💰 <b>+{mt}р</b>\n📚 <b>+{eg} опыта</b>{item_text}\n🎯 <b>Шанс:</b> {ch}%\n<i>Он теперь боится!</i>"
    else:
        mp = int(a.get("dengi",0)*0.05)
        a["dengi"] = a.get("dengi",0) - mp
        a["avtoritet"] = max(1, a.get("avtoritet",1) - 1)
        eg, rt = 5, ""
        if random.random()<0.2:
            rm = int(a.get("dengi",0)*0.05)
            a["dengi"] = a.get("dengi",0) - rm
            t["dengi"] = t.get("dengi",0) + rm
            rt = f"\n💥 <b>Он отомстил и забрал {rm}р!</b>"
        a["experience"] = a.get("experience",0) + eg
        
        txt = f"❌ <b>ПРОВАЛ!</b>\n\n<i>Сам оказался радёмкой...</i>\n\n{t.get('nickname','Неизвестно')} круче!\n⭐ <b>-1 авторитет</b> (теперь {a.get('avtoritet',1)})\n💰 <b>-{mp}р</b>\n📚 <b>+{eg} опыта</b>{rt}\n🎯 <b>Шанс:</b> {ch}%\n<i>Теперь смеются...</i>"
    
    await save_patsan(a)
    await save_patsan(t)
    await save_rademka_fight(winner_id=uid if suc else tid, loser_id=tid if suc else uid, money_taken=mt, item_stolen=it, scouted=False)
    
    lup, ltxt = await check_level_up(a), ""
    if lup[0]: 
        ltxt = f"\n\n🎉 <b>ПОВЫШЕНИЕ УРОВНЯ!</b> Теперь ты {a.get('level',1)} уровня!"
        await save_patsan(a)
    
    await c.message.edit_text(txt + ltxt, reply_markup=back_to_rademka_keyboard(), parse_mode="HTML")
    await c.answer()

@router.callback_query(F.data == "rademka_stats")
async def rademka_stats(c: types.CallbackQuery):
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT COUNT(*) as tf, SUM(CASE WHEN winner_id=? THEN 1 ELSE 0 END) as w, SUM(CASE WHEN loser_id=? THEN 1 ELSE 0 END) as l, SUM(CASE WHEN winner_id=? THEN money_taken ELSE 0 END) as mt, SUM(CASE WHEN loser_id=? THEN money_taken ELSE 0 END) as ml FROM rademka_fights WHERE winner_id=? OR loser_id=?', (c.from_user.id,)*6)
        s = await cur.fetchone()
        if s and s.get("tf") and s["tf"]>0:
            t, w, l, mt, ml = s["tf"], s.get("w",0) or 0, s.get("l",0) or 0, s.get("mt",0) or 0, s.get("ml",0) or 0
            wr = (s.get("w",0)/s["tf"]*100) if s["tf"]>0 else 0
            txt = f"📊 <b>СТАТИСТИКА РАДЁМОК</b>\n\n🎲 <b>Всего:</b> {t}\n✅ <b>Побед:</b> {w}\n❌ <b>Поражений:</b> {l}\n📈 <b>Винрейт:</b> {wr:.1f}%\n💰 <b>Отжато:</b> {mt}р\n💸 <b>Потеряно:</b> {ml}р\n💎 <b>Прибыль:</b> {mt-ml}р\n\n"
            if w>0:
                cur = await cn.execute('SELECT loser_id, COUNT(*) as f, SUM(money_taken) as tm FROM rademka_fights WHERE winner_id=? GROUP BY loser_id ORDER BY f DESC, tm DESC LIMIT 3', (c.from_user.id,))
                tt = await cur.fetchall()
                if tt:
                    txt+="<b>🎯 Любимые цели:</b>\n"
                    for i, tg in enumerate(tt,1):
                        cur2 = await cn.execute("SELECT nickname, avtoritet FROM users WHERE user_id=?", (tg.get("loser_id"),))
                        tu = await cur2.fetchone()
                        nn = (tu.get("nickname") if tu else f"Пацан_{tg.get('loser_id')}")[:17]+("..." if len(tu.get('nickname',''))>20 else "")
                        txt+=f"{i}. {nn} (⭐{tu.get('avtoritet',1) if tu else 1}) - {tg.get('f',0)} раз, +{tg.get('tm',0) or 0}р\n"
            if l>0:
                cur = await cn.execute('SELECT winner_id, COUNT(*) as f, SUM(money_taken) as tm FROM rademka_fights WHERE loser_id=? GROUP BY winner_id ORDER BY f DESC, tm DESC LIMIT 2', (c.from_user.id,))
                to = await cur.fetchall()
                if to:
                    txt+="\n<b>💥 Противники:</b>\n"
                    for i, op in enumerate(to,1):
                        cur2 = await cn.execute("SELECT nickname FROM users WHERE user_id=?", (op.get("winner_id"),))
                        ou = await cur2.fetchone()
                        nn = (ou.get("nickname") if ou else f"Пацан_{op.get('winner_id')}")[:17]+("..." if len(ou.get('nickname',''))>20 else "")
                        txt+=f"{i}. {nn} - {op.get('f',0)} раз, -{op.get('tm',0) or 0}р\n"
        else: 
            txt = f"📊 <b>СТАТИСТИКА РАДёМОК</b>\n\nНет радёмок!\nВыбери цель!\n\n<i>Пока мирный пацан...</i>"
        await cn.close()
    except Exception as e:
        print(f"Ошибка статистики: {e}")
        txt = f"📊 <b>СТАТИСТИКА РАДЁМОК</b>\n\nБаза готовится...\n\n<i>Система учится считать!</i>"
    await c.message.edit_text(txt, reply_markup=back_to_rademka_keyboard(), parse_mode="HTML")
    await c.answer()

@router.callback_query(F.data == "rademka_top")
async def rademka_top(c: types.CallbackQuery):
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT u.nickname, u.user_id, u.avtoritet, u.level, COUNT(CASE WHEN rf.winner_id=u.user_id THEN 1 END) as w, COUNT(CASE WHEN rf.loser_id=u.user_id THEN 1 END) as l, SUM(CASE WHEN rf.winner_id=u.user_id THEN rf.money_taken ELSE 0 END) as tm FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id OR u.user_id=rf.loser_id GROUP BY u.user_id, u.nickname, u.avtoritet, u.level HAVING w>0 ORDER BY w DESC, tm DESC LIMIT 10')
        tp = await cur.fetchall()
        if tp:
            mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 <b>ТОП РАДЁМЩИКОВ</b>\n\n"
            for i, p in enumerate(tp):
                if i>=len(mds): 
                    break
                md, nn, w, l, tm, av, lv = mds[i], p.get("nickname","Неизвестно"), p.get("w",0) or 0, p.get("l",0) or 0, p.get("tm",0) or 0, p.get("avtoritet",1), p.get("level",1) or 1
                rn, re = get_rank(av)
                if len(nn)>15: 
                    nn=nn[:12]+"..."
                win_rate = 0 if w+l==0 else (w/(w+l)*100)
                txt+=f"{md} <code>{nn}</code> {re}\n   📈 {lv} ур. | ⭐ {av}\n   ✅ {w} ({win_rate:.0f}%) | 💰 {tm}р\n\n"
            txt+="<i>Топ по победам</i>"
        else: 
            txt = f"🥇 <b>ТОП РАДЁМЩИКОВ</b>\n\nПока никого!\nБудь первым!\n\n<i>Слава ждёт!</i>"
        await cn.close()
    except Exception as e:
        print(f"Ошибка топа: {e}")
        txt = f"🥇 <b>ТОП РАДЁМЩИКОВ</b>\n\nРейтинг формируется...\n\n<i>Места скоро будут!</i>"
    await c.message.edit_text(txt, reply_markup=back_to_rademka_keyboard(), parse_mode="HTML")
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(c: types.CallbackQuery):
    try:
        p = await get_patsan_cached(c.from_user.id)
        a, m = p.get('atm_count',0), p.get('max_atm',12)
        pb_fill = int((a/m)*10) if m>0 else 0
        pb_empty = 10 - pb_fill
        progress_bar = "█" * pb_fill + "░" * pb_empty
        rn, re = p.get('rank_name','Пацанчик'), p.get('rank_emoji','👶')
        await c.message.edit_text(f"<b>Главное меню</b>\n{re} <b>{rn}</b> | ⭐ {p.get('avtoritet',1)} | 📈 Ур. {p.get('level',1)}\n\n🌀 Атмосферы: [{progress_bar}] {a}/{m}\n💸 {p.get('dengi',0)}р | 🐍 {p.get('zmiy',0.0):.1f}кг\n\n<i>Выбери действие:</i>", reply_markup=main_keyboard(), parse_mode="HTML")
    except Exception as e: 
        print(f"Ошибка главного: {e}")
        await c.message.edit_text("<b>Главное меню</b>\n\nБот работает!", reply_markup=main_keyboard(), parse_mode="HTML")

__all__ = ["router", "process_nickname"]
