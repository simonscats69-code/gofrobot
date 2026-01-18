from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram import BaseMiddleware
import time
import random
from functools import partial
from database.db_manager import *
from keyboards.keyboards import *

router = Router()

# =================== УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ===================
async def edit_or_answer(callback: types.CallbackQuery, text: str, keyboard=None, parse_mode="HTML"):
    """Универсальная функция для редактирования или ответа"""
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

def progress_bar(current: int, total: int, length: int = 10) -> str:
    """Создание прогресс-бара"""
    filled = int((current / total) * length) if total > 0 else 0
    return "█" * filled + "░" * (length - filled)

def format_time(seconds: int) -> str:
    """Форматирование времени"""
    if seconds < 60:
        return f"{seconds}с"
    minutes = seconds // 60
    hours = minutes // 60
    if hours > 0:
        return f"{hours}ч {minutes % 60}м"
    return f"{minutes}м {seconds % 60}с"

def get_item_emoji(item_name: str) -> str:
    """Получение эмодзи для предмета"""
    emoji_map = {
        "двенашка": "🧱", "атмосфера": "🌀", "энергетик": "⚡",
        "перчатки": "🧤", "швабра": "🧹", "ведро": "🪣",
        "золотая_двенашка": "🌟", "кристалл_атмосферы": "💎",
        "секретная_схема": "📜", "супер_двенашка": "✨",
        "вечный_двигатель": "⚙️", "царский_обед": "👑",
        "бустер_атмосфер": "🌀"
    }
    return emoji_map.get(item_name, "📦")

# =================== МИДЛВАРЬ ===================
class IgnoreNotModifiedMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            error = str(e)
            if "message is not modified" in error or "Bad Request" in error and "exactly the same" in error:
                if callback := data.get('callback_query', event.callback_query if hasattr(event, 'callback_query') else None):
                    if hasattr(callback, 'answer'):
                        await callback.answer()
                return
            raise

router.callback_query.middleware(IgnoreNotModifiedMiddleware())

# =================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ===================
async def get_main_menu_text(patsan: dict) -> str:
    """Текст главного меню"""
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    progress = progress_bar(atm_count, max_atm)
    
    return (f"<b>Главное меню</b>\n"
            f"{patsan['rank_emoji']} <b>{patsan['rank_name']}</b> | ⭐ {patsan['avtoritet']} | 📈 Ур. {patsan.get('level', 1)}\n\n"
            f"🌀 Атмосферы: [{progress}] {atm_count}/{max_atm}\n"
            f"💸 Деньги: {patsan['dengi']}р | 🐍 Змий: {patsan['zmiy']:.1f}кг\n\n"
            f"<i>Выбери действие, пацан:</i>")

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    await edit_or_answer(callback, await get_main_menu_text(patsan), main_keyboard())

# =================== ОБРАБОТЧИКИ ДЕЙСТВИЙ ===================

@router.callback_query(F.data == "davka")
async def callback_davka(callback: types.CallbackQuery):
    """Давка змия"""
    user_id = callback.from_user.id
    patsan, result = await davka_zmiy(user_id)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    # Формируем сообщение
    cost = result.get("cost", 2)
    total = result.get("total", 0)
    kg, g = total//1000, total%1000
    weight_msg = f"{kg}кг {g}г" if g else f"{kg}кг"
    
    nagnetatel_msg = ""
    if patsan["upgrades"].get("ryazhenka"):
        nagnetatel_msg = "\n🥛 <i>Ряженка жмёт двенашку как надо! (+75%)</i>"
    elif patsan["upgrades"].get("bubbleki"):
        nagnetatel_msg = "\n🧋 <i>Бублэки создают нужную турбулентность! (+35% к шансу)</i>"
    
    spec_bonus_msg = ""
    if patsan.get("specialization") == "давила":
        spec_bonus_msg = "\n💪 <b>Специализация 'Давила': +50% к давке!</b>"
    
    dvenashka_msg = ""
    if result.get("found"):
        dvenashka_msg = "\n✨ <b>Нашёл двенашку в турбулентности!</b>"
    
    rare_item_msg = ""
    if result.get("rare"):
        rare_item_msg = f"\n🌟 <b>Редкая находка: {result['rare']}!</b>"
    
    exp_msg = ""
    if result.get("exp", 0) > 0:
        exp_msg = f"\n📚 +{result['exp']} опыта"
    
    text = f"""<b>Заварвариваем дело...</b>{nagnetatel_msg}{spec_bonus_msg}

🔄 Потрачено атмосфер: {cost}
<i>"{weight_msg} коричневага за 25 секунд высрал я сейчас"</i>

➕ {total/1000:.3f} кг коричневага{dvenashka_msg}{rare_item_msg}{exp_msg}

Всего змия накоплено: {patsan['zmiy']:.3f} кг
⚡ Осталось атмосфер: {patsan['atm_count']}/{patsan.get('max_atm', 12)}"""
    
    await edit_or_answer(callback, text, main_keyboard())

@router.callback_query(F.data == "sdat")
async def callback_sdat(callback: types.CallbackQuery):
    """Сдать змия"""
    user_id = callback.from_user.id
    patsan, result = await sdat_zmiy(user_id)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    avtoritet_bonus_text = ""
    if result.get("bonus", 0) > 0:
        avtoritet_bonus_text = f"\n⭐ <b>Бонус авторитета:</b> +{result['bonus']}р"
    
    exp_msg = ""
    if result.get("exp", 0) > 0:
        exp_msg = f"\n📚 +{result['exp']} опыта"
    
    text = f"""<b>Сдал коричневага на металлолом</b>

📦 Сдано: {result['old']:.3f} кг змия
💰 <b>Получил: {result['money']} руб.</b>{avtoritet_bonus_text}{exp_msg}

💸 Теперь на кармане: {patsan['dengi']} руб.
📈 Уровень: {patsan.get('level', 1)} ({patsan.get('experience', 0)} опыта)

<i>Приёмщик: "Опять эту дрянь принёс... Но плачу больше!"</i>"""
    
    await edit_or_answer(callback, text, main_keyboard())

# =================== ПРОКАЧКА ===================
@router.callback_query(F.data == "pump")
async def callback_pump(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    costs = {
        'davka': 180 + (patsan['skill_davka'] * 10),
        'zashita': 270 + (patsan['skill_zashita'] * 15),
        'nahodka': 225 + (patsan['skill_nahodka'] * 12)
    }
    
    text = (f"<b>Прокачка скиллов:</b>\n"
            f"💰 Деньги: {patsan['dengi']} руб.\n"
            f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n\n"
            f"💪 <b>Давка змия</b> (+100г за уровень)\n"
            f"Уровень: {patsan['skill_davka']} | Следующий: {costs['davka']}р/ур\n\n"
            f"🛡️ <b>Защита атмосфер</b> (ускоряет восстановление)\n"
            f"Уровень: {patsan['skill_zashita']} | Следующий: {costs['zashita']}р/ур\n\n"
            f"🔍 <b>Находка двенашек</b> (+5% шанс за уровень)\n"
            f"Уровень: {patsan['skill_nahodka']} | Следующий: {costs['nahodka']}р/ур\n\n"
            f"<i>Выбери, что прокачать:</i>")
    
    await edit_or_answer(callback, text, pump_keyboard())

@router.callback_query(F.data.startswith("pump_"))
async def callback_pump_skill(callback: types.CallbackQuery):
    skill = callback.data.split("_")[1]
    user_id = callback.from_user.id
    patsan, result = await pump_skill(user_id, skill)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    await callback.answer(result, show_alert=True)
    await callback_pump(callback)

# =================== ИНВЕНТАРЬ ===================
@router.callback_query(F.data == "inventory")
async def callback_inventory(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    inv = patsan.get("inventory", [])
    
    # Группируем предметы
    if not inv:
        inv_text = "Пусто... Только пыль и тоска"
    else:
        item_count = {}
        for item in inv:
            item_count[item] = item_count.get(item, 0) + 1
        
        inv_text = "<b>Твои вещи:</b>\n"
        for item, count in item_count.items():
            emoji = get_item_emoji(item)
            inv_text += f"{emoji} {item}: {count} шт.\n"
    
    # Активные бусты
    boosts_text = ""
    active_boosts = patsan.get("active_boosts", {})
    if active_boosts:
        boosts_text = "\n\n<b>🔮 Активные бусты:</b>\n"
        for boost, end_time in active_boosts.items():
            if isinstance(end_time, (int, float)):
                time_left = int(end_time) - int(time.time())
                if time_left > 0:
                    hours = time_left // 3600
                    minutes = (time_left % 3600) // 60
                    boosts_text += f"• {boost}: {hours}ч {minutes}м\n"
    
    text = f"{inv_text}{boosts_text}\n\n"
    text += f"🐍 Коричневагый змий: {patsan['zmiy']:.3f} кг\n"
    text += f"🔨 Скрафчено предметов: {len(patsan.get('crafted_items', []))}"
    
    await edit_or_answer(callback, text, inventory_management_keyboard())

# =================== ПРОФИЛЬ ===================
@router.callback_query(F.data == "profile")
async def callback_profile(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    
    # Апгрейды
    upgrade_text = ""
    bought_upgrades = [k for k, v in patsan["upgrades"].items() if v]
    if bought_upgrades:
        upgrade_text = "\n<b>🛒 Нагнетатели:</b>\n" + "\n".join([f"• {upg}" for upg in bought_upgrades])
    
    # Специализация
    spec_text = ""
    if patsan.get("specialization"):
        spec_bonuses = get_specialization_bonuses(patsan["specialization"])
        spec_text = f"\n<b>🌳 Специализация:</b> {patsan['specialization']}"
        if spec_bonuses:
            spec_text += f"\n<i>Бонусы: {', '.join(spec_bonuses.keys())}</i>"
    
    # Время восстановления
    regen_time = calculate_atm_regen_time(patsan)
    regen_str = format_time(regen_time)
    
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    progress = progress_bar(atm_count, max_atm)
    
    text = (f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n"
            f"{patsan['rank_emoji']} <b>{patsan['rank_name']}</b>\n"
            f"👤 {patsan['nickname']}\n"
            f"⭐ Авторитет: {patsan['avtoritet']}\n"
            f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n\n"
            f"<b>Ресурсы:</b>\n"
            f"🌀 Атмосферы: [{progress}] {atm_count}/{max_atm}\n"
            f"⏱️ Восстановление: {regen_str}\n"
            f"🐍 Коричневаг: {patsan['zmiy']:.3f} кг\n"
            f"💰 Деньги: {patsan['dengi']} руб.\n\n"
            f"<b>Скиллы:</b>\n"
            f"💪 Давка: {patsan['skill_davka']}\n"
            f"🛡️ Защита: {patsan['skill_zashita']}\n"
            f"🔍 Находка: {patsan['skill_nahodka']}"
            f"{upgrade_text}{spec_text}")
    
    await edit_or_answer(callback, text, profile_extended_keyboard())

# =================== СПЕЦИАЛИЗАЦИИ ===================

@router.callback_query(F.data == "specializations")
async def callback_specializations(callback: types.CallbackQuery):
    """Меню специализаций"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    current_spec = patsan.get("specialization", "")
    
    if current_spec:
        spec_bonuses = get_specialization_bonuses(current_spec)
        bonuses_text = "\n".join([f"• {k}: {v}" for k, v in spec_bonuses.items()])
        
        text = (f"<b>🌳 Твоя специализация:</b> {current_spec}\n\n"
                f"<b>Бонусы:</b>\n{bonuses_text}\n\n"
                f"<i>Сейчас у тебя может быть только одна специализация.</i>\n"
                f"<i>Чтобы сменить, нужно сначала сбросить текущую (стоимость: 2000р).</i>")
        
        await edit_or_answer(callback, text, back_to_specializations_keyboard())
        return
    
    available_specs = await get_available_specializations(user_id)
    text = "<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n"
    text += "<i>Специализация даёт уникальные бонусы и открывает новые возможности.</i>\n"
    text += "<i>Можно выбрать только одну. Выбор бесплатен при выполнении требований.</i>\n\n"
    
    for spec in available_specs:
        status = "✅ Доступна" if spec["available"] else "❌ Недоступна"
        price_text = f" | Цена: {spec['price']}р" if spec['available'] else ""
        text += f"<b>{spec['name']}</b> {status}{price_text}\n"
        text += f"<i>{spec['desc']}</i>\n"
        if not spec["available"] and spec["missing"]:
            text += f"<code>Требуется: {', '.join(spec['missing'])}</code>\n"
        text += "\n"
    
    text += "<i>Выбери специализацию для подробной информации:</i>"
    await edit_or_answer(callback, text, specializations_keyboard())

@router.callback_query(F.data.startswith("specialization_"))
async def callback_specialization_detail(callback: types.CallbackQuery):
    spec_type = callback.data.replace("specialization_", "")
    
    if spec_type == "info":
        text = ("<b>🌳 ИНФОРМАЦИЯ О СПЕЦИАЛИЗАЦИЯХ</b>\n\n"
                "<b>Что даёт специализация?</b>\n"
                "• Уникальные бонусы к игровым механикам\n"
                "• Новые возможности и действия\n"
                "• Преимущества в определённых ситуациях\n\n"
                "<b>Как получить?</b>\n"
                "1. Выполнить требования специализации\n"
                "2. Иметь достаточно денег для покупки\n"
                "3. Выбрать и активировать\n\n"
                "<b>Можно ли сменить?</b>\n"
                "Да, но за 2000р. Текущая специализация сбрасывается.")
        await edit_or_answer(callback, text, specializations_info_keyboard())
        return
    
    # Получаем информацию о конкретной специализации
    user_id = callback.from_user.id
    available_specs = await get_available_specializations(user_id)
    
    spec_found = None
    for spec in available_specs:
        if spec["id"] == spec_type:
            spec_found = spec
            break
    
    if not spec_found:
        await callback.answer("Неизвестная специализация", show_alert=True)
        return
    
    text = (f"<b>🌳 {spec_found['name'].upper()}</b>\n\n"
            f"<i>{spec_found['desc']}</i>\n\n"
            f"<b>💰 Цена:</b> {spec_found['price']}р\n\n")
    
    if spec_found["bon"]:
        text += "<b>🎁 Бонусы:</b>\n"
        for bonus, value in spec_found["bon"].items():
            text += f"• {bonus}: {value}\n"
        text += "\n"
    
    if not spec_found["available"] and spec_found["missing"]:
        text += f"<b>❌ Требования не выполнены:</b>\n"
        for miss in spec_found["missing"]:
            text += f"• {miss}\n"
        text += "\n"
    
    text += f"<i>Выбрать эту специализацию?</i>"
    
    await edit_or_answer(callback, text, specialization_confirmation_keyboard(spec_type))

@router.callback_query(F.data.startswith("specialization_buy_"))
async def callback_specialization_buy(callback: types.CallbackQuery):
    spec_id = callback.data.replace("specialization_buy_", "")
    user_id = callback.from_user.id
    
    success, message = await buy_specialization(user_id, spec_id)
    if success:
        text = (f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n"
                f"{message}\n\n"
                f"Теперь ты обладатель уникальной специализации!\n"
                f"Используй её бонусы по максимуму.")
        await edit_or_answer(callback, text, main_keyboard())
    else:
        await callback.answer(message, show_alert=True)
        await callback_specializations(callback)

# =================== КРАФТ ===================
@router.callback_query(F.data == "craft")
async def callback_craft(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    crafted_count = len(patsan.get("crafted_items", []))
    
    text = (f"<b>🔨 КРАФТ ПРЕДМЕТОВ</b>\n\n"
            f"<i>Создавай мощные предметы из ингредиентов!</i>\n\n"
            f"📦 Инвентарь: {len(patsan.get('inventory', []))} предметов\n"
            f"🔨 Скрафчено: {crafted_count} предметов\n"
            f"💰 Деньги: {patsan['dengi']}р\n\n"
            f"<b>Выбери действие:</b>")
    
    await edit_or_answer(callback, text, craft_keyboard())

@router.callback_query(F.data == "craft_items")
async def callback_craft_items(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    craftable_items = await get_craftable_items(user_id)
    
    if not craftable_items:
        text = ("😕 <b>НЕТ ДОСТУПНЫХ РЕЦЕПТОВ</b>\n\n"
                "У тебя пока нет нужных ингредиентов для крафта.\n"
                "Собирай двенашки, атмосферы и другие предметы!")
        await edit_or_answer(callback, text, back_to_craft_keyboard())
        return
    
    text = "<b>🔨 ДОСТУПНЫЕ ДЛЯ КРАФТА:</b>\n\n"
    for item in craftable_items:
        status = "✅ МОЖНО" if item["can"] else "❌ НЕЛЬЗЯ"
        text += f"<b>{item['name']}</b> {status}\n"
        text += f"<i>{item['desc']}</i>\n"
        text += f"🎲 Шанс успеха: {int(item['chance'] * 100)}%\n"
        if not item["can"] and item["miss"]:
            text += f"<code>Не хватает: {', '.join(item['miss'][:2])}</code>\n"
        text += "\n"
    
    text += "<i>Выбери предмет для крафта:</i>"
    await edit_or_answer(callback, text, craft_items_keyboard())

@router.callback_query(F.data.startswith("craft_execute_"))
async def callback_craft_execute(callback: types.CallbackQuery):
    recipe_id = callback.data.replace("craft_execute_", "")
    user_id = callback.from_user.id
    
    success, message, result = await craft_item(user_id, recipe_id)
    
    if success:
        item_name = result.get("item", "предмет")
        duration = result.get("dur")
        duration_text = ""
        if duration:
            hours = duration // 3600
            if hours > 0:
                duration_text = f"\n⏱️ Действует: {hours} часов"
        
        text = (f"✨ <b>КРАФТ УСПЕШЕН!</b>\n\n"
                f"{message}{duration_text}\n\n"
                f"🎉 Ты создал новый предмет!\n"
                f"Проверь инвентарь, чтобы использовать его.")
        
        await edit_or_answer(callback, text, main_keyboard())
        await unlock_achievement(user_id, "successful_craft", f"Успешный крафт: {item_name}", 100)
    else:
        text = (f"💥 <b>КРАФТ ПРОВАЛЕН</b>\n\n"
                f"{message}\n\n"
                f"Ингредиенты потеряны...\n"
                f"Попробуй снова, когда соберёшь больше!")
        
        await edit_or_answer(callback, text, back_to_craft_keyboard())

@router.callback_query(F.data == "craft_recipes")
async def callback_craft_recipes(callback: types.CallbackQuery):
    text = ("<b>📜 ВСЕ РЕЦЕПТЫ КРАФТА</b>\n\n"
            "<b>✨ Супер-двенашка</b>\n"
            "Ингредиенты: 3× двенашка, 500р\n"
            "Шанс: 100% | Эффект: Повышает удачу на 1 час\n\n"
            "<b>⚡ Вечный двигатель</b>\n"
            "Ингредиенты: 5× атмосфера, 1× энергетик\n"
            "Шанс: 80% | Эффект: Ускоряет восстановление атмосфер на 24ч\n\n"
            "<b>👑 Царский обед</b>\n"
            "Ингредиенты: 1× курвасаны, 1× ряженка, 300р\n"
            "Шанс: 100% | Эффект: Максимальный буст на 30 минут\n\n"
            "<b>🌀 Бустер атмосфер</b>\n"
            "Ингредиенты: 2× энергетик, 1× двенашка, 2000р\n"
            "Шанс: 70% | Эффект: +3 к максимальному запасу атмосфер\n\n"
            "<i>Собирай ингредиенты и создавай мощные предметы!</i>")
    
    await edit_or_answer(callback, text, craft_recipes_keyboard())

# =================== РАЗВЕДКА РАДЁМКИ ===================
@router.callback_query(F.data == "rademka_scout_menu")
async def callback_rademka_scout_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    scouts_used = patsan.get("rademka_scouts", 0)
    free_scouts_left = max(0, 5 - scouts_used)
    
    text = (f"<b>🕵️ РАЗВЕДКА РАДЁМКИ</b>\n\n"
            f"<i>Узнай точный шанс успеха перед атакой!</i>\n\n"
            f"🎯 <b>Преимущества разведки:</b>\n"
            f"• Точно знаешь шанс победы\n"
            f"• Учитываются все факторы\n"
            f"• Можно выбрать другую цель\n\n"
            f"📊 <b>Твоя статистика:</b>\n"
            f"• Использовано разведок: {scouts_used}\n"
            f"• Бесплатных осталось: {free_scouts_left}/5\n"
            f"• Стоимость разведки: {0 if free_scouts_left > 0 else 50}р\n\n"
            f"<i>Выбери действие:</i>")
    
    await edit_or_answer(callback, text, rademka_scout_keyboard())

@router.callback_query(F.data == "rademka_scout_random")
async def callback_rademka_scout_random(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    top_players = await get_top_players(limit=50, sort="avtoritet")
    possible_targets = [p for p in top_players if p["user_id"] != user_id]
    
    if not possible_targets:
        text = ("😕 <b>НЕКОГО РАЗВЕДЫВАТЬ!</b>\n\n"
                "На гофроцентрале кроме тебя никого нет...\n"
                "Приведи друзей, чтобы было кого разведывать!")
        await edit_or_answer(callback, text, back_to_rademka_keyboard())
        return
    
    target = random.choice(possible_targets)
    target_id = target["user_id"]
    
    success, message, scout_data = await rademka_scout(user_id, target_id)
    if not success:
        await callback.answer(message, show_alert=True)
        return
    
    chance = scout_data["chance"]
    target_name = target["nickname"]
    factors_text = "\n".join([f"• {f}" for f in scout_data["factors"]])
    
    text = (f"🎯 <b>РАЗВЕДКА ЗАВЕРШЕНА!</b>\n\n"
            f"<b>Цель:</b> {target_name}\n"
            f"🎲 <b>Точный шанс победы:</b> {chance}%\n\n"
            f"<b>📊 Факторы:</b>\n{factors_text}\n\n"
            f"<b>📈 Статистика:</b>\n"
            f"• Твой авторитет: {scout_data['attacker']['av']} ({scout_data['attacker']['rank'][1]})\n"
            f"• Его авторитет: {scout_data['target']['av']} ({scout_data['target']['rank'][1]})\n"
            f"• Последняя активность: {scout_data['target']['last_hrs']}ч назад\n\n"
            f"💸 Стоимость разведки: {'Бесплатно' if scout_data['cost'] == 0 else '50р'}\n"
            f"🕵️ Бесплатных разведок осталось: {scout_data['free_left']}\n\n"
            f"<i>Атаковать эту цель?</i>")
    
    await edit_or_answer(callback, text, rademka_fight_keyboard(target_id, scouted=True))

# =================== ДОСТИЖЕНИЯ ===================

@router.callback_query(F.data == "achievements_progress")
async def callback_achievements_progress(callback: types.CallbackQuery):
    """Прогресс достижений"""
    user_id = callback.from_user.id
    progress_data = await get_achievement_progress(user_id)
    
    if not progress_data:
        text = ("📊 <b>ПРОГРЕСС ДОСТИЖЕНИЙ</b>\n\n"
                "Пока нет прогресса по уровневым достижениям.\n"
                "Играй активно, и прогресс появится!")
        await edit_or_answer(callback, text, achievements_progress_keyboard())
        return
    
    text = "<b>📊 ПРОГРЕСС ПО УРОВНЕВЫМ ДОСТИЖЕНИЯМ</b>\n\n"
    for ach_id, data in progress_data.items():
        text += f"<b>{data['name']}</b>\n"
        if data['next']:
            text += f"Уровень: {data['cur_lvl']}\n"
            text += f"Прогресс: {data['prog']:.1f}/{data['next']} "
            text += f"({data['perc']:.1f}%)\n"
            text += f"Следующий уровень: {data['title']}\n"
        else:
            text += f"✅ Все уровни пройдены! (Максимум)\n"
        text += "\n"
    
    text += "<i>Выбери достижение для подробной информации:</i>"
    await edit_or_answer(callback, text, achievements_progress_keyboard())

# =================== СТАТИСТИКА УРОВНЕЙ ===================
@router.callback_query(F.data == "level_stats")
async def callback_level_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    current_level = patsan.get("level", 1)
    current_exp = patsan.get("experience", 0)
    
    # Рассчитываем опыт для следующего уровня
    required_exp = int(100 * (current_level ** 1.5))
    progress_percent = (current_exp / required_exp) * 100
    
    # Прогресс-бар
    progress_bars = 10
    filled_bars = int(progress_percent / 10)
    progress_bar_str = "█" * filled_bars + "░" * (progress_bars - filled_bars)
    
    # Награда за следующий уровень
    next_level_reward = (current_level + 1) * 100
    max_atm_increase = (current_level + 1) % 5 == 0
    
    text = (
        f"<b>📈 ИНФОРМАЦИЯ ОБ УРОВНЕ</b>\n\n"
        f"🏆 <b>Текущий уровень:</b> {current_level}\n"
        f"📚 <b>Опыт:</b> {current_exp}/{required_exp}\n"
        f"📊 <b>Прогресс:</b> [{progress_bar_str}] {progress_percent:.1f}%\n\n"
        f"🎁 <b>Награда за {current_level + 1} уровень:</b>\n"
        f"• +{next_level_reward}р\n"
    )
    
    if max_atm_increase:
        text += f"• +1 к максимальным атмосферам\n"
    
    text += f"\n<b>ℹ️ Как получить опыт?</b>\n"
    text += f"• Давка коричневага: 1-10 опыта\n"
    text += f"• Сдача змия: 5-20 опыта\n"
    text += f"• Прокачка скиллов: 15-30 опыта\n"
    text += f"• Достижения: 10-1000 опыта\n"
    text += f"• Ежедневные награды: переменный\n"
    
    await edit_or_answer(callback, text, level_stats_keyboard())

# =================== СОСТОЯНИЕ АТМОСФЕР ===================
@router.callback_query(F.data == "atm_status")
async def callback_atm_status(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    regen_time = calculate_atm_regen_time(patsan)
    regen_str = format_time(regen_time)
    
    # Бонусы
    bonuses = []
    if patsan.get("skill_zashita", 1) >= 10:
        bonuses.append("Скилл защиты ≥10: -10% времени")
    if patsan.get("specialization") == "непробиваемый":
        bonuses.append("Специализация: -10% времени")
    if "вечный_двигатель" in patsan.get("active_boosts", {}):
        bonuses.append("Вечный двигатель: -30% времени")
    
    progress = progress_bar(atm_count, max_atm)
    
    text = (f"<b>🌡️ СОСТОЯНИЕ АТМОСФЕР</b>\n\n"
            f"🌀 <b>Текущий запас:</b> {atm_count}/{max_atm}\n"
            f"📊 <b>Заполненность:</b> [{progress}] {(atm_count/max_atm)*100:.1f}%\n\n"
            f"⏱️ <b>Время восстановления:</b>\n"
            f"• 1 атмосфера: {regen_str}\n"
            f"• До полного: {format_time(regen_time * (max_atm - atm_count))}\n\n")
    
    if bonuses:
        text += f"⚡ <b>Активные бонусы:</b>\n"
        for bonus in bonuses:
            text += f"• {bonus}\n"
        text += "\n"
    
    text += (f"<b>ℹ️ Как увеличить?</b>\n"
             f"• Каждый 5 уровень: +1 к максимуму\n"
             f"• Бустер атмосфер: +3 к максимуму\n"
             f"• Прокачка защиты: ускоряет восстановление\n")
    
    await edit_or_answer(callback, text, atm_status_keyboard())

# =================== ТОП ИГРОКОВ ===================
@router.callback_query(F.data == "top")
async def callback_top_menu(callback: types.CallbackQuery):
    text = ("🏆 <b>ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА</b>\n\n"
            "Выбери, по какому показателю сортировать рейтинг:\n\n"
            "<i>Новые варианты:</i>\n"
            "• 📈 По уровню - кто больше прокачался\n"
            "• 👊 По победам в радёмках - кто самый дерзкий</i>")
    
    await edit_or_answer(callback, text, top_sort_keyboard())

@router.callback_query(F.data.startswith("top_"))
async def show_top(callback: types.CallbackQuery):
    sort_type = callback.data.replace("top_", "")
    
    sort_map = {
        "avtoritet": ("авторитету", "⭐", "avtoritet"),
        "dengi": ("деньгам", "💰", "dengi"),
        "zmiy": ("змию", "🐍", "zmiy"),
        "level": ("уровню", "📈", "level")
    }
    
    if sort_type not in sort_map:
        await callback.answer("Неизвестный тип топа", show_alert=True)
        return
    
    sort_name, emoji, db_key = sort_map[sort_type]
    
    # Получаем топ
    try:
        top_players = await get_top_players(limit=10, sort=db_key)
    except Exception as e:
        await callback.answer(f"Ошибка при получении топа: {e}", show_alert=True)
        return
    
    if not top_players:
        text = ("😕 <b>Топ пуст!</b>\n\n"
                "Ещё никто не заслужил места в рейтинге.\n"
                "Будь первым!")
        await edit_or_answer(callback, text, top_sort_keyboard())
        return
    
    # Формируем текст топа
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    top_text = f"{emoji} <b>Топ пацанов по {sort_name}:</b>\n\n"
    
    for i, player in enumerate(top_players):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        
        # Значение в зависимости от типа сортировки
        if sort_type == "avtoritet":
            value = f"⭐ {player['avtoritet']}"
        elif sort_type == "dengi":
            value = f"💰 {player['dengi']}р"
        elif sort_type == "zmiy":
            value = f"🐍 {player['zmiy']:.1f}кг"
        elif sort_type == "level":
            value = f"📈 {player.get('level', 1)} ур."
        else:
            value = ""
        
        nickname = player.get('nickname', f'Пацан_{player.get("user_id", "?")}')
        if len(nickname) > 20:
            nickname = nickname[:17] + "..."
        
        rank_info = ""
        if "rank_name" in player:
            rank_info = f" ({player['rank_name']})"
        
        top_text += f"{medal} <code>{nickname}</code>{rank_info} — {value}\n"
    
    top_text += f"\n📊 <i>Всего пацанов в системе: {len(top_players)}</i>"
    
    # Позиция текущего пользователя
    current_user_id = callback.from_user.id
    for i, player in enumerate(top_players):
        if player.get('user_id') == current_user_id:
            user_medal = medals[i] if i < len(medals) else str(i+1)
            top_text += f"\n\n🎯 <b>Твоя позиция:</b> {user_medal}"
            break
    
    await edit_or_answer(callback, top_text, top_sort_keyboard())

# =================== ДЕЙСТВИЯ С ИНВЕНТАРЁМ ===================
@router.callback_query(F.data.startswith("inventory_"))
async def callback_inventory_action(callback: types.CallbackQuery):
    action = callback.data.replace("inventory_", "")
    
    if action == "use":
        await callback.answer("Функция использования предметов в разработке!", show_alert=True)
    elif action == "sort":
        await callback.answer("Инвентарь отсортирован!", show_alert=True)
        await callback_inventory(callback)
    elif action == "trash":
        text = ("🗑️ <b>ВЫБРОСИТЬ МУСОР</b>\n\n"
                "Ты уверен? Это действие удалит:\n"
                "• Все 'перчатки'\n"
                "• Все 'швабры'\n"
                "• Все 'вёдра'\n\n"
                "Зато освободит место в инвентаре!")
        await edit_or_answer(callback, text, confirmation_keyboard("trash_inventory"))
    else:
        await callback.answer("Неизвестное действие", show_alert=True)

@router.callback_query(F.data == "confirm_trash_inventory")
async def callback_confirm_trash_inventory(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan(user_id)
    
    inventory = patsan.get("inventory", [])
    trash_items = ["перчатки", "швабра", "ведро"]
    
    count_before = len(inventory)
    new_inventory = [item for item in inventory if item not in trash_items]
    count_after = len(new_inventory)
    removed = count_before - count_after
    
    if removed > 0:
        patsan["inventory"] = new_inventory
        await save_patsan(patsan)
        
        text = (f"✅ <b>МУСОР ВЫБРОШЕН!</b>\n\n"
                f"Выброшено предметов: {removed}\n"
                f"Осталось в инвентаре: {count_after}\n\n"
                f"<i>Теперь есть место для чего-то полезного!</i>")
        await edit_or_answer(callback, text, main_keyboard())
    else:
        text = ("🤷 <b>НЕТ МУСОРА</b>\n\n"
                "В твоём инвентаре не нашлось мусора.\n"
                "Всё полезное, всё пригодится!")
        await edit_or_answer(callback, text, main_keyboard())
