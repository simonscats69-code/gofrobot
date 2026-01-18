from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db_manager import get_patsan, get_patsan_cached, get_top_players, get_user_achievements
from keyboards.keyboards import main_keyboard, specializations_keyboard, craft_keyboard, profile_extended_keyboard
from keyboards.keyboards import daily_keyboard, achievements_keyboard, rademka_keyboard, top_sort_keyboard
from keyboards.keyboards import nickname_keyboard, inventory_management_keyboard, level_stats_keyboard, shop_keyboard
from handlers.callbacks import get_user_rank  # Импортируем функцию из callbacks.py

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start (ОБНОВЛЁННЫЙ)"""
    patsan = await get_patsan(message.from_user.id)
    
    # Получаем ранг пользователя
    rank_emoji, rank_name = get_user_rank(patsan)
    
    # Прогресс-бар атмосфер
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    progress = int((atm_count / max_atm) * 10)
    progress_bar = "█" * progress + "░" * (10 - progress)
    
    await message.answer(
        f"<b>НУ ЧЁ, ПАЦАН?</b> 👊\n\n"
        f"Добро пожаловать на гофроцентрал, <b>{patsan['nickname']}</b>!\n"
        f"{rank_emoji} <b>{rank_name}</b> | ⭐ {patsan['avtoritet']} | 📈 Ур. {patsan.get('level', 1)}\n\n"
        f"🌀 <b>Атмосферы:</b> [{progress_bar}] {atm_count}/{max_atm}\n"
        f"💰 <b>Деньги:</b> {patsan['dengi']}р | 🐍 <b>Змий:</b> {patsan['zmiy']:.1f}кг\n\n"
        f"<i>Иди заварваривай коричневага, а то старшие придут и спросят.</i>\n"
        f"<i>🔥 Новое в обновлении: специализации, крафт, уровни!</i>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Обработчик команды /profile (ОБНОВЛЁННЫЙ)"""
    patsan = await get_patsan(message.from_user.id)
    
    # Получаем ранг пользователя
    rank_emoji, rank_name = get_user_rank(patsan)
    
    upgrades = patsan["upgrades"]
    bought_upgrades = [k for k, v in upgrades.items() if v]
    
    upgrade_text = ""
    if bought_upgrades:
        upgrade_text = "\n<b>🛒 Нагнетатели:</b>\n" + "\n".join([f"• {upg}" for upg in bought_upgrades])
    
    # Специализация
    spec_text = ""
    if patsan.get("specialization"):
        spec_text = f"\n<b>🌳 Специализация:</b> {patsan['specialization']}"
    
    # Прогресс-бар атмосфер
    atm_count = patsan['atm_count']
    max_atm = patsan.get('max_atm', 12)
    progress = int((atm_count / max_atm) * 10)
    progress_bar = "█" * progress + "░" * (10 - progress)
    
    await message.answer(
        f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n"
        f"{rank_emoji} <b>{rank_name}</b>\n"
        f"👤 {patsan['nickname']}\n"
        f"⭐ Авторитет: {patsan['avtoritet']}\n"
        f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n\n"
        f"<b>Ресурсы:</b>\n"
        f"🌀 Атмосферы: [{progress_bar}] {atm_count}/{max_atm}\n"
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

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    """Обработчик команды /top (ОБНОВЛЁННЫЙ)"""
    await message.answer(
        "🏆 <b>ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА</b>\n\n"
        "Выбери, по какому показателю сортировать рейтинг:\n\n"
        "<i>Новые варианты:</i>\n"
        "• 📈 По уровню - кто больше прокачался\n"
        "• 👊 По победам в радёмках - кто самый дерзкий</i>",
        reply_markup=top_sort_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("daily"))
async def cmd_daily(message: types.Message):
    """Команда /daily - ежедневная награда (ОБНОВЛЁННАЯ)"""
    from database.db_manager import get_daily_reward
    
    user_id = message.from_user.id
    result = await get_daily_reward(user_id)
    
    if result["success"]:
        # Успешное получение награды
        streak_bonus = result.get('streak_bonus', '')
        level_multiplier = result.get('level_multiplier', 1)
        
        reward_text = (
            f"🎁 <b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n"
            f"💰 +{result['money']} руб. ({result['base']} баз. + {result['random_bonus']} бонус)\n"
            f"📈 Множитель уровня (x{level_multiplier/100:.1f}) учтён!\n"
            f"🎒 +1 {result['item']}\n"
            f"🔥 Стрик: {result['streak']} дней{streak_bonus}\n\n"
            f"<i>Приходи завтра за новой наградой!</i>"
        )
        
        await message.answer(
            reward_text,
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Нужно подождать
        wait_text = (
            f"⏰ <b>РАНО, ПАЦАН!</b>\n\n"
            f"Ты уже получал сегодняшнюю награду.\n"
            f"Следующая награда через: {result['wait_time']}\n\n"
            f"<i>Приходи позже, не торопись!</i>"
        )
        
        await message.answer(
            wait_text,
            reply_markup=daily_keyboard(),
            parse_mode="HTML"
        )

@router.message(Command("achievements"))
async def cmd_achievements(message: types.Message):
    """Команда /achievements - список достижений (ОБНОВЛЁННАЯ)"""
    from database.db_manager import get_user_achievements
    
    user_id = message.from_user.id
    achievements = await get_user_achievements(user_id)
    
    if not achievements:
        await message.answer(
            "📜 <b>Твои достижения:</b>\n\n"
            "Пока пусто... Действуй, пацан!\n"
            "Заработай первое достижение!\n\n"
            "<i>Есть уровневие достижения с прогрессом!</i>",
            reply_markup=achievements_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Формируем список достижений
    achievements_text = "📜 <b>ТВОИ ДОСТИЖЕНИИ:</b>\n\n"
    
    for i, ach in enumerate(achievements[:15], 1):  # Ограничиваем 15 достижениями
        name = ach.get("name", "Неизвестное")
        reward = ach.get("reward", 0)
        unlocked_at = ach.get("unlocked_at", 0)
        
        # Форматируем дату
        if unlocked_at:
            from datetime import datetime
            date_str = datetime.fromtimestamp(unlocked_at).strftime("%d.%m.%Y")
        else:
            date_str = "давно"
        
        reward_text = f" (+{reward}р)" if reward > 0 else ""
        
        achievements_text += f"{i}. <b>{name}</b>{reward_text}\n   📅 {date_str}\n\n"
    
    # Добавляем статистику
    total_rewards = sum(ach.get("reward", 0) for ach in achievements)
    achievements_text += f"💰 <i>Всего получено с достижений: {total_rewards}р</i>\n"
    achievements_text += f"🔢 <i>Всего достижений: {len(achievements)}</i>"
    
    await message.answer(
        achievements_text,
        reply_markup=achievements_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("rademka"))
async def cmd_rademka(message: types.Message):
    """Команда /rademka - меню радёмки (ОБНОВЛЁННАЯ)"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    scouts_used = patsan.get("rademka_scouts", 0)
    free_scouts_left = max(0, 5 - scouts_used)
    
    message_text = (
        f"👊 <b>ПРОТАЩИТЬ КАК РАДЁМКУ!</b>\n\n"
        f"<i>ИДИ СЮДА РАДЁМКА БАЛЯ!</i>\n\n"
        f"Выбери пацана и протащи его по гофроцентралу!\n"
        f"За успешную радёмку получишь:\n"
        f"• +1 авторитет\n"
        f"• 10% его денег\n"
        f"• Шанс забрать двенашку\n\n"
        f"<b>Риски:</b>\n"
        f"• Можешь потерять 5% своих денег\n"
        f"• -1 авторитет при неудаче\n"
        f"• Отжатый пацан может отомстить\n\n"
        f"🎯 <b>НОВОЕ: Разведка!</b>\n"
        f"• Узнай точный шанс победы\n"
        f"• {free_scouts_left}/5 бесплатных разведок\n"
        f"• Потом 50р за разведку\n\n"
        f"<b>Твои статы:</b>\n"
        f"⭐ Авторитет: {patsan['avtoritet']}\n"
        f"💰 Деньги: {patsan['dengi']}р\n"
        f"📈 Уровень: {patsan.get('level', 1)}"
    )
    
    await message.answer(
        message_text,
        reply_markup=rademka_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("specializations"))
async def cmd_specializations(message: types.Message):
    """Команда /specializations - меню специализаций"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    current_spec = patsan.get("specialization", "")
    
    if current_spec:
        from database.db_manager import get_specialization_bonuses
        spec_bonuses = get_specialization_bonuses(current_spec)
        bonuses_text = "\n".join([f"• {k}: {v}" for k, v in spec_bonuses.items()])
        
        await message.answer(
            f"<b>🌳 ТВОЯ СПЕЦИАЛИЗАЦИЯ</b>\n\n"
            f"<b>{current_spec.upper()}</b>\n\n"
            f"<b>🎁 Бонусы:</b>\n{bonuses_text}\n\n"
            f"<i>Сейчас у тебя может быть только одна специализация.</i>\n"
            f"<i>Чтобы сменить, нужно сначала сбросить текущую (стоимость: 2000р).</i>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        "<b>🌳 ВЫБОР СПЕЦИАЛИЗАЦИИ</b>\n\n"
        "<i>Специализация даёт уникальные бонусы и открывает новые возможности.</i>\n"
        "<i>Можно выбрать только одну. Выбор бесплатен при выполнении требований.</i>\n\n"
        "<b>Доступные специализации:</b>\n"
        "• 💪 <b>Давила</b> - мастер давления коричневага\n"
        "• 🔍 <b>Охотник за двенашками</b> - находит то, что другие не видят\n"
        "• 🛡️ <b>Непробиваемый</b> - железные кишки и стальные нервы\n\n"
        "<i>Выбери специализацию для подробной информации:</i>",
        reply_markup=specializations_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("craft"))
async def cmd_craft(message: types.Message):
    """Команда /craft - меню крафта"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    crafted_count = len(patsan.get("crafted_items", []))
    
    text = (
        f"<b>🔨 КРАФТ ПРЕДМЕТОВ</b>\n\n"
        f"<i>Создавай мощные предметы из ингредиентов!</i>\n\n"
        f"📦 Инвентарь: {len(patsan.get('inventory', []))} предметов\n"
        f"🔨 Скрафчено: {crafted_count} предметов\n"
        f"💰 Деньги: {patsan['dengi']}р\n\n"
        f"<b>Доступные рецепты:</b>\n"
        f"• ✨ Супер-двенашка (3× двенашка + 500р)\n"
        f"• ⚡ Вечный двигатель (5× атмосфера + 1× энергетик)\n"
        f"• 👑 Царский обед (курвасаны + ряженка + 300р)\n"
        f"• 🌀 Бустер атмосфер (2× энергетик + двенашка + 2000р)\n\n"
        f"<i>Выбери действие:</i>"
    )
    
    await message.answer(
        text,
        reply_markup=craft_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    """Команда /inventory - просмотр инвентаря (ОБНОВЛЁННАЯ)"""
    patsan = await get_patsan_cached(message.from_user.id)
    
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
        import time
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
    
    await message.answer(
        text, 
        reply_markup=inventory_management_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("level"))
async def cmd_level(message: types.Message):
    """Команда /level - информация об уровне"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    current_level = patsan.get("level", 1)
    current_exp = patsan.get("experience", 0)
    
    # Рассчитываем опыт для следующего уровня
    required_exp = int(100 * (current_level ** 1.5))
    progress_percent = (current_exp / required_exp) * 100
    
    # Прогресс-бар
    progress_bars = 10
    filled_bars = int(progress_percent / 10)
    progress_bar = "█" * filled_bars + "░" * (progress_bars - filled_bars)
    
    # Награда за следующий уровень
    next_level_reward = (current_level + 1) * 100
    max_atm_increase = (current_level + 1) % 5 == 0
    
    text = (
        f"<b>📈 ИНФОРМАЦИЯ ОБ УРОВНЕ</b>\n\n"
        f"🏆 <b>Текущий уровень:</b> {current_level}\n"
        f"📚 <b>Опыт:</b> {current_exp}/{required_exp}\n"
        f"📊 <b>Прогресс:</b> [{progress_bar}] {progress_percent:.1f}%\n\n"
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
    
    await message.answer(
        text,
        reply_markup=level_stats_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help - помощь (ОБНОВЛЁННАЯ)"""
    help_text = (
        "<b>🆘 ПОМОЩЬ ПО БОТУ</b>\n\n"
        
        "<b>📋 Основные команды:</b>\n"
        "/start - Запуск бота\n"
        "/profile - Профиль игрока\n"
        "/inventory - Инвентарь\n"
        "/daily - Ежедневная награда\n"
        "/top - Топ игроков\n"
        "/nickname - Никнейм и репутация\n\n"
        
        "<b>🎮 Игровые действия:</b>\n"
        "• Давка коричневага (кнопка в меню)\n"
        "• Сдача змия на металл\n"
        "• Прокачка скиллов\n"
        "• Радёмка (PvP)\n\n"
        
        "<b>🛠️ Новые системы:</b>\n"
        "/specializations - Специализации\n"
        "/craft - Крафт предметов\n"
        "/level - Информация об уровне\n\n"
        
        "<b>🏪 Магазин:</b>\n"
        "• Ряженка (300р) - +75% к давке\n"
        "• Чай сливовый (500р) - -2 атмосферы\n"
        "• Бублэки (800р) - +35% к находкам\n"
        "• Курвасаны (1500р) - +2 авторитета\n\n"
        
        "<b>👤 Никнейм и репутация:</b>\n"
        "• Первая смена ника бесплатно\n"
        "• Репутация = авторитет\n"
        "• Повышай авторитет через радёмки\n\n"
        
        "<b>🎯 Советы:</b>\n"
        "• Атмосферы восстанавливаются каждые 10 минут\n"
        "• Чем выше авторитет - тем больше бонус\n"
        "• Используй разведку перед радёмкой\n"
        "• Собирай предметы для крафта\n\n"
        
        "<i>Вопросы и предложения: @username</i>"
    )
    
    await message.answer(
        help_text,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Команда /stats - статистика бота"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    # Получаем ранг пользователя
    rank_emoji, rank_name = get_user_rank(patsan)
    
    # Получаем статистику из разных систем
    scouts_used = patsan.get("rademka_scouts", 0)
    crafted_count = len(patsan.get("crafted_items", []))
    achievements_count = len(patsan.get("achievements", []))
    
    text = (
        f"<b>📊 ТВОЯ СТАТИСТИКА</b>\n\n"
        
        f"<b>🎮 Общая:</b>\n"
        f"{rank_emoji} <b>{rank_name}</b>\n"
        f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n"
        f"💰 Деньги: {patsan['dengi']}р\n"
        f"🐍 Всего собрано змия: {patsan['zmiy']:.1f}кг\n\n"
        
        f"<b>🔧 Прокачка:</b>\n"
        f"💪 Давка: {patsan['skill_davka']} ур.\n"
        f"🛡️ Защита: {patsan['skill_zashita']} ур.\n"
        f"🔍 Находка: {patsan['skill_nahodka']} ур.\n\n"
        
        f"<b>🎯 Активность:</b>\n"
        f"🕵️ Разведок: {scouts_used}\n"
        f"🔨 Скрафчено: {crafted_count}\n"
        f"🏆 Достижений: {achievements_count}\n\n"
        
        f"<b>📦 Ресурсы:</b>\n"
        f"🌀 Атмосферы: {patsan['atm_count']}/{patsan.get('max_atm', 12)}\n"
        f"📦 Инвентарь: {len(patsan.get('inventory', []))} предметов\n"
        f"🛒 Улучшений: {sum(1 for v in patsan['upgrades'].values() if v)}/4\n"
    )
    
    if patsan.get("specialization"):
        text += f"🌳 Специализация: {patsan['specialization']}\n"
    
    await message.answer(
        text,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("rank"))
async def cmd_rank(message: types.Message):
    """Команда /rank - информация о званиях"""
    from database.db_manager import RANKS
    
    text = "<b>⭐ СИСТЕМА ЗВАНИЙ</b>\n\n"
    text += "<i>Звание зависит от авторитета и даёт уважение среди пацанов.</i>\n\n"
    
    for threshold, (name, emoji) in sorted(RANKS.items()):
        text += f"{emoji} <b>{name}</b> - от {threshold} авторитета\n"
    
    text += "\n<b>🎁 Бонусы званий:</b>\n"
    text += "• Уважение в чатах\n"
    text += "• Влияние на шансы в радёмках\n"
    text += "• Бонус к сдазе змия\n"
    text += "• Возможность стать лидером банды (скоро)\n\n"
    
    text += "<i>Повышай авторитет через радёмки и покупку курвасанов!</i>"
    
    await message.answer(
        text,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    """Команда /shop - магазин (ОБНОВЛЁННЫЙ)"""
    user_id = message.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    text = (
        "<b>🛒 НАГНЕТАТЕЛЬНАЯ СТОЛОВАЯ</b>\n\n"
        "<i>Покупай питание для заварваривания двенашки</i>\n\n"
        
        "<b>🥛 Ряженка</b> - 300р\n"
        "<i>+75% давления в двенашке</i>\n"
        f"Статус: {'✅ Куплено' if patsan['upgrades'].get('ryazhenka') else '❌ Нет в наличии'}\n\n"
        
        "<b>🍵 Чай сливовый</b> - 500р\n"
        "<i>Разгоняет процесс (-2 атмосферы)</i>\n"
        f"Статус: {'✅ Куплено' if patsan['upgrades'].get('tea_slivoviy') else '❌ Нет в наличии'}\n\n"
        
        "<b>🧋 Бублэки</b> - 800р\n"
        "<i>Турбулентность (+35% к находкам + редкие предметы)</i>\n"
        f"Статус: {'✅ Куплено' if patsan['upgrades'].get('bubbleki') else '❌ Нет в наличии'}\n\n"
        
        "<b>🥐 Курвасаны с телотинкой</b> - 1500р\n"
        "<i>Заряд энергии (+2 авторитета)</i>\n"
        f"Статус: {'✅ Куплено' if patsan['upgrades'].get('kuryasany') else '❌ Нет в наличии'}\n\n"
        
        f"💰 <b>Твои деньги:</b> {patsan['dengi']} руб.\n\n"
        
        "<i>💡 Совет: Купи все улучшения для достижения 'Все нагнетатели' (+1500р)!</i>"
    )
    
    await message.answer(
        text,
        reply_markup=shop_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена текущего действия (для FSM)"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=main_keyboard())
        return
    
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=main_keyboard()
    )

@router.message(Command("version"))
async def cmd_version(message: types.Message):
    """Команда /version - информация о версии"""
    version_text = (
        "<b>🔄 ВЕРСИЯ БОТА: 2.0</b>\n\n"
        
        "<b>🎉 НОВОЕ В ОБНОВЛЕНИИ 2.0:</b>\n"
        "• 🌳 <b>Система специализаций</b> - уникальные бонусы\n"
        "• 🔨 <b>Крафт предметов</b> - создавай мощные вещи\n"
        "• 📈 <b>Уровни и опыт</b> - прогрессируй и получай награды\n"
        "• 🏆 <b>Уровневые достижения</b> - долгосрочные цели\n"
        "• 🕵️ <b>Разведка радёмки</b> - узнавай шансы перед боем\n"
        "• ⭐ <b>Система званий</b> - от Пацанчика до Царя гофры\n"
        "• 👤 <b>Никнейм и репутация</b> - система авторитета\n\n"
        
        "<b>⚖️ Балансные изменения:</b>\n"
        "• Цены в магазине пересмотрены\n"
        "• Заработок с дачки увеличен\n"
        "• Стоимость прокачки снижена\n"
        "• Ежедневные награды зависят от уровня\n\n"
        
        "<b>📅 Следующее обновление:</b>\n"
        "• 🤝 Банды и союзы\n"
        "• 🎪 Ивенты и турниры\n"
        "• 🏛️ Территории и влияние\n"
        "• 📊 Расширенная статистика\n\n"
        
        "<i>Следи за новостями в @channel_name</i>"
    )
    
    await message.answer(
        version_text,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("nickname"))
async def cmd_nickname(message: types.Message):
    """Команда /nickname - меню никнейма и репутации (ОБНОВЛЁННАЯ)"""
    user_id = message.from_user.id
    
    try:
        patsan = await get_patsan_cached(user_id)
        
        message_text = (
            f"👤 <b>НИКНЕЙМ И РЕПУТАЦИЯ</b>\n\n"
            f"📝 <b>Твой ник:</b> <code>{patsan.get('nickname', 'Неизвестно')}</code>\n"
            f"⭐ <b>Авторитет:</b> {patsan.get('avtoritet', 1)} (используется как репутация)\n"
            f"💰 <b>Стоимость смены ника:</b> {'Бесплатно (первый раз)' if not patsan.get('nickname_changed', False) else '5000 руб.'}\n\n"
            f"<i>Выбери действие:</i>"
        )
        
        await message.answer(
            message_text,
            reply_markup=nickname_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка в команде /nickname: {e}")
        await message.answer(
            "❌ Ошибка при загрузке меню никнейма.\n"
            "Попробуйте позже.",
            parse_mode="HTML"
        )
