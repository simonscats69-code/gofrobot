from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db_manager import get_patsan, get_patsan_cached, get_top_players, RANKS
from db_manager import get_daily_reward
from keyboards import main_keyboard, profile_extended_keyboard
from keyboards import daily_keyboard, rademka_keyboard, top_sort_keyboard
from keyboards import nickname_keyboard, inventory_management_keyboard, level_stats_keyboard, shop_keyboard
from handlers.callbacks import get_user_rank, pb, ft, get_emoji

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    rank_emoji, rank_name = get_user_rank(patsan)
    atm_count, max_atm = patsan.get('atm_count', 0), patsan.get('max_atm', 12)
    
    await message.answer(
        f"<b>НУ ЧЁ, ПАЦАН?</b> 👊\n\n"
        f"Добро пожаловать на гофроцентрал, <b>{patsan.get('nickname', 'Пацанчик')}</b>!\n"
        f"{rank_emoji} <b>{rank_name}</b> | ⭐ {patsan.get('avtoritet', 1)} | 📈 Ур. {patsan.get('level', 1)}\n\n"
        f"🌀 <b>Атмосферы:</b> [{pb(atm_count, max_atm)}] {atm_count}/{max_atm}\n"
        f"💰 <b>Деньги:</b> {patsan.get('dengi', 0)}р | 🐍 <b>Змий:</b> {patsan.get('zmiy', 0.0):.1f}кг\n\n"
        f"<i>Иди заварваривай коричневага, а то старшие придут и спросят.</i>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    rank_emoji, rank_name = get_user_rank(patsan)
    atm_count, max_atm = patsan.get('atm_count', 0), patsan.get('max_atm', 12)
    upgrades = patsan.get("upgrades", {})
    bought = [k for k, v in upgrades.items() if v] if upgrades else []
    upgrade_text = "\n<b>🛒 Нагнетатели:</b>\n" + "\n".join(f"• {upg}" for upg in bought) if bought else ""
    
    await message.answer(
        f"<b>📊 ПРОФИЛЬ ПАЦАНА:</b>\n\n{rank_emoji} <b>{rank_name}</b>\n"
        f"👤 {patsan.get('nickname', 'Пацанчик')}\n⭐ Авторитет: {patsan.get('avtoritet', 1)}\n"
        f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n\n"
        f"<b>Ресурсы:</b>\n🌀 Атмосферы: [{pb(atm_count, max_atm)}] {atm_count}/{max_atm}\n"
        f"🐍 Коричневаг: {patsan.get('zmiy', 0.0):.3f} кг\n💰 Деньги: {patsan.get('dengi', 0)} руб.\n\n"
        f"<b>Скиллы:</b>\n💪 Давка: {patsan.get('skill_davka', 1)}\n"
        f"🛡️ Защита: {patsan.get('skill_zashita', 1)}\n🔍 Находка: {patsan.get('skill_nahodka', 1)}"
        f"{upgrade_text}",
        reply_markup=profile_extended_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    await message.answer(
        "🏆 <b>ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА</b>\n\nВыбери, по какому показателю сортировать рейтинг:\n\n"
        "<i>Новые варианты:</i>\n• 📈 По уровню - кто больше прокачался\n• 👊 По победам в радёмках - кто самый дерзкий</i>",
        reply_markup=top_sort_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("daily"))
async def cmd_daily(message: types.Message):
    result = await get_daily_reward(message.from_user.id)
    
    if result.get("ok", False):
        streak = result.get('streak', 1)
        level_multiplier = result.get('lvl', 1) / 10
        base = result.get('base', 0)
        bonus = result.get('bonus', 0)
        
        await message.answer(
            f"🎁 <b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n💰 +{result.get('money', 0)} руб. ({base} баз. + {bonus} бонус)\n"
            f"🎒 +1 {result.get('item', 'предмет')}\n"
            f"🔥 Стрик: {streak} дней\n\n<i>Приходи завтра за новой наградой!</i>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⏰ <b>РАНО, ПАЦАН!</b>\n\nТы уже получал сегодняшнюю награды.\n"
            f"Следующая награда через: {result.get('wait', 'неизвестно')}\n\n<i>Приходи позже, не торопись!</i>",
            reply_markup=daily_keyboard(),
            parse_mode="HTML"
        )

@router.message(Command("rademka"))
async def cmd_rademka(message: types.Message):
    patsan = await get_patsan_cached(message.from_user.id)
    
    await message.answer(
        f"👊 <b>ПРОТАЩИТЬ КАК РАДЁМКУ!</b>\n\n<i>ИДИ СЮДА РАДЁМКУ БАЛЯ!</I>\n\n"
        f"Выбери пацана и протащи его по гофроцентралу!\nЗа успешную радёмку получишь:\n• +1 авторитет\n• 10% его денег\n• Шанс забрать двенашку\n\n"
        f"<b>Риски:</b>\n• Можешь потерять 5% своих денег\n• -1 авторитет при неудаче\n• Отжатый пацан может отомстить\n\n"
        f"<b>Твои статы:</b>\n⭐ Авторитет: {patsan.get('avtoritet', 1)}\n💰 Деньги: {patsan.get('dengi', 0)}р\n📈 Уровень: {patsan.get('level', 1)}",
        reply_markup=rademka_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    patsan = await get_patsan_cached(message.from_user.id)
    inv = patsan.get("inventory", [])
    
    if not inv:
        inv_text = "Пусто... Только пыль и тоска"
    else:
        item_count = {}
        for item in inv: item_count[item] = item_count.get(item, 0) + 1
        inv_text = "<b>Твои вещи:</b>\n" + "\n".join(f"{get_emoji(item)} {item}: {c} шт." for item,c in item_count.items())
    
    text = f"{inv_text}\n\n🐍 Коричневагый змий: {patsan.get('zmiy', 0.0):.3f} кг"
    
    await message.answer(text, reply_markup=inventory_management_keyboard(), parse_mode="HTML")

@router.message(Command("level"))
async def cmd_level(message: types.Message):
    patsan = await get_patsan_cached(message.from_user.id)
    cl, ce = patsan.get("level", 1), patsan.get("experience", 0)
    re, pp = int(100 * (cl ** 1.5)), (ce / re * 100) if re > 0 else 0
    next_level_reward, max_atm_increase = (cl + 1) * 100, (cl + 1) % 5 == 0
    
    text = (f"<b>📈 ИНФОРМАЦИЯ ОБ УРОВНЕ</b>\n\n🏆 <b>Текущий уровень:</b> {cl}\n"
           f"📚 <b>Опыт:</b> {ce}/{re}\n📊 <b>Прогресс:</b> [{pb(ce, re, 10)}] {pp:.1f}%\n\n"
           f"🎁 <b>Награда за {cl + 1} уровень:</b>\n• +{next_level_reward}р\n")
    if max_atm_increase: text += "• +1 к максимальным атмосферам\n"
    text += (f"\n<b>ℹ️ Как получить опыт?</b>\n• Давка коричневага: 1-10 опыта\n• Сдача змия: 5-20 опыта\n"
            f"• Прокачка скиллов: 15-30 опыта\n• Ежедневные награды: переменный\n")
    
    await message.answer(text, reply_markup=level_stats_keyboard(), parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = ("<b>🆘 ПОМОЩЬ ПО БОТУ</b>\n\n<b>📋 Основные команды:</b>\n/start - Запуск бота\n/profile - Профиль игрока\n"
                "/inventory - Инвентарь\n/daily - Ежедневная награда\n/top - Топ игроков\n/nickname - Никнейм и репутация\n\n"
                "<b>🎮 Игровые действия:</b>\n• Давка коричневага (кнопка в меню)\n• Сдача змия на металл\n• Прокачка скиллов\n• Радёмка (PvP)\n\n"
                "<b>🏪 Магазин:</b>\n• Ряженка (300р) - +75% к давке\n• Чай сливовый (500р) - -2 атмосферы\n• Бублэки (800р) - +35% к находкам\n"
                "• Курвасаны (1500р) - +2 авторитета\n\n<b>👤 Никнейм и репутация:</b>\n• Первая смена ника бесплатно\n"
                "• Репутация = авторитет\n• Повышай авторитет через радёмки\n\n<b>🎯 Советы:</b>\n• Атмосферы восстанавливаются каждые 10 минут\n"
                "• Чем выше авторитет - тем больше бонус\n• Используй разведку перед радёмкой\n\n"
                "<i>Вопросы и предложения: @username</i>")
    
    await message.answer(help_text, reply_markup=main_keyboard(), parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    patsan = await get_patsan_cached(message.from_user.id)
    rank_emoji, rank_name = get_user_rank(patsan)
    
    text = (f"<b>📊 ТВОЯ СТАТИСТИКА</b>\n\n<b>🎮 Общая:</b>\n{rank_emoji} <b>{rank_name}</b>\n"
           f"📈 Уровень: {patsan.get('level', 1)} | 📚 Опыт: {patsan.get('experience', 0)}\n"
           f"💰 Деньги: {patsan.get('dengi', 0)}р\n🐍 Всего собрано змия: {patsan.get('zmiy', 0.0):.1f}кг\n\n"
           f"<b>🔧 Прокачка:</b>\n💪 Давка: {patsan.get('skill_davka', 1)} ур.\n🛡️ Защита: {patsan.get('skill_zashita', 1)} ур.\n"
           f"🔍 Находка: {patsan.get('skill_nahodka', 1)} ур.\n\n<b>📦 Ресурсы:</b>\n"
           f"🌀 Атмосферы: {patsan.get('atm_count', 0)}/{patsan.get('max_atm', 12)}\n"
           f"📦 Инвентарь: {len(patsan.get('inventory', []))} предметов\n"
           f"🛒 Улучшений: {sum(1 for v in patsan.get('upgrades', {}).values() if v)}/4\n")
    
    await message.answer(text, reply_markup=main_keyboard(), parse_mode="HTML")

@router.message(Command("rank"))
async def cmd_rank(message: types.Message):
    text = "<b>⭐ СИСТЕМА ЗВАНИЙ</b>\n\n<i>Звание зависит от авторитета и даёт уважение среди пацанов.</i>\n\n"
    for threshold, (emoji, name) in sorted(RANKS.items()):
        text += f"{emoji} <b>{name}</b> - от {threshold} авторитета\n"
    
    text += ("\n<b>🎁 Бонусы званий:</b>\n• Уважение в чатах\n• Влияние на шансы в радёмках\n• Бонус к сдазе змия\n"
            "• Возможность стать лидером банды (скоро)\n\n<i>Повышай авторитет через радёмки и покупку курвасанов!</i>")
    
    await message.answer(text, reply_markup=main_keyboard(), parse_mode="HTML")

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    patsan = await get_patsan_cached(message.from_user.id)
    upgrades = patsan.get("upgrades", {})
    
    text = ("<b>🛒 НАГНЕТАТЕЛЬНАЯ СТОЛОВАЯ</b>\n\n<i>Покупай питание для заварваривания двенашки</i>\n\n"
           f"<b>🥛 Ряженка</b> - 300р\n<i>+75% давления в двенашке</i>\n"
           f"Статус: {'✅ Куплено' if upgrades.get('ryazhenka') else '❌ Нет в наличии'}\n\n"
           f"<b>🍵 Чай сливовый</b> - 500р\n<i>Разгоняет процесс (-2 атмосферы)</i>\n"
           f"Статус: {'✅ Куплено' if upgrades.get('tea_slivoviy') else '❌ Нет в наличии'}\n\n"
           f"<b>🧋 Бублэки</b> - 800р\n<i>Турбулентность (+35% к находкам + редкие предметы)</i>\n"
           f"Статус: {'✅ Куплено' if upgrades.get('bubbleki') else '❌ Нет в наличии'}\n\n"
           f"<b>🥐 Курвасаны с телотинкой</b> - 1500р\n<i>Заряд энергии (+2 авторитета)</i>\n"
           f"Статус: {'✅ Куплено' if upgrades.get('kuryasany') else '❌ Нет в наличии'}\n\n"
           f"💰 <b>Твои деньги:</b> {patsan.get('dengi', 0)} руб.\n\n"
           "<i>💡 Совет: Купи все улучшения для максимальной эффективности!</i>")
    
    await message.answer(text, reply_markup=shop_keyboard(), parse_mode="HTML")

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=main_keyboard())
        return
    
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_keyboard())

@router.message(Command("version"))
async def cmd_version(message: types.Message):
    version_text = ("<b>🔄 ВЕРСИЯ БОТА: 2.1</b>\n\n<b>🎉 НОВОЕ В ОБНОВЛЕНИИ 2.1:</b>\n"
                   "• ⭐ <b>Система званий</b> - от Пацанчика до Царя гофры\n• 👤 <b>Никнейм и репутация</b> - система авторитета\n\n"
                   "<b>⚖️ Балансные изменения:</b>\n• Упрощена игровая механика\n• Улучшена производительность\n"
                   "• Снижена сложность для новых игроков\n\n<b>📅 Следующее обновление:</b>\n"
                   "• 🤝 Банды и союзы\n• 🎪 Ивенты и турниры\n• 🏛️ Территории и влияние\n• 📊 Расширенная статистика\n\n"
                   "<i>Следи за новостями в @channel_name</i>")
    
    await message.answer(version_text, reply_markup=main_keyboard(), parse_mode="HTML")

@router.message(Command("nickname"))
async def cmd_nickname(message: types.Message):
    try:
        patsan = await get_patsan_cached(message.from_user.id)
        cost = 'Бесплатно (первый раз)' if not patsan.get('nickname_changed', False) else '5000 руб.'
        
        await message.answer(
            f"👤 <b>НИКНЕЙМ И РЕПУТАЦИЯ</b>\n\n📝 <b>Твой ник:</b> <code>{patsan.get('nickname', 'Пацанчик')}</code>\n"
            f"⭐ <b>Авторитет:</b> {patsan.get('avtoritet', 1)} (используется как репутация)\n"
            f"💰 <b>Стоимость смены ника:</b> {cost}\n\n<i>Выбери действие:</i>",
            reply_markup=nickname_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка в команде /nickname: {e}")
        await message.answer("❌ Ошибка при загрузке меню никнейма.\nПопробуйте позже.", parse_mode="HTML")

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    rank_emoji, rank_name = get_user_rank(patsan)
    atm_count, max_atm = patsan.get('atm_count', 0), patsan.get('max_atm', 12)
    
    await message.answer(
        f"<b>Главное меню</b>\n{rank_emoji} <b>{rank_name}</b> | ⭐ {patsan.get('avtoritet', 1)} | 📈 Ур. {patsan.get('level', 1)}\n\n"
        f"🌀 Атмосферы: [{pb(atm_count, max_atm)}] {atm_count}/{max_atm}\n"
        f"💸 Деньги: {patsan.get('dengi', 0)}р | 🐍 Змий: {patsan.get('zmiy', 0.0):.1f}кг\n\n"
        f"<i>Выбери действие, пацан:</i>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )
