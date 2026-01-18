from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram import BaseMiddleware
import time, random
from database.db_manager import *
from keyboards.keyboards import *

router = Router()

# =================== УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ===================
async def edit_or_answer(c, text, kb=None, parse="HTML"):
    try: await c.message.edit_text(text, reply_markup=kb, parse_mode=parse)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e): raise

def pb(current, total, length=10): 
    filled = int((current/total)*length) if total>0 else 0
    return "█"*filled + "░"*(length-filled)

def ft(sec):
    if sec<60: return f"{sec}с"
    m, h = sec//60, sec//3600
    return f"{h}ч {m%60}м" if h>0 else f"{m}м {sec%60}с"

def get_emoji(item):
    emoji_map = {"двенашка":"🧱","атмосфера":"🌀","энергетик":"⚡","перчатки":"🧤",
                 "швабра":"🧹","ведро":"🪣","золотая_двенашка":"🌟","кристалл_атмосферы":"💎",
                 "секретная_схема":"📜","супер_двенашка":"✨","вечный_двигатель":"⚙️",
                 "царский_обед":"👑","бустер_атмосфер":"🌀"}
    return emoji_map.get(item, "📦")

# =================== МИДЛВАРЬ ===================
class IgnoreNotModifiedMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try: return await handler(event, data)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e) or ("Bad Request" in str(e) and "exactly the same" in str(e)):
                if cb := data.get('callback_query', getattr(event, 'callback_query', None)):
                    if hasattr(cb, 'answer'): await cb.answer()
                return
            raise

router.callback_query.middleware(IgnoreNotModifiedMiddleware())

# =================== ОБРАБОТЧИКИ ===================
async def mm_text(p):
    atm, max_a = p.get('atm_count',0), p.get('max_atm',12)
    return (f"<b>Главное меню</b>\n{p.get('rank_emoji','👶')} <b>{p.get('rank_name','Пацанчик')}</b> | ⭐ {p.get('avtoritet',1)} | 📈 Ур. {p.get('level',1)}\n\n"
            f"🌀 Атмосферы: [{pb(atm,max_a)}] {atm}/{max_a}\n💸 Деньги: {p.get('dengi',0)}р | 🐍 Змий: {p.get('zmiy',0):.1f}кг\n\n<i>Выбери действие, пацан:</i>")

@router.callback_query(F.data == "back_main")
async def back_main(c):
    await edit_or_answer(c, await mm_text(await get_patsan_cached(c.from_user.id)), main_keyboard())

@router.callback_query(F.data == "nickname_menu")
async def nickname_menu(c):
    try:
        p = await get_patsan_cached(c.from_user.id)
        cost = "Бесплатно (первый раз)" if not p.get('nickname_changed',False) else "5000 руб."
        await edit_or_answer(c, f"👤 <b>НИКНЕЙМ И РЕПУТАЦИЯ</b>\n\n📝 <b>Твой ник:</b> <code>{p.get('nickname','Неизвестно')}</code>\n⭐ <b>Авторитет:</b> {p.get('avtoritet',1)}\n💰 <b>Стоимость смены ника:</b> {cost}\n\n<i>Выбери действие:</i>", nickname_keyboard())
    except Exception as e:
        print(f"Ошибка nickname_menu: {e}")
        await c.answer("Ошибка при загрузке меню", show_alert=True)

ACTION_HANDLERS = {
    "davka": {"func": davka_zmiy, "t": """<b>Заварвариваем дело...</b>{nm}{sm}
🔄 Потрачено атмосфер: {cost}
<i>"{wm} говна за 25 секунд высрал я сейчас"</i>
➕ {tg:.3f} кг коричневага{dm}{rm}{em}
Всего змия накоплено: {zmiy:.3f} кг
⚡ Осталось атмосфер: {atm_count}/{max_atm}"""},
    "sdat": {"func": sdat_zmiy, "t": """<b>Сдал коричневага на металлолом</b>
📦 Сдано: {oz:.3f} кг змия
💰 <b>Получил: {tm} руб.</b>{abt}{em}
💸 Теперь на кармане: {dengi} руб.
📈 Уровень: {level} ({experience}/?? опыта)
<i>Приёмщик: "Опять эту дрянь принёс... Но плачу больше!"</i>"""}
}

async def handle_act(c, act):
    h = ACTION_HANDLERS.get(act)
    if not h: return
    uid = c.from_user.id
    p, r = await h["func"](uid)
    if p is None:
        await c.answer(r, show_alert=True)
        return
    ex = {}
    if act == "davka":
        up = p.get("upgrades",{})
        ex["nm"] = "\n🥛 <i>Ряженка жмёт двенашку как надо! (+75%)</i>" if up.get("ryazhenka") else "\n🧋 <i>Бублэки создают нужную турбулентность! (+35% к шансу)</i>" if up.get("bubbleki") else ""
        ex["sm"] = "\n💪 <b>Специализация 'Давила': +50% к давке!</b>" if p.get("specialization") == "давила" else ""
        ex["dm"] = "\n✨ <b>Нашёл двенашку в турбулентности!</b>" if r.get("dvenashka_found") else ""
        ex["rm"] = f"\n🌟 <b>Редкая находка: {r['rare_item_found']}!</b>" if r.get("rare_item_found") else ""
        ex["em"] = f"\n📚 +{r.get('exp_gained',0)} опыта" if r.get('exp_gained',0) > 0 else ""
        ex["tg"] = r.get('total_grams',0) / 1000
    elif act == "sdat":
        ex["abt"] = f"\n⭐ <b>Бонус авторитета:</b> +{r['avtoritet_bonus']}р" if r.get('avtoritet_bonus',0) > 0 else ""
        ex["em"] = f"\n📚 +{r.get('exp_gained',0)} опыта" if r.get('exp_gained',0) > 0 else ""
    await edit_or_answer(c, h["t"].format(**{**p, **r, **ex}), main_keyboard())

@router.callback_query(F.data == "davka")
async def cb_davka(c): await handle_act(c, "davka")

@router.callback_query(F.data == "sdat")
async def cb_sdat(c): await handle_act(c, "sdat")

@router.callback_query(F.data == "pump")
async def cb_pump(c):
    p = await get_patsan_cached(c.from_user.id)
    d,z,n = p.get('skill_davka',1), p.get('skill_zashita',1), p.get('skill_nahodka',1)
    costs = {'davka':180+(d*10), 'zashita':270+(z*15), 'nahodka':225+(n*12)}
    await edit_or_answer(c, f"<b>Прокачка скиллов:</b>\n💰 Деньги: {p.get('dengi',0)} руб.\n📈 Уровень: {p.get('level',1)} | 📚 Опыт: {p.get('experience',0)}\n\n💪 <b>Давка змия</b> (+100г за уровень)\nУровень: {d} | Следующий: {costs['davka']}р/ур\n\n🛡️ <b>Защита атмосфер</b> (ускоряет восстановление)\nУровень: {z} | Следующий: {costs['zashita']}р/ур\n\n🔍 <b>Находка двенашек</b> (+5% шанс за уровень)\nУровень: {n} | Следующий: {costs['nahodka']}р/ур\n\n<i>Выбери, что прокачать:</i>", pump_keyboard())

@router.callback_query(F.data.startswith("pump_"))
async def cb_pump_skill(c):
    skill, uid = c.data.split("_")[1], c.from_user.id
    p, res = await pump_skill(uid, skill)
    await c.answer(res if p else res, show_alert=True)
    if p: await cb_pump(c)

@router.callback_query(F.data == "inventory")
async def cb_inventory(c):
    p = await get_patsan_cached(c.from_user.id)
    inv = p.get("inventory",[])
    if not inv: t = "Пусто... Только пыль и тоска"
    else:
        cnt = {}
        for i in inv: cnt[i] = cnt.get(i,0)+1
        t = "<b>Твои вещи:</b>\n" + "\n".join(f"{get_emoji(i)} {i}: {n} шт." for i,n in cnt.items())
    
    ab = p.get("active_boosts",{})
    if ab:
        t += "\n\n<b>🔮 Активные бусты:</b>\n"
        for b,e in ab.items():
            if isinstance(e,(int,float)):
                tl = int(e)-int(time.time())
                if tl>0: t += f"• {b}: {tl//3600}ч {(tl%3600)//60}м\n"
    
    await edit_or_answer(c, f"{t}\n\n🐍 Коричневагый змий: {p.get('zmiy',0):.3f} кг\n🔨 Скрафчено предметов: {len(p.get('crafted_items',[]))}", inventory_management_keyboard())

@router.callback_query(F.data == "profile")
async def cb_profile(c):
    p = await get_patsan_cached(c.from_user.id)
    re, rn = p.get('rank_emoji','👶'), p.get('rank_name','Пацанчик')
    ac, ma = p.get('atm_count',0), p.get('max_atm',12)
    up = p.get("upgrades",{})
    bu = [k for k,v in up.items() if v] if up else []
    ut = "\n<b>🛒 Нагнетатели:</b>\n" + "\n".join(f"• {u}" for u in bu) if bu else ""
    
    sp = p.get("specialization")
    st = f"\n<b>🌳 Специализация:</b> {sp}" if sp else ""
    if sp:
        sb = get_specialization_bonuses(sp)
        if sb: st += f"\n<i>Бонусы: {', '.join(sb.keys())}</i>"
    
    await edit_or_answer(c, f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n{re} <b>{rn}</b>\n👤 {p.get('nickname','Неизвестно')}\n⭐ Авторитет: {p.get('avtoritet',1)}\n📈 Уровень: {p.get('level',1)} | 📚 Опыт: {p.get('experience',0)}\n\n<b>Ресурсы:</b>\n🌀 Атмосферы: [{pb(ac,ma)}] {ac}/{ma}\n⏱️ Восстановление: {ft(calculate_atm_regen_time(p))}\n🐍 Коричневаг: {p.get('zmiy',0):.3f} кг\n💰 Деньги: {p.get('dengi',0)} руб.\n\n<b>Скиллы:</b>\n💪 Давка: {p.get('skill_davka',1)}\n🛡️ Защита: {p.get('skill_zashita',1)}\n🔍 Находка: {p.get('skill_nahodka',1)}{ut}{st}", profile_extended_keyboard())

SPECS = {
    "davila": {"n":"Давила","d":"Мастер давления коричневага","r":"💪 Давка змия: 5 ур.\n🐍 Накоплено змия: 50кг","b":"• +50% к выходу змия\n• -1 атмосфера на действие\n• Открывает: Гигантская давка","p":1500},
    "ohotnik": {"n":"Охотник за двенашками","d":"Находит то, что другие не видят","r":"🔍 Находка двенашек: 5 ур.\n🧱 Двенашка в инвентаре","b":"• +15% к шансу находок\n• 5% шанс на редкий предмет\n• Открывает: Детектор двенашек","p":1200},
    "neprobivaemy": {"n":"Непробиваемый","d":"Железные кишки и стальные нервы","r":"🛡️ Защита атмосфер: 5 ур.\n⭐ Авторитет: 20","b":"• -10% времени восстановления атмосфер\n• +15% защиты в радёмках\n• Открывает: Железный живот","p":2000}
}

@router.callback_query(F.data == "specializations")
async def cb_specs(c):
    uid, p = c.from_user.id, await get_patsan_cached(c.from_user.id)
    cs = p.get("specialization","")
    if cs:
        sb = get_specialization_bonuses(cs)
        bt = "\n".join(f"• {k}: {v}" for k,v in sb.items())
        await edit_or_answer(c, f"<b>🌳 Твоя специализация:</b> {cs}\n\n<b>Бонусы:</b>\n{bt}\n\n<i>Сейчас у тебя может быть только одна специализация.</i>\n<i>Чтобы сменить, нужно сначала сбросить текущую (стоимость: 2000р).</i>", back_to_specializations_keyboard())
        return
    
    av = await get_available_specializations(uid)
    t = "<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n<i>Специализация даёт уникальные бонусы и открывает новые возможности.</i>\n<i>Можно выбрать только одну. Выбор бесплатен при выполнении требований.</i>\n\n"
    for s in av:
        st = "✅ Доступна" if s["available"] else "❌ Недоступна"
        pt = f" | Цена: {s['price']}р" if s['available'] else ""
        t += f"<b>{s['name']}</b> {st}{pt}\n<i>{s['description']}</i>\n"
        if not s["available"] and s["missing"]:
            t += f"<code>Требуется: {', '.join(s['missing'])}</code>\n"
        t += "\n"
    t += "<i>Выбери специализацию для подробной информации:</i>"
    await edit_or_answer(c, t, specializations_keyboard())

@router.callback_query(F.data.startswith("specialization_"))
async def cb_spec_detail(c):
    st = c.data.replace("specialization_","")
    if st == "info":
        await edit_or_answer(c, "<b>🌳 ИНФОРМАЦИЯ О СПЕЦИАЛИЗАЦИЯХ</b>\n\n<b>Что даёт специализация?</b>\n• Уникальные бонусы к игровым механикам\n• Новые возможности и действия\n• Преимущества в определённых ситуациях\n\n<b>Как получить?</b>\n1. Выполнить требования специализации\n2. Иметь достаточно денег для покупки\n3. Выбрать и активировать\n\n<b>Можно ли сменить?</b>\nДа, но за 2000р. Текущая специализация сбрасывается.", specializations_info_keyboard())
        return
    
    if st not in SPECS:
        await c.answer("Неизвестная специализация", show_alert=True)
        return
    
    s = SPECS[st]
    await edit_or_answer(c, f"<b>🌳 {s['n'].upper()}</b>\n\n<i>{s['d']}</i>\n\n<b>💰 Цена:</b> {s['p']}р\n\n<b>📋 Требования:</b>\n{s['r']}\n\n<b>🎁 Бонусы:</b>\n{s['b']}\n\n<i>Выбрать эту специализацию?</i>", specialization_confirmation_keyboard(st))

@router.callback_query(F.data.startswith("specialization_buy_"))
async def cb_spec_buy(c):
    sid, uid = c.data.replace("specialization_buy_",""), c.from_user.id
    ok, msg = await buy_specialization(uid, sid)
    if ok:
        await edit_or_answer(c, f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n{msg}\n\nТеперь ты обладатель уникальной специализации!\nИспользуй её бонусы по максимуму.", main_keyboard())
    else:
        await c.answer(msg, show_alert=True)
        await cb_specs(c)

@router.callback_query(F.data == "craft")
async def cb_craft(c):
    p = await get_patsan_cached(c.from_user.id)
    await edit_or_answer(c, f"<b>🔨 КРАФТ ПРЕДМЕТОВ</b>\n\n<i>Создавай мощные предметы из ингредиентов!</i>\n\n📦 Инвентарь: {len(p.get('inventory',[]))} предметов\n🔨 Скрафчено: {len(p.get('crafted_items',[]))} предметов\n💰 Деньги: {p.get('dengi',0)}р\n\n<b>Выбери действие:</b>", craft_keyboard())

@router.callback_query(F.data == "craft_items")
async def cb_craft_items(c):
    ci = await get_craftable_items(c.from_user.id)
    if not ci:
        await edit_or_answer(c, "😕 <b>НЕТ ДОСТУПНЫХ РЕЦЕПТОВ</b>\n\nУ тебя пока нет нужных ингредиентов для крафта.\nСобирай двенашки, атмосферы и другие предметы!", back_to_craft_keyboard())
        return
    
    t = "<b>🔨 ДОСТУПНЫЕ ДЛЯ КРАФТА:</b>\n\n"
    for i in ci:
        st = "✅ МОЖНО" if i["can_craft"] else "❌ НЕЛЬЗЯ"
        t += f"<b>{i['name']}</b> {st}\n<i>{i['description']}</i>\n🎲 Шанс успеха: {int(i['success_chance']*100)}%\n"
        if not i["can_craft"] and i["missing"]:
            t += f"<code>Не хватает: {', '.join(i['missing'][:2])}</code>\n"
        t += "\n"
    t += "<i>Выбери предмет для крафта:</i>"
    await edit_or_answer(c, t, craft_items_keyboard())

@router.callback_query(F.data.startswith("craft_execute_"))
async def cb_craft_exec(c):
    rid, uid = c.data.replace("craft_execute_",""), c.from_user.id
    ok, msg, res = await craft_item(uid, rid)
    if ok:
        iname, dur = res.get("item","предмет"), res.get("duration")
        dt = f"\n⏱️ Действует: {dur//3600} часов" if dur else ""
        await edit_or_answer(c, f"✨ <b>КРАФТ УСПЕШЕН!</b>\n\n{msg}{dt}\n\n🎉 Ты создал новый предмет!\nПроверь инвентарь, чтобы использовать его.", main_keyboard())
        await unlock_achievement(uid, "successful_craft", f"Успешный крафт: {iname}", 100)
    else:
        await edit_or_answer(c, f"💥 <b>КРАФТ ПРОВАЛЕН</b>\n\n{msg}\n\nИнгредиенты потеряны...\nПопробуй снова, когда соберёшь больше!", back_to_craft_keyboard())

@router.callback_query(F.data == "craft_recipes")
async def cb_craft_recipes(c):
    await edit_or_answer(c, "<b>📜 ВСЕ РЕЦЕПТЫ КРАФТА</b>\n\n<b>✨ Супер-двенашка</b>\nИнгредиенты: 3× двенашка, 500р\nШанс: 100% | Эффект: Повышает удачу на 1 час\n\n<b>⚡ Вечный двигатель</b>\nИнгредиенты: 5× атмосфера, 1× энергетик\nШанс: 80% | Эффект: Ускоряет восстановление атмосфер на 24ч\n\n<b>👑 Царский обед</b>\nИнгредиенты: 1× курвасаны, 1× ряженка, 300р\nШанс: 100% | Эффект: Максимальный буст на 30 минут\n\n<b>🌀 Бустер атмосфер</b>\nИнгредиенты: 2× энергетик, 1× двенашка, 2000р\nШанс: 70% | Эффект: +3 к максимальному запасу атмосфер\n\n<i>Собирай ингредиенты и создавай мощные предметы!</i>", craft_recipes_keyboard())

@router.callback_query(F.data == "rademka_scout_menu")
async def cb_scout_menu(c):
    p = await get_patsan_cached(c.from_user.id)
    su, fl = p.get("rademka_scouts",0), max(0,5-p.get("rademka_scouts",0))
    await edit_or_answer(c, f"<b>🕵️ РАЗВЕДКА РАДЁМКИ</b>\n\n<i>Узнай точный шанс успеха перед атакой!</i>\n\n🎯 <b>Преимущества разведки:</b>\n• Точно знаешь шанс победы\n• Учитываются все факторы\n• Можно выбрать другую цель\n\n📊 <b>Твоя статистика:</b>\n• Использовано разведок: {su}\n• Бесплатных осталось: {fl}/5\n• Стоимость разведки: {0 if fl>0 else 50}р\n\n<i>Выбери действие:</i>", rademka_scout_keyboard())

@router.callback_query(F.data == "rademka_scout_random")
async def cb_scout_random(c):
    uid, tp = c.from_user.id, await get_top_players(limit=50, sort_by="avtoritet")
    targets = [p for p in tp if p.get("user_id") != uid]
    if not targets:
        await edit_or_answer(c, "😕 <b>НЕКОГО РАЗВЕДЫВАТЬ!</b>\n\nНа гофроцентрале кроме тебя никого нет...\nПриведи друзей, чтобы было кого разведывать!", back_to_rademka_keyboard())
        return
    
    t = random.choice(targets)
    ok, msg, sd = await rademka_scout(uid, t.get("user_id"))
    if not ok:
        await c.answer(msg, show_alert=True)
        return
    
    ch, tn = sd.get("chance",50), t.get("nickname","Неизвестно")
    f = sd.get("factors",[])
    ftx = "\n".join(f"• {x}" for x in f) if f else "• Неизвестные факторы"
    as_, ts = sd.get('attacker_stats',{}), sd.get('target_stats',{})
    ar, tr = as_.get('rank',('👶','Пацанчик'))[1], ts.get('rank',('👶','Пацанчик'))[1]
    
    txt = (f"🎯 <b>РАЗВЕДКА ЗАВЕРШЕНА!</b>\n\n<b>Цель:</b> {tn}\n🎲 <b>Точный шанс победы:</b> {ch}%\n\n<b>📊 Факторы:</b>\n{ftx}\n\n<b>📈 Статистика:</b>\n• Твой авторитет: {as_.get('avtoritet',0)} ({ar})\n• Его авторитет: {ts.get('avtoritet',0)} ({tr})\n• Последняя активность: {ts.get('last_active_hours',0)}ч назад\n\n💸 Стоимость разведки: {'Бесплатно' if sd.get('cost',0)==0 else '50р'}\n🕵️ Бесплатных разведок осталось: {sd.get('free_scouts_left',0)}\n\n<i>Атаковать эту цель?</i>")
    await edit_or_answer(c, txt, rademka_fight_keyboard(t.get("user_id"), scouted=True))

@router.callback_query(F.data.startswith("rademka_scout_"))
async def cb_scout_target(c):
    d = c.data.replace("rademka_scout_","")
    if d == "choose":
        await edit_or_answer(c, "🎯 <b>ВЫБОР ЦЕЛИ ДЛЯ РАЗВЕДКИ</b>\n\nДля этой функции нужен список игроков.\nПока используй случайную цель или выбери из топа.", rademka_scout_keyboard())
    elif d == "stats":
        p = await get_patsan_cached(c.from_user.id)
        su, fu, pu = p.get("rademka_scouts",0), min(5,p.get("rademka_scouts",0)), max(0,p.get("rademka_scouts",0)-5)
        await edit_or_answer(c, f"📊 <b>СТАТИСТИКА РАЗВЕДОК</b>\n\n🕵️ Всего разведок: {su}\n🎯 Бесплатных: {fu}/5\n💰 Платных: {pu}\n💸 Потрачено на разведки: {pu*50}р\n\n", rademka_scout_keyboard())
    else:
        try:
            ok, msg, _ = await rademka_scout(c.from_user.id, int(d))
            await c.answer("Разведка выполнена!" if ok else msg, show_alert=True)
        except ValueError:
            await c.answer("Ошибка: неверный ID цели", show_alert=True)

ACHS = {
    "zmiy_collector": {"n":"Коллекционер змия","d":"Собери определённое количество змия",
        "l":[{"g":10,"r":50,"t":"Новичок","e":10},{"g":100,"r":300,"t":"Любитель","e":50},
             {"g":1000,"r":1500,"t":"Профессионал","e":200},{"g":10000,"r":5000,"t":"КОРОЛЬ ГОФРОЦЕНТРАЛА","e":1000}]},
    "money_maker": {"n":"Денежный мешок","d":"Заработай много денег",
        "l":[{"g":1000,"r":100,"t":"Бедолага","e":10},{"g":10000,"r":1000,"t":"Состоятельный","e":100},
             {"g":100000,"r":5000,"t":"Олигарх","e":500},{"g":1000000,"r":25000,"t":"РОТШИЛЬД","e":2500}]},
    "rademka_king": {"n":"Король радёмок","d":"Победи в множестве радёмок",
        "l":[{"g":5,"r":200,"t":"Задира","e":20},{"g":25,"r":1000,"t":"Гроза района","e":100},
             {"g":100,"r":5000,"t":"Неприкасаемый","e":500},{"g":500,"r":25000,"t":"ЛЕГЕНДА РАДЁМКИ","e":2500}]}
}

@router.callback_query(F.data == "achievements_progress")
async def cb_ach_progress(c):
    pd = await get_achievement_progress(c.from_user.id)
    if not pd:
        await edit_or_answer(c, "📊 <b>ПРОГРЕСС ДОСТИЖЕНИЙ</b>\n\nПока нет прогресса по уровневым достижениям.\nИграй активно, и прогресс появится!", achievements_progress_keyboard())
        return
    
    t = "<b>📊 ПРОГРЕСС ПО УРОВНЕВЫМ ДОСТИЖЕНИЯМ</b>\n\n"
    for aid, d in pd.items():
        t += f"<b>{d['name']}</b>\n"
        if d['next_level']:
            t += f"Уровень: {d['current_level']}/{len(d['all_levels'])}\nПрогресс: {d['current_progress']:.1f}/{d['next_level']['goal']} ({d['progress_percent']:.1f}%)\n"
            t += f"Следующий уровень: {d['next_level']['title']} (+{d['next_level']['reward']}р, +{d['next_level']['exp']} опыта)\n"
        else:
            t += f"✅ Все уровни пройдены! (Максимум)\n"
        t += "\n"
    t += "<i>Выбери достижение для подробной информации:</i>"
    await edit_or_answer(c, t, achievements_progress_keyboard())

@router.callback_query(F.data.startswith("achievement_"))
async def cb_ach_detail(c):
    at = c.data.replace("achievement_","")
    if at not in ACHS:
        await c.answer("Неизвестное достижение", show_alert=True)
        return
    
    a = ACHS[at]
    t = f"<b>🏆 {a['n'].upper()}</b>\n\n<i>{a['d']}</i>\n\n<b>📊 Уровни:</b>\n"
    for i, l in enumerate(a['l'], 1):
        t += f"{i}. <b>{l['t']}</b>: {l['g']} → +{l['r']}р (+{l['e']} опыта)\n"
    t += "\n<i>Прогресс автоматически отслеживается во время игры.</i>"
    await edit_or_answer(c, t, back_to_profile_keyboard())

@router.callback_query(F.data == "level_stats")
async def cb_level_stats(c):
    p = await get_patsan_cached(c.from_user.id)
    cl, ce = p.get("level",1), p.get("experience",0)
    re, pp = int(100*(cl**1.5)), (ce/re*100) if re>0 else 0
    nr, ai = (cl+1)*100, (cl+1)%5==0
    t = f"<b>📈 СТАТИСТИКА УРОВНЕЙ</b>\n\n🏆 <b>Текущий уровень:</b> {cl}\n📚 <b>Опыт:</b> {ce}/{re}\n📊 <b>Прогресс:</b> [{pb(ce,re,10)}] {pp:.1f}%\n\n🎁 <b>Награда за {cl+1} уровень:</b>\n• +{nr}р\n"
    if ai: t += "• +1 к максимальным атмосферам\n"
    t += f"\n<b>ℹ️ Информация:</b>\n• Опыт даётся за все действия\n• Каждый 5 уровень увеличивает запас атмосфер\n• Уровень влияет на ежедневные награды\n"
    await edit_or_answer(c, t, level_stats_keyboard())

@router.callback_query(F.data == "atm_status")
async def cb_atm_status(c):
    p = await get_patsan_cached(c.from_user.id)
    ac, ma = p.get('atm_count',0), p.get('max_atm',12)
    rt = calculate_atm_regen_time(p)
    bs = []
    if p.get("skill_zashita",1)>=10: bs.append("Скилл защиты ≥10: -10% времени")
    if p.get("specialization")=="непробиваемый": bs.append("Специализация: -10% времени")
    if "вечный_двигатель" in p.get("active_boosts",{}): bs.append("Вечный двигатель: -30% времени")
    
    t = f"<b>🌡️ СОСТОЯНИЕ АТМОСФЕР</b>\n\n🌀 <b>Текущий запас:</b> {ac}/{ma}\n📊 <b>Заполненность:</b> [{pb(ac,ma)}] {(ac/ma)*100:.1f}%\n\n⏱️ <b>Время восстановления:</b>\n• 1 атмосфера: {ft(rt)}\n• До полного: {ft(rt*(ma-ac))}\n\n"
    if bs: t += f"⚡ <b>Активные бонусы:</b>\n" + "\n".join(f"• {b}" for b in bs) + "\n\n"
    t += f"<b>ℹ️ Как увеличить?</b>\n• Каждый 5 уровень: +1 к максимуму\n• Бустер атмосфер: +3 к максимуму\n• Прокачка защиты: ускоряет восстановление\n"
    await edit_or_answer(c, t, atm_status_keyboard())

TOPS = {
    "avtoritet":("авторитету","⭐","avtoritet"),"dengi":("деньгам","💰","dengi"),
    "zmiy":("змию","🐍","zmiy"),"total_skill":("сумме скиллов","💪","total_skill"),
    "level":("уровню","📈","level"),"rademka_wins":("победам в радёмках","👊","rademka_wins")
}

@router.callback_query(F.data == "top")
async def cb_top_menu(c):
    await edit_or_answer(c, "🏆 <b>ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА</b>\n\nВыбери, по какому показателю сортировать рейтинг:\n\n<i>Новые варианты:</i>\n• 📈 По уровню - кто больше прокачался\n• 👊 По победам в радёмках - кто самый дерзкий</i>", top_sort_keyboard())

@router.callback_query(F.data.startswith("top_"))
async def cb_show_top(c):
    st = c.data.replace("top_","")
    if st not in TOPS:
        await c.answer("Неизвестный тип топа", show_alert=True)
        return
    
    sn, em, dk = TOPS[st]
    try:
        if st == "rademka_wins":
            cn = await get_connection()
            cur = await cn.execute('SELECT u.user_id,u.nickname,u.avtoritet,COUNT(rf.id)as wins FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id GROUP BY u.user_id,u.nickname,u.avtoritet ORDER BY wins DESC LIMIT 10')
            tp = [dict(r)|{"wins":r["wins"]or0,"rank":"?","zmiy":0,"dengi":0,"level":1} for r in await cur.fetchall()]
            await cn.close()
        else:
            tp = await get_top_players(limit=10, sort_by=dk)
    except Exception as e:
        await c.answer(f"Ошибка при получении топа: {e}", show_alert=True)
        return
    
    if not tp:
        await edit_or_answer(c, "😕 <b>Топ пуст!</b>\n\nЕщё никто не заслужил места в рейтинге.\nБудь первым!", top_sort_keyboard())
        return
    
    mds = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    tt = f"{em} <b>Топ пацанов по {sn}:</b>\n\n"
    for i, pl in enumerate(tp):
        md = mds[i] if i<len(mds) else f"{i+1}."
        nn = pl.get('nickname',f'Пацан_{pl.get("user_id","?")}')
        if len(nn)>20: nn = nn[:17]+"..."
        
        if st=="avtoritet": v=f"⭐ {pl.get('avtoritet',0)}"
        elif st=="dengi": v=f"💰 {pl.get('dengi_formatted',f'{pl.get('dengi',0)}р')}"
        elif st=="zmiy": v=f"🐍 {pl.get('zmiy_formatted',f'{pl.get('zmiy',0):.1f}кг')}"
        elif st=="total_skill": v=f"💪 {pl.get('total_skill',0)} ур."
        elif st=="level": v=f"📈 {pl.get('level',1)} ур."
        elif st=="rademka_wins": v=f"👊 {pl.get('wins',0)} побед"
        else: v=""
        
        ri=f" ({pl.get('rank','').split(' ')[1]})" if st!="rademka_wins" and len(pl.get('rank','').split(' '))>1 else ""
        tt+=f"{md} <code>{nn}</code>{ri} — {v}\n"
    
    tt+=f"\n📊 <i>Всего пацанов в системе: {len(tp)}</i>"
    uid=c.from_user.id
    for i,pl in enumerate(tp):
        if pl.get('user_id')==uid:
            tt+=f"\n\n🎯 <b>Твоя позиция:</b> {mds[i] if i<len(mds) else str(i+1)}"
            break
    
    await edit_or_answer(c, tt, top_sort_keyboard())

@router.callback_query(F.data.startswith("inventory_"))
async def cb_inv_action(c):
    a=c.data.replace("inventory_","")
    if a=="use": await c.answer("Функция использования предметов в разработке!", show_alert=True)
    elif a=="sort": 
        await c.answer("Инвентарь отсортирован!", show_alert=True)
        await cb_inventory(c)
    elif a=="trash": 
        await edit_or_answer(c, "🗑️ <b>ВЫБРОСИТЬ МУСОР</b>\n\nТы уверен? Это действие удалит:\n• Все 'перчатки'\n• Все 'швабры'\n• Все 'вёдра'\n\nЗато освободит место в инвентаре!", confirmation_keyboard("trash_inventory"))
    else: await c.answer("Неизвестное действие", show_alert=True)

@router.callback_query(F.data == "confirm_trash_inventory")
async def cb_confirm_trash(c):
    p=await get_patsan(c.from_user.id)
    inv=p.get("inventory",[])
    new=[i for i in inv if i not in ["перчатки","швабра","ведро"]]
    r=len(inv)-len(new)
    if r>0:
        p["inventory"]=new
        await save_patsan(p)
        await edit_or_answer(c, f"✅ <b>МУСОР ВЫБРОШЕН!</b>\n\nВыброшено предметов: {r}\nОсталось в инвентаре: {len(new)}\n\n<i>Теперь есть место для чего-то полезного!</i>", main_keyboard())
    else:
        await edit_or_answer(c, "🤷 <b>НЕТ МУСОРА</b>\n\nВ твоём инвентаре не нашлось мусора.\nВсё полезное, всё пригодится!", main_keyboard())
