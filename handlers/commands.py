from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db_manager import get_patsan, get_gofra_info, calculate_atm_regen_time, format_length
from keyboards import main_keyboard, profile_extended_kb
from keyboards import rademka_keyboard, top_sort_keyboard, nickname_keyboard, gofra_info_kb, cable_info_kb, atm_status_kb, mk

# Импорты для визуальных эффектов (если доступны)
try:
    from utils.visual_effects import visual_effects
    from utils.formatters import formatters
    from utils.animations import animation_manager, notification_effects
    from utils.keyboards import beautiful_keyboards
    VISUAL_EFFECTS_AVAILABLE = True
except ImportError:
    VISUAL_EFFECTS_AVAILABLE = False

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
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

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Handle /admin command - show admin panel"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    # Show admin panel
    admin_text = """
🔧 <b>Админ-панель</b>

Доступные команды:
"""
    
    await message.answer(admin_text, reply_markup=mk("admin"), parse_mode='HTML')

@router.message(Command("admin_repair"))
async def cmd_admin_repair(message: types.Message):
    """Handle /admin_repair command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Import and run repair
        from persistent_storage import storage_manager
        await storage_manager._repair_database()
        
        await message.answer("✅ База данных успешно отремонтирована!", reply_markup=mk("admin"))
    except Exception as e:
        await message.answer(f"❌ Ошибка при ремонте базы данных: {e}", reply_markup=mk("admin"))

@router.message(Command("admin_backup"))
async def cmd_admin_backup(message: types.Message):
    """Handle /admin_backup command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Import and run backup
        from persistent_storage import storage_manager
        await storage_manager._create_backup("manual")
        
        await message.answer("✅ Резервная копия создана!", reply_markup=mk("admin"))
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании резервной копии: {e}", reply_markup=mk("admin"))

@router.message(Command("admin_status"))
async def cmd_admin_status(message: types.Message):
    """Handle /admin_status command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Import and get status
        from persistent_storage import storage_manager
        
        # Run diagnostics
        diagnostics = await storage_manager.diagnostic_system.run_comprehensive_diagnostic()
        health = storage_manager.diagnostic_system.get_health_summary()
        
        # Format status message
        status_text = f"""
📊 <b>Статус системы</b>

🏥 <b>Здоровье:</b> {health['status'].upper()}
📝 <b>Сообщение:</b> {health['message']}
⚠️ <b>Проблем:</b> {health['total_issues']}

📋 <b>Последняя проверка:</b> {health['last_check'].strftime('%Y-%m-%d %H:%M:%S') if health['last_check'] else 'Нет данных'}

🔧 <b>Рекомендации:</b>
"""
        
        for result in diagnostics:
            if result.severity in ["warning", "error", "critical"]:
                status_text += f"• {result.message}\n"
                for suggestion in result.suggestions:
                    status_text += f"  - {suggestion}\n"
        
        await message.answer(status_text, reply_markup=mk("admin"), parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении статуса: {e}", reply_markup=mk("admin"))

@router.message(Command("admin_cleanup"))
async def cmd_admin_cleanup(message: types.Message):
    """Handle /admin_cleanup command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Import and run cleanup
        from persistent_storage import storage_manager
        await storage_manager._cleanup_backups()
        
        await message.answer("✅ Очистка завершена!", reply_markup=mk("admin"))
    except Exception as e:
        await message.answer(f"❌ Ошибка при очистке: {e}", reply_markup=mk("admin"))

@router.message(Command("admin_logs"))
async def cmd_admin_logs(message: types.Message):
    """Handle /admin_logs command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Get recent log entries
        import logging
        from logging_system import get_recent_logs
        
        logs = await get_recent_logs(50)  # Get last 50 log entries
        
        if not logs:
            await message.answer("📋 Логи пусты", reply_markup=mk("admin"))
            return
        
        # Format logs
        log_text = "<b>Последние логи:</b>\n\n"
        for log in logs:
            log_text += f"{log}\n"
        
        await message.answer(log_text, reply_markup=mk("admin"), parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении логов: {e}", reply_markup=mk("admin"))

@router.message(Command("admin_settings"))
async def cmd_admin_settings(message: types.Message):
    """Handle /admin_settings command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    # Show settings menu
    settings_text = """
⚙️ <b>Настройки системы</b>

Текущие настройки:
• Авто-ремонт: {}
• Интервал бэкапов: {} минут
• Интервал диагностики: {} минут
""".format(
        "Включён" if ADMIN_CONFIG["auto_repair_enabled"] else "Выключен",
        ADMIN_CONFIG["backup_interval"] // 60,
        ADMIN_CONFIG["diagnostic_interval"] // 60
    )
    
    await message.answer(settings_text, reply_markup=mk("admin_settings"), parse_mode='HTML')

@router.message(Command("admin_enable_auto_repair"))
async def cmd_admin_enable_auto_repair(message: types.Message):
    """Handle /admin_enable_auto_repair command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    ADMIN_CONFIG["auto_repair_enabled"] = True
    await message.answer("✅ Автоматический ремонт включён!", reply_markup=mk("admin_settings"))

@router.message(Command("admin_disable_auto_repair"))
async def cmd_admin_disable_auto_repair(message: types.Message):
    """Handle /admin_disable_auto_repair command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    ADMIN_CONFIG["auto_repair_enabled"] = False
    await message.answer("❌ Автоматический ремонт выключен!", reply_markup=mk("admin_settings"))

@router.message(Command("admin_export"))
async def cmd_admin_export(message: types.Message):
    """Handle /admin_export command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Import and run export
        from persistent_storage import storage_manager
        
        export_file = await storage_manager.export_data("json")
        
        if export_file:
            await message.answer(f"📤 Экспорт завершён: {export_file}", reply_markup=mk("admin"))
        else:
            await message.answer("❌ Ошибка при экспорте данных", reply_markup=mk("admin"))
    except Exception as e:
        await message.answer(f"❌ Ошибка при экспорте: {e}", reply_markup=mk("admin"))

@router.message(Command("admin_import"))
async def cmd_admin_import(message: types.Message):
    """Handle /admin_import command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    await message.answer("📥 Отправьте файл для импорта (JSON или SQL)", reply_markup=mk("admin"))

@router.message(Command("admin_restore"))
async def cmd_admin_restore(message: types.Message):
    """Handle /admin_restore command"""
    user_id = message.from_user.id
    
    # Check if user is admin
    from config import ADMIN_CONFIG
    if user_id not in ADMIN_CONFIG["admin_ids"]:
        await message.answer("❌ Доступ запрещён. Вы не являетесь администратором.", reply_markup=main_keyboard())
        return
    
    try:
        # Import and run restore
        from persistent_storage import storage_manager
        await storage_manager._restore_from_backup()
        
        await message.answer("✅ Восстановление из резервной копии завершено!", reply_markup=mk("admin"))
    except Exception as e:
        await message.answer(f"❌ Ошибка при восстановлении: {e}", reply_markup=mk("admin"))

@router.message(Command("version"))
async def cmd_version(message: types.Message):
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
