from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import time
import random
import re
import logging
from db_manager import (
    get_patsan, davka_zmiy, uletet_zmiy, get_gofra_info, 
    format_length, ChatManager, calculate_atm_regen_time,
    calculate_pvp_chance, can_fight_pvp, save_patsan, save_rademka_fight,
    calculate_davka_cooldown, get_top_players
)
from keyboards import (
    main_keyboard, profile_extended_kb, rademka_keyboard, 
    top_sort_keyboard, nickname_keyboard, gofra_info_kb, 
    cable_info_kb, atm_status_kb, mk, back_kb, 
    rademka_fight_keyboard, chat_menu_keyboard as get_chat_menu_keyboard
)
from .shared import ignore_not_modified_error

router = Router()

# Визуальные эффекты отключены
VISUAL_EFFECTS_AVAILABLE = False
logger = logging.getLogger(__name__)

# FSM States for nickname changes
class NicknameChange(StatesGroup):
    waiting_for_nickname = State()

def validate_nickname(nickname):
    """Validate nickname format and content"""
    if len(nickname) < 3 or len(nickname) > 20:
        return False, "Длина ника должна быть от 3 до 20 символов"

    banned_words = ["admin", "root", "support", "бот", "модератор",
                    "админ", "help", "техподдержка"]
    nickname_lower = nickname.lower()
    if any(word in nickname_lower for word in banned_words):
        return False, "Запрещённый ник"

    pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9_\- ]+$'
    if not re.match(pattern, nickname):
        return False, "Только буквы, цифры, пробелы, дефисы и подчёркивания"

    if nickname.strip() != nickname:
        return False, "Убери пробелы в начале или конце"

    if nickname.count('  ') > 0:
        return False, "Слишком много пробелов подряд"

    return True, "OK"

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        welcome_text = formatters.format_welcome(
            nickname=patsan.get('nickname', 'Пацанчик'),
            gofra_emoji=gofra_info['emoji'],
            gofra_name=gofra_info['name'],
            gofra_length=gofra_info['length_display'],
            cable_length=format_length(patsan.get('cable_mm', 10.0)),
            atm_count=patsan.get('atm_count', 0),
            atm_max=12,
            zmiy_grams=patsan.get('zmiy_grams', 0.0)
        )
        keyboard = beautiful_keyboards.get_main_menu()
    else:
        # Стандартное сообщение
        welcome_text = (
            f"НУ ЧЁ, ПАЦАН? 👊\n\n"
            f"Добро пожаловать на гофроцентрал, {patsan.get('nickname', 'Пацанчик')}!\n"
            f"{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {gofra_info['length_display']} | 🔌 {format_length(patsan.get('cable_mm', 10.0))}\n\n"
            f"🌀 Атмосферы: {patsan.get('atm_count', 0)}/12\n"
            f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n\n"
            f"Иди заварваривай коричневага, а то старшие придут и спросят."
        )
        keyboard = main_keyboard()

    await message.answer(welcome_text, reply_markup=keyboard)

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Handle /profile command"""
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
    
    regen_info = await calculate_atm_regen_time(patsan)
    
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование профиля
        profile_text = formatters.format_profile(
            nickname=patsan.get('nickname', 'Пацанчик'),
            gofra_emoji=gofra_info['emoji'],
            gofra_name=gofra_info['name'],
            gofra_length=gofra_info['length_display'],
            cable_length=format_length(patsan.get('cable_mm', 10.0)),
            atm_count=patsan.get('atm_count', 0),
            atm_max=12,
            atm_regen=regen_info['per_atm'],
            zmiy_grams=patsan.get('zmiy_grams', 0.0),
            total_davki=patsan.get('total_davki', 0),
            total_zmiy_grams=patsan.get('total_zmiy_grams', 0.0)
        )
        keyboard = beautiful_keyboards.get_profile_menu()
    else:
        # Стандартное сообщение
        profile_text = (
            f"📊 ПРОФИЛЬ ПАЦАНА:\n\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"👤 {patsan.get('nickname', 'Пацанчик')}\n"
            f"🏗️ Гофра: {gofra_info['length_display']}\n"
            f"🔌 Кабель: {format_length(patsan.get('cable_mm', 10.0))}\n\n"
            f"Ресурсы:\n"
            f"🌀 Атмосферы: {patsan.get('atm_count', 0)}/12\n"
            f"⏱️ Восстановление: {regen_info['per_atm']:.0f} сек за 1 атм.\n"
            f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n\n"
            f"Статистика:\n"
            f"📊 Всего давок: {patsan.get('total_davki', 0)}\n"
            f"📈 Всего змия: {patsan.get('total_zmiy_grams', 0.0):.0f}г"
        )
        keyboard = profile_extended_kb()

    await message.answer(profile_text, reply_markup=keyboard)

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    """Handle /top command"""
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        top_text = formatters.format_section_header("🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА")
        top_text += "\nВыбери, по какому показателю сортировать рейтинг:"
        keyboard = beautiful_keyboards.get_top_menu()
    else:
        # Стандартное сообщение
        top_text = (
            "🏆 ТОП ПАЦАНОВ С ГОФРОЦЕНТРАЛА\n\n"
            "Выбери, по какому показателю сортировать рейтинг:"
        )
        keyboard = top_sort_keyboard()

    await message.answer(top_text, reply_markup=keyboard)

@router.message(Command("gofra"))
async def cmd_gofra(message: types.Message):
    """Handle /gofra command"""
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
    
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        gofra_text = formatters.format_gofra_info(
            gofra_emoji=gofra_info['emoji'],
            gofra_name=gofra_info['name'],
            gofra_length=gofra_info['length_display'],
            atm_speed=gofra_info['atm_speed'],
            min_grams=gofra_info['min_grams'],
            max_grams=gofra_info['max_grams'],
            progress=gofra_info.get('progress', 0),
            next_gofra_name=gofra_info.get('next_gofra_name', ''),
            next_gofra_length=gofra_info.get('next_length_display', ''),
            next_atm_speed=gofra_info.get('next_atm_speed', 0),
            next_min_grams=gofra_info.get('next_min_grams', 0),
            next_max_grams=gofra_info.get('next_max_grams', 0)
        )
        keyboard = beautiful_keyboards.get_gofra_menu()
    else:
        # Стандартное сообщение
        text = f"🏗️ ИНФОРМАЦИЯ О ГОФРОШКЕ\n\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"📊 Длина гофрошки: {gofra_info['length_display']}\n\n"
        text += f"Характеристики:\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г\n\n"
        
        if gofra_info.get('next_threshold'):
            progress = gofra_info['progress']
            next_gofra = get_gofra_info(gofra_info['next_threshold'])
            text += f"Следующая гофрошка:\n"
            text += f"{gofra_info['emoji']} → {next_gofra['emoji']}\n"
            text += f"{next_gofra['name']} (от {next_gofra['length_display']})\n"
            text += f"📈 Прогресс: {progress*100:.1f}%\n"
            text += f"⚡ Новая скорость: x{next_gofra['atm_speed']:.2f}\n"
            text += f"⚖️ Новый вес: {next_gofra['min_grams']}-{next_gofra['max_grams']}г"
        else:
            text += "🎉 Максимальный уровень гофрошки!"
        
        gofra_text = text
        keyboard = gofra_info_kb()

    await message.answer(gofra_text, reply_markup=keyboard)

@router.message(Command("cable"))
async def cmd_cable(message: types.Message):
    """Handle /cable command"""
    patsan = await get_patsan(message.from_user.id)
    
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        cable_text = formatters.format_cable_info(
            cable_length=format_length(patsan.get('cable_mm', 10.0)),
            pvp_bonus=(patsan.get('cable_mm', 10.0) * 0.02),
            total_zmiy_grams=patsan.get('total_zmiy_grams', 0),
            next_upgrade=(2000 - (patsan.get('total_zmiy_grams', 0) % 2000))
        )
        keyboard = beautiful_keyboards.get_cable_menu()
    else:
        # Стандартное сообщение
        text = f"🔌 СИЛОВОЙ КАБЕЛЬ\n\n"
        text += f"💪 Длина кабеля: {format_length(patsan.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(patsan.get('cable_mm', 10.0) * 0.02):.1f}% к шансу\n\n"
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм к кабелю\n"
        text += f"• Победы в радёмках дают +0.2 мм\n\n"
        text += f"Прогресс:\n"
        text += f"📊 Всего змия: {patsan.get('total_zmiy_grams', 0):.0f}г\n"
        text += f"📈 Следующий +0.1 мм через: {(2000 - (patsan.get('total_zmiy_grams', 0) % 2000)):.0f}г"
        
        cable_text = text
        keyboard = cable_info_kb()

    await message.answer(cable_text, reply_markup=keyboard)

@router.message(Command("atm"))
async def cmd_atm(message: types.Message):
    """Handle /atm command"""
    patsan = await get_patsan(message.from_user.id)
    regen_info = await calculate_atm_regen_time(patsan)
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
    
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        atm_text = formatters.format_atm_status(
            atm_count=patsan.get('atm_count', 0),
            atm_max=12,
            per_atm=regen_info['per_atm'],
            total=regen_info['total'],
            needed=regen_info['needed'],
            gofra_emoji=gofra_info['emoji'],
            gofra_name=gofra_info['name'],
            atm_speed=gofra_info['atm_speed']
        )
        keyboard = beautiful_keyboards.get_atm_menu()
    else:
        # Стандартное сообщение
        text = f"🌡️ СОСТОЯНИЕ АТМОСФЕР\n\n"
        text += f"🌀 Текущий запас: {patsan.get('atm_count', 0)}/12\n\n"
        text += f"Восстановление:\n"
        text += f"⏱️ 1 атмосфера: {regen_info['per_atm']:.0f}сек\n"
        text += f"🕐 До полного: {regen_info['total']:.0f}сек\n"
        text += f"📈 Осталось: {regen_info['needed']} атмосфер\n\n"
        text += f"Влияние гофрошки:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}\n\n"
        text += f"Полные 12 атмосфер нужны для давки!"
        
        atm_text = text
        keyboard = atm_status_kb()

    await message.answer(atm_text, reply_markup=keyboard)

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Handle /menu command"""
    patsan = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))
    
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        menu_text = formatters.format_main_menu(
            gofra_emoji=gofra_info['emoji'],
            gofra_name=gofra_info['name'],
            gofra_length=gofra_info['length_display'],
            cable_length=format_length(patsan.get('cable_mm', 10.0)),
            atm_count=patsan.get('atm_count', 0),
            atm_max=12,
            zmiy_grams=patsan.get('zmiy_grams', 0.0)
        )
        keyboard = beautiful_keyboards.get_main_menu()
    else:
        # Стандартное сообщение
        menu_text = (
            f"Главное меню\n"
            f"{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {gofra_info['length_display']} | 🔌 {format_length(patsan.get('cable_mm', 10.0))}\n\n"
            f"🌀 Атмосферы: {patsan.get('atm_count', 0)}/12\n"
            f"🐍 Змий: {patsan.get('zmiy_grams', 0.0):.0f}г\n\n"
            f"Выбери действие, пацан:"
        )
        keyboard = main_keyboard()

    await message.answer(menu_text, reply_markup=keyboard)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        help_text = formatters.format_help()
        keyboard = beautiful_keyboards.get_help_menu()
    else:
        # Стандартное сообщение
        help_text = (
            "🆘 ПОМОЩЬ ПО БОТУ\n\n"
            "📋 Основные команды:\n"
            "/start - Запуск бота\n"
            "/profile - Профиль игрока\n"
            "/gofra - Информация о гофрошке\n"
            "/cable - Информация о кабеле\n"
            "/atm - Состояние атмосфер\n"
            "/top - Топ игроков\n"
            "/menu - Главное меню\n\n"
            "🎮 Игровые действия:\n"
            "• 🐍 Давка коричневага - при 12 атмосферах\n"
            "• ✈️ Отправить змия - в коричневую страну\n"
            "• 👊 Радёмка (PvP)\n"
            "• 👤 Никнейм и репутация\n\n"
            "🏗️ Система гофрошки (в мм/см):\n"
            "• Чем длиннее гофрошка, тем тяжелее змий\n"
            "• Быстрее атмосферы\n"
            "• Медленная прогрессия (0.02 мм/г змия)\n\n"
            "🔌 Силовой кабель (в мм/см):\n"
            "• Увеличивает шанс в PvP (+0.02%/мм)\n"
            "• Прокачивается медленно (0.2 мм/кг змия)\n\n"
            "⏱️ Атмосферы:\n"
            "• Восстанавливаются автоматически\n"
            "• Нужны все 12 для давки\n"
            "• Скорость зависит от гофрошки"
        )
        keyboard = main_keyboard()

    await message.answer(help_text, reply_markup=keyboard)

# ==================== NICKNAME AND REPUTATION COMMANDS ====================

@router.message(Command("nickname"))
async def cmd_nickname_handler(m: types.Message, state: FSMContext):
    """Handle /nickname command with FSM"""
    p = await get_patsan(m.from_user.id)
    await m.answer(f"🏷️ НИКНЕЙМ И РЕПУТАЦИЯ\n\n🔤 Твой ник: {p.get('nickname','Неизвестно')}\n🏗️ Гофра: {format_length(p.get('gofra_mm', 10.0))}\n🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n\nВыбери действие:", reply_markup=nickname_keyboard())

@router.callback_query(F.data == "nickname_menu")
@ignore_not_modified_error
async def nickname_menu(c: types.CallbackQuery):
    """Handle nickname menu callback"""
    await c.answer()
    p = await get_patsan(c.from_user.id)
    await c.message.edit_text(f"🏷️ НИКНЕЙМ И РЕПУТАЦИЯ\n\n🔤 Твой ник: {p.get('nickname','Неизвестно')}\n🏗️ Гофра: {format_length(p.get('gofra_mm', 10.0))}\n🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n\nВыбери действие:", reply_markup=nickname_keyboard())

@ignore_not_modified_error
@router.callback_query(F.data == "my_reputation")
async def my_reputation(c: types.CallbackQuery):
    """Show user reputation"""
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
    await c.message.edit_text(f"⭐ МОЯ РЕПУТАЦИЯ\n\n{gofra_info['emoji']} Звание: {gofra_info['name']}\n🏗️ Гофрошка: {format_length(p.get('gofra_mm', 10.0))}\n🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n🐍 Змий: {p.get('zmiy_grams',0):.0f}г\n\nКак повысить?\n• Дави змия при полных атмосферах\n• Отправляй змия в коричневую страну\n• Участвуй в радёмках\n\nЧем больше гофрошка, тем больше уважения!", reply_markup=nickname_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "top_reputation")
async def top_reputation(c: types.CallbackQuery):
    """Show top reputation"""
    tp = await get_top_players(limit=10, sort_by="gofra")
    if not tp: 
        await c.message.edit_text("🥇 ТОП ГОФРЫ\n\nПока никого нет в топе!\nБудь первым!\n\nСлава ждёт!", reply_markup=nickname_keyboard())
    else:
        mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 ТОП ГОФРЫ\n\n"
        for i, p in enumerate(tp):
            md = mds[i] if i<len(mds) else f"{i+1}."
            nn = p.get("nickname", f"Пацан_{p.get('user_id','?')}")[:12]+("..." if len(p.get('nickname',''))>15 else "")
            gi = get_gofra_info(p.get('gofra_mm', 10.0))
            txt += f"{md} {nn} - {gi['emoji']} {gi['name']} ({gi['length_display']})\n"
        uid = c.from_user.id
        for i, p in enumerate(tp):
            if p.get('user_id')==uid: 
                txt+=f"\n🎯 Твоя позиция: {mds[i] if i<len(mds) else str(i+1)}"
                break
        txt+=f"\n👥 Всего пацанов: {len(tp)}"
        await c.message.edit_text(txt, reply_markup=nickname_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "change_nickname")
async def callback_change_nickname(c: types.CallbackQuery, state: FSMContext):
    """Handle nickname change request"""
    p = await get_patsan(c.from_user.id)

    current_state = await state.get_state()
    if current_state == NicknameChange.waiting_for_nickname:
        await c.answer("Ты уже в процессе смены ника!", show_alert=True)
        return

    txt = f"✏️ СМЕНА НИКА\n\nТвой текущий ник: {p.get('nickname','Неизвестно')}\n"
    txt += f"Правила ника:\n"
    txt += f"• 3-20 символов\n"
    txt += f"• Буквы, цифры, пробелы, дефисы, подчёркивания\n"
    txt += f"• Без запрещённых слов (admin, бот и т.д.)\n"
    txt += f"• Без лишних пробелов\n\n"
    txt += f"Напиши новый ник в чат:"

    await c.message.edit_text(txt, reply_markup=back_kb("nickname_menu"))
    await state.set_state(NicknameChange.waiting_for_nickname)
    await c.answer("Введи новый ник в чат")

# ОБРАБОТЧИК ВВОДА НИКА
@router.message(NicknameChange.waiting_for_nickname)
async def process_nickname_input(message: types.Message, state: FSMContext):
    """Process nickname input with validation"""
    nn = message.text.strip()

    is_valid, error_msg = validate_nickname(nn)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nПопробуй другой ник:", reply_markup=back_kb("nickname_menu"))
        return

    ok, msg = await change_nickname(message.from_user.id, nn)
    if ok:
        await message.answer(f"✅ Ник изменён!\nТеперь ты: {nn}", reply_markup=main_keyboard())
    else:
        await message.answer(f"❌ {msg}\nПопробуй другой:", reply_markup=main_keyboard())

    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(m: types.Message, state: FSMContext):
    """Cancel nickname change"""
    current_state = await state.get_state()
    if not current_state:
        return await m.answer("Нечего отменять.", reply_markup=main_keyboard())
    
    if current_state == NicknameChange.waiting_for_nickname:
        await state.clear()
        await m.answer("Смена ника отменена.", reply_markup=main_keyboard())
    else:
        await m.answer("Нет активного процесса для отмены.", reply_markup=main_keyboard())

# ==================== RADEMKA (PvP) COMMANDS ====================

@router.message(Command("rademka"))
async def cmd_rademka(m: types.Message):
    """Handle /rademka command"""
    p = await get_patsan(m.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
    
    can_fight, fight_msg = await can_fight_pvp(m.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"
    
    txt = f"👊 ПРОТАЩИТЬ КАК РАДЁМКУ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ!\n\n{fight_status}\n\nВыбери пацана и протащи его по гофроцентралу!\nЗа успешную радёмку получишь:\n• +0.2 мм к кабелю\n• +5-12 мм к гофрошке\n• Шанс унизить публично\n\nРиски:\n• Можешь опозориться перед всеми\n• Потеряешь уважение\n\nТвои статы:\n{gofra_info['emoji']} {gofra_info['name']}\n🏗️ {format_length(p.get('gofra_mm', 10.0))}\n🔌 {format_length(p.get('cable_mm', 10.0))}"
    await m.answer(txt, reply_markup=rademka_keyboard())

@router.message(Command("rademka"))
async def cmd_rademka_handler(m: types.Message):
    """Handle /rademka command"""
    await cmd_rademka(m)

@ignore_not_modified_error
@router.callback_query(F.data == "rademka")
async def callback_rademka(c: types.CallbackQuery):
    """Handle rademka callback"""
    p = await get_patsan(c.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
    
    can_fight, fight_msg = await can_fight_pvp(c.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"
    
    await c.message.edit_text(f"👊 ПРОТАЩИТЬ КАК РАДЁМКУ!\n\n{fight_status}\n\nВыбери пацана!\nЗа успех: +0.2 мм к кабелю, +5-12 мм к гофрошке, публичное унижение\n\nРиски: публичный позор\n\nТвои статы:\n{gofra_info['emoji']} {gofra_info['name']}\n🏗️ {format_length(p.get('gofra_mm', 10.0))} | 🔌 {format_length(p.get('cable_mm', 10.0))}", reply_markup=rademka_keyboard())
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "rademka_random")
async def rademka_random(c: types.CallbackQuery):
    """Handle random rademka selection"""
    can_fight, fight_msg = await can_fight_pvp(c.from_user.id)
    if not can_fight:
        await c.answer(f"❌ {fight_msg}", show_alert=True)
        return
    
    tp = await get_top_players(limit=50, sort_by="gofra")
    tg = [p for p in tp if p.get("user_id")!=c.from_user.id]
    if not tg: 
        return await c.message.edit_text("😕 НЕКОГО ПРОТАЩИВАТЬ!\n\nПриведи друзей!", reply_markup=back_kb("rademka"))
    
    t = random.choice(tg)
    pid, tn = t.get("user_id"), t.get("nickname","Неизвестно")
    tgofra_info = get_gofra_info(t.get("gofra_mm", 10.0))
    tcable = format_length(t.get("cable_mm", 10.0))
    
    p = await get_patsan(c.from_user.id)
    mgofra_info = get_gofra_info(p.get("gofra_mm", 10.0))
    mcable = format_length(p.get("cable_mm", 10.0))
    
    chance = await calculate_pvp_chance(p, t)

    await c.message.edit_text(f"🎯 НАШЁЛ ЦЕЛЬ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ!\n\n👤 Цель: {tn}\n{tgofra_info['emoji']} {tgofra_info['name']}\n🏗️ {tgofra_info['length_display']} | 🔌 {tcable}\n\n👤 Ты: {mgofra_info['emoji']} {mgofra_info['name']}\n🏗️ {mgofra_info['length_display']} | 🔌 {mcable}\n🎯 Шанс: {chance}%\n\nНаграда: +0.2 мм к кабелю, +5-12 мм к гофрошке\nРиск: позор\n\nПротащить?", reply_markup=rademka_fight_keyboard(pid))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data.startswith("rademka_confirm_"))
async def rademka_confirm(c: types.CallbackQuery):
    """Handle rademka confirmation"""
    uid = c.from_user.id
    tid = int(c.data.replace("rademka_confirm_", ""))
    
    can_fight, fight_msg = await can_fight_pvp(uid)
    if not can_fight:
        await c.answer(f"❌ {fight_msg}", show_alert=True)
        return
    
    a = await get_patsan(uid)
    t = await get_patsan(tid)
    
    if not a or not t: 
        return await c.answer("Ошибка: пацан не найден!", show_alert=True)
    
    chance = await calculate_pvp_chance(a, t)
    suc = random.random() < (chance/100)
    
    if suc:
        cable_gain_mm = 0.2
        a["cable_mm"] = a.get("cable_mm", 10.0) + cable_gain_mm
        
        level_diff = t.get("gofra_mm", 10.0) - a.get("gofra_mm", 10.0)
        if level_diff > 0:
            gofra_gain_mm = 12.0 + min(level_diff / 100, 8.0)
        else:
            gofra_gain_mm = max(5.0, 12.0 + level_diff / 200)
        
        gofra_gain_mm = round(gofra_gain_mm, 2)
        a["gofra_mm"] = a.get("gofra_mm", 10.0) + gofra_gain_mm
        
        a["cable_power"] = int(a["cable_mm"] / 5)
        a["gofra"] = int(a["gofra_mm"] / 10)
        
        txt = f"✅ УСПЕХ!\n\nИДИ СЮДА РАДЁМКУ БАЛЯ! ТЫ ПРОТАЩИЛ!\n\n"
        txt += f"Ты унизил {t.get('nickname','Неизвестно')}!\n"
        txt += f"🔌 Кабель: +{cable_gain_mm:.1f} мм (теперь {format_length(a['cable_mm'])})\n"
        txt += f"🏗️ Гофрошка: +{gofra_gain_mm:.1f} мм (теперь {format_length(a['gofra_mm'])})\n"
        txt += f"🎯 Шанс был: {chance}%\n"
        txt += "Он теперь боится!"
    else:
        txt = f"❌ ПРОВАЛ!\n\nСам оказался радёмкой...\n\n"
        txt += f"{t.get('nickname','Неизвестно')} круче!\n"
        txt += f"🎯 Шанс был: {chance}%\n"
        txt += "Теперь смеются..."
    
    await save_patsan(a)
    await save_patsan(t)
    await save_rademka_fight(winner_id=uid if suc else tid, loser_id=tid if suc else uid)
    
    await c.message.edit_text(txt, reply_markup=back_kb("rademka"))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "rademka_stats")
async def rademka_stats(c: types.CallbackQuery):
    """Show rademka statistics"""
    try:
        from db_manager import get_connection
        cn = await get_connection()
        cur = await cn.execute('SELECT COUNT(*) as tf, SUM(CASE WHEN winner_id=? THEN 1 ELSE 0 END) as w, SUM(CASE WHEN loser_id=? THEN 1 ELSE 0 END) as l FROM rademka_fights WHERE winner_id=? OR loser_id=?', (c.from_user.id,)*4)
        s = await cur.fetchone()
        if s and s[0] and s[0] > 0:
            t, w, l = s[0], s[1] or 0, s[2] or 0
            wr = (w / t * 100) if t > 0 else 0
            
            cur2 = await cn.execute('SELECT COUNT(*) as hour_fights FROM rademka_fights WHERE (winner_id=? OR loser_id=?) AND created_at > ?',
                                   (c.from_user.id, c.from_user.id, int(time.time()) - 3600))
            hour_row = await cur2.fetchone()
            hour_fights = hour_row[0] if hour_row else 0
            
            txt = f"📊 СТАТИСТИКА РАДЁМОК\n\n"
            txt += f"🎲 Всего: {t}\n"
            txt += f"✅ Побед: {w}\n"
            txt += f"❌ Поражений: {l}\n"
            txt += f"📈 Винрейт: {wr:.1f}%\n"
            txt += f"⏱️ За час: {hour_fights}/10 боёв\n\n"
            txt += f"Лимит: 10 боёв в час"
        else: 
            txt = f"📊 СТАТИСТИКА РАДёмОК\n\nНет радёмок!\nВыбери цель!\n\nПока мирный пацан..."
        await cn.close()
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        txt = f"📊 СТАТИСТИКА РАДёмОК\n\nБаза готовится...\n\nСистема учится считать!"
    await c.message.edit_text(txt, reply_markup=back_kb("rademka"))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "rademka_top")
async def rademka_top(c: types.CallbackQuery):
    """Show rademka leaderboard"""
    try:
        from db_manager import get_connection
        cn = await get_connection()
        cur = await cn.execute('SELECT u.nickname, u.user_id, u.gofra_mm, u.cable_mm, COUNT(CASE WHEN rf.winner_id=u.user_id THEN 1 END) as w, COUNT(CASE WHEN rf.loser_id=u.user_id THEN 1 END) as l FROM users u LEFT JOIN rademka_fights rf ON u.user_id=rf.winner_id OR u.user_id=rf.loser_id GROUP BY u.user_id, u.nickname, u.gofra_mm, u.cable_mm HAVING w>0 ORDER BY w DESC LIMIT 10')
        tp = await cur.fetchall()
        if tp:
            mds, txt = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"], "🥇 ТОП РАДёМЩИКОВ\n\n"
            for i, p in enumerate(tp):
                if i>=len(mds): 
                    break
                md, nn, w, l, gofra_mm, cable_mm = mds[i], p.get("nickname","Неизвестно"), p.get("w",0) or 0, p.get("l",0) or 0, p.get("gofra_mm",10.0), p.get("cable_mm",10.0)
                gofra_info = get_gofra_info(gofra_mm)
                if len(nn)>15:
                    nn=nn[:12]+"..."
                win_rate = 0 if w+l==0 else (w/(w+l)*100)
                txt+=f"{md} {nn} {gofra_info['emoji']}\n   🏗️ {format_length(gofra_mm)} | 🔌 {format_length(cable_mm)} | ✅ {w} ({win_rate:.0f}%)\n\n"
            txt+="Топ по победам"
        else: 
            txt = f"🥇 ТОП РАДёмЩИКОВ\n\nПока никого!\nБудь первым!\n\nСлава ждёт!"
        await cn.close()
    except Exception as e:
        logger.error(f"Ошибка топа: {e}")
        txt = f"🥇 ТОП РАДёмЩИКОВ\n\nРейтинг формируется...\n\nМеста скоро будут!"
    await c.message.edit_text(txt, reply_markup=back_kb("rademka"))
    await c.answer()

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(c: types.CallbackQuery):
    """Return to main menu"""
    try:
        p = await get_patsan(c.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
        await c.message.edit_text(f"Главное меню\n{gofra_info['emoji']} {gofra_info['name']} | 🏗️ {gofra_info['length_display']} | 🔌 {format_length(p.get('cable_mm', 10.0))}\n\n🌀 Атмосферы: {p.get('atm_count',0)}/12\n🐍 Змий: {p.get('zmiy_grams',0):.0f}г\n\nВыбери действие:", reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка главного: {e}")
        await c.message.edit_text("Главное меню\n\nБот работает!", reply_markup=main_keyboard())

# ==================== CHAT COMMANDS ====================

@router.message(Command("start", "gofra", "gofrastart"))
async def group_start(message: types.Message):
    """Handle group start command"""
    chat = message.chat

    await ChatManager.register_chat(
        chat_id=chat.id,
        chat_title=chat.title if hasattr(chat, 'title') else "",
        chat_type=chat.type
    )

    await message.answer(
        f"👋 Саламчик пополамчик родные! Приветствуем в гофроцентрале, {chat.title if hasattr(chat, 'title') else 'чатик'}!\n\n"
        f"Я бот для давки коричневага и прокачки гофрошки.\n\n"
        f"В чате доступно:\n"
        f"🐍 Общая статистика\n"
        f"🏆 Топ участников\n"
        f"👊 Радёмки между участниками\n\n"
        f"Используй /ghelp или кнопки ниже:",
        reply_markup=get_chat_menu_keyboard()
    )

@router.message(Command("ghelp", "g_help", "chathelp"))
async def group_help(message: types.Message):
    """Handle group help command"""
    await message.answer(
        "🆘 ГОФРА-КОМАНДЫ ДЛЯ ЧАТОВ:\n\n"
        "👤 Личные команды:\n"
        "/start - Начать игру\n"
        "/davka - Давить коричневага\n"
        "/profile - Профиль\n"
        "/top - Топ игроков\n"
        "/rademka - Радёмка (PvP)\n\n"
        "👥 Команды чата:\n"
        "/gtop - Топ этого чата\n"
        "/gstats - Статистика чата\n"
        "/gme - Моя статистика в чате\n"
        "/gdavka - Давить змия в чате\n"
        "/grademka - Радёмка в чате\n"
        "/fight @игрок - Протащить игрока (ответом на сообщение)\n"
        "/gmenu - Меню для чата\n"
        "/ghelp - Эта справка\n\n"
        "📊 В чате сохраняется общая статистика!\n"
        "👊 Радёмки работают только между участниками чата!",
        reply_markup=get_chat_menu_keyboard()
    )

@router.message(Command("gmenu", "chatmenu"))
async def group_menu_command(message: types.Message):
    """Handle group menu command"""
    await message.answer(
        "🏗️ ГОФРА-МЕНЮ ДЛЯ ЧАТА 🏗️\n\n"
        "Выбери действие:",
        reply_markup=get_chat_menu_keyboard()
    )

@router.message(Command("gtop", "g_top", "chattop"))
async def chat_top_command(message: types.Message):
    """Handle chat top command"""
    await show_chat_top_message(message.chat.id, message)

@router.message(Command("gstats", "g_stats", "chatstats"))
async def chat_stats_command(message: types.Message):
    """Handle chat stats command"""
    await show_chat_stats_message(message.chat.id, message)

@router.message(Command("gdavka", "g_davka", "chatdavka"))
async def group_davka_command(message: types.Message):
    """Handle group davka command"""
    await process_chat_davka_message(message.from_user.id, message.chat.id, message)

@router.message(Command("grademka", "g_rademka", "chatrademka"))
async def group_rademka_command(message: types.Message):
    """Handle group rademka command"""
    chat = message.chat

    await ChatManager.register_chat(
        chat_id=chat.id,
        chat_title=chat.title if hasattr(chat, 'title') else "",
        chat_type=chat.type
    )

    p = await get_patsan(message.from_user.id)
    gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

    can_fight, fight_msg = await can_fight_pvp(message.from_user.id)
    fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"

    text = f"👊 РАДЁМКА В ЧАТЕ\n\n"
    text += f"{fight_status}\n\n"
    text += f"Выбери пацана из участников чата!\n"
    text += f"За победу: +0.2 мм к кабелю, +5-12 мм к гофрошке\n\n"

    try:
        chat_stats = await ChatManager.get_chat_stats(message.chat.id)
        if chat_stats['total_players'] > 1:
            top_players = await ChatManager.get_chat_top(message.chat.id, limit=20)
            opponents = [p for p in top_players if p['user_id'] != message.from_user.id]

            if opponents:
                text += f"🎯 Доступные цели ({len(opponents)}):\n"
                for i, opp in enumerate(opponents[:5], 1):
                    nickname = opp.get('nickname', f'Игрок_{opp.get("user_id")}')
                    if len(nickname) > 15:
                        nickname = nickname[:12] + "..."
                    text += f"{i}. {nickname}\n"
                text += f"\nНажми на игрока в ответном сообщении с командой /fight"
            else:
                text += "😕 В чате нет других активных игроков!"
        else:
            text += "😕 В чате пока только ты один!\nПриведи друзей для радёмок!"
    except Exception as e:
        logger.error(f"Error getting chat players: {e}")
        text += "\nОшибка загрузки списка игроков"

    await message.answer(text, reply_markup=get_chat_menu_keyboard())

@router.message(Command("fight", "протащить", "радёмка"))
async def fight_command(message: types.Message, command: CommandObject):
    """Handle fight command"""
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение игрока, которого хочешь протащить!")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id == message.from_user.id:
        await message.answer("❌ Нельзя драться с самим собой!")
        return

    target_data = await get_patsan(target_user.id)
    attacker_data = await get_patsan(message.from_user.id)

    if not target_data:
        await message.answer(f"❌ {target_user.first_name} ещё не зарегистрирован в боте!")
        return

    can_fight, fight_msg = await can_fight_pvp(message.from_user.id)
    if not can_fight:
        await message.answer(f"❌ {fight_msg}")
        return

    can_target_fight, target_fight_msg = await can_fight_pvp(target_user.id)
    if not can_target_fight:
        await message.answer(f"❌ {target_user.first_name} превысил лимит боёв на сегодня!")
        return

    chance = await calculate_pvp_chance(attacker_data, target_data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Протащить!", callback_data=f"chat_fight_{target_user.id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="chat_menu")
        ]
    ])

    gofra_info_att = get_gofra_info(attacker_data.get('gofra_mm', 10.0))
    gofra_info_tar = get_gofra_info(target_data.get('gofra_mm', 10.0))

    text = f"👊 ЗАПРОС НА РАДЁМКУ!\n\n"
    text += f"🗡️ Атакующий: {message.from_user.first_name}\n"
    text += f"{gofra_info_att['emoji']} {gofra_info_att['name']}\n"
    text += f"🏗️ {format_length(attacker_data.get('gofra_mm', 10.0))} | 🔌 {format_length(attacker_data.get('cable_mm', 10.0))}\n\n"

    text += f"🛡️ Цель: {target_user.first_name}\n"
    text += f"{gofra_info_tar['emoji']} {gofra_info_tar['name']}\n"
    text += f"🏗️ {format_length(target_data.get('gofra_mm', 10.0))} | 🔌 {format_length(target_data.get('cable_mm', 10.0))}\n\n"

    text += f"🎯 Шанс успеха: {chance}%\n"
    text += f"🏆 Награда за победу: +0.2 мм к кабелю, +5-12 мм к гофрошке\n"
    text += f"💀 Риск: публичный позор при проигрыше\n\n"
    text += f"Подтверждаешь радёмку?"

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("chat_"))
async def handle_chat_callbacks(callback: types.CallbackQuery):
    """Handle all chat-related callbacks"""
    action = callback.data.replace("chat_", "")
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    try:
        if action == "davka":
            await process_chat_davka_callback(callback, user_id, chat_id)
        elif action == "top":
            await show_chat_top_callback(callback, chat_id)
        elif action == "stats":
            await show_chat_stats_callback(callback, chat_id)
        elif action == "me":
            await show_user_chat_stats_callback(callback, user_id, chat_id)
        elif action == "gofra":
            await show_user_gofra_callback(callback, user_id)
        elif action == "cable":
            await show_user_cable_callback(callback, user_id)
        elif action == "atm":
            await show_user_atm_callback(callback, user_id)
        elif action == "profile":
            await show_user_profile_callback(callback, user_id)
        elif action == "atm_regen":
            await show_user_atm_regen_callback(callback, user_id)
        elif action == "rademka":
            await show_rademka_callback(callback, user_id, chat_id)
        elif action == "help":
            await show_chat_help_callback(callback)
        elif action == "menu":
            await show_chat_menu_callback(callback)
        elif action == "fight":
            await callback.answer("Используй команду /fight в ответ на сообщение игрока", show_alert=True)
        elif action.startswith("chat_fight_"):
            await handle_chat_fight(callback)
        else:
            await callback.answer("❌ Неизвестное действие", show_alert=True)

    except Exception as e:
        logger.error(f"Error in chat callback {action}: {e}")
        await callback.answer("❌ Ошибка, попробуй позже", show_alert=True)

# ==================== UTILITY FUNCTIONS FOR CHAT COMMANDS ====================

async def show_chat_top_message(chat_id, message_obj):
    """Show chat top leaderboard"""
    try:
        top_players = await ChatManager.get_chat_top(chat_id, limit=10)

        if not top_players:
            await message_obj.answer(
                "📊 ТОП ЧАТА ПУСТ!\n\n"
                "Пока никто не давил змия в этом чате.\n"
                "Будь первым!",
                reply_markup=get_chat_menu_keyboard()
            )
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        text = f"🏆 ТОП ЧАТА:\n\n"

        for i, player in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            nickname = player.get('nickname', f'Игрок_{player.get("user_id")}')
            if len(nickname) > 20:
                nickname = nickname[:17] + "..."

            total_kg = player['total_zmiy_grams'] / 1000

            text += f"{medal} {nickname}\n"
            text += f"   🐍 {total_kg:.1f} кг змия | #{player['rank']}\n\n"

        stats = await ChatManager.get_chat_stats(chat_id)
        text += f"📈 Статистика чата:\n"
        text += f"• Участников: {stats['total_players']}\n"
        text += f"• Всего змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• Всего давок: {stats['total_davki_all']}\n"
        text += f"• Активных: {stats['active_players']}"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error getting chat top: {e}")
        await message_obj.answer("❌ Ошибка загрузки топа чата.", reply_markup=get_chat_menu_keyboard())

async def show_chat_stats_message(chat_id, message_obj):
    """Show chat statistics"""
    try:
        stats = await ChatManager.get_chat_stats(chat_id)

        if stats['last_activity'] > 0:
            last_active = time.strftime('%d.%m.%Y %H:%M', time.localtime(stats['last_activity']))
        else:
            last_active = "никогда"

        text = f"📊 СТАТИСТИКА ЧАТА\n\n"
        text += f"👥 Участников: {stats['total_players']}\n"
        text += f"🔥 Активных: {stats['active_players']}\n\n"

        text += f"🐍 Змий добыто:\n"
        text += f"• Всего: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• На игрока: {stats['total_zmiy_all']/max(1, stats['total_players'])/1000:.1f} кг\n\n"

        text += f"⚡ Давок сделано:\n"
        text += f"• Всего: {stats['total_davki_all']}\n"
        text += f"• На игрока: {stats['total_davki_all']/max(1, stats['total_players']):.0f}\n\n"

        text += f"⏱️ Последняя активность: {last_active}"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        await message_obj.answer("❌ Ошибка загрузки статистики.", reply_markup=get_chat_menu_keyboard())

async def process_chat_davka_message(user_id, chat_id, message_obj):
    """Process chat davka command"""
    await ChatManager.register_chat(
        chat_id=chat_id,
        chat_title=message_obj.chat.title if hasattr(message_obj.chat, 'title') else "",
        chat_type=message_obj.chat.type
    )

    try:
        success, p, res = await davka_zmiy(user_id, chat_id)

        if not success:
            await message_obj.answer(res, reply_markup=get_chat_menu_keyboard())
            return

        await ChatManager.update_chat_activity(chat_id)

        user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)
        top_players = await ChatManager.get_chat_top(chat_id, limit=50)

        rank = None
        for i, player in enumerate(top_players, 1):
            if player['user_id'] == user_id:
                rank = i
                break

        davka_texts = [
            f"🐍 {message_obj.from_user.first_name} ЗАВАРВАРИЛ ДВАНАШКУ!\n\n",
            f"🐍 {message_obj.from_user.first_name} ВЫДАВИЛ КОРИЧНЕВАГА!\n\n",
            f"🐍 {message_obj.from_user.first_name} ОТЖАЛ ЗМИЯ!\n\n"
        ]

        text = random.choice(davka_texts)
        text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
        text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
        text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
        text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"

        text += f"📊 В этом чате:\n"
        text += f"• Всего змия: {user_total/1000:.1f} кг\n"
        if rank:
            text += f"• Место в топе: #{rank}\n"

        if rank == 1:
            text += "\n🏆 ЛИДЕР ЧАТА! 🏆\n"

        await message_obj.answer(text, reply_markup=get_chat_menu_keyboard())

    except Exception as e:
        logger.error(f"Error in group davka: {e}")
        await message_obj.answer("❌ Ошибка при давке змия.", reply_markup=get_chat_menu_keyboard())

@router.callback_query(F.data.startswith("chat_fight_"))
async def handle_chat_fight(callback: types.CallbackQuery):
    """Handle chat fight callback"""
    try:
        target_id = int(callback.data.replace("chat_fight_", ""))
        attacker_id = callback.from_user.id

        if attacker_id == target_id:
            await callback.answer("❌ Нельзя драться с самим собой!", show_alert=True)
            return

        can_fight, fight_msg = await can_fight_pvp(attacker_id)
        if not can_fight:
            await callback.answer(f"❌ {fight_msg}", show_alert=True)
            return

        attacker = await get_patsan(attacker_id)
        target = await get_patsan(target_id)

        if not attacker or not target:
            await callback.answer("❌ Ошибка: игрок не найден!", show_alert=True)
            return

        chance = await calculate_pvp_chance(attacker, target)
        success = random.random() < (chance / 100)

        winner_id = attacker_id if success else target_id
        loser_id = target_id if success else attacker_id

        winner = await get_patsan(winner_id)
        loser = await get_patsan(loser_id)

        if success:
            cable_gain_mm = 0.2
            attacker["cable_mm"] = attacker.get("cable_mm", 10.0) + cable_gain_mm

            level_diff = target.get("gofra_mm", 10.0) - attacker.get("gofra_mm", 10.0)
            if level_diff > 0:
                gofra_gain_mm = 12.0 + min(level_diff / 100, 8.0)
            else:
                gofra_gain_mm = max(5.0, 12.0 + level_diff / 200)

            gofra_gain_mm = round(gofra_gain_mm, 2)
            attacker["gofra_mm"] = attacker.get("gofra_mm", 10.0) + gofra_gain_mm

            attacker["cable_power"] = int(attacker["cable_mm"] / 5)
            attacker["gofra"] = int(attacker["gofra_mm"] / 10)

            await save_patsan(attacker)
            winner_nick = attacker.get('nickname', callback.from_user.first_name)
            loser_nick = target.get('nickname', 'Неизвестно')
        else:
            cable_gain_mm = 0.1
            target["cable_mm"] = target.get("cable_mm", 10.0) + cable_gain_mm

            level_diff = attacker.get("gofra_mm", 10.0) - target.get("gofra_mm", 10.0)
            if level_diff > 0:
                gofra_gain_mm = 6.0 + min(level_diff / 200, 4.0)
            else:
                gofra_gain_mm = max(2.5, 6.0 + level_diff / 400)

            gofra_gain_mm = round(gofra_gain_mm, 2)
            target["gofra_mm"] = target.get("gofra_mm", 10.0) + gofra_gain_mm

            target["cable_power"] = int(target["cable_mm"] / 5)
            target["gofra"] = int(target["gofra_mm"] / 10)

            await save_patsan(target)
            winner_nick = target.get('nickname', 'Неизвестно')
            loser_nick = attacker.get('nickname', callback.from_user.first_name)

        await save_rademka_fight(winner_id=winner_id, loser_id=loser_id)

        if success:
            result_text = f"🎉 РАДЁМКА ЗАВЕРШЕНА!\n\n"
            result_text += f"🏆 ПОБЕДИТЕЛЬ: {callback.from_user.first_name}\n"
            result_text += f"💀 ПРОИГРАВШИЙ: {target.get('nickname', 'Неизвестно')}\n\n"
            result_text += f"Награды победителю:\n"
            result_text += f"🔌 Кабель: +{cable_gain_mm:.1f} мм\n"
            result_text += f"🏗️ Гофра: +{gofra_gain_mm:.1f} мм\n"
            result_text += f"🎯 Шанс был: {chance}%\n\n"
            result_text += f"{target.get('nickname', 'Неизвестно')} теперь будет носить твои кроссовки!"
        else:
            result_text = f"💀 РАДЁМКА ЗАВЕРШЕНА!\n\n"
            result_text += f"🏆 ПОБЕДИТЕЛЬ: {target.get('nickname', 'Неизвестно')}\n"
            result_text += f"😭 ПРОИГРАВШИЙ: {callback.from_user.first_name}\n\n"
            result_text += f"{callback.from_user.first_name} был унижен публично!\n"
            result_text += f"🎯 Шанс был: {chance}%\n\n"
            result_text += f"Теперь {callback.from_user.first_name} моет туалеты на гофроцентрале!"

        try:
            await callback.message.edit_text(result_text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(result_text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

        try:
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=f"👊 Результат радёмки: {winner_nick} протащил {loser_nick}!"
            )
        except:
            pass

    except Exception as e:
        logger.error(f"Error in chat fight: {e}", exc_info=True)
        await callback.answer("❌ Ошибка в радёмке!", show_alert=True)

async def process_chat_davka_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    """Process chat davka callback"""
    await ChatManager.register_chat(
        chat_id=chat_id,
        chat_title=callback.message.chat.title if hasattr(callback.message.chat, 'title') else "",
        chat_type=callback.message.chat.type
    )

    success, p, res = await davka_zmiy(user_id, chat_id)

    if not success:
        await callback.answer(res, show_alert=True)
        return

    await ChatManager.update_chat_activity(chat_id)

    user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)
    top_players = await ChatManager.get_chat_top(chat_id, limit=50)

    rank = None
    for i, player in enumerate(top_players, 1):
        if player['user_id'] == user_id:
            rank = i
            break

    davka_texts = [
        f"🐍 {callback.from_user.first_name} ЗАВАРВАРИЛ ДВАНАШКУ!\n\n",
        f"🐍 {callback.from_user.first_name} ВЫДАВИЛ КОРИЧНЕВАГА!\n\n",
        f"🐍 {callback.from_user.first_name} ОТЖАЛ ЗМИЯ!\n\n"
    ]

    text = random.choice(davka_texts)
    text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
    text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
    text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
    text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"

    text += f"📊 В этом чате:\n"
    text += f"• Всего змия: {user_total/1000:.1f} кг\n"
    if rank:
        text += f"• Место в топе: #{rank}\n"

    if rank == 1:
        text += "\n🏆 ЛИДЕР ЧАТА! 🏆\n"

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()

async def show_chat_top_callback(callback: types.CallbackQuery, chat_id: int):
    """Show chat top callback"""
    try:
        top_players = await ChatManager.get_chat_top(chat_id, limit=10)

        if not top_players:
            await callback.answer("📊 Топ чата пуст! Будь первым!", show_alert=True)
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        text = f"🏆 ТОП ЧАТА:\n\n"

        for i, player in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            nickname = player.get('nickname', f'Игрок_{player.get("user_id")}')
            if len(nickname) > 20:
                nickname = nickname[:17] + "..."

            total_kg = player['total_zmiy_grams'] / 1000

            text += f"{medal} {nickname}\n"
            text += f"   🐍 {total_kg:.1f} кг змия | #{player['rank']}\n\n"

        stats = await ChatManager.get_chat_stats(chat_id)
        text += f"📈 Статистика чата:\n"
        text += f"• Участников: {stats['total_players']}\n"
        text += f"• Всего змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• Всего давок: {stats['total_davki_all']}\n"
        text += f"• Активных: {stats['active_players']}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback top: {e}")
        await callback.answer("❌ Ошибка загрузки топа", show_alert=True)

async def show_chat_stats_callback(callback: types.CallbackQuery, chat_id: int):
    """Show chat stats callback"""
    try:
        stats = await ChatManager.get_chat_stats(chat_id)

        if stats['last_activity'] > 0:
            last_active = time.strftime('%d.%m.%Y %H:%M', time.localtime(stats['last_activity']))
        else:
            last_active = "никогда"

        text = f"📊 СТАТИСТИКА ЧАТА\n\n"
        text += f"👥 Участников: {stats['total_players']}\n"
        text += f"🔥 Активных: {stats['active_players']}\n\n"

        text += f"🐍 Змий добыто:\n"
        text += f"• Всего: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• На игрока: {stats['total_zmiy_all']/max(1, stats['total_players'])/1000:.1f} кг\n\n"

        text += f"⚡ Давок сделано:\n"
        text += f"• Всего: {stats['total_davki_all']}\n"
        text += f"• На игрока: {stats['total_davki_all']/max(1, stats['total_players']):.0f}\n\n"

        text += f"⏱️ Последняя активность: {last_active}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

async def show_user_chat_stats_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    """Show user chat stats callback"""
    try:
        user_total = await ChatManager.get_user_total_in_chat(chat_id, user_id)

        if user_total == 0:
            text = f"📊 Твоя статистика в этом чате:\n\n"
            text += f"Пока ты не давил змия в этом чате.\n"
            text += f"Нажми кнопку 🐍 Давить в чате!"

            try:
                await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

            await callback.answer()
            return

        top_players = await ChatManager.get_chat_top(chat_id, limit=50)
        rank = None
        total_in_chat = 0

        for i, player in enumerate(top_players, 1):
            total_in_chat += 1
            if player['user_id'] == user_id:
                rank = i

        stats = await ChatManager.get_chat_stats(chat_id)

        text = f"📊 ТВОЯ СТАТИСТИКА В ЧАТЕ\n\n"
        text += f"🐍 Всего змия: {user_total/1000:.1f} кг\n"

        if rank:
            text += f"🏆 Место в топе: #{rank} из {total_in_chat}\n"

            if rank > 1:
                prev_player = top_players[rank-2]
                diff = user_total - prev_player['total_zmiy_grams']
                text += f"📈 До #{rank-1}: +{diff/1000:.1f} кг\n"

            if rank < len(top_players):
                next_player = top_players[rank]
                diff = next_player['total_zmiy_grams'] - user_total
                text += f"📉 До #{rank+1}: -{diff/1000:.1f} кг\n"

        text += f"\n📊 Статистика чата:\n"
        text += f"• Всего участников: {stats['total_players']}\n"
        text += f"• Общий вес змия: {stats['total_zmiy_all']/1000:.1f} кг\n"
        text += f"• Твой вклад: {(user_total/stats['total_zmiy_all']*100):.1f}%"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback me: {e}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

async def show_user_gofra_callback(callback: types.CallbackQuery, user_id: int):
    """Show user gofra callback"""
    try:
        p = await get_patsan(user_id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🏗️ ТВОЯ ГОФРА\n\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"📏 Длина: {gofra_info['length_display']}\n\n"
        text += f"Характеристики:\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г\n\n"

        if gofra_info.get('next_threshold'):
            progress = gofra_info['progress']
            next_gofra = get_gofra_info(gofra_info['next_threshold'])
            text += f"Следующая гофрошка:\n"
            text += f"{gofra_info['emoji']} → {next_gofra['emoji']}\n"
            text += f"{next_gofra['name']}\n"
            text += f"📈 Прогресс: {progress*100:.1f}%"
        else:
            text += "🎉 Максимальный уровень гофрошки!"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback gofra: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_user_cable_callback(callback: types.CallbackQuery, user_id: int):
    """Show user cable callback"""
    try:
        p = await get_patsan(user_id)

        text = f"🔌 ТВОЙ КАБЕЛЬ\n\n"
        text += f"💪 Длина: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм\n"
        text += f"• Победы в радёмках = +0.2 мм\n\n"
        text += f"📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback cable: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_user_atm_callback(callback: types.CallbackQuery, user_id: int):
    """Show user atm callback"""
    try:
        p = await get_patsan(user_id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        def ft(s):
            if s < 60: return f"{s}с"
            m, h, d = s // 60, s // 3600, s // 86400
            if d > 0: return f"{d}д {h%24}ч {m%60}м"
            if h > 0: return f"{h}ч {m%60}м {s%60}с"
            return f"{m}м {s%60}с"

        text = f"🌡️ ТВОИ АТМОСФЕРЫ\n\n"
        text += f"🌀 Текущий запас: {p.get('atm_count', 0)}/12\n\n"
        text += f"Восстановление:\n"
        text += f"⏱️ 1 атмосфера: {ft(regen_info['per_atm'])}\n"
        text += f"🕐 До полного: {ft(regen_info['total'])}\n"
        text += f"📈 Осталось: {regen_info['needed']} атм.\n\n"
        text += f"Влияние гофрошки:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback atm: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_user_profile_callback(callback: types.CallbackQuery, user_id: int):
    """Show user profile callback"""
    try:
        p = await get_patsan(user_id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"📊 ТВОЙ ПРОФИЛЬ\n\n"
        text += f"🏗️ Гофра: {gofra_info['width_display']}\n"
        text += f"🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г\n\n"
        text += f"📈 Прогресс:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback profile: {e}")
        await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)

async def show_user_atm_regen_callback(callback: types.CallbackQuery, user_id: int):
    """Show user atm regen callback"""
    try:
        p = await get_patsan(user_id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        def ft(s):
            if s < 60: return f"{s}с"
            m, h, d = s // 60, s // 3600, s // 86400
            if d > 0: return f"{d}д {h%24}ч {m%60}м"
            if h > 0: return f"{h}ч {m%60}м {s%60}с"
            return f"{m}м {s%60}с"

        atm_count = p.get('atm_count', 0)
        max_atm = 12

        text = f"⏱️ ТОЧНЫЙ ТАЙМЕР ВОССТАНОВЛЕНИЯ\n\n"
        text += f"Текущее состояние:\n"
        text += f"🌀 Атмосферы: {atm_count}/{max_atm}\n"
        text += f"📈 Нужно восстановить: {regen_info['needed']} шт.\n\n"
        text += f"Точный таймер:\n"
        text += f"🕒 До следующей атмосферы: {ft(regen_info['time_to_next_atm'])}\n"
        text += f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
        text += f"Скорость восстановления:\n"
        text += f"• Базовая: 1 атм. за 2 часа (7200с)\n"
        text += f"• С учётом гофрошки ({gofra_info['name']}): x{gofra_info['atm_speed']:.2f}\n"
        text += f"• 1 атм. за: {ft(regen_info['time_to_one_atm'])}\n\n"
        text += f"Как ускорить:\n"
        text += f"• Повышай гофрошку - ускоряет восстановление\n"
        text += f"• Дави змия при полных 12 атмосферах\n"
        text += f"• Больше опыт → выше гофрошка → быстрее атмосферы"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback atm regen: {e}")
        await callback.answer("❌ Ошибка загрузки таймера", show_alert=True)

async def show_rademka_callback(callback: types.CallbackQuery, user_id: int, chat_id: int):
    """Show rademka callback"""
    try:
        p = await get_patsan(user_id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        can_fight, fight_msg = await can_fight_pvp(user_id)
        fight_status = "✅ Можно атаковать" if can_fight else f"❌ {fight_msg}"

        text = f"👊 РАДЁМКА (PvP)\n\n"
        text += f"{fight_status}\n\n"
        text += f"Выбери пацана из участников чата!\n"
        text += f"За победу: +0.2 мм к кабелю, +5-12 мм к гофрошке\n\n"

        try:
            chat_stats = await ChatManager.get_chat_stats(chat_id)
            if chat_stats['total_players'] > 1:
                top_players = await ChatManager.get_chat_top(chat_id, limit=20)
                opponents = [p for p in top_players if p['user_id'] != user_id]

                if opponents:
                    text += f"🎯 Доступные цели ({len(opponents)}):\n"
                    for i, opp in enumerate(opponents[:5], 1):
                        nickname = opp.get('nickname', f'Игрок_{opp.get("user_id")}')
                        if len(nickname) > 15:
                            nickname = nickname[:12] + "..."
                        text += f"{i}. {nickname}\n"
                    text += f"\nНажми на игрока в ответном сообщении с командой /fight"
                else:
                    text += "😕 В чате нет других активных игроков!"
            else:
                text += "😕 В чате пока только ты один!\nПриведи друзей для радёмок!"
        except Exception as e:
            logger.error(f"Error getting chat players in callback: {e}")
            text += "\nОшибка загрузки списка игроков"

        text += f"\n\nТвои статы:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"🏗️ {format_length(p.get('gofra_mm', 10.0))} | 🔌 {format_length(p.get('cable_mm', 10.0))}"

        try:
            await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in chat callback rademka: {e}")
        await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

async def show_chat_help_callback(callback: types.CallbackQuery):
    """Show chat help callback"""
    text = (
        "🆘 ГОФРА-КОМАНДЫ ДЛЯ ЧАТОВ:\n\n"
        "👤 Личные команды:\n"
        "/start - Начать игру\n"
        "/davka - Давить коричневага\n"
        "/profile - Профиль\n"
        "/top - Топ игроков\n"
        "/rademka - Радёмка (PvP)\n\n"
        "👥 Команды чата:\n"
        "/gtop - Топ этого чата\n"
        "/gstats - Статистика чата\n"
        "/gme - Моя статистика в чате\n"
        "/gdavka - Давить змия в чате\n"
        "/grademka - Радёмка в чате\n"
        "/fight @игрок - Протащить игрока (ответом на сообщение)\n"
        "/gmenu - Меню для чата\n"
        "/ghelp - Эта справка\n\n"
        "📊 В чате сохраняется общая статистика!\n"
        "👊 Радёмки работают только между участниками чата!"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()

async def show_chat_menu_callback(callback: types.CallbackQuery):
    """Show chat menu callback"""
    text = "🏗️ ГОФРА-МЕНЮ ДЛЯ ЧАТА 🏗️\n\nВыбери действие:"

    try:
        await callback.message.edit_text(text, reply_markup=get_chat_menu_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_chat_menu_keyboard())

    await callback.answer()

@router.message(F.text.contains("гофрошка") | F.text.contains("змий") | F.text.contains("давка"))
async def group_keywords(message: types.Message):
    """Handle group keywords"""
    text_lower = message.text.lower()

    responses = []

    if "гофрошка" in text_lower:
        responses.extend([
            "Гофрошка - это жизнь! 🏗️",
            "Чем больше гофрошка, тем тяжелее змий! 💪",
            "Моя гофрошка уже {length} см! А твоя? 🏗️",
            "Без гофрошки и змий не выдавишь! ⚡"
        ])

    if "змий" in text_lower or "зме" in text_lower:
        responses.extend([
            "Змий надо давить, а не обсуждать! 🐍",
            "У меня сегодня {weight}г змия вышло! 💩",
            "Коричневаг ждёт тебя! Нажми /davka 🐍"
        ])

    if "давка" in text_lower:
        responses.extend([
            "Давка - святое дело! 🐍",
            "Все 12 атмосфер готовы? Тогда /davka ⚡",
            "Лучшая давка - это утренняя давка! ☀️"
        ])

    if responses:
        response = random.choice(responses)

        if "{length}" in response:
            try:
                user = await get_patsan(message.from_user.id)
                length = format_length(user.get('gofra_mm', 10.0))
                response = response.format(length=length)
            except:
                response = response.format(length="1.5")

        if "{weight}" in response:
            weight = random.randint(50, 500)
            response = response.format(weight=weight)

        await message.reply(response)

@router.message(Command("version"))
async def cmd_version(message: types.Message):
    """Show version information"""
    if VISUAL_EFFECTS_AVAILABLE:
        # Используем красивое форматирование
        version_text = formatters.format_version_info()
        keyboard = beautiful_keyboards.get_version_menu()
    else:
        # Стандартное сообщение
        version_text = (
            "🔄 ВЕРСИЯ БОТА\n\n"
            "📊 Информация о системе:\n"
            "• 🏗️ Гофра измеряется в мм\n"
            "• 🔌 Кабель измеряется в мм\n"
            "• 🐍 Вес змия зависит от гофрошки\n\n"
            "👥 Функции:\n"
            "• /chat_top - топ участников чата\n"
            "• /chat_stats - статистика чата\n"
            "• Сохранение прогресса в каждом чате"
        )
        keyboard = main_keyboard()

    await message.answer(version_text, reply_markup=keyboard)

# ==================== NICKNAME CHANGE FUNCTION ====================

async def change_nickname(user_id: int, new_nickname: str) -> tuple[bool, str]:
    """Change user nickname with validation"""
    try:
        from db_manager import get_connection
        
        # Validate nickname
        is_valid, error_msg = validate_nickname(new_nickname)
        if not is_valid:
            return False, error_msg
        
        # Check if nickname is already taken
        cn = await get_connection()
        cur = await cn.execute('SELECT user_id FROM users WHERE nickname=? AND user_id!=?', (new_nickname, user_id))
        existing = await cur.fetchone()
        
        if existing:
            await cn.close()
            return False, "Ник уже занят"
        
        # Update nickname
        await cn.execute('UPDATE users SET nickname=? WHERE user_id=?', (new_nickname, user_id))
        await cn.commit()
        await cn.close()
        
        return True, "OK"
        
    except Exception as e:
        logger.error(f"Error changing nickname: {e}")
        return False, "Ошибка базы данных"

__all__ = ["router", "process_nickname_input", "cmd_nickname_handler", "cmd_rademka", "cmd_rademka_handler", "group_start", "group_help", "group_menu_command", "chat_top_command", "chat_stats_command", "group_davka_command", "group_rademka_command", "fight_command", "handle_chat_callbacks", "group_keywords", "cmd_version"]
