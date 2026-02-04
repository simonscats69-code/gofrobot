"""
Пример интеграции всех систем оптимизации для Telegram бота.

Этот файл демонстрирует:
- Как объединить все оптимизационные системы
- Пример использования в реальном боте
- Паттерны интеграции
- Примеры middleware
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters

# Импортируем все наши системы оптимизации
from optimization_manager import (
    get_optimization_manager, 
    initialize_optimization, 
    get_optimization_status,
    get_performance_report,
    shutdown_optimization
)
from cache_manager import cache_get, cache_set, cache_exists
from rate_limiter import check_rate_limit, is_user_blocked
from error_handler import get_error_handler, handle_bot_error
from metrics_collector import get_metrics_collector, measure_performance
from backup_manager import create_backup, list_backups, restore_backup
from db_manager import get_connection, release_connection

logger = logging.getLogger(__name__)

class BotOptimizationMiddleware:
    """Middleware для интеграции всех систем оптимизации."""
    
    def __init__(self):
        self.optimization_manager = get_optimization_manager()
    
    async def initialize(self):
        """Инициализирует все системы оптимизации."""
        logger.info("🚀 Инициализация всех систем оптимизации...")
        
        # Инициализируем оптимизацию с высоким уровнем
        await initialize_optimization(level="high")
        
        # Настраиваем дополнительные параметры
        self.optimization_manager.config.cache_ttl = 600  # 10 минут
        self.optimization_manager.config.monitoring_interval = 30  # 30 секунд
        self.optimization_manager.config.backup_interval = 1800  # 30 минут
        
        logger.info("✅ Все системы оптимизации инициализированы")
    
    async def shutdown(self):
        """Останавливает все системы оптимизации."""
        await shutdown_optimization()
        logger.info("🛑 Все системы оптимизации остановлены")
    
    async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает обновление через все системы оптимизации."""
        start_time = datetime.now()
        
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            command = self._extract_command(update)
            
            # 1. Проверка rate limiting
            if command:
                rate_result = await check_rate_limit(user_id, chat_id, command)
                if not rate_result.allowed:
                    await self._handle_rate_limit_exceeded(update, rate_result)
                    return
            
            # 2. Проверка блокировки пользователя
            if is_user_blocked(user_id):
                await update.message.reply_text("🚫 Вы временно заблокированы.")
                return
            
            # 3. Проверка кэша (если команда поддерживает кэширование)
            if command and self._is_cacheable_command(command):
                cached_result = await self._check_cache(update, command)
                if cached_result:
                    await update.message.reply_text(cached_result)
                    return
            
            # 4. Продолжаем обработку команды
            context.user_data['processing_start_time'] = start_time
            
        except Exception as e:
            logger.error(f"❌ Ошибка в middleware: {e}")
            await handle_bot_error(update, context)
    
    def _extract_command(self, update: Update) -> Optional[str]:
        """Извлекает команду из обновления."""
        if update.message and update.message.text:
            text = update.message.text.strip()
            if text.startswith('/'):
                return text.split()[0].lstrip('/')
        return None
    
    def _is_cacheable_command(self, command: str) -> bool:
        """Определяет, можно ли кэшировать команду."""
        cacheable_commands = ['stats', 'top', 'help', 'info']
        return command in cacheable_commands
    
    async def _handle_rate_limit_exceeded(self, update: Update, rate_result):
        """Обрабатывает превышение лимита запросов."""
        if rate_result.retry_after:
            await update.message.reply_text(
                f"⏰ Слишком много запросов! Подождите {rate_result.retry_after} секунд."
            )
        else:
            await update.message.reply_text("⏰ Слишком много запросов!")
    
    async def _check_cache(self, update: Update, command: str) -> Optional[str]:
        """Проверяет кэш для команды."""
        try:
            cache_key = f"command_result:{command}:{update.effective_user.id}"
            
            if await cache_exists('command', cache_key):
                result = await cache_get('command', cache_key)
                return result
            
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка проверки кэша: {e}")
            return None
    
    async def cache_command_result(self, update: Update, command: str, result: str):
        """Кэширует результат команды."""
        try:
            cache_key = f"command_result:{command}:{update.effective_user.id}"
            await cache_set('command', cache_key, result, ttl=300)  # 5 минут
        except Exception as e:
            logger.error(f"❌ Ошибка кэширования результата: {e}")

class OptimizedBotHandlers:
    """Оптимизированные обработчики команд."""
    
    def __init__(self, middleware: BotOptimizationMiddleware):
        self.middleware = middleware
        self.metrics_collector = get_metrics_collector()
    
    @measure_performance("davka")
    async def handle_davka_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду давки с оптимизациями."""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            # Проверяем кэш для статистики пользователя
            cache_key = f"user_stats:{user_id}"
            cached_stats = await cache_get('user', cache_key)
            
            if cached_stats:
                await update.message.reply_text(f"📊 Кэшированная статистика: {cached_stats}")
                return
            
            # Выполняем давку (реализация из db_manager)
            from db_manager import davka_zmiy
            success, patsan, result_data = await davka_zmiy(user_id, chat_id)
            
            if success:
                response = f"🐍 Давка прошла успешно! Змий: {result_data['zmiy_grams']}г"
                
                # Кэшируем результат
                await cache_set('user', cache_key, response, ttl=600)
                
                await update.message.reply_text(response)
            else:
                await update.message.reply_text(f"❌ Ошибка: {result_data['error']}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в команде давки: {e}")
            await handle_bot_error(update, context)
    
    @measure_performance("stats")
    async def handle_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду статистики с оптимизациями."""
        try:
            user_id = update.effective_user.id
            
            # Проверяем кэш
            cache_key = f"user_stats:{user_id}"
            cached_stats = await cache_get('user', cache_key)
            
            if cached_stats:
                await update.message.reply_text(f"📊 Кэшированная статистика:\n{cached_stats}")
                return
            
            # Получаем статистику из базы данных
            conn = await get_connection()
            try:
                cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user_data = await cursor.fetchone()
                
                if user_data:
                    stats = f"""
📊 Ваша статистика:
Никнейм: {user_data['nickname']}
Гофра: {user_data['gofra_mm']:.1f} мм
Кабель: {user_data['cable_mm']:.1f} мм
Змий: {user_data['zmiy_grams']:.1f} г
Атмосферы: {user_data['atm_count']}/12
                    """
                    
                    # Кэшируем результат
                    await cache_set('user', cache_key, stats, ttl=300)
                    
                    await update.message.reply_text(stats)
                else:
                    await update.message.reply_text("❌ Пользователь не найден")
                    
            finally:
                await release_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в команде статистики: {e}")
            await handle_bot_error(update, context)
    
    @measure_performance("backup")
    async def handle_backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду резервного копирования."""
        try:
            # Создаем резервную копию
            success, backup_info = await create_backup(description="Ручная резервная копия")
            
            if success and backup_info:
                await update.message.reply_text(
                    f"✅ Резервная копия создана: {backup_info.filename}\n"
                    f"Размер: {backup_info.size} байт"
                )
            else:
                await update.message.reply_text("❌ Не удалось создать резервную копию")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в команде бэкапа: {e}")
            await handle_bot_error(update, context)
    
    @measure_performance("performance")
    async def handle_performance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду проверки производительности."""
        try:
            # Получаем статус оптимизации
            status = get_optimization_status()
            
            # Получаем отчет о производительности
            report = get_performance_report(1)  # за последний час
            
            # Формируем ответ
            response = f"""
🚀 Статус оптимизации:
Уровень: {status['optimization_level']}
Системы: {len([s for s in status['systems'].values() if s['enabled']])}/5 активны

📊 Производительность (последний час):
Среднее время ответа: {report['performance_metrics']['response_time']['avg']:.2f}ms
Использование CPU: {report['performance_metrics']['cpu_usage']['avg']:.1f}%
Использование памяти: {report['performance_metrics']['memory_usage']['avg']:.1f}MB
Процент попаданий в кэш: {report['performance_metrics']['cache_hit_rate']['avg']:.1f}%

💡 Рекомендации:
{chr(10).join(report['recommendations'][:3])}
            """
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в команде производительности: {e}")
            await handle_bot_error(update, context)

async def create_optimized_bot_application():
    """Создает оптимизированное приложение бота."""
    
    # Создаем middleware
    middleware = BotOptimizationMiddleware()
    await middleware.initialize()
    
    # Создаем обработчики
    handlers = OptimizedBotHandlers(middleware)
    
    # Создаем приложение
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # Добавляем middleware
    application.add_handler(MessageHandler(filters.ALL, middleware.process_update), group=-1)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("davka", handlers.handle_davka_command))
    application.add_handler(CommandHandler("stats", handlers.handle_stats_command))
    application.add_handler(CommandHandler("backup", handlers.handle_backup_command))
    application.add_handler(CommandHandler("performance", handlers.handle_performance_command))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(handle_bot_error)
    
    # Сохраняем ссылки для последующего использования
    application.middleware = middleware
    application.handlers = handlers
    
    return application

async def run_optimized_bot():
    """Запускает оптимизированного бота."""
    try:
        # Создаем и запускаем приложение
        application = await create_optimized_bot_application()
        
        logger.info("🚀 Запуск оптимизированного бота...")
        await application.run_polling()
        
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота по запросу пользователя...")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        # Останавливаем все системы оптимизации
        if hasattr(application, 'middleware'):
            await application.middleware.shutdown()

# Пример использования в реальном проекте

def setup_optimized_bot():
    """Настройка оптимизированного бота."""
    
    # 1. Инициализация систем оптимизации
    asyncio.run(initialize_optimization())
    
    # 2. Настройка middleware в основном приложении
    # application.add_handler(MessageHandler(filters.ALL, process_update), group=-1)
    
    # 3. Использование оптимизированных функций в обработчиках
    # @measure_performance("command_name")
    # async def handle_command(update, context):
    #     # Ваш код команды
    
    # 4. Мониторинг производительности
    # status = get_optimization_status()
    # report = get_performance_report()

def performance_monitoring_example():
    """Пример мониторинга производительности."""
    
    async def monitor_performance():
        while True:
            try:
                # Получаем статус
                status = get_optimization_status()
                
                # Проверяем критические метрики
                metrics = status['metrics']
                
                if metrics['response_time']['avg'] > 1000:
                    logger.warning(f"⚠️ Высокое время ответа: {metrics['response_time']['avg']}ms")
                
                if metrics['cpu_usage']['current'] > 80:
                    logger.warning(f"⚠️ Высокая нагрузка CPU: {metrics['cpu_usage']['current']}%")
                
                if metrics['memory_usage']['current'] > 512:
                    logger.warning(f"⚠️ Высокое использование памяти: {metrics['memory_usage']['current']}MB")
                
                # Генерируем отчет каждый час
                if datetime.now().minute == 0:
                    report = get_performance_report(1)
                    logger.info(f"📊 Часовой отчет: {report['performance_metrics']}")
                
                await asyncio.sleep(60)  # Проверяем каждую минуту
                
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга: {e}")
                await asyncio.sleep(60)
    
    # Запускаем мониторинг в фоновом режиме
    asyncio.create_task(monitor_performance())

def backup_automation_example():
    """Пример автоматизации резервного копирования."""
    
    async def automated_backup():
        while True:
            try:
                # Создаем резервную копию
                success, backup_info = await create_backup(
                    backup_type="daily",
                    description="Автоматическая резервная копия"
                )
                
                if success:
                    logger.info(f"✅ Автоматическая резервная копия создана: {backup_info.filename}")
                else:
                    logger.error("❌ Не удалось создать автоматическую резервную копию")
                
                # Очищаем старые резервные копии (старше 7 дней)
                from backup_manager import cleanup_old_backups
                await cleanup_old_backups(days=7)
                
                # Ждем 24 часа
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"❌ Ошибка автоматического бэкапа: {e}")
                await asyncio.sleep(3600)  # Ждем час перед повторной попыткой
    
    # Запускаем автоматический бэкап
    asyncio.create_task(automated_backup())

# Пример использования всех систем вместе

async def full_integration_example():
    """Полный пример интеграции всех систем."""
    
    # 1. Инициализация
    await initialize_optimization(level="high")
    
    # 2. Создание middleware
    middleware = BotOptimizationMiddleware()
    await middleware.initialize()
    
    # 3. Пример обработки команды с использованием всех систем
    async def optimized_command_handler(update, context):
        start_time = datetime.now()
        
        try:
            user_id = update.effective_user.id
            command = "example"
            
            # Rate limiting
            rate_result = await check_rate_limit(user_id, update.effective_chat.id, command)
            if not rate_result.allowed:
                return
            
            # Cache check
            cache_key = f"command:{command}:{user_id}"
            cached_result = await cache_get('command', cache_key)
            if cached_result:
                await update.message.reply_text(cached_result)
                return
            
            # Database operation with connection pooling
            conn = await get_connection()
            try:
                # Выполняем запрос
                cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                result = await cursor.fetchone()
                
                # Process result
                response = f"Результат: {result}"
                
                # Cache result
                await cache_set('command', cache_key, response, ttl=300)
                
                await update.message.reply_text(response)
                
            finally:
                await release_connection(conn)
            
            # Metrics collection
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Команда {command} выполнена за {execution_time:.2f}ms")
            
        except Exception as e:
            # Error handling
            await handle_bot_error(update, context)
    
    # 4. Запуск фоновых задач
    performance_monitoring_example()
    backup_automation_example()
    
    # 5. Получение отчетов
    status = get_optimization_status()
    report = get_performance_report(24)
    
    logger.info(f"📊 Статус оптимизации: {status}")
    logger.info(f"📈 Отчет о производительности: {report}")

if __name__ == "__main__":
    # Запуск полной интеграции
    asyncio.run(full_integration_example())