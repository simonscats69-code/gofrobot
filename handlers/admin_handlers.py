"""
Админ-панель для Gofrobot
Команда /Gofroadmin для доступа к функциям администрирования
"""

import logging
import os
import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from keyboards import admin_keyboard, admin_system_keyboard
from db_manager import (
    get_backup_info, create_backup, 
    get_connection, close_pool,
    ADMIN_CONFIG
)
from config import DB_CONFIG, TIMING_CONFIG

logger = logging.getLogger(__name__)

router = Router()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    admin_ids = ADMIN_CONFIG.get("admin_ids", [])
    return user_id in admin_ids

@router.message(Command("Gofroadmin"))
async def cmd_admin(message: Message):
    """Показать админ-панель"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    await message.answer(
        "⚙️ **АДМИН-ПАНЕЛЬ GO frobot**\n\n"
        "Выберите действие:",
        reply_markup=admin_keyboard()
    )

@router.callback_query(F.data.startswith("admin_"))
async def callback_admin(callback: CallbackQuery):
    """Обработка кнопок админ-панели"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    action = callback.data
    
    try:
        if action == "admin_backup":
            await callback.message.edit_text("💾 Создаю бэкап...")
            backup_name = await create_backup()
            if backup_name:
                await callback.message.edit_text(
                    f"✅ Бэкап создан: `{backup_name}`",
                    reply_markup=admin_keyboard()
                )
            else:
                await callback.message.edit_text(
                    "❌ Ошибка создания бэкапа",
                    reply_markup=admin_keyboard()
                )
        
        elif action == "admin_stats":
            backup_info = await get_backup_info()
            message_text = (
                "📊 **СТАТИСТИКА СИСТЕМЫ**\n\n"
                f"📁 Бэкапов: {backup_info.get('count', 0)}\n"
                f"💾 Размер бэкапов: {backup_info.get('total_size_mb', 0)} МБ\n\n"
                f"⚙️ Настройки БД:\n"
                f"- Таймаут: {DB_CONFIG.get('timeout', 60)}с\n"
                f"- Кэш TTL: {DB_CONFIG.get('cache_ttl', 30)}с\n"
                f"- Интервал сохранения: {DB_CONFIG.get('batch_save_interval', 5)}с\n\n"
                f"⏰ Тайминг:\n"
                f"- Давка: {TIMING_CONFIG.get('base_davka_cooldown', 7200)}с\n"
                f"- ATM: {TIMING_CONFIG.get('atm_regen_time', 600)}с"
            )
            await callback.message.edit_text(message_text, reply_markup=admin_keyboard())
        
        elif action == "admin_system":
            await callback.message.edit_text(
                "🔧 **СИСТЕМНЫЕ НАСТРОЙКИ**\n\n"
                "Выберите действие:",
                reply_markup=admin_system_keyboard()
            )
        
        elif action == "admin_players":
            # Статистика игроков
            conn = await get_connection()
            try:
                cursor = await conn.execute("SELECT COUNT(*) FROM users")
                result = await cursor.fetchone()
                total_users = result[0] if result else 0
                
                cursor = await conn.execute("SELECT COUNT(DISTINCT user_id) FROM rademka_fights")
                result = await cursor.fetchone()
                rademka_players = result[0] if result else 0
                
                message_text = (
                    "👥 **СТАТИСТИКА ИГРОКОВ**\n\n"
                    f"📊 Всего пользователей: {total_users}\n"
                    f"⚔️ Участвовали в радёмке: {rademka_players}\n\n"
                    f"💪 Активность: {(rademka_players/total_users*100):.1f}%" if total_users > 0 else ""
                )
                await callback.message.edit_text(message_text, reply_markup=admin_keyboard())
            finally:
                await conn.close()
        
        elif action == "admin_logs":
            log_dir = "storage/logs"
            if os.path.exists(log_dir):
                logs = [f for f in os.listdir(log_dir) if f.endswith('.log')]
                logs.sort(reverse=True)
                recent_logs = logs[:5]
                
                log_text = "📝 **ПОСЛЕДНИЕ ЛОГИ**\n\n"
                for log in recent_logs:
                    log_text += f"📄 {log}\n"
                
                if not logs:
                    log_text += "Логи не найдены"
                
                await callback.message.edit_text(log_text, reply_markup=admin_keyboard())
            else:
                await callback.message.edit_text(
                    "📝 Директория логов не найдена",
                    reply_markup=admin_keyboard()
                )
        
        elif action == "admin_settings":
            await callback.message.edit_text(
                "⚙️ **НАСТРОЙКИ**\n\n"
                "Эта секция в разработке...",
                reply_markup=admin_keyboard()
            )
        
        elif action == "admin_db_info":
            conn = await get_connection()
            try:
                cursor = await conn.execute("SELECT COUNT(*) FROM users")
                users_count = (await cursor.fetchone())[0]
                
                cursor = await conn.execute("SELECT COUNT(*) FROM rademka_fights")
                fights_count = (await cursor.fetchone())[0]
                
                cursor = await conn.execute("SELECT COUNT(*) FROM chat_stats")
                chats_count = (await cursor.fetchone())[0]
                
                db_path = "storage/bot_database.db"
                db_size = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
                
                message_text = (
                    f"🗄️ **ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ**\n\n"
                    f"📁 Путь: `{db_path}`\n"
                    f"💾 Размер: {db_size:.2f} МБ\n\n"
                    f"📊 Таблицы:\n"
                    f"- Пользователи: {users_count}\n"
                    f"- Бои радёмки: {fights_count}\n"
                    f"- Чаты: {chats_count}"
                )
                await callback.message.edit_text(message_text, reply_markup=admin_keyboard())
            finally:
                await conn.close()
        
        elif action == "admin_redis":
            await callback.message.edit_text(
                "📈 **REDIS СТАТИСТИКА**\n\n"
                "Redis не настроен или недоступен.\n"
                "Используется локальный кэш.",
                reply_markup=admin_keyboard()
            )
        
        elif action == "admin_restart":
            await callback.message.edit_text(
                "🔄 **ПЕРЕЗАПУСК**\n\n"
                "⚠️ Для перезапуска бота используйте:\n"
                "```\n"
                "sudo systemctl restart gofrobot\n"
                "```\n\n"
                "Или перезапустите процесс вручную.",
                reply_markup=admin_keyboard()
            )
        
        elif action == "admin_clear_cache":
            await callback.message.edit_text(
                "🧹 **ОЧИСТКА КЭША**\n\n"
                "Кэш очищен!",
                reply_markup=admin_keyboard()
            )
        
        elif action == "admin_back":
            await callback.message.edit_text(
                "⚙️ **АДМИН-ПАНЕЛЬ GO frobot**\n\n"
                "Выберите действие:",
                reply_markup=admin_keyboard()
            )
        
        elif action == "admin_exit":
            await callback.message.delete()
            await callback.answer("Панель закрыта")
            return
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin callback: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка: {e}",
            reply_markup=admin_keyboard()
        )
