from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
import logging
from db_manager import (
    get_patsan, davka_zmiy, uletet_zmiy, get_gofra_info,
    calculate_atm_regen_time, calculate_davka_cooldown
)
from utils.display import format_length
from keyboards import (
    main_keyboard, gofra_info_kb, cable_info_kb, atm_status_kb,
    back_to_profile_keyboard
)
from .shared import ignore_not_modified_error, ft, pb
from .chat_handlers import show_user_chat_stats_message, show_user_gofra, show_user_cable, show_user_atm, show_user_profile, show_user_atm_regen

router = Router()
logger = logging.getLogger(__name__)

# ==================== ОСНОВНЫЕ CALLBACK ОБРАБОТЧИКИ ====================

@router.callback_query(F.data == "davka")
async def handle_davka_callback(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        success, p, res = await davka_zmiy(user_id)

        if not success:
            error_msg = res.get('error', 'Ошибка при давке змия')
            await callback.answer(error_msg, show_alert=True)
            return

        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        # Calculate cooldown for next davka
        cooldown_info = await calculate_davka_cooldown(p)

        text = f"🐍 ДАВКА КОРИЧНЕВАГА!\n\n"
        text += f"💩 Выдавил: {res['zmiy_grams']}г коричневага!\n"
        text += f"🏗️ Гофра: {format_length(res['old_gofra_mm'])} → {format_length(res['new_gofra_mm'])}\n"
        text += f"🔌 Кабель: {format_length(res['old_cable_mm'])} → {format_length(res['new_cable_mm'])}\n"
        text += f"📈 Опыта: +{res['exp_gained_mm']:.1f} мм\n\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г\n\n"

        # Add precise timer information
        text += f"⏱️ ТОЧНЫЙ ТАЙМЕР ДО СЛЕДУЮЩЕЙ ДАВКИ:\n"
        text += f"🕒 Следующая давка через: {cooldown_info['formatted_time']}\n"
        text += f"📅 Точное время: {cooldown_info['time_until_next']} секунд"

        try:
            await callback.message.edit_text(text, reply_markup=main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=main_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in davka callback: {e}")
        await callback.answer("❌ Ошибка при давке змия", show_alert=True)

@router.callback_query(F.data == "uletet")
async def handle_uletet_callback(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        success, p, res = await uletet_zmiy(user_id)

        if not success:
            error_msg = res.get('error', 'Ошибка при отправке змия')
            await callback.answer(error_msg, show_alert=True)
            return

        text = f"✈️ ЗМИЙ ОТПРАВЛЕН!\n\n"
        text += f"🐍 Отправлено: {res['zmiy_grams']:.0f}г коричневага!\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г"

        try:
            await callback.message.edit_text(text, reply_markup=main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=main_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in uletet callback: {e}")
        await callback.answer("❌ Ошибка при отправке змия", show_alert=True)

@router.callback_query(F.data == "gofra_info")
async def handle_gofra_info_callback(callback: types.CallbackQuery):
    await show_user_gofra(callback, callback.from_user.id, gofra_info_kb())

@router.callback_query(F.data == "cable_info")
async def handle_cable_info_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"🔌 ТВОЙ КАБЕЛЬ\n\n"
        text += f"💪 Длина: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"А у тебя пацанчик с гофроцентрала кишка как кабель силовой висит на {format_length(p.get('cable_mm', 10.0))}!\n\n"
        text += f"Как прокачать:\n"
        text += f"• Каждые 2кг змия = +0.2 мм\n"
        text += f"• Победы в радёмках дают +0.2 мм\n\n"
        text += f"📊 Всего змия: {p.get('total_zmiy_grams', 0):.0f}г"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable info callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о кабеле", show_alert=True)

@router.callback_query(F.data == "atm_status")
async def handle_atm_status_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        regen_info = await calculate_atm_regen_time(p)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🌡️ ТВОИ АТМОСФЕРЫ\n\n"
        text += f"🌀 Текущий запас: {p.get('atm_count', 0)}/12\n\n"
        text += f"Точный таймер:\n"
        text += f"🕒 До следующей атмосферы: {ft(regen_info['time_to_next_atm'])}\n"
        text += f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
        text += f"Восстановление:\n"
        text += f"⏱️ 1 атмосфера: {ft(regen_info['time_to_one_atm'])}\n"
        text += f"📈 Нужно восстановить: {regen_info['needed']} атм.\n\n"
        text += f"Влияние гофрошки:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость: x{gofra_info['atm_speed']:.2f}"

        try:
            await callback.message.edit_text(text, reply_markup=atm_status_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=atm_status_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in atm status callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации об атмосферах", show_alert=True)

@router.callback_query(F.data == "profile")
async def handle_profile_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))
        
        # Получаем информацию о таймере до следующей давки
        cooldown_info = await calculate_davka_cooldown(p)

        text = f"📊 ТВОЙ ПРОФИЛЬ\n\n"
        text += f"🏗️ Гофра: {format_length(p.get('gofra_mm', 10.0))}\n"
        text += f"🔌 Кабель: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"🌀 Атмосферы: {p.get('atm_count', 0)}/12\n"
        text += f"🐍 Змий: {p.get('zmiy_grams', 0.0):.0f}г\n\n"
        
        # Таймер до следующей давки
        if cooldown_info.get('can_davka'):
            text += f"⏰ ДАВКА ГОТОВА! 🎉\n"
            text += f"Нажми кнопку 🐍 чтобы начать!\n\n"
        else:
            text += f"⏰ СЛЕДУЮЩАЯ ДАВКА ЧЕРЕЗ:\n"
            text += f"{ft(cooldown_info['time_until_next'])}\n\n"
        
        text += f"📈 Прогресс:\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n"
        text += f"⚡ Скорость атмосфер: x{gofra_info['atm_speed']:.2f}\n"
        text += f"⚖️ Вес змия: {gofra_info['min_grams']}-{gofra_info['max_grams']}г"

        try:
            await callback.message.edit_text(text, reply_markup=main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=main_keyboard())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in profile callback: {e}")
        await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)

# ==================== GOFRA DETAIL CALLBACKS ====================

@router.callback_query(F.data == "gofra_progress")
async def handle_gofra_progress_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"📈 ПРОГРЕСС ГОФРЫ\n\n"
        text += f"🏗️ Текущая гофрошка: {gofra_info['length_display']}\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n\n"

        if gofra_info.get('next_threshold'):
            current_gofra = p.get('gofra_mm', 10.0)
            next_threshold = gofra_info['next_threshold']
            progress = (current_gofra - gofra_info['threshold']) / (next_threshold - gofra_info['threshold'])
            progress_percent = progress * 100

            next_gofra = get_gofra_info(next_threshold)

            text += f"🎯 Следующая гофрошка:\n"
            text += f"{next_gofra['emoji']} {next_gofra['name']}\n"
            text += f"📏 Требуется: {next_gofra['length_display']}\n"
            text += f"📊 Прогресс: [{'█' * int(progress_percent/10)}{'░' * (10 - int(progress_percent/10))}] {progress_percent:.1f}%\n\n"
            text += f"💪 Осталось: {next_threshold - current_gofra:.1f} мм"
        else:
            text += "🎉 Ты достиг максимального уровня гофрошки!\n"
            text += "🏆 Коричневый бог - это ты!"

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra progress callback: {e}")
        await callback.answer("❌ Ошибка загрузки прогресса гофрошки", show_alert=True)

@router.callback_query(F.data == "gofra_speed")
async def handle_gofra_speed_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"⚡ СКОРОСТЬ ВОССТАНОВЛЕНИЯ АТМОСФЕР\n\n"
        text += f"🏗️ Твоя гофрошка: {gofra_info['length_display']}\n"
        text += f"{gofra_info['emoji']} {gofra_info['name']}\n\n"
        text += f"📊 Скорость восстановления:\n"
        text += f"• Базовая: 1 атмосфера за 2 часа\n"
        text += f"• Твой множитель: x{gofra_info['atm_speed']:.2f}\n"
        text += f"• Фактическая: 1 атмосфера за {ft(7200 / gofra_info['atm_speed'])}\n\n"
        text += f"💡 Как ускорить:\n"
        text += f"• Повышай гофрошку (дави змия при 12 атмосферах)\n"
        text += f"• Чем выше гофрошка, тем быстрее восстанавливаются атмосферы\n"
        text += f"• Максимальный множитель: x2.0 (Коричневый бог)"

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra speed callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о скорости", show_alert=True)

@router.callback_query(F.data == "gofra_next")
async def handle_gofra_next_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)
        gofra_info = get_gofra_info(p.get('gofra_mm', 10.0))

        text = f"🎯 СЛЕДУЮЩАЯ ГОФРА\n\n"

        if gofra_info.get('next_threshold'):
            current_gofra = p.get('gofra_mm', 10.0)
            next_threshold = gofra_info['next_threshold']
            next_gofra = get_gofra_info(next_threshold)

            text += f"🏗️ Текущая гофрошка: {gofra_info['length_display']}\n"
            text += f"{gofra_info['emoji']} {gofra_info['name']}\n\n"
            text += f"📈 Следующая гофрошка:\n"
            text += f"{next_gofra['emoji']} {next_gofra['name']}\n"
            text += f"📏 Требуется: {next_gofra['length_display']}\n\n"
            text += f"📊 Преимущества:\n"
            text += f"• Скорость атмосфер: x{next_gofra['atm_speed']:.2f} (текущая: x{gofra_info['atm_speed']:.2f})\n"
            text += f"• Вес змия: {next_gofra['min_grams']}-{next_gofra['max_grams']}г (текущий: {gofra_info['min_grams']}-{gofra_info['max_grams']}г)\n\n"
            text += f"💪 Как получить:\n"
            text += f"• Дави змия при 12 атмосферах\n"
            text += f"• Получай опыт: 0.02 мм за 1 грамм змия\n"
            text += f"• Нужно ещё: {next_threshold - current_gofra:.1f} мм"
        else:
            text += "🎉 Ты достиг максимального уровня!\n"
            text += "🏆 Коричневый бог - это ты!\n"
            text += "📊 Больше нет уровней гофрошки"

        try:
            await callback.message.edit_text(text, reply_markup=gofra_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=gofra_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in gofra next callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о следующей гофрошке", show_alert=True)

# ==================== CABLE DETAIL CALLBACKS ====================

@router.callback_query(F.data == "cable_power_info")
async def handle_cable_power_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"💪 СИЛА КАБЕЛЯ\n\n"
        text += f"🔌 Длина кабеля: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"⚔️ Бонус в PvP: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"📊 Как влияет на PvP:\n"
        text += f"• Каждый 1 мм кабеля = +0.02% к шансу победы\n"
        text += f"• Твой бонус: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n"
        text += f"• Максимальный бонус: +20% (1000 мм кабеля)\n\n"
        text += f"💡 Как прокачать:\n"
        text += f"• Дави змия: +0.2 мм за 1 кг змия\n"
        text += f"• Побеждай в радёмках: +0.2 мм за победу\n"
        text += f"• Участвуй в PvP боях"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable power callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о силе кабеля", show_alert=True)

@router.callback_query(F.data == "cable_pvp_info")
async def handle_cable_pvp_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"⚔️ КАБЕЛЬ В PVP\n\n"
        text += f"🔌 Твой кабель: {format_length(p.get('cable_mm', 10.0))}\n"
        text += f"💪 Бонус к шансу победы: +{(p.get('cable_mm', 10.0) * 0.02):.1f}%\n\n"
        text += f"📊 Формула PvP:\n"
        text += f"• Базовый шанс: 50%\n"
        text += f"• Бонус от гофрошки: +2% за каждые 10 мм разницы\n"
        text += f"• Бонус от кабеля: +0.2% за каждый 1 мм разницы\n"
        text += f"• Общий шанс: от 10% до 90%\n\n"
        text += f"💡 Стратегия:\n"
        text += f"• Прокачивай кабель для увеличения шанса\n"
        text += f"• Выбирай противников с меньшим кабелем\n"
        text += f"• Победы дают +0.2 мм к кабелю"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable pvp callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о PvP", show_alert=True)

@router.callback_query(F.data == "cable_upgrade_info")
async def handle_cable_upgrade_callback(callback: types.CallbackQuery):
    try:
        p = await get_patsan(callback.from_user.id)

        text = f"📈 ПРОКАЧКА КАБЕЛЯ\n\n"
        text += f"🔌 Текущая длина: {format_length(p.get('cable_mm', 10.0))}\n\n"
        text += f"📊 Способы прокачки:\n"
        text += f"1️⃣ Давка змия:\n"
        text += f"   • +0.2 мм за 1 кг змия\n"
        text += f"   • Твой прогресс: {p.get('total_zmiy_grams', 0)/1000:.1f} кг\n"
        text += f"   • Кабель от давки: +{(p.get('total_zmiy_grams', 0)/1000 * 0.2):.1f} мм\n\n"
        text += f"2️⃣ Победы в PvP:\n"
        text += f"   • +0.2 мм за каждую победу\n"
        text += f"   • Участвуй в радёмках\n"
        text += f"   • Выбирай слабых противников\n\n"
        text += f"💡 Советы:\n"
        text += f"• Дави больше змия для быстрой прокачки\n"
        text += f"• Участвуй в PvP для дополнительного бонуса\n"
        text += f"• Следи за прогрессом в профиле"

        try:
            await callback.message.edit_text(text, reply_markup=cable_info_kb())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=cable_info_kb())

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in cable upgrade callback: {e}")
        await callback.answer("❌ Ошибка загрузки информации о прокачке", show_alert=True)

# ==================== CHAT COMMAND HANDLERS ====================

@router.message(Command("gme", "g_me", "chatme"))
async def my_chat_stats_command(message: types.Message):
    await show_user_chat_stats_message(message.from_user.id, message.chat.id, message)

# ========== ATM HANDLERS ==========

@router.callback_query(F.data == "atm_regen_time")
@ignore_not_modified_error
async def atm_regen_time_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)

        atm_count = patsan.get('atm_count', 0)
        max_atm = 12

        regen_info = await calculate_atm_regen_time(patsan)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        text = (
            f"⏱️ ВРЕМЯ ВОССТАНОВЛЕНИЯ АТМОСФЕР\n\n"
            f"Текущее состояние:\n"
            f"🌀 Атмосферы: [{pb(atm_count, max_atm)}] {atm_count}/{max_atm}\n"
            f"📈 Нужно восстановить: {regen_info['needed']} шт.\n\n"
            f"Точный таймер:\n"
            f"🕒 До следующей атмосферы: {ft(regen_info['time_to_next_atm'])}\n"
            f"🕐 До полного восстановления: {ft(regen_info['total'])}\n\n"
            f"Скорость восстановления:\n"
            f"• Базовая: 1 атм. за 2 часа (7200с)\n"
            f"• С учётом гофрошки ({gofra_info['name']}): x{gofra_info['atm_speed']:.2f}\n"
            f"• 1 атм. за: {ft(regen_info['time_to_one_atm'])}\n\n"
            f"Как ускорить:\n"
            f"• Повышай гофрошку - ускоряет восстановление\n"
            f"• Дави змия при полных 12 атмосферах\n"
            f"• Больше опыт → выше гофрошка → быстрее атмосферы"
        )

        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "atm_max_info")
async def atm_max_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)

        current_max = 12
        atm_count = patsan.get('atm_count', 0)

        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        text = (
            f"📊 МАКСИМАЛЬНЫЙ ЗАПАС АТМОСФЕР\n\n"
            f"Текущие показатели:\n"
            f"🌀 Атмосферы: [{pb(atm_count, current_max)}] {atm_count}/{current_max}\n"
            f"🎯 Максимум: {current_max} атм.\n\n"
            f"Особенности системы:\n"
            f"• Фиксированный максимум: 12 атмосфер\n"
            f"• Только при полных 12 можно давить змия\n"
            f"• Восстановление зависит от гофрошки\n\n"
            f"Твоя гофрошка:\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"⚡ Скорость восстановления: x{gofra_info['atm_speed']:.2f}\n\n"
            f"Зачем ждать 12 атмосфер?\n"
            f"• Более тяжёлый змий при давке\n"
            f"• Больше опыт для гофрошки\n"
            f"• Укрепление кабеля (+0.1 мм за 1кг змия)"
        )

        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)

@ignore_not_modified_error
@router.callback_query(F.data == "atm_boosters")
async def atm_boosters_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        user_id = callback.from_user.id
        patsan = await get_patsan(user_id)
        gofra_info = get_gofra_info(patsan.get('gofra_mm', 10.0))

        text = (
            f"⚡ УСКОРЕНИЕ ВОССТАНОВЛЕНИЯ\n\n"
            f"В новой системе нет платных бустеров!\n\n"
            f"Вместо них работает:\n"
            f"🏗️ СИСТЕМА ГОФРЫ\n\n"
            f"Твоя гофрошка:\n"
            f"{gofra_info['emoji']} {gofra_info['name']}\n"
            f"⚡ Множитель скорости: x{gofra_info['atm_speed']:.2f}\n\n"
            f"Как улучшить гофрошку?\n"
            f"1. Дождись 12 атмосфер (кнопка 🌡️)\n"
            f"2. Дави змия (кнопка 🐍)\n"
            f"3. Получай опыт (0.02 мм/г змия)\n"
            f"4. Повышай гофрошку\n\n"
            f"Следующие уровни гофрошки:\n"
        )

        thresholds = [10.0, 50.0, 150.0, 300.0, 600.0, 1200.0, 2500.0, 5000.0, 10000.0, 20000.0]
        current_gofra = patsan.get('gofra_mm', 10.0)

        for i, threshold in enumerate(thresholds):
            if current_gofra < threshold:
                next_info = get_gofra_info(threshold)
                text += f"• {next_info['emoji']} {next_info['name']}: x{next_info['atm_speed']:.2f}\n"
                if i >= 2:
                    break

        await callback.message.edit_text(
            text,
            reply_markup=back_to_profile_keyboard()
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)
