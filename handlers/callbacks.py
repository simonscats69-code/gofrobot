from aiogram import Router, types, F, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import time, random, asyncio
from db_manager import (
    get_patsan, save_patsan, get_top_players,
    save_rademka_fight, calculate_atm_regen_time, get_connection,
    davka_zmiy, sdat_zmiy, get_gofra_info
)
from keyboards import (
    main_keyboard, gofra_info_kb, atm_status_keyboard,
    top_sort_keyboard, rademka_keyboard, nickname_keyboard,
    profile_extended_keyboard
)

router = Router()

# Декоратор для обработки ошибок
def handle_callback_errors(func):
    async def wrapper(callback: types.CallbackQuery, *args, **kwargs):
        try:
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
    """Форматирование времени"""
    if s < 60: return f"{s}с"
    m, h, d = s // 60, s // 3600, s // 86400
    if d > 0: return f"{d}д {h%24}ч {m%60}м"
    if h > 0: return f"{h}ч {m%60}м {s%60}с"
    return f"{m}м {s%60}с"

def pb(c, t, l=10):
    """Прогресс-бар"""
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
    """Главное меню текст"""
    atm = p.get('atm_count', 0)
    max_atm = 12
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    return f"""Главное меню
{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {p.get('gofra', 1)} | 💰 {p.get('dengi', 0)}р

🌀 Атмосферы: [{pb(atm, max_atm)}] {atm}/{max_atm}
🐍 Змий: {p.get('zmiy_cm', 0):.1f}см | 📊 Давок: {p.get('total_davki', 0)}

Выбери действие, пацан:"""

@router.callback_query(F.data == "back_main")
@handle_callback_errors
async def bm(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    await c.message.edit_text(await mmt(p), reply_markup=main_keyboard())

@router.callback_query(F.data.in_(["davka", "sdat"]))
@handle_callback_errors
async def handle_actions(c):
    await c.answer("🔄 Обработка...")
    
    if c.data == "davka":
        success, p, res = await davka_zmiy(c.from_user.id)
        if not success:
            await c.answer(res, show_alert=True)
            return
            
        gofra_info = get_gofra_info(p.get('gofra', 1))
        
        text = f"""🐍 ДАВКА КОРИЧНЕВАГА!

⚡ Силовой кабель свис: {res['cable_cm']}см
🏗️ Гофра: {res['old_gofra']} → {res['new_gofra']}
{gofra_info['emoji']} Теперь: {gofra_info['name']}
📈 Опыта: +{res['exp_gained']}

🌀 Атмосферы: 0/12 (полная перезарядка)
⚡ Скорость восстановления: x{res['atm_speed']:.1f}

Кабель завис идеально! Ждём перезарядки атмосфер..."""
        
        await c.message.edit_text(text, reply_markup=main_keyboard())
        
    elif c.data == "sdat":
        success, p, res = await sdat_zmiy(c.from_user.id)
        if not success:
            await c.answer(res, show_alert=True)
            return
            
        text = f"""💰 СДАЛ ЗМИЯ НА МЕТАЛЛОЛОМ

📦 Сдано: {res['zmiy_cm']:.1f}см змия
💰 Получил: {res['money']}р
   (база: {res['base_money']}р + бонус гофры: {res['gofra_bonus']}р)

💸 Теперь на кармане: {p.get('dengi', 0)}р
🏗️ Гофра: {p.get('gofra', 1)}

Приёмщик: "Кабель огонь! Беру с наценкой!" """
        
        await c.message.edit_text(text, reply_markup=main_keyboard())

@router.callback_query(F.data == "profile")
@handle_callback_errors
async def cpr(c):
    await c.answer()
    p = await get_patsan(c.from_user.id)
    
    atm = p.get('atm_count', 0)
    max_atm = 12
    gofra_info = get_gofra_info(p.get('gofra', 1))
    
    # Расчет времени восстановления
    regen_info = calculate_atm_regen_time(p)
    
    text = f"""📊 ПРОФИЛЬ ПАЦАНА

{gofra_info['emoji']} {gofra_info['name']}
👤 {p.get('nickname', 'Пацанчик')}
🏗️ Гофра: {p.get('gofra', 1)}

Ресурсы:
🌀 Атмосферы: [{pb(atm, max_atm)}] {atm}/{max_atm}
⏱️ Восстановление: {ft(regen_info['per_atm'])} за 1 атм.
🐍 Змий: {p.get('zmiy_cm', 0):.1f}см
💰 Деньги: {p.get('dengi', 0)}р

Статистика:
📊 Всего давок: {p.get('total_davki', 0)}
📈 Всего змия: {p.get('total_zmiy_cm', 0):.1f}см
⭐ Опыт: {p.get('experience', 0)}

Чем больше гофра - тем быстрее атмосферы!"""
    
    await c.message.edit_text(text, reply_markup=profile_extended_keyboard())

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
⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.1f}
📏 Длина кабеля: {gofra_info['min_cm']:.1f}-{gofra_info['max_cm']:.1f}см

Следующая гофра:"""
    
    if gofra_info.get('next_threshold'):
        progress = gofra_info['progress']
        next_gofra = get_gofra_info(gofra_info['next_threshold'])
        text += f"\n{gofra_info['emoji']} → {next_gofra['emoji']}"
        text += f"\n{next_gofra['name']} (от {gofra_info['next_threshold']} опыта)"
        text += f"\n📈 Прогресс: [{pb(progress, 1, 10)}] {progress*100:.1f}%"
        text += f"\n⚡ Новая скорость: x{next_gofra['atm_speed']:.1f}"
    else:
        text += "\n🎉 Максимальный уровень гофры!"
    
    text += "\n\nЧем больше гофра - тем быстрее атмосферы и длиннее кабель!"
    
    await c.message.edit_text(text, reply_markup=gofra_info_kb())

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
⚡ Скорость: x{gofra_info['atm_speed']:.1f}

Полные 12 атмосфер нужны для давки!"""
    
    await c.message.edit_text(text, reply_markup=atm_status_keyboard())

@router.callback_query(F.data.in_(["gofra_progress", "gofra_speed", "gofra_next", "atm_regen_time"]))
@handle_callback_errors
async def gofra_details(c):
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
    
    elif c.data == "gofra_speed":
        text = f"""⚡ СКОРОСТЬ ВОССТАНОВЛЕНИЯ АТМОСФЕР

{gofra_info['emoji']} {gofra_info['name']}
⚡ Множитель скорости: x{gofra_info['atm_speed']:.1f}

Базовая скорость:
⏱️ 1 атмосфера: 24 часа

С вашей гофрой:
⏱️ 1 атмосфера: {ft(86400 * gofra_info['atm_speed'])}
🕐 12 атмосфер: {ft(86400 * 12 * gofra_info['atm_speed'])}

Следующие уровни:"""
        
        # Показываем следующие 3 уровня
        thresholds = [1, 10, 25, 50, 100, 200, 500, 1000]
        current_idx = thresholds.index(gofra_info['threshold'])
        
        for i in range(1, 4):
            if current_idx + i < len(thresholds):
                next_threshold = thresholds[current_idx + i]
                next_info = get_gofra_info(next_threshold)
                text += f"\n{gofra_info['emoji']}→{next_info['emoji']} {next_info['name']}: x{next_info['atm_speed']:.1f}"
    
    elif c.data in ["gofra_next", "atm_regen_time"]:
        regen_info = calculate_atm_regen_time(p)
        text = f"""⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ

🌀 Атмосфер сейчас: {p.get('atm_count', 0)}/12
📈 Нужно восстановить: {regen_info['needed']} атм.

{gofra_info['emoji']} {gofra_info['name']}
⚡ Скорость: x{gofra_info['atm_speed']:.1f}

⏱️ Время на 1 атмосферу: {ft(regen_info['per_atm'])}
🕐 Общее время: {ft(regen_info['total'])}
📅 Полная зарядка: через {ft(regen_info['total'])}"""
    
    await c.message.edit_text(text, reply_markup=gofra_info_kb())

@router.callback_query(F.data == "top")
@handle_callback_errors
async def ctm(c):
    try:
        await c.answer()
        await c.message.edit_text(
            "🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА\n\nВыбери, по какому показателю сортировать рейтинг:\n\nНовые варианты:\n• 🏗️ По гофре - кто больше разъездил\n• 👊 По победам в радёмках - кто самый дерзкий",
            reply_markup=top_sort_keyboard()
        )
    except Exception as e:
        await c.answer(f"Ошибка топа: {str(e)[:50]}", show_alert=True)

async def grwt():
    try:
        cn = await get_connection()
        cur = await cn.execute('SELECT u.user_id,u.nickname,u.gofra,COUNT(rf.id) as wins FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id GROUP BY u.user_id,u.nickname,u.gofra ORDER BY wins DESC LIMIT 10')
        r = await cur.fetchall()
        await cn.close()
        return [dict(x) | {"wins": x["wins"] or 0, "zmiy_cm": 0, "dengi": 0, "atm_count": 0} for x in r]
    except Exception:
        return []

@router.callback_query(F.data.startswith("top_"))
@handle_callback_errors
async def cst(c):
    try:
        await c.answer()
        sort_map = {
            "gofra": ("гофре", "🏗️", "gofra"),
            "zmiy": ("змию", "🐍", "zmiy_cm"),
            "dengi": ("деньгам", "💰", "dengi"),
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
                v = f"🏗️ {pl.get('gofra', 0)}"
            elif st == "dengi":
                v = f"💰 {pl.get('dengi', 0)}р"
            elif st == "zmiy":
                v = f"🐍 {pl.get('zmiy_cm', 0):.1f}см"
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

# Остальные обработчики (nickname_menu, daily, rademka, inventory и т.д.) 
# нужно будет адаптировать под новую систему

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

# Добавляем недостающие импорты для совместимости
get_user_rank = lambda p: ("👶", "Пацанчик")  # Заглушка для совместимости
get_emoji = lambda i: "📦"  # Заглушка для совместимости
