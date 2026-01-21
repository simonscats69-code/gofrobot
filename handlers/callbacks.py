from aiogram import Router, types, F, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import time, random, asyncio
from db_manager import (
    get_patsan, get_patsan_cached, save_patsan, get_top_players,
    save_rademka_fight, calculate_atm_regen_time, get_connection,
    davka_zmiy, sdat_zmiy, pump_skill, get_rank
)
from keyboards import (
    main_keyboard, pump_keyboard, inventory_management_keyboard,
    profile_extended_keyboard, level_stats_keyboard, atm_status_keyboard,
    top_sort_keyboard, confirmation_keyboard, shop_keyboard,
    daily_keyboard, rademka_keyboard, nickname_keyboard
)

router = Router()

def gr(p):
    if 'rank_emoji' in p and 'rank_name' in p:
        return p['rank_emoji'], p['rank_name']
    a = p.get('avtoritet', 1)
    R = {1:("👶","Пацанчик"), 11:("👊","Браток"), 51:("👑","Авторитет"), 
         201:("🐉","Царь гофры"), 501:("🏛️","Император"), 1001:("💩","БОГ ГОВНА")}
    rn, re = "Пацанчик", "👶"
    for t, (e, n) in sorted(R.items()):
        if a >= t: rn, re = n, e
    p['rank_emoji'], p['rank_name'] = re, rn
    return re, rn

async def eoa(c, t, kb=None, p="HTML"):
    try:
        await c.message.edit_text(t, reply_markup=kb, parse_mode=p)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e): raise

def pb(c, t, l=10):
    f = int((c / t) * l) if t > 0 else 0
    return "█" * f + "░" * (l - f)

def ft(s):
    if s < 60: return f"{s}с"
    m, h = s // 60, s // 3600
    return f"{h}ч {m % 60}м" if h > 0 else f"{m}м {s % 60}с"

def ge(i):
    m = {"двенашка":"🧱", "атмосфера":"🌀", "энергетик":"⚡", "перчатки":"🧤", "швабра":"🧹", "ведро":"🪣",
         "золотая_двенашка":"🌟", "кристалл_атмосферы":"💎", "секретная_схема":"📜", "супер_двенашка":"✨",
         "вечный_двигатель":"⚙️", "царский_обед":"👑", "бустер_атмосфер":"🌀"}
    return m.get(i, "📦")

class IgnoreNotModifiedMiddleware(BaseMiddleware):
    async def __call__(self, h, e, d):
        try: return await h(e, d)
        except TelegramBadRequest as ex:
            if "message is not modified" in str(ex) or ("Bad Request" in str(ex) and "exactly the same" in str(ex)):
                if cb := d.get('callback_query', getattr(e, 'callback_query', None)):
                    if hasattr(cb, 'answer'): await cb.answer()
                return
            raise

router.callback_query.middleware(IgnoreNotModifiedMiddleware())

async def mmt(p):
    a, m = p.get('atm_count', 0), p.get('max_atm', 12)
    re, rn = gr(p)
    return f"<b>Главное меню</b>\n{re} <b>{rn}</b> | ⭐ {p.get('avtoritet', 1)} | 📈 Ур. {p.get('level', 1)}\n\n🌀 Атмосферы: [{pb(a, m)}] {a}/{m}\n💸 Деньги: {p.get('dengi', 0)}р | 🐍 Змий: {p.get('zmiy', 0):.1f}кг\n\n<i>Выбери действие, пацан:</i>"

async def _complete_operation(c, func, uid, act):
    try:
        result = await func(uid)
        if result and len(result) >= 2:
            p, r_data = result[1], result[2] if len(result) > 2 else {}
            ex = {}
            if act == "davka":
                u = p.get("upgrades",{})
                ex["nm"] = "\n🥛 Ряженка жмёт двенашку как надо! (+75%)" if u.get("ryazhenka") else "\n🧋 Бублэки создают нужную турбулентность! (+35% к шансу)" if u.get("bubbleki") else ""
                ex["dm"] = "\n✨ <b>Нашёл двенашку в турбулентности!</b>" if r_data.get("dvenashka_found") else ""
                ex["rm"] = f"\n🌟 <b>Редкая находка: {r_data['rare_item_found']}!</b>" if r_data.get("rare_item_found") else ""
                ex["em"] = f"\n📚 +{r_data.get('exp_gained', 0)} опыта" if r_data.get('exp_gained', 0) > 0 else ""
                ex["tg"] = r_data.get('total_grams', 0) / 1000 if r_data.get('total_grams') else 0
            elif act == "sdat":
                ex["abt"] = f"\n⭐ <b>Бонус авторитета:</b> +{r_data['avtoritet_bonus']}р" if r_data.get('avtoritet_bonus', 0) > 0 else ""
                ex["em"] = f"\n📚 +{r_data.get('exp_gained', 0)} опыта" if r_data.get('exp_gained', 0) > 0 else ""
            if h := AH.get(act):
                text = h["t"].format(**{**p, **r_data, **ex})
                try: await eoa(c, text, main_keyboard())
                except:
                    try: await c.message.edit_text(text[:4000], parse_mode="HTML", reply_markup=main_keyboard())
                    except: await c.message.answer(text[:4000], parse_mode="HTML")
    except Exception as e:
        try: await c.message.answer(f"❌ Ошибка при завершении: {str(e)[:100]}")
        except: pass

AH = {
    "davka": {
        "func": davka_zmiy,
        "t": "<b>Заварвариваем дело...</b>{nm}\n🔄 Потрачено атмосфер: {cost}\n<i>\"{wm} говна за 25 секунд высрал я сейчас\"</i>\n➕ {tg:.3f} кг коричневага{dm}{rm}{em}\nВсего змия накоплено: {zmiy:.3f} кг\n⚡ Осталось атмосфер: {atm_count}/{max_atm}"
    },
    "sdat": {
        "func": sdat_zmiy,
        "t": "<b>Сдал коричневага на металлолом</b>\n📦 Сдано: {oz:.3f} кг змия\n💰 <b>Получил: {tm} руб.</b>{abt}{em}\n💸 Теперь на кармане: {dengi} руб.\n📈 Уровень: {level} ({experience}/?? опыта)\n<i>Приёмщик: \"Опять эту дрянь принёс... Но плачу больше!\"</i>"
    }
}

async def ha(c, act):
    try: await c.answer("🔄 Обработка...")
    except: pass
    try:
        if not (h := AH.get(act)): return
        uid = c.from_user.id
        try: result = await asyncio.wait_for(h["func"](uid), timeout=7.0)
        except asyncio.TimeoutError:
            await eoa(c, "⏳ Операция занимает время...", main_keyboard())
            asyncio.create_task(_complete_operation(c, h["func"], uid, act))
            return
        if not result or len(result) < 2:
            await eoa(c, "❌ Ошибка: некорректный ответ", main_keyboard())
            return
        p, r = result[1], result[2] if len(result) > 2 else {}
        if p is None:
            await eoa(c, f"⚠️ {r}", main_keyboard())
            return
        ex = {}
        if act == "davka":
            u = p.get("upgrades", {})
            ex["nm"] = "\n🥛 Ряженка жмёт двенашку как надо! (+75%)" if u.get("ryazhenka") else "\n🧋 Бублэки создают нужную турбулентности! (+35% к шансу)" if u.get("bubbleki") else ""
            ex["dm"] = "\n✨ <b>Нашёл двенашку в турбулентности!</b>" if r.get("dvenashka_found") else ""
            ex["rm"] = f"\n🌟 <b>Редкая находка: {r['rare_item_found']}!</b>" if r.get("rare_item_found") else ""
            ex["em"] = f"\n📚 +{r.get('exp_gained', 0)} опыта" if r.get('exp_gained', 0) > 0 else ""
            ex["tg"] = r.get('total_grams', 0) / 1000 if r.get('total_grams') else 0
        elif act == "sdat":
            ex["abt"] = f"\n⭐ <b>Бонус авторитета:</b> +{r['avtoritet_bonus']}р" if r.get('avtoritet_bonus', 0) > 0 else ""
            ex["em"] = f"\n📚 +{r.get('exp_gained', 0)} опыта" if r.get('exp_gained', 0) > 0 else ""
        await eoa(c, h["t"].format(**{**p, **r, **ex}), main_keyboard())
    except Exception as e:
        try: await eoa(c, f"❌ Ошибка: {str(e)[:100]}", main_keyboard())
        except: await c.message.answer(f"❌ Ошибка: {str(e)[:100]}")

@router.callback_query(F.data.in_(["davka", "sdat"]))
async def cba(c):
    try: await c.answer("🔄 Обработка...")
    except: pass
    await ha(c, c.data)

@router.callback_query(F.data == "back_main")
async def bm(c):
    try:
        print(f"DEBUG: Нажата кнопка back_main")
        await c.answer("Возвращаемся в главное меню...")
        p = await get_patsan_cached(c.from_user.id)
        print(f"DEBUG: Получили пользователя: {p.get('nickname')}")
        
        menu_text = await mmt(p)
        print(f"DEBUG: Текст меню: {menu_text[:50]}...")
        
        keyboard = main_keyboard()
        print(f"DEBUG: Клавиатура создана")
        
        await eoa(c, menu_text, keyboard)
        print(f"DEBUG: Сообщение обновлено")
        
    except Exception as e:
        print(f"DEBUG: Ошибка в bm: {e}")
        import traceback
        traceback.print_exc()
        await c.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "nickname_menu")
async def nm(c):
    try:
        await c.answer()
        from handlers.commands import cmd_nickname
        await cmd_nickname(c.message)
    except Exception:
        await c.answer("Ошибка загрузки меню ника", show_alert=True)

@router.callback_query(F.data == "daily")
async def cd(c):
    try:
        await c.answer()
        from handlers.commands import cmd_daily
        await cmd_daily(c.message)
    except Exception:
        await c.answer("Ошибка загрузки ежедневной награды", show_alert=True)

@router.callback_query(F.data == "rademka")
async def cr(c):
    try:
        await c.answer()
        from handlers.commands import cmd_rademka
        await cmd_rademka(c.message)
    except Exception:
        await c.answer("Ошибка загрузки радёмки", show_alert=True)

@router.callback_query(F.data == "pump")
async def cp(c):
    try:
        await c.answer()
        p = await get_patsan_cached(c.from_user.id)
        d, z, n = p.get('skill_davka', 1), p.get('skill_zashita', 1), p.get('skill_nahodka', 1)
        cs = {'davka': 180 + (d * 10), 'zashita': 270 + (z * 15), 'nahodka': 225 + (n * 12)}
        await eoa(c, f"<b>Прокачка скиллов:</b>\n💰 Деньги: {p.get('dengi', 0)} руб.\n📈 Уровень: {p.get('level', 1)} | 📚 Опыт: {p.get('experience', 0)}\n\n💪 <b>Давка змия</b> (+100г за уровень)\nУровень: {d} | Следующий: {cs['davka']}р/ур\n\n🛡️ <b>Защита атмосфер</b> (ускоряет восстановление)\nУровень: {z} | Следующий: {cs['zashita']}р/ур\n\n🔍 <b>Находка двенашек</b> (+5% шанс за уровень)\nУровень: {n} | Следующий: {cs['nahodka']}р/ур\n\n<i>Выбери, что прокачать:</i>", pump_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка прокачки: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data.startswith("pump_"))
async def cps(c):
    try:
        await c.answer("⚙️ Прокачка...")
        s, uid = c.data.split("_")[1], c.from_user.id
        p, res = await pump_skill(uid, s)
        await c.answer(res if p else res, show_alert=True)
        if p: await cp(c)
    except Exception as e:
        await c.answer(f"Ошибка прокачки: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "inventory")
async def ci(c):
    try:
        await c.answer()
        p = await get_patsan_cached(c.from_user.id)
        i = p.get("inventory", [])
        if not i: 
            t = "Пусто... Только пыль и тоска"
        else:
            cnt = {x: i.count(x) for x in set(i)}
            t = "<b>Твои вещи:</b>\n" + "\n".join(f"{ge(x)} {x}: {c} шт." for x, c in cnt.items())
        
        await eoa(c, f"{t}\n\n🐍 Коричневагый змий: {p.get('zmiy', 0):.3f} кг", inventory_management_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка инвентаря: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "profile")
async def cpr(c):
    try:
        await c.answer()
        p = await get_patsan_cached(c.from_user.id)
        re, rn = gr(p)
        a, m, up = p.get('atm_count', 0), p.get('max_atm', 12), p.get("upgrades", {})
        bu = [k for k, v in up.items() if v] if up else []
        t = f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n{re} <b>{rn}</b>\n👤 {p.get('nickname','Неизвестно')}\n⭐ Авторитет: {p.get('avtoritet', 1)}\n📈 Уровень: {p.get('level', 1)} | 📚 Опыт: {p.get('experience', 0)}\n\n<b>Ресурсы:</b>\n🌀 Атмосферы: [{pb(a, m)}] {a}/{m}\n⏱️ Восстановление: {ft(calculate_atm_regen_time(p))}\n🐍 Коричневаг: {p.get('zmiy', 0):.3f} кг\n💰 Деньги: {p.get('dengi', 0)} руб.\n\n<b>Скиллы:</b>\n💪 Давка: {p.get('skill_davka', 1)}\n🛡️ Защита: {p.get('skill_zashita', 1)}\n🔍 Находка: {p.get('skill_nahodka', 1)}"
        if bu: t += f"\n<b>🛒 Нагнетатели:</b>\n" + "\n".join(f"• {u}" for u in bu)
        await eoa(c, t, profile_extended_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка профиля: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "level_stats")
async def cls(c):
    try:
        await c.answer()
        p = await get_patsan_cached(c.from_user.id)
        cl, ce = p.get("level", 1), p.get("experience", 0)
        re, pp = int(100 * (cl ** 1.5)), (ce / re * 100) if re > 0 else 0
        t = f"<b>📈 СТАТИСТИКА УРОВНЕЙ</b>\n\n🏆 <b>Текущий уровень:</b> {cl}\n📚 <b>Опыт:</b> {ce}/{re}\n📊 <b>Прогресс:</b> [{pb(ce, re, 10)}] {pp:.1f}%\n\n🎁 <b>Награда за {cl + 1} уровень:</b>\n• +{(cl + 1) * 100}р\n" + ("• +1 к максимальным атмосферам\n" if (cl + 1) % 5 == 0 else "") + f"\n<b>ℹ️ Информация:</b>\n• Опыт даётся за все действия\n• Каждый 5 уровень увеличивает запас атмосфер\n• Уровень влияет на ежедневные награды\n"
        await eoa(c, t, level_stats_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка статистики уровней: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "atm_status")
async def cas(c):
    try:
        await c.answer()
        p = await get_patsan_cached(c.from_user.id)
        a, m = p.get('atm_count', 0), p.get('max_atm', 12)
        rt, bs = calculate_atm_regen_time(p), []
        if p.get("skill_zashita", 1) >= 10: bs.append("Скилл защиты ≥10: -10% времени")
        if "вечный_двигатель" in p.get("active_boosts", {}): bs.append("Вечный двигатель: -30% времени")
        t = f"<b>🌡️ СОСТОЯНИЕ АТМОСФЕР</b>\n\n🌀 <b>Текущий запас:</b> {a}/{m}\n📊 <b>Заполненность:</b> [{pb(a, m)}] {(a / m) * 100:.1f}%\n\n⏱️ <b>Время восстановление:</b>\n• 1 атмосфера: {ft(rt)}\n• До полного: {ft(rt * (m - a))}\n\n" + (f"⚡ <b>Активные бонусы:</b>\n" + "\n".join(f"• {b}" for b in bs) + "\n\n" if bs else "") + f"<b>ℹ️ Как увеличить?</b>\n• Каждый 5 уровень: +1 к максимуму\n• Бустер атмосфер: +3 к максимуму\n• Прокачка защиты: ускоряет восстановление\n"
        await eoa(c, t, atm_status_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка статуса атмосфер: {str(e)[:50]}", show_alert=True)

TO = {"avtoritet":("авторитету","⭐","avtoritet"),"dengi":("деньгам","💰","dengi"),"zmiy":("змию","🐍","zmiy"),"total_skill":("сумме скиллов","💪","total_skill"),"level":("уровню","📈","level"),"rademka_wins":("победам в радёмках","👊","rademka_wins")}

@router.callback_query(F.data == "top")
async def ctm(c):
    try:
        await c.answer()
        # Вместо импорта из commands.py показываем меню выбора топа
        await eoa(c, "🏆 <b>ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА</b>\n\nВыбери, по какому показателю сортировать рейтинг:\n\n<i>Новые варианты:</i>\n• 📈 По уровню - кто больше прокачался\n• 👊 По победам в радёмках - кто самый дерзкий</i>", top_sort_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка топа: {str(e)[:50]}", show_alert=True)

async def grwt():
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT u.user_id,u.nickname,u.avtoritet,COUNT(rf.id) as wins FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id GROUP BY u.user_id,u.nickname,u.avtoritet ORDER BY wins DESC LIMIT 10')
        r = await cur.fetchall()
        await cn.close()
        return [dict(x) | {"wins": x["wins"] or 0, "rank": "?", "zmiy": 0, "dengi": 0, "level": 1} for x in r]
    except Exception:
        return []

@router.callback_query(F.data.startswith("top_"))
async def cst(c):
    try:
        await c.answer()
        if (st := c.data.replace("top_", "")) not in TO:
            return await c.answer("Неизвестный тип топа", show_alert=True)
        sn, em, dk = TO[st]
        if st != "rademka_wins": tp = await get_top_players(limit=10, sort_by=dk)
        else: tp = await grwt()
        if not tp: return await eoa(c, "😕 <b>Топ пуст!</b>\n\nЕщё никто не заслужил места в рейтинге.\nБудь первым!", top_sort_keyboard())
        mds, tt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], f"{em} <b>Топ пацанов по {sn}:</b>\n\n"
        for i, pl in enumerate(tp[:10]):
            nn = pl.get('nickname', f'Пацан_{pl.get("user_id", "?")}')[:20] + ("..." if len(pl.get('nickname', '')) > 20 else "")
            if st == "avtoritet": v = f"⭐ {pl.get('avtoritet', 0)}"
            elif st == "dengi":
                dv = pl.get("dengi", 0)
                df = f'{dv}р'
                v = f"💰 {df}"
            elif st == "zmiy":
                zv = pl.get("zmiy", 0)
                zf = f'{zv:.1f}кг'
                v = f"🐍 {zf}"
            elif st == "total_skill": v = f"💪 {pl.get('total_skill', 0)} ур."
            elif st == "level": v = f"📈 {pl.get('level', 1)} ур."
            elif st == "rademka_wins": v = f"👊 {pl.get('wins', 0)} побед"
            else: v = ""
            rv = pl.get('rank', '').split(' ')
            ri = f" ({rv[1]})" if len(rv) > 1 and st != "rademka_wins" else ""
            tt += f"{mds[i] if i < 10 else f'{i + 1}.'} <code>{nn}</code>{ri} — {v}\n"
        tt += f"\n📊 <i>Всего пацанов в системе: {len(tp)}</i>"
        uid = c.from_user.id
        for i, pl in enumerate(tp):
            if pl.get('user_id') == uid:
                tt += f"\n\n🎯 <b>Твоя позиция:</b> {mds[i] if i < 10 else str(i + 1)}"
                break
        await eoa(c, tt, top_sort_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка загрузки топа: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data.startswith("inventory_"))
async def cia(c):
    try:
        await c.answer()
        a = c.data.replace("inventory_", "")
        if a == "use": await c.answer("Функция использования предметов в разработке!", show_alert=True)
        elif a == "sort":
            await c.answer("Инвентарь отсортирован!", show_alert=True)
            await ci(c)
        elif a == "trash":
            await eoa(c, "🗑️ <b>ВЫБРОСИТЬ МУСОР</b>\n\nТы уверен? Это действие удалит:\n• Все 'перчатки'\n• Все 'швабры'\n• Все 'вёдра'\n\nЗато освободит место в инвентаре!", confirmation_keyboard("trash_inventory"))
        else: await c.answer("Неизвестное действие", show_alert=True)
    except Exception as e:
        await c.answer(f"Ошибка инвентаря: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "confirm_trash_inventory")
async def cct(c):
    try:
        await c.answer("🗑️ Удаление...")
        p = await get_patsan(c.from_user.id)
        i = p.get("inventory", [])
        n = [x for x in i if x not in ["перчатки", "швабра", "ведро"]]
        if (r := len(i) - len(n)) > 0:
            p["inventory"] = n
            await save_patsan(p)
            await eoa(c, f"✅ <b>МУСОР ВЫБРОШЕН!</b>\n\nВыброшено предметов: {r}\nОсталось в инвентаре: {len(n)}\n\n<i>Теперь есть место для чего-то полезного!</i>", main_keyboard())
        else:
            await eoa(c, "🤷 <b>НЕТ МУСОРА</b>\n\nВ твоём инвентаре не нашлось мусора.\nВсё полезное, всё пригодится!", main_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка удаления мусора: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "shop")
async def cs(c):
    try:
        await c.answer()
        from handlers.shop import callback_shop as sh
        await sh(c)
    except Exception as e:
        await c.answer(f"Ошибка магазина: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data.startswith("buy_"))
async def cb(c):
    try:
        await c.answer("💰 Покупка...")
        from handlers.shop import callback_buy as sb
        await sb(c)
    except Exception as e:
        await c.answer(f"Ошибка покупки: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data.in_(["level_progress", "level_next", "atm_regen_time", "atm_max_info", "atm_boosters"]))
async def handle_progress(c):
    try:
        await c.answer()
        if c.data in ["level_progress", "level_next"]: await cls(c)
        elif c.data in ["atm_regen_time", "atm_max_info", "atm_boosters"]: await cas(c)
    except Exception:
        await c.answer("Ошибка загрузки", show_alert=True)

@router.callback_query(F.data.in_(["rademka_stats", "rademka_top", "rademka_random"]))
async def handle_placeholders(c):
    try:
        await c.answer()
        if c.data == "rademka_random":
            from handlers.nickname_and_rademka import rademka_random
            await rademka_random(c)
        elif c.data == "rademka_stats":
            from handlers.nickname_and_rademka import rademka_stats
            await rademka_stats(c)
        elif c.data == "rademka_top":
            from handlers.nickname_and_rademka import rademka_top
            await rademka_top(c)
    except Exception:
        await c.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "my_reputation")
async def cmr(c):
    try:
        await c.answer()
        p = await get_patsan_cached(c.from_user.id)
        await c.answer(f"Твоя репутация (авторитет): {p.get('avtoritet', 1)}", show_alert=True)
    except Exception:
        await c.answer("Ошибка репутации", show_alert=True)

@router.callback_query(F.data == "top_reputation")
async def ctr(c):
    try:
        await c.answer()
        from handlers.commands import cmd_top
        await cmd_top(c.message)
    except Exception:
        await c.answer("Ошибка топа репутации", show_alert=True)

@router.callback_query(F.data == "change_nickname")
async def ccn(c, state: FSMContext):
    try:
        await c.answer()
        from handlers.nickname_and_rademka import process_nickname
        await process_nickname(c.message, state)
    except Exception:
        await c.answer("Ошибка смены ника", show_alert=True)

# ДОБАВЛЕНЫ НОВЫЕ ОБРАБОТЧИКИ ДЛЯ КНОПОК "НАЗАД"
@router.callback_query(F.data == "back_rademka")
async def back_rademka_handler(c):
    try:
        await c.answer()
        from handlers.nickname_and_rademka import callback_rademka
        await callback_rademka(c)
    except Exception as e:
        await c.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "back_profile")
async def back_profile_handler(c):
    try:
        await c.answer()
        await cpr(c)  # Вызываем обработчик профиля
    except Exception as e:
        await c.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "back_inventory")
async def back_inventory_handler(c):
    try:
        await c.answer()
        await ci(c)  # Вызываем обработчик инвентаря
    except Exception as e:
        await c.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)

@router.callback_query()
async def uc(c):
    try:
        await c.answer(f"Кнопка '{c.data}' пока не работает. Разработчик в курсе!", show_alert=True)
    except: pass

get_user_rank = gr
get_emoji = ge
