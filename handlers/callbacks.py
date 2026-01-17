from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
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
    craft_confirmation_keyboard, specialization_confirmation_keyboard,
    inventory_management_keyboard, back_to_craft_keyboard, back_to_specializations_keyboard
)
from keyboards.new_keyboards import (
    daily_keyboard, achievements_keyboard, rademka_keyboard,
    rademka_fight_keyboard, back_to_rademka_keyboard, achievements_progress_keyboard,
    level_stats_keyboard, atm_status_keyboard, specializations_info_keyboard,
    craft_recipes_keyboard, top_sort_keyboard, back_to_profile_keyboard
)

router = Router()

# ==================== ОСНОВНЫЕ КОЛБЭКИ ====================

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    patsan = await get_patsan_cached(callback.from_user.id)
    
    # Форматируем информацию об атмосферах с прогресс-баром
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    
    # Создаём прогресс-бар
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
    """Давка коричневага (ОБНОВЛЁННАЯ С ОПЫТОМ И БОНУСАМИ)"""
    user_id = callback.from_user.id
    
    patsan, result = await davka_zmiy(user_id)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    # Формируем сообщение о нагнетателе
    nagnetatel_msg = ""
    if patsan["upgrades"].get("ryazhenka"):
        nagnetatel_msg = "\n🥛 <i>Ряженка жмёт двенашку как надо! (+75%)</i>"
    elif patsan["upgrades"].get("bubbleki"):
        nagnetatel_msg = "\n🧋 <i>Бублэки создают нужную турбулентность! (+35% к шансу)</i>"
    
    # Бонусы от специализации
    spec_bonus_msg = ""
    if patsan.get("specialization") == "давила":
        spec_bonus_msg = "\n💪 <b>Специализация 'Давила': +50% к давке!</b>"
    
    # Сообщение о находках
    dvenashka_msg = ""
    if result.get("dvenashka_found"):
        dvenashka_msg = "\n✨ <b>Нашёл двенашку в турбулентности!</b>"
    
    rare_item_msg = ""
    if result.get("rare_item_found"):
        rare_item_msg = f"\n🌟 <b>Редкая находка: {result['rare_item_found']}!</b>"
    
    # Опыт
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
    """Сдача змия (ОБНОВЛЁННАЯ С БОЛЬШЕЙ ЦЕНОЙ)"""
    user_id = callback.from_user.id
    
    patsan, result = await sdat_zmiy(user_id)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    # Бонус от авторитета (увеличенный)
    avtoritet_bonus_text = ""
    if result['avtoritet_bonus'] > 0:
        avtoritet_bonus_text = f"\n⭐ <b>Бонус авторитета:</b> +{result['avtoritet_bonus']}р"
    
    # Опыт
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
    """Меню прокачки (ОБНОВЛЁННОЕ С УРОВНЯМИ)"""
    patsan = await get_patsan_cached(callback.from_user.id)
    
    # Рассчитываем стоимость следующего уровня для каждого скилла
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
    """Прокачка конкретного скилла"""
    skill = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    patsan, result = await pump_skill(user_id, skill)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    await callback.answer(result, show_alert=True)
    await callback_pump(callback)  # Обновляем меню прокачки

@router.callback_query(F.data == "inventory")
async def callback_inventory(callback: types.CallbackQuery):
    """Инвентарь (ОБНОВЛЁННЫЙ С КРАФТОМ)"""
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
            # Эмодзи для разных предметов
            emoji = {
                "двенашка": "🧱", "атмосфера": "🌀", "энергетик": "⚡",
                "перчатки": "🧤", "швабра": "🧹", "ведро": "🪣",
                "золотая_двенашка": "🌟", "кристалл_атмосферы": "💎",
                "секретная_схема": "📜", "супер_двенашка": "✨",
                "вечный_двигатель": "⚙️", "царский_обед": "👑",
                "бустер_атмосфер": "🌀"
            }.get(item, "📦")
            
            inv_text += f"{emoji} {item}: {count} шт.\n"
    
    # Активные бусты
    active_boosts = patsan.get("active_boosts", {})
    boosts_text = ""
    if active_boosts:
        boosts_text = "\n\n<b>🔮 Активные бусты:</b>\n"
        for boost, end_time in active_boosts.items():
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
    """Профиль (ОБНОВЛЁННЫЙ С НОВЫМИ СИСТЕМАМИ)"""
    patsan = await get_patsan_cached(callback.from_user.id)
    
    upgrades = patsan["upgrades"]
    bought_upgrades = [k for k, v in upgrades.items() if v]
    
    upgrade_text = ""
    if bought_upgrades:
        upgrade_text = "\n<b>🛒 Нагнетатели:</b>\n" + "\n".join([f"• {upg}" for upg in bought_upgrades])
    
    # Специализация
    spec_text = ""
    if patsan.get("specialization"):
        spec_bonuses = get_specialization_bonuses(patsan["specialization"])
        spec_text = f"\n<b>🌳 Специализация:</b> {patsan['specialization']}"
        if spec_bonuses:
            spec_text += f"\n<i>Бонусы: {', '.join(spec_bonuses.keys())}</i>"
    
    # Время восстановления атмосфер
    regen_time = calculate_atm_regen_time(patsan)
    regen_minutes = regen_time // 60
    regen_seconds = regen_time % 60
    
    # Прогресс-бар атмосфер
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

# ==================== НОВЫЕ ОБРАБОТЧИКИ ДЛЯ СПЕЦИАЛИЗАЦИЙ ====================

@router.callback_query(F.data == "specializations")
async def callback_specializations(callback: types.CallbackQuery):
    """Меню специализаций"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    # Проверяем текущую специализацию
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
    
    # Если специализации нет, показываем доступные
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
    
    await callback.message.edit_text(
        text,
        reply_markup=specializations_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("specialization_"))
async def callback_specialization_detail(callback: types.CallbackQuery):
    """Детальная информация о специализации"""
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
    """Покупка специализации"""
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

# ==================== НОВЫЕ ОБРАБОТЧИКИ ДЛЯ КРАФТА ====================

@router.callback_query(F.data == "craft")
async def callback_craft(callback: types.CallbackQuery):
    """Меню крафта"""
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
    """Список предметов для крафта"""
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
    """Выполнение крафта"""
    recipe_id = callback.data.replace("craft_execute_", "")
    user_id = callback.from_user.id
    
    success, message, result = await craft_item(user_id, recipe_id)
    
    if success:
        # Успешный крафт
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
        
        # Достижение за успешный крафт
        await unlock_achievement(user_id, "successful_craft", f"Успешный крафт: {item_name}", 100)
    else:
        # Неудачный крафт
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
    """Список всех рецептов"""
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

# ==================== НОВЫЕ ОБРАБОТЧИКИ ДЛЯ РАЗВЕДКИ РАДЁМКИ ====================

@router.callback_query(F.data == "rademka_scout_menu")
async def callback_rademka_scout_menu(callback: types.CallbackQuery):
    """Меню разведки радёмки"""
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
    """Разведка случайной цели"""
    user_id = callback.from_user.id
    
    # Получаем топ игроков для выбора цели
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
    
    # Выполняем разведку
    success, message, scout_data = await rademka_scout(user_id, target_id)
    
    if not success:
        await callback.answer(message, show_alert=True)
        return
    
    chance = scout_data["chance"]
    target_name = target["nickname"]
    
    # Форматируем факторы
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
    """Разведка конкретной цели"""
    data = callback.data.replace("rademka_scout_", "")
    
    if data == "choose":
        # Показываем список целей для выбора
        await callback.message.edit_text(
            "🎯 <b>ВЫБОР ЦЕЛИ ДЛЯ РАЗВЕДКИ</b>\n\n"
            "Для этой функции нужен список игроков.\n"
            "Пока используй случайную цель или выбери из топа.",
            reply_markup=rademka_scout_keyboard(),
            parse_mode="HTML"
        )
    elif data == "stats":
       
