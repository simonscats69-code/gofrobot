from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram import BaseMiddleware
import time
from database.db_manager import (
    get_patsan, get_patsan_cached, davka_zmiy, sdat_zmiy, pump_skill,
    buy_upgrade, get_user_achievements, get_available_specializations,
    buy_specialization, get_craftable_items, craft_item, get_achievement_progress,
    rademka_scout, get_top_players, save_patsan, unlock_achievement,
    calculate_atm_regen_time, get_specialization_bonuses
)
from keyboards.keyboards import (
    main_keyboard, pump_keyboard, back_keyboard, shop_keyboard,
    specializations_keyboard, craft_keyboard, craft_items_keyboard,
    rademka_scout_keyboard, profile_extended_keyboard, confirmation_keyboard,
    specialization_confirmation_keyboard,
    inventory_management_keyboard, back_to_craft_keyboard, back_to_specializations_keyboard
)
from keyboards.new_keyboards import (
    daily_keyboard, achievements_keyboard, rademka_keyboard,
    rademka_fight_keyboard, back_to_rademka_keyboard, achievements_progress_keyboard,
    level_stats_keyboard, atm_status_keyboard, specializations_info_keyboard,
    craft_recipes_keyboard, top_sort_keyboard, back_to_profile_keyboard,
    craft_confirmation_keyboard
)

router = Router()

# Middleware для обработки ошибки "message not modified"
class IgnoreNotModifiedMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            error_message = str(e)
            if "message is not modified" in error_message or "Bad Request" in error_message and "specified new message content and reply markup are exactly the same" in error_message:
                # Получаем callback_query из данных или event
                callback_query = None
                if hasattr(event, 'callback_query'):
                    callback_query = event.callback_query
                elif 'callback_query' in data:
                    callback_query = data['callback_query']
                
                if callback_query and hasattr(callback_query, 'answer'):
                    await callback_query.answer()
                return
            raise

# Регистрируем middleware для обработки callback_query
router.callback_query.middleware(IgnoreNotModifiedMiddleware())

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    progress = int((atm_count / max_atm) * 10)
    progress_bar = "█" * progress + "░" * (10 - progress)
    await callback.message.edit_text(
        f"<b>Главное меню</b>\n"
        f"{patsan['rank_emoji']} <b>{patsan['rank_name']}</b> | ⭐ {patsan['avtoritet']} | 📈 Ур. {patsan.get('level', 1)}\n\n"
        f"🌀 Атмосферы: [{progress_bar}] {atm_count}/{max_atm}\n"
        f"💸 Деньги: {patsan['dengi']}р | 🐍 Змий: {patsan['zmiy']:.1f}кг\n\n"
        f"<i>Выбери действие, пацан:</i>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "davka")
async def callback_davka(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan, result = await davka_zmiy(user_id)
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    nagnetatel_msg = ""
    if patsan["upgrades"].get("ryazhenka"):
        nagnetatel_msg = "\n🥛 <i>Ряженка жмёт двенашку как надо! (+75%)</i>"
    elif patsan["upgrades"].get("bubbleki"):
        nagnetatel_msg = "\n🧋 <i>Бублэки создают нужную турбулентность! (+35% к шансу)</i>"
    spec_bonus_msg = ""
    if patsan.get("specialization") == "давила":
        spec_bonus_msg = "\n💪 <b>Специализация 'Давила': +50% к давке!</b>"
    dvenashka_msg = ""
    if result.get("dvenashka_found"):
        dvenashka_msg = "\n✨ <b>Нашёл двенашку в турбулентности!</b>"
    rare_item_msg = ""
    if result.get("rare_item_found"):
        rare_item_msg = f"\n🌟 <b>Редкая находка: {result['rare_item_found']}!</b>"
    exp_msg = f"\n📚 +{result.get('exp_gained', 0)} опыта" if result.get('exp_gained', 0) > 0 else ""
    await callback.message.edit_text(
        f"<b>Заварвариваем дело...</b>{nagnetatel_msg}{spec_bonus_msg}\n\n"
        f"🔄 Потрачено атмосфер: {result['cost']}\n"
        f"<i>\"{result['weight_msg']} говна за 25 секунд высрал я сейчас\"</i>\n\n"
        f"➕ {result['total_grams']/1000:.3f} кг коричневага"
        f"{dvenashka_msg}{rare_item_msg}{exp_msg}\n\n"
        f"Всего змия накоплено: {patsan['zmiy']:.3f} кг\n"
        f"⚡ Осталось атмосфер: {patsan['atm_count']}/{patsan.get('max_atm', 12)}",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "sdat")
async def callback_sdat(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan, result = await sdat_zmiy(user_id)
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    avtoritet_bonus_text = ""
    if result['avtoritet_bonus'] > 0:
        avtoritet_bonus_text = f"\n⭐ <b>Бонус авторитета:</b> +{result['avtoritet_bonus']}р"
    exp_msg = f"\n📚 +{result.get('exp_gained', 0)} опыта" if result.get('exp_gained', 0) > 0 else ""
    await callback.message.edit_text(
        f"<b>Сдал коричневага на металлолом</b>\n\n"
        f"📦 Сдано: {result['old_zmiy']:.3f} кг змия\n"
        f"💰 <b>Получил: {result['total_money']} руб.</b>"
        f"{avtoritet_bonus_text}{exp_msg}\n\n"
        f"💸 Теперь на кармане: {patsan['dengi']} руб.\n"
        f"📈 Уровень: {patsan.get('level', 1)} ({patsan.get('experience', 0)}/?? опыта)\n\n"
        f"<i>Приёмщик: \"Опять эту дрянь принёс... Но плачу больше!\"</i>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "pump")
async def callback_pump(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    davka_cost = 180 + (patsan['skill_davka'] * 10)
    zashita_cost = 270 + (patsan['skill_zashita'] * 15)
    nahodka_cost = 225 + (patsan['skill_nahodka'] * 12)
    text = (
        f"<b>Прокачка скиллов:</b>\n"
        f"💰 Деньги: {patsan['dengi']} руб.\n"
        f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n\n"
        f"💪 <b>Давка змия</b> (+100г за уровень)\n"
        f"Уровень: {patsan['skill_davka']} | Следующий: {davka_cost}р/ур\n\n"
        f"🛡️ <b>Защита атмосфер</b> (ускоряет восстановление)\n"
        f"Уровень: {patsan['skill_zashita']} | Следующий: {zashita_cost}р/ур\n\n"
        f"🔍 <b>Находка двенашек</b> (+5% шанс за уровень)\n"
        f"Уровень: {patsan['skill_nahodka']} | Следующий: {nahodka_cost}р/ур\n\n"
        f"<i>Выбери, что прокачать:</i>"
    )
    await callback.message.edit_text(
        text, 
        reply_markup=pump_keyboard(),
        parse_mode="HTML"
    )

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

@router.callback_query(F.data == "inventory")
async def callback_inventory(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    inv = patsan.get("inventory", [])
    if not inv:
        inv_text = "Пусто... Только пыль и тоска"
    else:
        item_count = {}
        for item in inv:
            item_count[item] = item_count.get(item, 0) + 1
        inv_text = "<b>Твои вещи:</b>\n"
        for item, count in item_count.items():
            emoji = {
                "двенашка": "🧱", "атмосфера": "🌀", "энергетик": "⚡",
                "перчатки": "🧤", "швабра": "🧹", "ведро": "🪣",
                "золотая_двенашка": "🌟", "кристалл_атмосферы": "💎",
                "секретная_схема": "📜", "супер_двенашка": "✨",
                "вечный_двигатель": "⚙️", "царский_обед": "👑",
                "бустер_атмосфер": "🌀"
            }.get(item, "📦")
            inv_text += f"{emoji} {item}: {count} шт.\n"
    active_boosts = patsan.get("active_boosts", {})
    boosts_text = ""
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
    await callback.message.edit_text(
        text, 
        reply_markup=inventory_management_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "profile")
async def callback_profile(callback: types.CallbackQuery):
    patsan = await get_patsan_cached(callback.from_user.id)
    upgrades = patsan["upgrades"]
    bought_upgrades = [k for k, v in upgrades.items() if v]
    upgrade_text = ""
    if bought_upgrades:
        upgrade_text = "\n<b>🛒 Нагнетатели:</b>\n" + "\n".join([f"• {upg}" for upg in bought_upgrades])
    spec_text = ""
    if patsan.get("specialization"):
        spec_bonuses = get_specialization_bonuses(patsan["specialization"])
        spec_text = f"\n<b>🌳 Специализация:</b> {patsan['specialization']}"
        if spec_bonuses:
            spec_text += f"\n<i>Бонусы: {', '.join(spec_bonuses.keys())}</i>"
    regen_time = calculate_atm_regen_time(patsan)
    regen_minutes = regen_time // 60
    regen_seconds = regen_time % 60
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    progress = int((atm_count / max_atm) * 10)
    progress_bar = "█" * progress + "░" * (10 - progress)
    await callback.message.edit_text(
        f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n"
        f"{patsan['rank_emoji']} <b>{patsan['rank_name']}</b>\n"
        f"👤 {patsan['nickname']}\n"
        f"⭐ Авторитет: {patsan['avtoritet']}\n"
        f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n\n"
        f"<b>Ресурсы:</b>\n"
        f"🌀 Атмосферы: [{progress_bar}] {atm_count}/{max_atm}\n"
        f"⏱️ Восстановление: {regen_minutes}м {regen_seconds}с\n"
        f"🐍 Коричневаг: {patsan['zmiy']:.3f} кг\n"
        f"💰 Деньги: {patsan['dengi']} руб.\n\n"
        f"<b>Скиллы:</b>\n"
        f"💪 Давка: {patsan['skill_davka']}\n"
        f"🛡️ Защита: {patsan['skill_zashita']}\n"
        f"🔍 Находка: {patsan['skill_nahodka']}"
        f"{upgrade_text}{spec_text}",
        reply_markup=profile_extended_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "specializations")
async def callback_specializations(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    current_spec = patsan.get("specialization", "")
    if current_spec:
        spec_bonuses = get_specialization_bonuses(current_spec)
        bonuses_text = "\n".join([f"• {k}: {v}" for k, v in spec_bonuses.items()])
        await callback.message.edit_text(
            f"<b>🌳 Твоя специализация:</b> {current_spec}\n\n"
            f"<b>Бонусы:</b>\n{bonuses_text}\n\n"
            f"<i>Сейчас у тебя может быть только одна специализация.</i>\n"
            f"<i>Чтобы сменить, нужно сначала сбросить текущую (стоимость: 2000р).</i>",
            reply_markup=back_to_specializations_keyboard(),
            parse_mode="HTML"
        )
        return
    available_specs = await get_available_specializations(user_id)
    text = "<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n"
    text += "<i>Специализация даёт уникальные бонусы и открывает новые возможности.</i>\n"
    text += "<i>Можно выбрать только одну. Выбор бесплатен при выполнении требований.</i>\n\n"
    for spec in available_specs:
        status = "✅ Доступна" if spec["available"] else "❌ Недоступна"
        price_text = f" | Цена: {spec['price']}р" if spec['available'] else ""
        text += f"<b>{spec['name']}</b> {status}{price_text}\n"
        text += f"<i>{spec['description']}</i>\n"
        if not spec["available"] and spec["missing"]:
            text += f"<code>Требуется: {', '.join(spec['missing'])}</code>\n"
        text += "\n"
    text += "<i>Выбери специализацию для подробной информации:</i>"
    await callback.message.edit_text(
        text,
        reply_markup=specializations_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("specialization_"))
async def callback_specialization_detail(callback: types.CallbackQuery):
    spec_type = callback.data.replace("specialization_", "")
    spec_map = {
        "davila": {
            "name": "Давила",
            "description": "Мастер давления коричневага",
            "requirements": "💪 Давка змия: 5 ур.\n🐍 Накоплено змия: 50кг",
            "bonuses": "• +50% к выходу змия\n• -1 атмосфера на действие\n• Открывает: Гигантская давка",
            "price": 1500
        },
        "ohotnik": {
            "name": "Охотник за двенашками",
            "description": "Находит то, что другие не видят",
            "requirements": "🔍 Находка двенашек: 5 ур.\n🧱 Двенашка в инвентаре",
            "bonuses": "• +15% к шансу находок\n• 5% шанс на редкий предмет\n• Открывает: Детектор двенашек",
            "price": 1200
        },
        "neprobivaemy": {
            "name": "Непробиваемый",
            "description": "Железные кишки и стальные нервы",
            "requirements": "🛡️ Защита атмосфер: 5 ур.\n⭐ Авторитет: 20",
            "bonuses": "• -10% времени восстановления атмосфер\n• +15% защиты в радёмках\n• Открывает: Железный живот",
            "price": 2000
        }
    }
    if spec_type not in spec_map and spec_type != "info":
        await callback.answer("Неизвестная специализация", show_alert=True)
        return
    if spec_type == "info":
        await callback.message.edit_text(
            "<b>🌳 ИНФОРМАЦИЯ О СПЕЦИАЛИЗАЦИЯХ</b>\n\n"
            "<b>Что даёт специализация?</b>\n"
            "• Уникальные бонусы к игровым механикам\n"
            "• Новые возможности и действия\n"
            "• Преимущества в определённых ситуациях\n\n"
            "<b>Как получить?</b>\n"
            "1. Выполнить требования специализации\n"
            "2. Иметь достаточно денег для покупки\n"
            "3. Выбрать и активировать\n\n"
            "<b>Можно ли сменить?</b>\n"
            "Да, но за 2000р. Текущая специализация сбрасывается.",
            reply_markup=specializations_info_keyboard(),
            parse_mode="HTML"
        )
        return
    spec_data = spec_map[spec_type]
    await callback.message.edit_text(
        f"<b>🌳 {spec_data['name'].upper()}</b>\n\n"
        f"<i>{spec_data['description']}</i>\n\n"
        f"<b>💰 Цена:</b> {spec_data['price']}р\n\n"
        f"<b>📋 Требования:</b>\n{spec_data['requirements']}\n\n"
        f"<b>🎁 Бонусы:</b>\n{spec_data['bonuses']}\n\n"
        f"<i>Выбрать эту специализацию?</i>",
        reply_markup=specialization_confirmation_keyboard(spec_type),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("specialization_buy_"))
async def callback_specialization_buy(callback: types.CallbackQuery):
    spec_id = callback.data.replace("specialization_buy_", "")
    user_id = callback.from_user.id
    success, message = await buy_specialization(user_id, spec_id)
    if success:
        await callback.message.edit_text(
            f"🎉 <b>ПОЗДРАВЛЯЮ!</b>\n\n"
            f"{message}\n\n"
            f"Теперь ты обладатель уникальной специализации!\n"
            f"Используй её бонусы по максимуму.",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer(message, show_alert=True)
        await callback_specializations(callback)

@router.callback_query(F.data == "craft")
async def callback_craft(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    crafted_count = len(patsan.get("crafted_items", []))
    text = (
        f"<b>🔨 КРАФТ ПРЕДМЕТОВ</b>\n\n"
        f"<i>Создавай мощные предметы из ингредиентов!</i>\n\n"
        f"📦 Инвентарь: {len(patsan.get('inventory', []))} предметов\n"
        f"🔨 Скрафчено: {crafted_count} предметов\n"
        f"💰 Деньги: {patsan['dengi']}р\n\n"
        f"<b>Выбери действие:</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=craft_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "craft_items")
async def callback_craft_items(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    craftable_items = await get_craftable_items(user_id)
    if not craftable_items:
        await callback.message.edit_text(
            "😕 <b>НЕТ ДОСТУПНЫХ РЕЦЕПТОВ</b>\n\n"
            "У тебя пока нет нужных ингредиентов для крафта.\n"
            "Собирай двенашки, атмосферы и другие предметы!",
            reply_markup=back_to_craft_keyboard(),
            parse_mode="HTML"
        )
        return
    text = "<b>🔨 ДОСТУПНЫЕ ДЛЯ КРАФТА:</b>\n\n"
    for item in craftable_items:
        status = "✅ МОЖНО" if item["can_craft"] else "❌ НЕЛЬЗЯ"
        text += f"<b>{item['name']}</b> {status}\n"
        text += f"<i>{item['description']}</i>\n"
        text += f"🎲 Шанс успеха: {int(item['success_chance'] * 100)}%\n"
        if not item["can_craft"] and item["missing"]:
            text += f"<code>Не хватает: {', '.join(item['missing'][:2])}</code>\n"
        text += "\n"
    text += "<i>Выбери предмет для крафта:</i>"
    await callback.message.edit_text(
        text,
        reply_markup=craft_items_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("craft_execute_"))
async def callback_craft_execute(callback: types.CallbackQuery):
    recipe_id = callback.data.replace("craft_execute_", "")
    user_id = callback.from_user.id
    success, message, result = await craft_item(user_id, recipe_id)
    if success:
        item_name = result.get("item", "предмет")
        duration = result.get("duration")
        duration_text = ""
        if duration:
            hours = duration // 3600
            if hours > 0:
                duration_text = f"\n⏱️ Действует: {hours} часов"
        await callback.message.edit_text(
            f"✨ <b>КРАФТ УСПЕШЕН!</b>\n\n"
            f"{message}{duration_text}\n\n"
            f"🎉 Ты создал новый предмет!\n"
            f"Проверь инвентарь, чтобы использовать его.",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
        await unlock_achievement(user_id, "successful_craft", f"Успешный крафт: {item_name}", 100)
    else:
        await callback.message.edit_text(
            f"💥 <b>КРАФТ ПРОВАЛЕН</b>\n\n"
            f"{message}\n\n"
            f"Ингредиенты потеряны...\n"
            f"Попробуй снова, когда соберёшь больше!",
            reply_markup=back_to_craft_keyboard(),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "craft_recipes")
async def callback_craft_recipes(callback: types.CallbackQuery):
    text = (
        "<b>📜 ВСЕ РЕЦЕПТЫ КРАФТА</b>\n\n"
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
        "<i>Собирай ингредиенты и создавай мощные предметы!</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=craft_recipes_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "rademka_scout_menu")
async def callback_rademka_scout_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    scouts_used = patsan.get("rademka_scouts", 0)
    free_scouts_left = max(0, 5 - scouts_used)
    text = (
        f"<b>🕵️ РАЗВЕДКА РАДЁМКИ</b>\n\n"
        f"<i>Узнай точный шанс успеха перед атакой!</i>\n\n"
        f"🎯 <b>Преимущества разведки:</b>\n"
        f"• Точно знаешь шанс победы\n"
        f"• Учитываются все факторы\n"
        f"• Можно выбрать другую цель\n\n"
        f"📊 <b>Твоя статистика:</b>\n"
        f"• Использовано разведок: {scouts_used}\n"
        f"• Бесплатных осталось: {free_scouts_left}/5\n"
        f"• Стоимость разведки: {0 if free_scouts_left > 0 else 50}р\n\n"
        f"<i>Выбери действие:</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=rademka_scout_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "rademka_scout_random")
async def callback_rademka_scout_random(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    top_players = await get_top_players(limit=50, sort_by="avtoritet")
    possible_targets = [p for p in top_players if p["user_id"] != user_id]
    if not possible_targets:
        await callback.message.edit_text(
            "😕 <b>НЕКОГО РАЗВЕДЫВАТЬ!</b>\n\n"
            "На гофроцентрале кроме тебя никого нет...\n"
            "Приведи друзей, чтобы было кого разведывать!",
            reply_markup=back_to_rademka_keyboard(),
            parse_mode="HTML"
        )
        return
    import random
    target = random.choice(possible_targets)
    target_id = target["user_id"]
    success, message, scout_data = await rademka_scout(user_id, target_id)
    if not success:
        await callback.answer(message, show_alert=True)
        return
    chance = scout_data["chance"]
    target_name = target["nickname"]
    factors_text = "\n".join([f"• {f}" for f in scout_data["factors"]])
    text = (
        f"🎯 <b>РАЗВЕДКА ЗАВЕРШЕНА!</b>\n\n"
        f"<b>Цель:</b> {target_name}\n"
        f"🎲 <b>Точный шанс победы:</b> {chance}%\n\n"
        f"<b>📊 Факторы:</b>\n{factors_text}\n\n"
        f"<b>📈 Статистика:</b>\n"
        f"• Твой авторитет: {scout_data['attacker_stats']['avtoritet']} ({scout_data['attacker_stats']['rank'][1]})\n"
        f"• Его авторитет: {scout_data['target_stats']['avtoritet']} ({scout_data['target_stats']['rank'][1]})\n"
        f"• Последняя активность: {scout_data['target_stats']['last_active_hours']}ч назад\n\n"
        f"💸 Стоимость разведки: {'Бесплатно' if scout_data['cost'] == 0 else '50р'}\n"
        f"🕵️ Бесплатных разведок осталось: {scout_data['free_scouts_left']}\n\n"
        f"<i>Атаковать эту цель?</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=rademka_fight_keyboard(target_id, scouted=True),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("rademka_scout_"))
async def callback_rademka_scout_target(callback: types.CallbackQuery):
    data = callback.data.replace("rademka_scout_", "")
    if data == "choose":
        await callback.message.edit_text(
            "🎯 <b>ВЫБОР ЦЕЛИ ДЛЯ РАЗВЕДКИ</b>\n\n"
            "Для этой функции нужен список игроков.\n"
            "Пока используй случайную цель или выбери из топа.",
            reply_markup=rademka_scout_keyboard(),
            parse_mode="HTML"
        )
    elif data == "stats":
        user_id = callback.from_user.id
        patsan = await get_patsan_cached(user_id)
        scouts_used = patsan.get("rademka_scouts", 0)
        free_used = min(5, scouts_used)
        paid_used = max(0, scouts_used - 5)
        text = (
            f"📊 <b>СТАТИСТИКА РАЗВЕДОК</b>\n\n"
            f"🕵️ Всего разведок: {scouts_used}\n"
            f"🎯 Бесплатных: {free_used}/5\n"
            f"💰 Платных: {paid_used}\n"
            f"💸 Потрачено на разведки: {paid_used * 50}р\n\n"
        )
        await callback.message.edit_text(
            text,
            reply_markup=rademka_scout_keyboard(),
            parse_mode="HTML"
        )
    else:
        try:
            target_id = int(data)
            user_id = callback.from_user.id
            success, message, scout_data = await rademka_scout(user_id, target_id)
            if success:
                await callback.answer("Разведка выполнена!", show_alert=True)
                pass
            else:
                await callback.answer(message, show_alert=True)
        except ValueError:
            await callback.answer("Ошибка: неверный ID цели", show_alert=True)

@router.callback_query(F.data == "achievements_progress")
async def callback_achievements_progress(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    progress_data = await get_achievement_progress(user_id)
    if not progress_data:
        await callback.message.edit_text(
            "📊 <b>ПРОГРЕСС ДОСТИЖЕНИЙ</b>\n\n"
            "Пока нет прогресса по уровневым достижениям.\n"
            "Играй активно, и прогресс появится!",
            reply_markup=achievements_progress_keyboard(),
            parse_mode="HTML"
        )
        return
    text = "<b>📊 ПРОГРЕСС ПО УРОВНЕВЫМ ДОСТИЖЕНИЯМ</b>\n\n"
    for ach_id, data in progress_data.items():
        text += f"<b>{data['name']}</b>\n"
        if data['next_level']:
            text += f"Уровень: {data['current_level']}/{len(data['all_levels'])}\n"
            text += f"Прогресс: {data['current_progress']:.1f}/{data['next_level']['goal']} "
            text += f"({data['progress_percent']:.1f}%)\n"
            text += f"Следующий уровень: {data['next_level']['title']} "
            text += f"(+{data['next_level']['reward']}р, +{data['next_level']['exp']} опыта)\n"
        else:
            text += f"✅ Все уровни пройдены! (Максимум)\n"
        text += "\n"
    text += "<i>Выбери достижение для подробной информации:</i>"
    await callback.message.edit_text(
        text,
        reply_markup=achievements_progress_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("achievement_"))
async def callback_achievement_detail(callback: types.CallbackQuery):
    ach_type = callback.data.replace("achievement_", "")
    ach_map = {
        "zmiy_collector": {
            "name": "Коллекционер змия",
            "description": "Собери определённое количество змия",
            "levels": [
                {"goal": 10, "reward": 50, "title": "Новичок", "exp": 10},
                {"goal": 100, "reward": 300, "title": "Любитель", "exp": 50},
                {"goal": 1000, "reward": 1500, "title": "Профессионал", "exp": 200},
                {"goal": 10000, "reward": 5000, "title": "КОРОЛЬ ГОФРОЦЕНТРАЛА", "exp": 1000}
            ]
        },
        "money_maker": {
            "name": "Денежный мешок",
            "description": "Заработай много денег",
            "levels": [
                {"goal": 1000, "reward": 100, "title": "Бедолага", "exp": 10},
                {"goal": 10000, "reward": 1000, "title": "Состоятельный", "exp": 100},
                {"goal": 100000, "reward": 5000, "title": "Олигарх", "exp": 500},
                {"goal": 1000000, "reward": 25000, "title": "РОТШИЛЬД", "exp": 2500}
            ]
        },
        "rademka_king": {
            "name": "Король радёмок",
            "description": "Победи в множестве радёмок",
            "levels": [
                {"goal": 5, "reward": 200, "title": "Задира", "exp": 20},
                {"goal": 25, "reward": 1000, "title": "Гроза района", "exp": 100},
                {"goal": 100, "reward": 5000, "title": "Неприкасаемый", "exp": 500},
                {"goal": 500, "reward": 25000, "title": "ЛЕГЕНДА РАДЁМКИ", "exp": 2500}
            ]
        }
    }
    if ach_type not in ach_map:
        await callback.answer("Неизвестное достижение", show_alert=True)
        return
    ach_data = ach_map[ach_type]
    text = f"<b>🏆 {ach_data['name'].upper()}</b>\n\n"
    text += f"<i>{ach_data['description']}</i>\n\n"
    text += "<b>📊 Уровни:</b>\n"
    for i, level in enumerate(ach_data['levels'], 1):
        text += f"{i}. <b>{level['title']}</b>: {level['goal']} → +{level['reward']}р (+{level['exp']} опыта)\n"
    text += "\n<i>Прогресс автоматически отслеживается во время игры.</i>"
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "level_stats")
async def callback_level_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    current_level = patsan.get("level", 1)
    current_exp = patsan.get("experience", 0)
    required_exp = int(100 * (current_level ** 1.5))
    progress_percent = (current_exp / required_exp) * 100
    progress_bars = 10
    filled_bars = int(progress_percent / 10)
    progress_bar = "█" * filled_bars + "░" * (progress_bars - filled_bars)
    next_level_reward = (current_level + 1) * 100
    max_atm_increase = (current_level + 1) % 5 == 0
    text = (
        f"<b>📈 СТАТИСТИКА УРОВНЕЙ</b>\n\n"
        f"🏆 <b>Текущий уровень:</b> {current_level}\n"
        f"📚 <b>Опыт:</b> {current_exp}/{required_exp}\n"
        f"📊 <b>Прогресс:</b> [{progress_bar}] {progress_percent:.1f}%\n\n"
        f"🎁 <b>Награда за {current_level + 1} уровень:</b>\n"
        f"• +{next_level_reward}р\n"
    )
    if max_atm_increase:
        text += f"• +1 к максимальным атмосферам\n"
    text += f"\n<b>ℹ️ Информация:</b>\n"
    text += f"• Опыт даётся за все действия\n"
    text += f"• Каждый 5 уровень увеличивает запас атмосфер\n"
    text += f"• Уровень влияет на ежедневные награды\n"
    await callback.message.edit_text(
        text,
        reply_markup=level_stats_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "atm_status")
async def callback_atm_status(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    regen_time = calculate_atm_regen_time(patsan)
    regen_minutes = regen_time // 60
    regen_seconds = regen_time % 60
    bonuses = []
    if patsan.get("skill_zashita", 1) >= 10:
        bonuses.append("Скилл защиты ≥10: -10% времени")
    if patsan.get("specialization") == "непробиваемый":
        bonuses.append("Специализация: -10% времени")
    if "вечный_двигатель" in patsan.get("active_boosts", {}):
        bonuses.append("Вечный двигатель: -30% времени")
    progress = int((atm_count / max_atm) * 10)
    progress_bar = "█" * progress + "░" * (10 - progress)
    text = (
        f"<b>🌡️ СОСТОЯНИЕ АТМОСФЕР</b>\n\n"
        f"🌀 <b>Текущий запас:</b> {atm_count}/{max_atm}\n"
        f"📊 <b>Заполненность:</b> [{progress_bar}] {(atm_count/max_atm)*100:.1f}%\n\n"
        f"⏱️ <b>Время восстановления:</b>\n"
        f"• 1 атмосфера: {regen_minutes}м {regen_seconds}с\n"
        f"• До полного: {regen_minutes * (max_atm - atm_count)}м\n\n"
    )
    if bonuses:
        text += f"⚡ <b>Активные бонусы:</b>\n"
        for bonus in bonuses:
            text += f"• {bonus}\n"
        text += "\n"
    text += f"<b>ℹ️ Как увеличить?</b>\n"
    text += f"• Каждый 5 уровень: +1 к максимуму\n"
    text += f"• Бустер атмосфер: +3 к максимуму\n"
    text += f"• Прокачка защиты: ускоряет восстановление\n"
    await callback.message.edit_text(
        text,
        reply_markup=atm_status_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "top")
async def callback_top_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏆 <b>ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА</b>\n\n"
        "Выбери, по какому показателю сортировать рейтинг:\n\n"
        "<i>Новые варианты:</i>\n"
        "• 📈 По уровню - кто больше прокачался\n"
        "• 👊 По победам в радёмках - кто самый дерзкий</i>",
        reply_markup=top_sort_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("top_"))
async def show_top(callback: types.CallbackQuery):
    sort_type = callback.data.replace("top_", "")
    sort_map = {
        "avtoritet": ("авторитету", "⭐", "avtoritet"),
        "dengi": ("деньгам", "💰", "dengi"),
        "zmiy": ("змию", "🐍", "zmiy"),
        "total_skill": ("сумме скиллов", "💪", "total_skill"),
        "level": ("уровню", "📈", "level"),
        "rademka_wins": ("победам в радёмках", "👊", "rademka_wins")
    }
    if sort_type not in sort_map:
        await callback.answer("Неизвестный тип топа", show_alert=True)
        return
    sort_name, emoji, db_key = sort_map[sort_type]
    if sort_type == "rademka_wins":
        try:
            from database.db_manager import get_connection
            conn = await get_connection()
            cursor = await conn.execute('''
                SELECT 
                    u.user_id,
                    u.nickname,
                    u.avtoritet,
                    COUNT(rf.id) as wins
                FROM users u
                LEFT JOIN rademka_fights rf ON u.user_id = rf.winner_id
                GROUP BY u.user_id, u.nickname, u.avtoritet
                ORDER BY wins DESC
                LIMIT 10
            ''')
            top_players_raw = await cursor.fetchall()
            await conn.close()
            top_players = []
            for row in top_players_raw:
                player = dict(row)
                player["wins"] = player["wins"] or 0
                player["rank"] = "?"
                player["zmiy"] = 0
                player["dengi"] = 0
                player["level"] = 1
                player["zmiy_formatted"] = "0кг"
                player["dengi_formatted"] = "0р"
                top_players.append(player)
        except Exception as e:
            print(f"Ошибка при получении топа радёмок: {e}")
            top_players = []
    else:
        try:
            top_players = await get_top_players(limit=10, sort_by=db_key)
        except Exception as e:
            await callback.answer(f"Ошибка при получении топа: {e}", show_alert=True)
            return
    if not top_players:
        await callback.message.edit_text(
            "😕 <b>Топ пуст!</b>\n\n"
            "Ещё никто не заслужил места в рейтинге.\n"
            "Будь первым!",
            reply_markup=top_sort_keyboard(),
            parse_mode="HTML"
        )
        return
    top_text = f"{emoji} <b>Топ пацанов по {sort_name}:</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, player in enumerate(top_players):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        if sort_type == "avtoritet":
            value = f"⭐ {player['avtoritet']}"
        elif sort_type == "dengi":
            dengi_value = player.get('dengi', 0)
            dengi_formatted = player.get('dengi_formatted', f"{dengi_value}р")
            value = f"💰 {dengi_formatted}"
        elif sort_type == "zmiy":
            zmiy_value = player.get('zmiy', 0)
            zmiy_formatted = player.get('zmiy_formatted', f"{zmiy_value:.1f}кг")
            value = f"🐍 {zmiy_formatted}"
        elif sort_type == "total_skill":
            value = f"💪 {player.get('total_skill', 0)} ур."
        elif sort_type == "level":
            value = f"📈 {player.get('level', 1)} ур."
        elif sort_type == "rademka_wins":
            value = f"👊 {player.get('wins', 0)} побед"
        else:
            value = ""
        nickname = player.get('nickname', f'Пацан_{player.get("user_id", "?")}')
        if len(nickname) > 20:
            nickname = nickname[:17] + "..."
        rank_info = ""
        if sort_type != "rademka_wins":
            rank_name = player.get("rank", "").split(" ")
            if len(rank_name) > 1:
                rank_info = f" ({rank_name[1]})"
        top_text += f"{medal} <code>{nickname}</code>{rank_info} — {value}\n"
    top_text += f"\n📊 <i>Всего пацанов в системе: {len(top_players)}</i>"
    current_user_id = callback.from_user.id
    user_position = None
    for i, player in enumerate(top_players):
        if player.get('user_id') == current_user_id:
            user_position = i + 1
            break
    if user_position:
        user_medal = medals[user_position-1] if user_position-1 < len(medals) else str(user_position)
        top_text += f"\n\n🎯 <b>Твоя позиция:</b> {user_medal}"
    await callback.message.edit_text(
        top_text,
        reply_markup=top_sort_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("inventory_"))
async def callback_inventory_action(callback: types.CallbackQuery):
    action = callback.data.replace("inventory_", "")
    if action == "use":
        await callback.answer("Функция использования предметов в разработке!", show_alert=True)
    elif action == "sort":
        await callback.answer("Инвентарь отсортирован!", show_alert=True)
        await callback_inventory(callback)
    elif action == "trash":
        await callback.message.edit_text(
            "🗑️ <b>ВЫБРОСИТЬ МУСОР</b>\n\n"
            "Ты уверен? Это действие удалит:\n"
            "• Все 'перчатки'\n"
            "• Все 'швабры'\n"
            "• Все 'вёдра'\n\n"
            "Зато освободит место в инвентаре!",
            reply_markup=confirmation_keyboard("trash_inventory"),
            parse_mode="HTML"
        )
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
        await callback.message.edit_text(
            f"✅ <b>МУСОР ВЫБРОШЕН!</b>\n\n"
            f"Выброшено предметов: {removed}\n"
            f"Осталось в инвентаре: {count_after}\n\n"
            f"<i>Теперь есть место для чего-то полезного!</i>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "🤷 <b>НЕТ МУСОРА</b>\n\n"
            "В твоём инвентаре не нашлось мусора.\n"
            "Всё полезное, всё пригодится!",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
