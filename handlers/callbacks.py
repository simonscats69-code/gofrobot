from aiogram import Router, types, F, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import time, random, asyncio
from db_manager import (
    get_patsan, save_patsan, get_top_players,
    save_rademka_fight, calculate_atm_regen_time, get_connection,
    davka_zmiy, uletet_zmiy, get_gofra_info, calculate_pvp_chance
)
from keyboards import (
    main_keyboard, gofra_info_kb, cable_info_kb, atm_status_keyboard,
    top_sort_keyboard, rademka_keyboard, nickname_keyboard, profile_extended_kb
)

router = Router()

def handle_callback_errors(func):
    async def wrapper(callback: types.CallbackQuery, *args, **kwargs):
        try:
            kwargs.pop('dispatcher', None)
            kwargs.pop('state', None)
            return await func(callback, *args, **kwargs)
        except Exception as e:
            import logging
            logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
            error_msg = f"❌ Ошибка: {str(e)[:100]}"
            try:
                await callback.answer(error_msg, show_alert=True)
            except:
                try:
                    await callback.message.answer(error_msg)
                except:
                    pass
            try:
                p = await get_patsan(callback.from_user.id)
                await callback.message.edit_text(
                    "Произошла ошибка\n\nВозвращаемся в главное меню...",
                    reply_markup=main_keyboard()
                )
            except:
                pass
    return wrapper

def ft(s):
    if s < 60: return f"{s}с"
    m, h, d = s // 60, s // 3600, s // 86400
    if d > 0: return f"{d}д {h%24}ч {m%60}м"
    if h > 0: return f"{h}ч {m%60}м {s%60}с"
    return f"{m}м {s%60}с"

def pb(c, t, l=10):
    f = int((c / t) * l) if t > 0 else 0
    return "█" * f + "░" * (l - f)

class IgnoreNotModifiedMiddleware(BaseMiddleware):
    async def __call__(self, h, e, d):
        try: return await h(e, d)
        except TelegramBadRequest as ex:
            if "message is not modified" in str(ex):
                if cb := d.get('callback_query', getattr(e, 'callback_query', None)):
                    if hasattr(cb, 'answer'): await cb.answer()
                return
            raise

router.callback_query.middleware(IgnoreNotModifiedMiddleware())

async def mmt(p):
    atm = p.get('atm_count', 0)
    max_atm = 12
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    return f"""Главное меню
{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {p.get('gofra', 1)} | 🔌 {p.get('cable_power', 1)}

🌀 Атмосферы: [{pb(atm, max_atm)}] {atm}/{max_atm}
🐍 Змий: {p.get('zmiy_grams', 0):.0f}г | 📊 Давок: {p.get('total_davki', 0)}

Выбери действие, пацан:"""

@router.callback_query(F.data == "back_main")
@handle_callback_errors
async def bm(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    await c.message.edit_text(await mmt(p), reply_markup=main_keyboard())

@router.callback_query(F.data.in_(["davka", "uletet"]))
@handle_callback_errors
async def handle_actions(c):
    await c.answer("🔄 Обработка...")
    
    if c.data == "davka":
        success, p, res = await davka_zmiy(c.from_user.id)
        if not success:
            await c.answer(res, show_alert=True)
            return
            
        davka_texts = [
            f"""🐍 ДАВКА КОРИЧНЕВАГА!

💩 Выдавил {res['zmiy_grams']}г КОРИЧНЕВАГО ЗМЕЯ!
🗑️ На полу остался килограмм говна...""",
            
            f"""🐍 ЗАВАРВАРИЛ ДВАНАШКУ!
    
⚡ Вылез {res['zmiy_grams']}г коричневага!
💩 Пахнет жутко...
🏗️ Гофра прокачалась!""",
            
            f"""🐍 КОРИЧНЕВАГ СДОХ!
    
📏 Свисло {res['zmiy_grams']}г говна
💩 Говна навалом...
🏗️ Гофра: {res['old_gofra']} → {res['new_gofra']}"""
        ]
        
        gofra_info = get_gofra_info(p.get('gofra', 1))
        text = random.choice(davka_texts) + f"""

⚡ Вес змия: {res['zmiy_grams']}г
🏗️ Гофра: {res['old_gofra']} → {res['new_gofra']}
{gofra_info['emoji']} Теперь: {gofra_info['name']}
🔌 Кабель: {res['old_cable_power']} → {res['new_cable_power']} (+{res['cable_power_gain']})
📈 Опыта: +{res['exp_gained']}

🌀 Атмосферы: 0/12 (полная перезарядка)
⚡ Скорость восстановления: x{res['atm_speed']:.2f}

Упорство пацана дало результат!"""
        
        await c.message.edit_text(text, reply_markup=main_keyboard())
        
    elif c.data == "uletet":
        success, p, res = await uletet_zmiy(c.from_user.id)
        if not success:
            await c.answer(res, show_alert=True)
            return
            
        text = f"""✈️ ЗМИЙ ОТПРАВЛЕН В КОРИЧНЕВУЮ СТРАНУ!

📦 Отправлено: {res['zmiy_grams']:.0f}г коричневага
🌍 Летит к братьям по говну...

🏗️ Гофра: {p.get('gofra', 1)}
🔌 Сила кабеля: {p.get('cable_power', 1)}

Диспетчер: "Рейс 322 готов к вылету! Курс - на коричневый закат!" """
        
        await c.message.edit_text(text, reply_markup=main_keyboard())

@router.callback_query(F.data == "profile")
@handle_callback_errors
async def cpr(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    
    atm = p.get('atm_count', 0)
    max_atm = 12
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    regen_info = calculate_atm_regen_time(p)
    
    text = f"""📊 ПРОФИЛЬ ПАЦАНА

{gofra_info['emoji']} {gofra_info['name']}
👤 {p.get('nickname', 'Пацанчик')}
🏗️ Гофра: {p.get('gofra', 1)}
🔌 Сила кабеля: {p.get('cable_power', 1)}

Ресурсы:
🌀 Атмосферы: [{pb(atm, max_atm)}] {atm}/{max_atm}
⏱️ Восстановление: {ft(regen_info['per_atm'])} за 1 атм.
🐍 Змий: {p.get('zmiy_grams', 0):.0f}г

Статистика:
📊 Всего давок: {p.get('total_davki', 0)}
📈 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г
⭐ Опыт: {p.get('experience', 0)}

Чем больше гофра - тем тяжелее змий!"""
    
    await c.message.edit_text(text, reply_markup=profile_extended_kb())

@router.callback_query(F.data == "gofra_info")
@handle_callback_errors
async def gofra_info_handler(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    text = f"""🏗️ ИНФОРМАЦИЯ О ГОФРЕ

{gofra_info['emoji']} {gofra_info['name']}
📊 Значение гофры: {p.get('gofra', 1)}

Характеристики:
⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}
⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г

Следующая гофра:"""
    
    if gofra_info.get('next_threshold'):
        progress = gofra_info['progress']
        next_gofra = get_gofra_info(gofra_info['next_threshold'])
        text += f"\n{gofra_info['emoji']} → {next_gofra['emoji']}"
        text += f"\n{next_gofra['name']} (от {gofra_info['next_threshold']} опыта)"
        text += f"\n📈 Прогресс: [{pb(progress, 1, 10)}] {progress*100:.1f}%"
        text += f"\n⚡ Новая скорость: x{next_gofra['atm_speed']:.2f}"
        text += f"\n⚖️ Новый вес: {next_gofra['min_grams']}-{next_gofra['max_grams']}г"
    else:
        text += "\n🎉 Максимальный уровень гофры!"
    
    text += "\n\nЧем больше гофра - тем тяжелее змий и быстрее атмосферы!"
    
    await c.message.edit_text(text, reply_markup=gofra_info_kb())

@router.callback_query(F.data == "cable_info")
@handle_callback_errors
async def cable_info_handler(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    
    text = f"""🔌 СИЛОВОЙ КАБЕЛЬ

💪 Сила кабеля: {p.get('cable_power', 1)}
⚔️ Бонус в PvP: +{p.get('cable_power', 1)}% к шансу

Как прокачать:
🐍 Дави змия - кабель укрепляется
⚖️ Каждые 1000г змия = +1 к силе
👊 Побеждай в радёмках

Текущий прогресс:
📊 Следующий уровень через: {1000 - (p.get('total_zmiy_grams', 0) % 1000):.0f}г змия

Сильный кабель = победы в радёмках!"""
    
    await c.message.edit_text(text, reply_markup=cable_info_kb())

@router.callback_query(F.data == "atm_status")
@handle_callback_errors
async def atm_status_handler(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    
    atm = p.get('atm_count', 0)
    max_atm = 12
    regen_info = calculate_atm_regen_time(p)
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    text = f"""🌡️ СОСТОЯНИЕ АТМОСФЕР

🌀 Текущий запас: {atm}/{max_atm}
📊 Заполненность: [{pb(atm, max_atm)}] {(atm/max_atm)*100:.1f}%

Восстановление:
⏱️ 1 атмосфера: {ft(regen_info['per_atm'])}
🕐 До полного: {ft(regen_info['total'])}
📈 Осталось: {regen_info['needed']} атмосфер

Влияние гофры:
{gofra_info['emoji']} {gofra_info['name']}
⚡ Скорость: x{gofra_info['atm_speed']:.2f}

Полные 12 атмосфер нужны для давки!"""
    
    await c.message.edit_text(text, reply_markup=atm_status_keyboard())

@router.callback_query(F.data.in_(["gofra_progress", "gofra_speed", "gofra_next", "cable_power_info", "cable_pvp_info", "cable_upgrade_info", "atm_regen_time"]))
@handle_callback_errors
async def details_handler(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    if c.data == "gofra_progress":
        if gofra_info.get('next_threshold'):
            progress = gofra_info['progress']
            next_gofra = get_gofra_info(gofra_info['next_threshold'])
            text = f"""📈 ПРОГРЕСС ГОФРЫ
            
{gofra_info['emoji']} → {next_gofra['emoji']}
{gofra_info['name']} → {next_gofra['name']}

📊 Прогресс: [{pb(progress, 1, 10)}] {progress*100:.1f}%
🎯 Нужно опыта: {gofra_info['next_threshold'] - p.get('gofra', 1)}
⭐ Текущий опыт: {p.get('gofra', 1)}/{gofra_info['next_threshold']}

Дави больше змия для прогресса!"""
        else:
            text = "🎉 МАКСИМАЛЬНАЯ ГОФРА!\n\nТы достиг максимального уровня гофры!"
        await c.message.edit_text(text, reply_markup=gofra_info_kb())
    
    elif c.data == "gofra_speed":
        text = f"""⚡ СКОРОСТЬ ВОССТАНОВЛЕНИЯ АТМОСФЕР

{gofra_info['emoji']} {gofra_info['name']}
⚡ Множитель скорости: x{gofra_info['atm_speed']:.2f}

Базовая скорость:
⏱️ 1 атмосфера: 2 часа

С вашей гофрой:
⏱️ 1 атмосфера: {ft(7200 * gofra_info['atm_speed'])}
🕐 12 атмосфер: {ft(7200 * 12 * gofra_info['atm_speed'])}

Следующие уровни:"""
        
        thresholds = [1, 10, 25, 50, 100, 200, 500, 1000]
        current_idx = thresholds.index(gofra_info['threshold']) if gofra_info['threshold'] in thresholds else len(thresholds)-1
        
        for i in range(1, 4):
            if current_idx + i < len(thresholds):
                next_threshold = thresholds[current_idx + i]
                next_info = get_gofra_info(next_threshold)
                text += f"\n{gofra_info['emoji']}→{next_info['emoji']} {next_info['name']}: x{next_info['atm_speed']:.2f}"
        await c.message.edit_text(text, reply_markup=gofra_info_kb())
    
    elif c.data == "gofra_next":
        regen_info = calculate_atm_regen_time(p)
        text = f"""⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ

🌀 Атмосфер сейчас: {p.get('atm_count', 0)}/12
📈 Нужно восстановить: {regen_info['needed']} атм.

{gofra_info['emoji']} {gofra_info['name']}
⚡ Скорость: x{gofra_info['atm_speed']:.2f}

⏱️ Время на 1 атмосферу: {ft(regen_info['per_atm'])}
🕐 Общее время: {ft(regen_info['total'])}
📅 Полная зарядка: через {ft(regen_info['total'])}"""
        await c.message.edit_text(text, reply_markup=gofra_info_kb())
    
    elif c.data == "cable_power_info":
        text = f"""💪 СИЛА КАБЕЛЯ

🔌 Текущая сила: {p.get('cable_power', 1)}
⚔️ Бонус в PvP: +{p.get('cable_power', 1)}% к шансу

Как работает:
• Каждый 1000г змия = +1 к силе
• Победы в радёмках тоже дают +1

Прогресс:
📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г
📈 Следующий +1 через: {1000 - (p.get('total_zmiy_grams', 0) % 1000):.0f}г

Сильный кабель = победы!"""
        await c.message.edit_text(text, reply_markup=cable_info_kb())
    
    elif c.data == "cable_pvp_info":
        text = f"""⚔️ КАБЕЛЬ В PvP

🔌 Сила кабеля: {p.get('cable_power', 1)}
🎯 Влияние на шанс: +{p.get('cable_power', 1)}%

Как считается шанс:
• База: 50% (равные силы)
• Разница в кабеле: ±1% за каждую единицу
• Разница в гофре: ±0.5% за каждые 10 опыта

Пример:
• Ваш кабель: 10, враг: 5 → +5% к шансу
• Ваша гофра: 100, враг: 50 → +2.5% к шансу
• Итого: 50% + 5% + 2.5% = 57.5%

Укрепляй кабель - побеждай чаще!"""
        await c.message.edit_text(text, reply_markup=cable_info_kb())
    
    elif c.data == "cable_upgrade_info":
        text = f"""📈 ПРОКАЧКА КАБЕЛЯ

🔌 Текущая сила: {p.get('cable_power', 1)}
📊 Змия для следующего уровня: {1000 - (p.get('total_zmiy_grams', 0) % 1000):.0f}г

Способы прокачки:
1. 🐍 Давка змия
   • Каждые 1000г = +1 к силе
   • Чем тяжелее змий - тем быстрее

2. 👊 Победы в радёмках
   • Каждая победа = +1 к силе
   • Проигрыш не отнимает силу

3. 📊 Общий прогресс
   • Всего змия: {p.get('total_zmiy_grams', 0):.0f}г
   • Уровень кабеля: {p.get('cable_power', 1)}

Кабель = сила пацана!"""
        await c.message.edit_text(text, reply_markup=cable_info_kb())
    
    elif c.data == "atm_regen_time":
        regen_info = calculate_atm_regen_time(p)
        text = f"""⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ

🌀 Атмосфер сейчас: {p.get('atm_count', 0)}/12
📈 Нужно восстановить: {regen_info['needed']} атм.

{gofra_info['emoji']} {gofra_info['name']}
⚡ Скорость: x{gofra_info['atm_speed']:.2f}

⏱️ Время на 1 атмосферу: {ft(regen_info['per_atm'])}
🕐 Общее время: {ft(regen_info['total'])}
📅 Полная зарядка: через {ft(regen_info['total'])}"""
        await c.message.edit_text(text, reply_markup=atm_status_keyboard())

@router.callback_query(F.data == "top")
@handle_callback_errors
async def ctm(c):
    try:
        await c.answer()
        await c.message.edit_text(
            "🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА\n\nВыбери, по какому показателю сортировать рейтинг:",
            reply_markup=top_sort_keyboard()
        )
    except Exception as e:
        await c.answer(f"Ошибка топа: {str(e)[:50]}", show_alert=True)

async def grwt():
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT u.user_id,u.nickname,u.gofra,u.cable_power,COUNT(rf.id) as wins FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id GROUP BY u.user_id,u.nickname,u.gofra,u.cable_power ORDER BY wins DESC LIMIT 10')
        r = await cur.fetchall()
        await cn.close()
        return [dict(x) | {"wins": x["wins"] or 0, "zmiy_grams": 0, "atm_count": 0} for x in r]
    except Exception:
        return []

@router.callback_query(F.data.startswith("top_"))
@handle_callback_errors
async def cst(c):
    try:
        await c.answer()
        sort_map = {
            "gofra": ("гофре", "🏗️", "gofra"),
            "cable": ("кабелю", "🔌", "cable_power"),
            "zmiy": ("змию", "🐍", "zmiy_grams"),
            "atm": ("атмосферам", "🌀", "atm_count")
        }
        
        st = c.data.replace("top_", "")
        if st not in sort_map:
            return await c.answer("Неизвестный тип топа", show_alert=True)
            
        sn, em, dk = sort_map[st]
        tp = await get_top_players(limit=10, sort_by=dk)
        
        if not tp: 
            return await c.message.edit_text("😕 Топ пуст!\n\nЕщё никто не заслужил места в рейтинге.\nБудь первым!", reply_markup=top_sort_keyboard())
        
        mds = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        tt = f"{em} Топ пацанов по {sn}:\n\n"
        
        for i, pl in enumerate(tp[:10]):
            nn = pl.get('nickname', f'Пацан_{pl.get("user_id", "?")}')[:20] + ("..." if len(pl.get('nickname', '')) > 20 else "")
            
            if st == "gofra": 
                gi = get_gofra_info(pl.get('gofra', 1))
                v = f"🏗️ {pl.get('gofra', 0)} {gi['emoji']}"
            elif st == "cable":
                v = f"🔌 {pl.get('cable_power', 0)}"
            elif st == "zmiy":
                v = f"🐍 {pl.get('zmiy_grams', 0):.0f}г"
            elif st == "atm":
                v = f"🌀 {pl.get('atm_count', 0)}/12"
            else: 
                v = ""
            
            tt += f"{mds[i] if i < 10 else f'{i + 1}.'} {nn} — {v}\n"
        
        tt += f"\n📊 Всего пацанов в системе: {len(tp)}"
        
        uid = c.from_user.id
        for i, pl in enumerate(tp):
            if pl.get('user_id') == uid:
                tt += f"\n\n🎯 Твоя позиция: {mds[i] if i < 10 else str(i + 1)}"
                break
        
        await c.message.edit_text(tt, reply_markup=top_sort_keyboard())
    except Exception as e:
        await c.answer(f"Ошибка загрузки топа: {str(e)[:50]}", show_alert=True)

@router.callback_query(F.data == "nickname_menu")
@handle_callback_errors
async def nm(c):
    try:
        await c.answer()
        from handlers.commands import cmd_nickname
        await cmd_nickname(c.message)
    except Exception:
        await c.answer("Ошибка загрузки меню ника", show_alert=True)

@router.callback_query(F.data == "rademka")
@handle_callback_errors
async def cr(c):
    try:
        await c.answer()
        from handlers.commands import cmd_rademka
        await cmd_rademka(c.message)
    except Exception:
        await c.answer("Ошибка загрузки радёмки", show_alert=True)

get_user_rank = lambda p: ("👶", "Пацанчик")
get_emoji = lambda i: "📦"
