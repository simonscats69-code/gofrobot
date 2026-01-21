from aiogram import Router, types, F, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import time
import random
import asyncio
from database.db_manager import *
from keyboards.keyboards import *

r = Router()

def gr(p):
    if 'rank_emoji' in p and 'rank_name' in p:
        return p['rank_emoji'], p['rank_name']
    
    a = p.get('avtoritet', 1)
    R = {
        1: ("👶", "Пацанчик"),
        11: ("👊", "Браток"),
        51: ("👑", "Авторитет"),
        201: ("🐉", "Царь гофры"),
        501: ("🏛️", "Император"),
        1001: ("💩", "БОГ ГОВНА")
    }
    rn, re = "Пацанчик", "👶"
    
    for t, (e, n) in sorted(R.items()):
        if a >= t:
            rn, re = n, e
    
    p['rank_emoji'], p['rank_name'] = re, rn
    return re, rn

async def eoa(c, t, kb=None, p="HTML"):
    try:
        await c.message.edit_text(t, reply_markup=kb, parse_mode=p)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

def pb(c, t, l=10):
    f = int((c / t) * l) if t > 0 else 0
    return "█" * f + "░" * (l - f)

def ft(s):
    if s < 60:
        return f"{s}с"
    m, h = s // 60, s // 3600
    return f"{h}ч {m % 60}м" if h > 0 else f"{m}м {s % 60}с"

def ge(i):
    m = {
        "двенашка": "🧱",
        "атмосфера": "🌀",
        "энергетик": "⚡",
        "перчатки": "🧤",
        "швабра": "🧹",
        "ведро": "🪣",
        "золотая_двенашка": "🌟",
        "кристалл_атмосферы": "💎",
        "секретная_схema": "📜",
        "супер_двенашка": "✨",
        "вечный_двигатель": "⚙️",
        "царский_обед": "👑",
        "бустер_атмосфер": "🌀"
    }
    return m.get(i, "📦")

class IgnoreNotModifiedMiddleware(BaseMiddleware):
    async def __call__(self, h, e, d):
        try:
            return await h(e, d)
        except TelegramBadRequest as ex:
            if "message is not modified" in str(ex) or ("Bad Request" in str(ex) and "exactly the same" in str(ex)):
                if cb := d.get('callback_query', getattr(e, 'callback_query', None)):
                    if hasattr(cb, 'answer'):
                        await cb.answer()
                return
            raise

r.callback_query.middleware(IgnoreNotModifiedMiddleware())

async def mmt(p):
    a, m = p.get('atm_count', 0), p.get('max_atm', 12)
    re, rn = gr(p)
    return f"<b>Главное меню</b>\n{re} <b>{rn}</b> | ⭐ {p.get('avtoritet', 1)} | 📈 Ур. {p.get('level', 1)}\n\n🌀 Атмосферы: [{pb(a, m)}] {a}/{m}\n💸 Деньги: {p.get('dengi', 0)}р | 🐍 Змий: {p.get('zmiy', 0):.1f}кг\n\n<i>Выбери действие, пацан:</i>"

async def _complete_operation(callback, func, uid, act):
    try:
        result = await func(uid)
        if result and len(result) >= 2:
            p, r_data = result[1], result[2] if len(result) > 2 else {}
            
            ex = {}
            if act == "davka":
                u = p.get("upgrades",{})
                ex["nm"] = "\n🥛 Ряженка жмёт двенашку как надо! (+75%)" if u.get("ryazhenka") else "\n🧋 Бублэки создают нужную турбулентность! (+35% к шансу)" if u.get("bubbleki") else ""
                ex["sm"] = "\n💪 <b>Специализация 'Давила': +50% к давке!</b>" if p.get("specialization") == "давила" else ""
                ex["dm"] = "\n✨ <b>Нашёл двенашку в турбулентности!</b>" if r_data.get("dvenashka_found") else ""
                ex["rm"] = f"\n🌟 <b>Редкая находка: {r_data['rare_item_found']}!</b>" if r_data.get("rare_item_found") else ""
                ex["em"] = f"\n📚 +{r_data.get('exp_gained', 0)} опыта" if r_data.get('exp_gained', 0) > 0 else ""
                ex["tg"] = r_data.get('total_grams', 0) / 1000 if r_data.get('total_grams') else 0
            elif act == "sdat":
                ex["abt"] = f"\n⭐ <b>Бонус авторитета:</b> +{r_data['avtoritet_bonus']}р" if r_data.get('avtoritet_bonus', 0) > 0 else ""
                ex["em"] = f"\n📚 +{r_data.get('exp_gained', 0)} опыта" if r_data.get('exp_gained', 0) > 0 else ""
            
            if h := AH.get(act):
                text = h["t"].format(**{**p, **r_data, **ex})
                try:
                    await eoa(callback, text, main_keyboard())
                except:
                    try:
                        await callback.message.edit_text(text[:4000], parse_mode="HTML", reply_markup=main_keyboard())
                    except:
                        await callback.message.answer(text[:4000], parse_mode="HTML")
    except Exception as e:
        try:
            await callback.message.answer(f"❌ Ошибка при завершении: {str(e)[:100]}")
        except:
            pass

AH = {
    "davka": {
        "func": davka_zmiy,
        "t": "<b>Заварвариваем дело...</b>{nm}{sm}\n🔄 Потрачено атмосфер: {cost}\n<i>\"{wm} говна за 25 секунд высрал я сейчас\"</i>\n➕ {tg:.3f} кг коричневага{dm}{rm}{em}\nВсего змия накоплено: {zmiy:.3f} кг\n⚡ Осталось атмосфер: {atm_count}/{max_atm}"
    },
    "sdat": {
        "func": sdat_zmiy,
        "t": "<b>Сдал коричневага на металлолом</b>\n📦 Сдано: {oz:.3f} кг змия\n💰 <b>Получил: {tm} руб.</b>{abt}{em}\n💸 Теперь на кармане: {dengi} руб.\n📈 Уровень: {level} ({experience}/?? опыта)\n<i>Приёмщик: \"Опять эту дрянь принёс... Но плачу больше!\"</i>"
    }
}

async def ha(c, act):
    try:
        await c.answer("🔄 Обработка...")
    except Exception:
        pass
    
    try:
        if not (h := AH.get(act)):
            return
        
        uid = c.from_user.id
        
        try:
            result = await asyncio.wait_for(h["func"](uid), timeout=7.0)
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
            ex["nm"] = "\n🥛 Ряженка жмёт двенашку как надо! (+75%)" if u.get("ryazhenka") else "\n🧋 Бублэки создают нужную турбулентность! (+35% к шансу)" if u.get("bubbleki") else ""
            ex["sm"] = "\n💪 <b>Специализация 'Давила': +50% к давке!</b>" if p.get("specialization") == "давила" else ""
            ex["dm"] = "\n✨ <b>Нашёл двенашку в турбулентности!</b>" if r.get("dvenashka_found") else ""
            ex["rm"] = f"\n🌟 <b>Редкая находка: {r['rare_item_found']}!</b>" if r.get("rare_item_found") else ""
            ex["em"] = f"\n📚 +{r.get('exp_gained', 0)} опыта" if r.get('exp_gained', 0) > 0 else ""
            ex["tg"] = r.get('total_grams', 0) / 1000 if r.get('total_grams') else 0
        elif act == "sdat":
            ex["abt"] = f"\n⭐ <b>Бонус авторитета:</b> +{r['avtoritet_bonus']}р" if r.get('avtoritet_bonus', 0) > 0 else ""
            ex["em"] = f"\n📚 +{r.get('exp_gained', 0)} опыта" if r.get('exp_gained', 0) > 0 else ""
        
        await eoa(c, h["t"].format(**{**p, **r, **ex}), main_keyboard())
        
    except Exception as e:
        error_msg = str(e)[:100]
        try:
            await eoa(c, f"❌ Ошибка: {error_msg}", main_keyboard())
        except:
            await c.message.answer(f"❌ Ошибка: {error_msg}")

@r.callback_query(F.data.in_(["davka", "sdat"]))
async def cba(c):
    try:
        await c.answer("🔄 Обработка...")
    except Exception as e:
        pass
    
    await ha(c, c.data)

@r.callback_query(F.data == "back_main")
async def bm(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        await eoa(c, await mmt(p), main_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "nickname_menu")
async def nm(c):
    try:
        await c.answer()
        
        from handlers.commands import cmd_nickname
        await cmd_nickname(c.message)
    except Exception:
        await c.answer("Ошибка загрузки меню ника", show_alert=True)

@r.callback_query(F.data == "daily")
async def cd(c):
    try:
        await c.answer()
        
        from handlers.commands import cmd_daily
        await cmd_daily(c.message)
    except Exception:
        await c.answer("Ошибка загрузки ежедневной награды", show_alert=True)

@r.callback_query(F.data == "achievements")
async def ca(c):
    try:
        await c.answer()
        
        from handlers.commands import cmd_achievements
        await cmd_achievements(c.message)
    except Exception:
        await c.answer("Ошибка загрузки достижений", show_alert=True)

@r.callback_query(F.data == "rademka")
async def cr(c):
    try:
        await c.answer()
        
        from handlers.commands import cmd_rademka
        await cmd_rademka(c.message)
    except Exception:
        await c.answer("Ошибка загрузки радёмки", show_alert=True)

@r.callback_query(F.data == "pump")
async def cp(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        d, z, n = p.get('skill_davka', 1), p.get('skill_zashita', 1), p.get('skill_nahodka', 1)
        cs = {'davka': 180 + (d * 10), 'zashita': 270 + (z * 15), 'nahodka': 225 + (n * 12)}
        
        await eoa(c, f"<b>Прокачка скиллов:</b>\n💰 Деньги: {p.get('dengi', 0)} руб.\n📈 Уровень: {p.get('level', 1)} | 📚 Опыт: {p.get('experience', 0)}\n\n💪 <b>Давка змия</b> (+100г за уровень)\nУровень: {d} | Следующий: {cs['davka']}р/ур\n\n🛡️ <b>Защита атмосфер</b> (ускоряет восстановление)\nУровень: {z} | Следующий: {cs['zashita']}р/ур\n\n🔍 <b>Находка двенашек</b> (+5% шанс за уровень)\nУровень: {n} | Следующий: {cs['nahodka']}р/ур\n\n<i>Выбери, что прокачать:</i>", pump_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка прокачки: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data.startswith("pump_"))
async def cps(c):
    try:
        await c.answer("⚙️ Прокачка...")
        
        s, uid = c.data.split("_")[1], c.from_user.id
        p, res = await pump_skill(uid, s)
        await c.answer(res if p else res, show_alert=True)
        
        if p:
            await cp(c)
    except Exception as e:
        await c.answer(f"Ошибка прокачки: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "inventory")
async def ci(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        i, ab = p.get("inventory", []), p.get("active_boosts", {})
        
        if not i:
            t = "Пусто... Только пыль и тоска"
        else:
            cnt = {x: i.count(x) for x in set(i)}
            t = "<b>Твои вещи:</b>\n" + "\n".join(f"{ge(x)} {x}: {c} шт." for x, c in cnt.items())
        
        if ab:
            t += "\n\n<b>🔮 Активные бусты:</b>\n"
            for b, e in ab.items():
                if isinstance(e, (int, float)) and (tl := int(e) - int(time.time())) > 0:
                    t += f"• {b}: {tl // 3600}ч {(tl % 3600) // 60}м\n"
        
        await eoa(c, f"{t}\n\n🐍 Коричневагый змий: {p.get('zmiy', 0):.3f} кг\n🔨 Скрафчено предметов: {len(p.get('crafted_items', []))}", inventory_management_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка инвентаря: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "profile")
async def cpr(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        re, rn = gr(p)
        a, m, up = p.get('atm_count', 0), p.get('max_atm', 12), p.get("upgrades", {})
        bu, sp = [k for k, v in up.items() if v] if up else [], p.get("specialization")
        sb = get_specialization_bonuses(sp) if sp else {}
        
        t = f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n{re} <b>{rn}</b>\n👤 {p.get('nickname','Неизвестно')}\n⭐ Авторитет: {p.get('avtoritet', 1)}\n📈 Уровень: {p.get('level', 1)} | 📚 Опыт: {p.get('experience', 0)}\n\n<b>Ресурсы:</b>\n🌀 Атмосферы: [{pb(a, m)}] {a}/{m}\n⏱️ Восстановление: {ft(calculate_atm_regen_time(p))}\n🐍 Коричневаг: {p.get('zmiy', 0):.3f} кг\n💰 Деньги: {p.get('dengi', 0)} руб.\n\n<b>Скиллы:</b>\n💪 Давка: {p.get('skill_davka', 1)}\n🛡️ Защита: {p.get('skill_zashita', 1)}\n🔍 Находка: {p.get('skill_nahodka', 1)}"
        
        if bu:
            t += f"\n<b>🛒 Нагнетатели:</b>\n" + "\n".join(f"• {u}" for u in bu)
        
        if sp:
            t += f"\n<b>🌳 Специализация:</b> {sp}\n<i>Бонусы: {', '.join(sb.keys())}</i>"
        
        await eoa(c, t, profile_extended_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка профиля: {str(e)[:50]}", show_alert=True)

SP = {
    "davila": {
        "n": "Давила",
        "d": "Мастер давления коричневага",
        "r": "💪 Давка змия: 5 ур.\n🐍 Накоплено змия: 50кг",
        "b": "• +50% к выходу змия\n• -1 атмосфера на действие\n• Открывает: Гигантская давка",
        "p": 1500
    },
    "ohotnik": {
        "n": "Охотник за двенашками",
        "d": "Находит то, что другие не видят",
        "r": "🔍 Находка двенашек: 5 ур.\n🧱 Двенашка в инвентаре",
        "b": "• +15% к шансу находок\n• 5% шанс на редкий предмет\n• Открывает: Детектор двенашек",
        "p": 1200
    },
    "neprobivaemy": {
        "n": "Непробиваемый",
        "d": "Железные кишки и стальные нервы",
        "r": "🛡️ Защита атмосфер: 5 ур.\n⭐ Авторитет: 20",
        "b": "• -10% времени восстановления атмосфер\n• +15% защиты в радёмках\n• Открывает: Железный живот",
        "p": 2000
    }
}

@r.callback_query(F.data == "specializations")
async def csp(c):
    try:
        await c.answer()
        
        uid, p = c.from_user.id, await get_patsan_cached(c.from_user.id)
        cs = p.get("specialization", "")
        
        if cs:
            sb = get_specialization_bonuses(cs)
            if sb:
                bonuses_text = "\n".join(f"• {k}: {v}" for k, v in sb.items())
            else:
                bonuses_text = "• Нет информации о бонусах"
                
            await eoa(c, f"<b>🌳 Твоя специализация:</b> {cs}\n\n<b>Бонусы:</b>\n{bonuses_text}\n\n<i>Сейчас у тебя может быть только одна специализация.</i>\n<i>Чтобы сменить, нужно сначала сбросить текущую (стоимость: 2000р).</i>", back_to_specializations_keyboard())
            return
        
        av = await get_available_specializations(uid)
        t = "<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n<i>Специализация даёт уникальные бонусы и открывает новые возможности.</i>\n<i>Можно выбрать только одну. Выбор бесплатен при выполнении требований.</i>\n\n"
        
        if not av:
            t += "<i>Нет доступных специализаций. Выполните требования для их открытия.</i>"
        else:
            for s in av:
                if not isinstance(s, dict):
                    continue
                
                name = s.get('name', 'Неизвестно')
                description = s.get('description', 'Нет описания')
                available = s.get('available', False)
                price = s.get('price', 0)
                
                status = "✅ Доступна" if available else "❌ Недоступна"
                price_text = f" | Цена: {price}р" if available else ""
                
                t += f"<b>{name}</b> {status}{price_text}\n<i>{description}</i>\n"
                
                if not available and s.get("missing"):
                    missing_items = s['missing'][:2]
                    t += f"<code>Требуется: {', '.join(missing_items)}</code>\n"
                
                t += "\n"
        
        await eoa(c, t + "<i>Выбери специализацию для подробной информации:</i>", specializations_keyboard())
    
    except Exception as e:
        print(f"Ошибка в csp: {e}")
        error_msg = str(e)[:100] if e else "Неизвестная ошибка"
        await eoa(c, f"<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n<i>Произошла ошибка при загрузке специализаций.</i>\n\n<code>Ошибка: {error_msg}</code>", specializations_keyboard())

@r.callback_query(F.data.startswith("specialization_"))
async def csd(c):
    try:
        await c.answer()
        
        st = c.data.replace("specialization_", "")
        
        if st == "info":
            await eoa(c, "<b>🌳 ИНФОРМАЦИЯ О СПЕЦИАЛИЗАЦИЯХ</b>\n\n<b>Что даёт специализация?</b>\n• Уникальные бонусы к игровым механикам\n• Новые возможности и действия\n• Преимущества в определённых ситуации\n\n<b>Как получить?</b>\n1. Выполнить требования\n2. Иметь достаточно денег\n3. Выбрать и активировать\n\n<b>Можно ли сменить?</b>\nДа, но за 2000р.", specializations_info_keyboard())
            return
        
        if st not in SP:
            return await c.answer("Неизвестная специализация", show_alert=True)
        
        s = SP[st]
        await eoa(c, f"<b>🌳 {s['n'].upper()}</b>\n\n<i>{s['d']}</i>\n\n<b>💰 Цена:</b> {s['p']}р\n\n<b>📋 Требования:</b>\n{s['r']}\n\n<b>🎁 Бонусы:</b>\n{s['b']}\n\n<i>Выбрать эту специализацию?</i>", specialization_confirmation_keyboard(st))
    except Exception as e:
        await c.answer(f"Ошибка специализации: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data.startswith("specialization_buy_"))
async def csb(c):
    try:
        await c.answer("💰 Покупка...")
        
        sid, uid = c.data.replace("specialization_buy_", ""), c.from_user.id
        ok, msg = await buy_specialization(uid, sid)
        
        if ok:
            await eoa(c, f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n{msg}\n\nТеперь ты обладатель уникальной специализации!\nИспользуй её бонусы по максимуму.", main_keyboard())
        else:
            await c.answer(msg, show_alert=True)
            await csp(c)
    except Exception as e:
        await c.answer(f"Ошибка покупки: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "craft")
async def cc(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        await eoa(c, f"<b>🔨 КРАФТ ПРЕДМЕТОВ</b>\n\n<i>Создавай мощные предметы из ингредиентов!</i>\n\n📦 Инвентарь: {len(p.get('inventory', []))} предметов\n🔨 Скрафчено: {len(p.get('crafted_items', []))} предметов\n💰 Деньги: {p.get('dengi', 0)}р\n\n<b>Выбери действие:</b>", craft_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка крафта: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "craft_items")
async def cci(c):
    try:
        await c.answer()
        
        ci = await get_craftable_items(c.from_user.id)
        
        if not ci:
            await eoa(c, "😕 <b>НЕТ ДОСТУПНЫХ РЕЦЕПТОВ</b>\n\nУ тебя пока нет нужных ингредиентов для крафта.\nСобирай двенашки, атмосферы и другие предметы!", back_to_craft_keyboard())
            return
        
        t = "<b>🔨 ДОСТУПНЫЕ ДЛЯ КРАФТА:</b>\n\n"
        
        for i in ci:
            if not isinstance(i, dict):
                continue
                
            name = i.get('name', 'Неизвестно')
            description = i.get('description', '')
            can_craft = i.get('can_craft', False)
            success_chance = i.get('success_chance', 0)
            
            t += f"<b>{name}</b> {'✅ МОЖНО' if can_craft else '❌ НЕЛЬЗЯ'}\n<i>{description}</i>\n🎲 Шанс успеха: {int(success_chance * 100)}%\n"
            
            if not can_craft and i.get("missing"):
                missing_items = i['missing'][:2]
                t += f"<code>Не хватает: {', '.join(missing_items)}</code>\n"
            
            t += "\n"
        
        await eoa(c, t + "<i>Выбери предмет для крафта:</i>", craft_items_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка списка крафта: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data.startswith("craft_execute_"))
async def cce(c):
    try:
        await c.answer("🔨 Крафт...")
        
        rid, uid = c.data.replace("craft_execute_", ""), c.from_user.id
        ok, msg, res = await craft_item(uid, rid)
        
        if ok:
            nm, dur = res.get("item", "предмет"), res.get("duration")
            dt = f"\n⏱️ Действует: {dur // 3600} часов" if dur else ""
            await eoa(c, f"✨ <b>КРАФТ УСПЕШЕН!</b>\n\n{msg}{dt}\n\n🎉 Ты создал новый предмет!\nПроверь инвентарь, чтобы использовать его.", main_keyboard())
            await unlock_achievement(uid, "successful_craft", f"Успешный крафт: {nm}", 100)
        else:
            await eoa(c, f"💥 <b>КРАФТ ПРОВАЛЕН</b>\n\n{msg}\n\nИнгредиенты потеряны...\nПроверь снова, когда соберёшь больше!", back_to_craft_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка выполнения крафта: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "craft_recipes")
async def ccr(c):
    try:
        await c.answer()
        
        await eoa(c, "<b>📜 ВСЕ РЕЦЕПТЫ КРАФТА</b>\n\n<b>✨ Супер-двенашка</b>\nИнгредиенты: 3× двенашка, 500р\nШанс: 100% | Эффект: Повышает удачу на 1 час\n\n<b>⚡ Вечный двигатель</b>\nИнгредиенты: 5× атмосфера, 1× энергетик\nШанс: 80% | Эффект: Ускоряет восстановление атмосфер на 24ч\n\n<b>👑 Царский обед</b>\nИngредиенты: 1× курвасаны, 1× ряженка, 300р\nШанс: 100% | Эффект: Максимальный буст на 30 минут\n\n<b>🌀 Бустер атмосфер</b>\nИнгредиенты: 2× энергетик, 1× двенашка, 2000р\nШанс: 70% | Эффект: +3 к максимальному запасу атмосфер\n\n<i>Собирай ингредиенты и создавай мощные предметы!</i>", craft_recipes_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка рецептов: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "rademka_scout_menu")
async def csm(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        su, fl = p.get("rademka_scouts", 0), max(0, 5 - p.get("rademka_scouts", 0))
        
        await eoa(c, f"<b>🕵️ РАЗВЕДКА РАДЁМКИ</b>\n\n<i>Узнай точный шанс успеха перед атакой!</i>\n\n🎯 <b>Преимущества разведки:</b>\n• Точно знаешь шанс победы\n• Учитываются все факторы\n• Можно выбрать другую цель\n\n📊 <b>Твоя статистика:</b>\n• Использовано разведок: {su}\n• Бесплатных осталось: {fl}/5\n• Стоимость разведки: {0 if fl > 0 else 50}р\n\n<i>Выбери действие:</i>", rademka_scout_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка разведки: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "rademka_scout_random")
async def csr(c):
    try:
        await c.answer("🕵️ Разведка...")
        
        uid, tp = c.from_user.id, await get_top_players(limit=50, sort_by="avtoritet")
        tg = [p for p in tp if p.get("user_id") != uid]
        
        if not tg:
            await eoa(c, "😕 <b>НЕКОГО РАЗВЕДЫВАТЬ!</b>\n\nНа гофроцентрале кроме тебя никого нет...\nПриведи друзей, чтобы было кого разведывать!", back_to_rademka_keyboard())
            return
        
        t = random.choice(tg)
        ok, msg, sd = await rademka_scout(uid, t.get("user_id"))
        
        if not ok:
            return await c.answer(msg, show_alert=True)
        
        ch, tn, f = sd.get("chance", 50), t.get("nickname", "Неизвестно"), sd.get("factors", [])
        as_, ts = sd.get('attacker_stats', {}), sd.get('target_stats', {})
        ar, tr = as_.get('rank', ('👶', 'Пацанчик'))[1], ts.get('rank', ('👶', 'Пацанчик'))[1]
        
        txt = f"🎯 <b>РАЗВЕДКА ЗАВЕРШЕНА!</b>\n\n<b>Цель:</b> {tn}\n🎲 <b>Точный шанс победы:</b> {ch}%\n\n<b>📊 Факторы:</b>\n" + ("\n".join(f"• {x}" for x in f) if f else "• Неизвестные факторы") + f"\n\n<b>📈 Статистика:</b>\n• Твой авторитет: {as_.get('avtoritet', 0)} ({ar})\n• Его авторитет: {ts.get('avtoritet', 0)} ({tr})\n• Последняя активность: {ts.get('last_active_hours', 0)}ч назад\n\n💸 Стоимость разведки: {'Бесплатно' if sd.get('cost', 0) == 0 else '50р'}\n🕵️ Бесплатных разведок осталось: {sd.get('free_scouts_left', 0)}\n\n<i>Атаковать эту цель?</i>"
        
        await eoa(c, txt, rademka_fight_keyboard(t.get("user_id"), scouted=True))
    except Exception as e:
        await c.answer(f"Ошибка случайной разведки: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data.startswith("rademka_scout_"))
async def cst(c):
    try:
        await c.answer()
        
        d = c.data.replace("rademka_scout_", "")
        
        if d == "choose":
            await eoa(c, "🎯 <b>ВЫБОР ЦЕЛИ ДЛЯ РАЗВЕДКИ</b>\n\nДля этой функции нужен список игроков.\nПока используй случайную цель или выбери из топа.", rademka_scout_keyboard())
        elif d == "stats":
            p = await get_patsan_cached(c.from_user.id)
            su, fu = p.get("rademka_scouts", 0), min(5, p.get("rademka_scouts", 0))
            
            await eoa(c, f"📊 <b>СТАТИСТИКА РАЗВЕДОК</b>\n\n🕵️ Всего разведок: {su}\n🎯 Бесплатных: {fu}/5\n💰 Платных: {max(0, su - 5)}\n💸 Потрачено на разведки: {max(0, su - 5) * 50}р\n\n", rademka_scout_keyboard())
        else:
            try:
                result = await rademka_scout(c.from_user.id, int(d))
                await c.answer("Разведка выполнена!" if result[0] else "Ошибка разведки", show_alert=True)
            except ValueError:
                await c.answer("Ошибка: неверный ID цели", show_alert=True)
    except Exception as e:
        await c.answer(f"Ошибка разведки: {str(e)[:50]}", show_alert=True)

ACH = {
    "zmiy_collector": {
        "n": "Коллекционер змия",
        "d": "Собери определённое количество змия",
        "l": [
            {"g": 10, "r": 50, "t": "Новичок", "e": 10},
            {"g": 100, "r": 300, "t": "Любитель", "e": 50},
            {"g": 1000, "r": 1500, "t": "Профессионал", "e": 200},
            {"g": 10000, "r": 5000, "t": "КОРОЛЬ ГОФРОЦЕНТРАЛА", "e": 1000}
        ]
    },
    "money_maker": {
        "n": "Денежный мешок",
        "d": "Заработай много денег",
        "l": [
            {"g": 1000, "r": 100, "t": "Бедолага", "e": 10},
            {"g": 10000, "r": 1000, "t": "Состоятельный", "e": 100},
            {"g": 100000, "r": 5000, "t": "Олигарх", "e": 500},
            {"g": 1000000, "r": 25000, "t": "РОТШИЛЬД", "e": 2500}
        ]
    },
    "rademka_king": {
        "n": "Король радёмок",
        "d": "Победи в множестве радёмок",
        "l": [
            {"g": 5, "r": 200, "t": "Задира", "e": 20},
            {"g": 25, "r": 1000, "t": "Гроза района", "e": 100},
            {"g": 100, "r": 5000, "t": "Неприкасаемый", "e": 500},
            {"g": 500, "r": 25000, "t": "ЛЕГЕНДА РАДЁМКИ", "e": 2500}
        ]
    }
}

@r.callback_query(F.data == "achievements_progress")
async def cap(c):
    try:
        await c.answer()
        
        pd = await get_achievement_progress(c.from_user.id)
        
        if not pd:
            await eoa(c, "📊 <b>ПРОГРЕСС ДОСТИЖЕНИЙ</b>\n\nПока нет прогресса по уровневым достижениям.\nИграй активно, и прогресс появится!", achievements_progress_keyboard())
            return
        
        t = "<b>📊 ПРОГРЕСС ПО УРОВНЕВЫМ ДОСТИЖЕНИЯМ</b>\n\n"
        
        for aid, d in pd.items():
            t += f"<b>{d.get('name', 'Неизвестно')}</b>\n"
            
            if d.get('next_level'):
                t += f"Уровень: {d.get('current_level', 0)}/{len(d.get('all_levels', []))}\n"
                t += f"Прогресс: {d.get('current_progress', 0):.1f}/{d['next_level'].get('goal', 0)} ({d.get('progress_percent', 0):.1f}%)\n"
                t += f"Следующий уровень: {d['next_level'].get('title', '')} (+{d['next_level'].get('reward', 0)}р, +{d['next_level'].get('exp', 0)} опыта)\n"
            else:
                t += f"✅ Все уровни пройдены! (Максимум)\n"
            
            t += "\n"
        
        await eoa(c, t + "<i>Выбери достижение для подробной информации:</i>", achievements_progress_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка прогресса: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data.startswith("achievement_"))
async def cad(c):
    try:
        await c.answer()
        
        if (at := c.data.replace("achievement_", "")) not in ACH:
            return await c.answer("Неизвестное достижение", show_alert=True)
        
        a = ACH[at]
        t = f"<b>🏆 {a.get('n', 'Неизвестно').upper()}</b>\n\n<i>{a.get('d', '')}</i>\n\n<b>📊 Уровни:</b>\n"
        
        levels = a.get('l', [])
        for i, l in enumerate(levels, 1):
            t += f"{i}. <b>{l.get('t', '')}</b>: {l.get('g', 0)} → +{l.get('r', 0)}р (+{l.get('e', 0)} опыта)\n"
        
        t += "\n\n<i>Прогресс автоматически отслеживается во время игры.</i>"
        
        await eoa(c, t, back_to_profile_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка достижения: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "level_stats")
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

@r.callback_query(F.data == "atm_status")
async def cas(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        a, m = p.get('atm_count', 0), p.get('max_atm', 12)
        rt, bs = calculate_atm_regen_time(p), []
        
        if p.get("skill_zashita", 1) >= 10:
            bs.append("Скилл защиты ≥10: -10% времени")
        if p.get("specialization") == "непробиваемый":
            bs.append("Специализация: -10% времени")
        if "вечный_двигатель" in p.get("active_boosts", {}):
            bs.append("Вечный двигатель: -30% времени")
        
        t = f"<b>🌡️ СОСТОЯНИЕ АТМОСФЕР</b>\n\n🌀 <b>Текущий запас:</b> {a}/{m}\n📊 <b>Заполненность:</b> [{pb(a, m)}] {(a / m) * 100:.1f}%\n\n⏱️ <b>Время восстановления:</b>\n• 1 атмосфера: {ft(rt)}\n• До полного: {ft(rt * (m - a))}\n\n" + (f"⚡ <b>Активные бонусы:</b>\n" + "\n".join(f"• {b}" for b in bs) + "\n\n" if bs else "") + f"<b>ℹ️ Как увеличить?</b>\n• Каждый 5 уровень: +1 к максимуму\n• Бустер атмосфер: +3 к максимуму\n• Прокачка защиты: ускоряет восстановление\n"
        
        await eoa(c, t, atm_status_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка статуса атмосфер: {str(e)[:50]}", show_alert=True)

TO = {
    "avtoritet": ("авторитету", "⭐", "avtoritet"),
    "dengi": ("деньгам", "💰", "dengi"),
    "zmiy": ("змию", "🐍", "zmiy"),
    "total_skill": ("сумме скиллов", "💪", "total_skill"),
    "level": ("уровню", "📈", "level"),
    "rademka_wins": ("победам в радёмках", "👊", "rademka_wins")
}

@r.callback_query(F.data == "top")
async def ctm(c):
    try:
        await c.answer()
        
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

@r.callback_query(F.data.startswith("top_"))
async def cst(c):
    try:
        await c.answer()
        
        if (st := c.data.replace("top_", "")) not in TO:
            return await c.answer("Неизвестный тип топа", show_alert=True)
        
        sn, em, dk = TO[st]
        
        if st != "rademka_wins":
            tp = await get_top_players(limit=10, sort_by=dk)
        else:
            tp = await grwt()
        
        if not tp:
            return await eoa(c, "😕 <b>Топ пуст!</b>\n\nЕщё никто не заслужил места в рейтинге.\nБудь первым!", top_sort_keyboard())
        
        mds, tt = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"], f"{em} <b>Топ пацанов по {sn}:</b>\n\n"
        
        for i, pl in enumerate(tp[:10]):
            nn = pl.get('nickname', f'Пацан_{pl.get("user_id", "?")}')[:20] + ("..." if len(pl.get('nickname', '')) > 20 else "")
            
            if st == "avtoritet":
                v = f"⭐ {pl.get('avtoritet', 0)}"
            elif st == "dengi":
                dv = pl.get("dengi", 0)
                df = f'{dv}р'
                v = f"💰 {df}"
            elif st == "zmiy":
                zv = pl.get("zmiy", 0)
                zf = f'{zv:.1f}кг'
                v = f"🐍 {zf}"
            elif st == "total_skill":
                v = f"💪 {pl.get('total_skill', 0)} ур."
            elif st == "level":
                v = f"📈 {pl.get('level', 1)} ур."
            elif st == "rademka_wins":
                v = f"👊 {pl.get('wins', 0)} побед"
            else:
                v = ""
            
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

@r.callback_query(F.data.startswith("inventory_"))
async def cia(c):
    try:
        await c.answer()
        
        a = c.data.replace("inventory_", "")
        
        if a == "use":
            await c.answer("Функция использования предметов в разработке!", show_alert=True)
        elif a == "sort":
            await c.answer("Инвентарь отсортирован!", show_alert=True)
            await ci(c)
        elif a == "trash":
            await eoa(c, "🗑️ <b>ВЫБРОСИТЬ МУСОР</b>\n\nТы уверен? Это действие удалит:\n• Все 'перчатки'\n• Все 'швабры'\n• Все 'вёдра'\n\nЗато освободит место в инвентаре!", confirmation_keyboard("trash_inventory"))
        else:
            await c.answer("Неизвестное действие", show_alert=True)
    except Exception as e:
        await c.answer(f"Ошибка инвентаря: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "confirm_trash_inventory")
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

@r.callback_query(F.data == "shop")
async def cs(c):
    try:
        await c.answer()
        
        from handlers.shop import callback_shop as sh
        await sh(c)
    except Exception as e:
        await c.answer(f"Ошибка магазина: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data == "achievements_progress_all")
async def cpa(c):
    try:
        await c.answer()
        
        await cap(c)
    except Exception:
        await c.answer("Ошибка прогресса", show_alert=True)

@r.callback_query(F.data == "level_progress")
async def clp(c):
    try:
        await c.answer()
        
        await cls(c)
    except Exception:
        await c.answer("Ошибка прогресса уровней", show_alert=True)

@r.callback_query(F.data == "level_next")
async def cln(c):
    try:
        await c.answer()
        
        await cls(c)
    except Exception:
        await c.answer("Ошибка следующего уровня", show_alert=True)

@r.callback_query(F.data == "atm_regen_time")
async def cart(c):
    try:
        await c.answer()
        
        await cas(c)
    except Exception:
        await c.answer("Ошибка восстановления атмосфер", show_alert=True)

@r.callback_query(F.data == "atm_max_info")
async def cami(c):
    try:
        await c.answer()
        
        await cas(c)
    except Exception:
        await c.answer("Ошибка информации об атмосферах", show_alert=True)

@r.callback_query(F.data == "atm_boosters")
async def cab(c):
    try:
        await c.answer()
        
        await cas(c)
    except Exception:
        await c.answer("Ошибка бустеров атмосфер", show_alert=True)

@r.callback_query(F.data == "craft_history")
async def cch(c):
    try:
        await c.answer()
        
        await c.answer("История крафта пока недоступна", show_alert=True)
    except:
        pass

@r.callback_query(F.data.startswith("buy_"))
async def cb(c):
    try:
        await c.answer("💰 Покупка...")
        
        from handlers.shop import callback_buy as sb
        await sb(c)
    except Exception as e:
        await c.answer(f"Ошибка покупки: {str(e)[:50]}", show_alert=True)

@r.callback_query(F.data.startswith("spec_info_"))
async def csi(c):
    try:
        await c.answer()
        
        spec_id = c.data.replace("spec_info_", "")
        await c.answer(f"Информация о специализации {spec_id}", show_alert=True)
    except:
        pass

@r.callback_query(F.data.startswith("recipe_"))
async def cri(c):
    try:
        await c.answer()
        
        await c.answer("Информация о рецепте", show_alert=True)
    except:
        pass

@r.callback_query(F.data == "rademka_stats")
async def crs(c):
    try:
        await c.answer()
        
        await c.answer("Статистика радёмок пока недоступна", show_alert=True)
    except:
        pass

@r.callback_query(F.data == "rademka_top")
async def crt(c):
    try:
        await c.answer()
        
        await c.answer("Топ радёмок пока недоступен", show_alert=True)
    except:
        pass

@r.callback_query(F.data == "rademka_random")
async def crr(c):
    try:
        await c.answer()
        
        await c.answer("Случайная цель пока недоступна", show_alert=True)
    except:
        pass

@r.callback_query(F.data == "my_reputation")
async def cmr(c):
    try:
        await c.answer()
        
        p = await get_patsan_cached(c.from_user.id)
        await c.answer(f"Твоя репутация (авторитет): {p.get('avtoritet', 1)}", show_alert=True)
    except Exception:
        await c.answer("Ошибка репутации", show_alert=True)

@r.callback_query(F.data == "top_reputation")
async def ctr(c):
    try:
        await c.answer()
        
        from handlers.commands import cmd_top
        await cmd_top(c.message)
    except Exception:
        await c.answer("Ошибка топа репутации", show_alert=True)

@r.callback_query(F.data == "change_nickname")
async def ccn(c, state: FSMContext):
    try:
        await c.answer()
        
        from handlers.nickname_and_rademka import process_nickname
        await process_nickname(c.message, state)
    except Exception:
        await c.answer("Ошибка смены ника", show_alert=True)

@r.callback_query(F.data == "specialization_info")
async def csi2(c):
    try:
        await c.answer()
        
        await csd(c)
    except Exception:
        await c.answer("Ошибка информации о специализации", show_alert=True)

@r.callback_query(F.data.startswith("craft_"))
async def ccs(c):
    try:
        await c.answer()
        
        if c.data in ["craft_super_dvenashka", "craft_vechnyy_dvigatel", "craft_tarskiy_obed", "craft_booster_atm"]:
            item_id = c.data.replace("craft_", "")
            await c.answer(f"Крафт {item_id} начат", show_alert=True)
        else:
            await c.answer("Неизвестный предмет для крафта", show_alert=True)
    except:
        pass

@r.callback_query()
async def uc(c):
    try:
        await c.answer(f"Кнопка '{c.data}' пока не работает. Разработчик в курсе!", show_alert=True)
    except:
        pass

get_user_rank = gr
get_emoji = ge
router = r
