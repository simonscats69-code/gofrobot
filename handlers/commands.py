from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db_manager import get_patsan, get_gofra_info, calculate_atm_regen_time
from keyboards import main_keyboard, profile_extended_kb
from keyboards import rademka_keyboard, top_sort_keyboard, nickname_keyboard, gofra_info_kb, cable_info_kb, atm_status_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra', 1))
    atm_count = patsan.get('atm_count', 0)
    
    await message.answer(
        f"НУ ЧЁ, ПАЦАН? 👊\n\n"
        f"Добро пожаловать на гофроцентрал, {patsan.get('nickname', 'Пацанчик')}!\n"
        f"{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {patsan.get('gofra', 1)} | 🔌 {patsan.get('cable_power', 1)} | 💰 {patsan.get('dengi', 0)}р\n\n"
        f"🌀 Атмосферы: {atm_count}/12\n"
        f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n\n"
        f"Иди заварваривай коричневага, а то старшие придут и спросят.",
        reply_markup=main_keyboard()
    )

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra', 1))
    atm_count = patsan.get('atm_count', 0)
    
    regen_info = calculate_atm_regen_time(patsan)
    
    await message.answer(
        f"📊 ПРОФИЛЬ ПАЦАНА:\n\n"
        f"{gofra_info['emoji']} {gofra_info['name']}\n"
        f"👤 {patsan.get('nickname', 'Пацанчик')}\n"
        f"🏗️ Гофра: {patsan.get('gofra', 1)}\n"
        f"🔌 Сила кабеля: {patsan.get('cable_power', 1)}\n\n"
        f"Ресурсы:\n"
        f"🌀 Атмосферы: {atm_count}/12\n"
        f"⏱️ Восстановление: {regen_info['per_atm']:.0f}сек за 1 атм.\n"
        f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n"
        f"💰 Деньги: {patsan.get('dengi', 0)}р\n\n"
        f"Статистика:\n"
        f"📊 Всего давок: {patsan.get('total_davki', 0)}\n"
        f"📈 Всего змия: {patsan.get('total_zmiy_grams', 0.0):.0f}г",
        reply_markup=profile_extended_kb()
    )

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    await message.answer(
        "🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА\n\n"
        "Выбери, по какому показателю сортировать рейтинг:",
        reply_markup=top_sort_keyboard()
    )

@router.message(Command("gofra"))
async def cmd_gofra(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra', 1))
    
    text = f"🏗️ ИНФОРМАЦИЯ О ГОФРЕ\n\n"
    text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
    text += f"📊 Значение гофры: {patsan.get('gofra', 1)}\n\n"
    text += f"Характеристики:\n"
    text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
    text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г\n\n"
    
    if gofra_info.get('next_threshold'):
        progress = gofra_info['progress']
        next_gofra = get_gofra_info(gofra_info['next_threshold'])
        text += f"Следующая гофра:\n"
        text += f"{gofra_info['emoji']} → {next_gofra['emoji']}\n"
        text += f"{next_gofra['name']} (от {gofra_info['next_threshold']} опыта)\n"
        text += f"📈 Прогресс: {progress*100:.1f}%\n"
        text += f"⚡ Новая скорость: x{next_gofra['atm_speed']:.2f}\n"
        text += f"⚖️ Новый вес: {next_gofra['min_grams']}-{next_gofra['max_grams']}г"
    else:
        text += "🎉 Максимальный уровень гофры!"
    
    await message.answer(text, reply_markup=gofra_info_kb())

@router.message(Command("cable"))
async def cmd_cable(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    
    text = f"🔌 СИЛОВОЙ КАБЕЛЬ\n\n"
    text += f"💪 Сила кабеля: {patsan.get('cable_power', 1)}\n"
    text += f"⚔️ Бонус в PvP: +{patsan.get('cable_power', 1)}% к шансу\n"
    text += f"💰 Бонус к деньгам: +{patsan.get('cable_power', 1) * 10}р\n\n"
    text += f"Как прокачать:\n"
    text += f"• Каждые 1000г змия = +1 к силе\n"
    text += f"• Победы в радёмках тоже дают +1\n\n"
    text += f"Прогресс:\n"
    text += f"📊 Всего змия: {patsan.get('total_zmiy_grams', 0):.0f}г\n"
    text += f"📈 Следующий +1 через: {1000 - (patsan.get('total_zmiy_grams', 0) % 1000):.0f}г"
    
    await message.answer(text, reply_markup=cable_info_kb())

@router.message(Command("atm"))
async def cmd_atm(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    regen_info = calculate_atm_regen_time(patsan)
    gofra_info = get_gofra_info(patsan.get('gofra', 1))
    
    text = f"🌡️ СОСТОЯНИЕ АТМОСФЕР\n\n"
    text += f"🌀 Текущий запас: {patsan.get('atm_count', 0)}/12\n\n"
    text += f"Восстановление:\n"
    text += f"⏱️ 1 атмосфера: {regen_info['per_atm']:.0f}сек\n"
    text += f"🕐 До полного: {regen_info['total']:.0f}сек\n"
    text += f"📈 Осталось: {regen_info['needed']} атмосфер\n\n"
    text += f"Влияние гофры:\n"
    text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
    text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}\n\n"
    text += f"Полные 12 атмосфер нужны для давки!"
    
    await message.answer(text, reply_markup=atm_status_keyboard())

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra', 1))
    
    await message.answer(
        f"Главное меню\n"
        f"{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {patsan.get('gofra', 1)} | 🔌 {patsan.get('cable_power', 1)} | 💰 {patsan.get('dengi', 0)}р\n\n"
        f"🌀 Атмосферы: {patsan.get('atm_count', 0)}/12\n"
        f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n\n"
        f"Выбери действие, пацан:",
        reply_markup=main_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "🆘 ПОМОЩЬ ПО БОТУ\n\n"
        "📋 Основные команды:\n"
        "/start - Запуск бота\n"
        "/profile - Профиль игрока\n"
        "/gofra - Информация о гофре\n"
        "/cable - Информация о кабеле\n"
        "/atm - Состояние атмосфер\n"
        "/top - Топ игроков\n"
        "/menu - Главное меню\n\n"
        "🎮 Игровые действия:\n"
        "• 🐍 Давка коричневага - при 12 атмосферах\n"
        "• 💰 Сдача змия - обмен на деньги\n"
        "• 👊 Радёмка (PvP)\n"
        "• 👤 Никнейм и репутация\n\n"
        "🏗️ Система гофры:\n"
        "• Чем больше гофра, тем тяжелее змий\n"
        "• Быстрее атмосферы\n"
        "• Больше бонус при сдаче\n\n"
        "🔌 Силовой кабель:\n"
        "• Увеличивает шанс в PvP\n"
        "• Даёт бонус к деньгам\n"
        "• Прокачивается давкой змия\n\n"
        "⏱️ Атмосферы:\n"
        "• Восстанавливаются автоматически\n"
        "• Нужны все 12 для давки\n"
        "• Скорость зависит от гофры"
    )
    
    await message.answer(help_text, reply_markup=main_keyboard())

@router.message(Command("version"))
async def cmd_version(message: types.Message):
    version_text = (
        "🔄 ВЕРСИЯ БОТА: 4.0\n\n"
        "🎉 НОВАЯ СИСТЕМА ГОФРЫ И КАБЕЛЯ:\n"
        "• 🏗️ Гофра влияет на вес змия (граммы)\n"
        "• 🔌 Силовой кабель для PvP\n"
        "• ⚡ Автоматическое восстановление атмосфер\n"
        "• 🐍 Змий измеряется в граммах\n"
        "• 💰 Новая формула денег\n\n"
        "❌ УБРАНО:\n"
        "• Сантиметры кабеля\n"
        "• Старая система уровней\n"
        "• Сложные механики\n\n"
        "🎯 ФИЛОСОФИЯ:\n"
        "Гофра = вес змия, Кабель = сила в PvP!"
    )
    
    await message.answer(version_text, reply_markup=main_keyboard())
