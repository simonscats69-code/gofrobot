"""
Пример интеграции системы оптимизации в существующий Telegram бот.

Этот файл показывает, как добавить все системы оптимизации
в уже работающий Telegram бот без полной переработки кода.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters

# Импортируем системы оптимизации
from optimization_manager import (
    get_optimization_manager, 
    initialize_optimization, 
    get_optimization_status,
    get_performance_report
)
from cache_manager import cache_get, cache_set, cache_exists
from rate_limiter import check_rate_limit, is_user_blocked
from error_handler import get_error_handler, handle_bot_error
from metrics_collector import get_metrics_collector, measure_performance
from backup_manager import create_backup, list_backups
from db_manager import get_connection, release_connection

logger = logging.getLogger(__name__)

class ExistingBotIntegration:
    """
    Пример интеграции оптимизаций в существующий бот.
    
    Показывает, как добавить оптимизации постепенно,
    не переписывая весь код бота.
    """
    
    def __init__(self):
        self.optimization_manager = get_optimization_manager()
        self.error_handler = get_error_handler()
        self.metrics_collector = get_metrics_collector()
    
    async def initialize_optimizations(self):
        """Инициализирует оптимизации в существующем боте."""
        logger.info("🚀 Инициализация оптимизаций в существующем боте...")
        
        # 1. Инициализация базовых систем
        await initialize_optimization(level="medium")
        
        # 2. Настройка дополнительных параметров
        self.optimization_manager.config.cache_ttl = 600  # 10 минут
        self.optimization_manager.config.monitoring_interval = 30  # 30 секунд
        self.optimization_manager.config.backup_interval = 1800  # 30 минут
        
        # 3. Настройка rate limiting для существующих команд
        rate_limiter = get_rate_limiter()
        rate_limiter.add_limit("command:davka", RateLimitConfig(limit=5, window_seconds=300))
        rate_limiter.add_limit("command:rademka", RateLimitConfig(limit=3, window_seconds=600))
        rate_limiter.add_limit("command:stats", RateLimitConfig(limit=10, window_seconds=60))
        
        logger.info("✅ Оптимизации инициализированы")
    
    def create_optimization_middleware(self):
        """Создает middleware для оптимизации существующих обработчиков."""
        
        class OptimizationMiddleware:
            def __init__(self, integration: 'ExistingBotIntegration'):
                self.integration = integration
            
            async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Обрабатывает обновление через все системы оптимизации."""
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
                    
                    # 3. Сохраняем время начала обработки
                    context.user_data['processing_start_time'] = datetime.now()
                    
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
            
            async def _handle_rate_limit_exceeded(self, update: Update, rate_result):
                """Обрабатывает превышение лимита запросов."""
                if rate_result.retry_after:
                    await update.message.reply_text(
                        f"⏰ Слишком много запросов! Подождите {rate_result.retry_after} секунд."
                    )
                else:
                    await update.message.reply_text("⏰ Слишком много запросов!")
        
        return OptimizationMiddleware(self)
    
    def optimize_existing_handler(self, original_handler):
        """
        Декоратор для оптимизации существующего обработчика.
        
        Добавляет кэширование, измерение производительности и обработку ошибок.
        """
        async def optimized_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            command = self._extract_command(update)
            
            try:
                # 1. Проверка кэша (если команда поддерживает кэширование)
                if command and self._is_cacheable_command(command):
                    cache_key = f"command_result:{command}:{user_id}"
                    cached_result = await cache_get('command', cache_key)
                    if cached_result:
                        await update.message.reply_text(cached_result)
                        return
                
                # 2. Выполнение оригинального обработчика
                start_time = datetime.now()
                result = await original_handler(update, context)
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # 3. Кэширование результата (если команда поддерживает)
                if command and self._is_cacheable_command(command) and result:
                    cache_key = f"command_result:{command}:{user_id}"
                    await cache_set('command', cache_key, result, ttl=300)  # 5 минут
                
                # 4. Сбор метрик
                self.metrics_collector.add_command_metric(
                    command=command,
                    execution_time=execution_time,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # 5. Обработка ошибок
                await self.error_handler.handle_error(
                    error_type="command_error",
                    error_message=str(e),
                    context={
                        'user_id': user_id,
                        'command': command,
                        'chat_id': update.effective_chat.id
                    }
                )
                await handle_bot_error(update, context)
        
        return optimized_handler
    
    def _extract_command(self, update: Update) -> Optional[str]:
        """Извлекает команду из обновления."""
        if update.message and update.message.text:
            text = update.message.text.strip()
            if text.startswith('/'):
                return text.split()[0].lstrip('/')
        return None
    
    def _is_cacheable_command(self, command: str) -> bool:
        """Определяет, можно ли кэшировать команду."""
        cacheable_commands = ['stats', 'top', 'help', 'info', 'profile']
        return command in cacheable_commands

# Пример существующих обработчиков (которые уже работают в боте)
class ExistingHandlers:
    """Пример существующих обработчиков команд."""
    
    @staticmethod
    async def handle_davka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Существующий обработчик команды давки."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Имитация давки (реализация из db_manager)
        from db_manager import davka_zmiy
        success, patsan, result_data = await davka_zmiy(user_id, chat_id)
        
        if success:
            response = f"🐍 Давка прошла успешно! Змий: {result_data['zmiy_grams']}г"
            await update.message.reply_text(response)
            return response
        else:
            await update.message.reply_text(f"❌ Ошибка: {result_data['error']}")
            return None
    
    @staticmethod
    async def handle_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Существующий обработчик команды статистики."""
        user_id = update.effective_user.id
        
        # Имитация получения статистики
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
                """
                await update.message.reply_text(stats)
                return stats
            else:
                await update.message.reply_text("❌ Пользователь не найден")
                return None
                
        finally:
            await release_connection(conn)
    
    @staticmethod
    async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Существующий обработчик команды помощи."""
        help_text = """
🤖 Доступные команды:
/davka - Давка змия
/stats - Статистика пользователя
/help - Эта справка
/backup - Создать резервную копию
/performance - Проверить производительность
        """
        await update.message.reply_text(help_text)
        return help_text

async def create_optimized_bot():
    """Создает оптимизированного бота на основе существующего."""
    
    # 1. Создаем интеграцию
    integration = ExistingBotIntegration()
    await integration.initialize_optimizations()
    
    # 2. Создаем middleware
    middleware = integration.create_optimization_middleware()
    
    # 3. Создаем приложение
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # 4. Добавляем middleware
    application.add_handler(MessageHandler(filters.ALL, middleware.process_update), group=-1)
    
    # 5. Добавляем оптимизированные обработчики
    handlers = ExistingHandlers()
    
    # Оптимизируем существующие обработчики
    optimized_davka = integration.optimize_existing_handler(handlers.handle_davka_command)
    optimized_stats = integration.optimize_existing_handler(handlers.handle_stats_command)
    optimized_help = integration.optimize_existing_handler(handlers.handle_help_command)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("davka", optimized_davka))
    application.add_handler(CommandHandler("stats", optimized_stats))
    application.add_handler(CommandHandler("help", optimized_help))
    
    # Добавляем новые оптимизированные команды
    application.add_handler(CommandHandler("backup", integration.handle_backup_command))
    application.add_handler(CommandHandler("performance", integration.handle_performance_command))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(handle_bot_error)
    
    # Сохраняем ссылки для последующего использования
    application.integration = integration
    application.middleware = middleware
    
    return application

class AdditionalOptimizedHandlers:
    """Дополнительные оптимизированные обработчики."""
    
    def __init__(self, integration: ExistingBotIntegration):
        self.integration = integration
    
    async def handle_backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды резервного копирования."""
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
    
    async def handle_performance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды проверки производительности."""
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

async def run_optimized_existing_bot():
    """Запускает оптимизированного существующего бота."""
    try:
        # Создаем и запускаем приложение
        application = await create_optimized_bot()
        
        # Добавляем дополнительные обработчики
        additional_handlers = AdditionalOptimizedHandlers(application.integration)
        application.add_handler(CommandHandler("backup", additional_handlers.handle_backup_command))
        application.add_handler(CommandHandler("performance", additional_handlers.handle_performance_command))
        
        logger.info("🚀 Запуск оптимизированного существующего бота...")
        await application.run_polling()
        
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота по запросу пользователя...")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        # Останавливаем все системы оптимизации
        if hasattr(application, 'integration'):
            await application.integration.optimization_manager.shutdown()

# Пример постепенной интеграции

async def gradual_integration_example():
    """Пример постепенной интеграции оптимизаций."""
    
    print("🎯 Постепенная интеграция оптимизаций")
    
    # Шаг 1: Добавляем только кэширование
    print("1. Добавляем кэширование...")
    await initialize_optimization(level="low")
    
    # Шаг 2: Добавляем rate limiting
    print("2. Добавляем rate limiting...")
    from rate_limiter import get_rate_limiter
    rate_limiter = get_rate_limiter()
    rate_limiter.add_limit("command:davka", RateLimitConfig(limit=5, window_seconds=300))
    
    # Шаг 3: Добавляем мониторинг
    print("3. Добавляем мониторинг...")
    from metrics_collector import start_metrics_collection
    start_metrics_collection()
    
    # Шаг 4: Добавляем обработку ошибок
    print("4. Добавляем обработку ошибок...")
    from error_handler import get_error_handler
    error_handler = get_error_handler()
    
    # Шаг 5: Добавляем бэкапы
    print("5. Добавляем бэкапы...")
    from backup_manager import get_backup_manager
    backup_manager = get_backup_manager()
    await backup_manager.start()
    
    # Шаг 6: Полная оптимизация
    print("6. Полная оптимизация...")
    await initialize_optimization(level="high")
    
    print("✅ Постепенная интеграция завершена")

# Пример использования в реальном проекте

def real_world_integration_example():
    """Пример интеграции в реальный проект."""
    
    # 1. В existing_bot.py добавляем:
    """
    # В начале файла
    from optimization_manager import initialize_optimization
    from cache_manager import initialize_cache
    from rate_limiter import get_rate_limiter
    
    async def setup_optimizations():
        # Инициализация оптимизаций
        await initialize_optimization(level="medium")
        
        # Настройка rate limiting
        rate_limiter = get_rate_limiter()
        rate_limiter.add_limit("command:davka", RateLimitConfig(limit=5, window_seconds=300))
    
    # В main() функции:
    async def main():
        await setup_optimizations()
        # ... остальной код бота
    """
    
    # 2. В handlers/commands.py добавляем:
    """
    # Для каждой команды добавляем декораторы
    from cache_manager import cache_get, cache_set
    from rate_limiter import check_rate_limit
    from error_handler import handle_errors
    from metrics_collector import measure_performance
    
    @handle_errors("davka_command")
    @measure_performance("davka_command")
    async def handle_davka(update, context):
        user_id = update.effective_user.id
        
        # Проверка кэша
        cache_key = f"user_stats:{user_id}"
        cached_stats = await cache_get('user', cache_key)
        if cached_stats:
            await update.message.reply_text(cached_stats)
            return
        
        # Проверка лимитов
        rate_result = await check_rate_limit(user_id, update.effective_chat.id, "davka")
        if not rate_result.allowed:
            await update.message.reply_text(f"⏰ Подождите {rate_result.retry_after} секунд")
            return
        
        # Выполнение команды
        result = await process_davka(user_id)
        
        # Кэширование результата
        await cache_set('user', cache_key, result, ttl=300)
        
        await update.message.reply_text(result)
    """
    
    # 3. В main.py добавляем мониторинг:
    """
    # Добавляем в main() функцию
    from optimization_manager import get_optimization_status
    from backup_manager import create_backup
    
    async def background_tasks():
        while True:
            try:
                # Мониторинг производительности
                status = get_optimization_status()
                metrics = status['metrics']
                
                if metrics['response_time']['avg'] > 1000:
                    logger.warning(f"⚠️ Высокое время ответа: {metrics['response_time']['avg']}ms")
                
                # Автоматическое создание бэкапа
                if datetime.now().hour == 2:
                    await create_backup(description="Ночной бэкап")
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в фоновых задачах: {e}")
                await asyncio.sleep(60)
    
    # Запускаем фоновые задачи
    asyncio.create_task(background_tasks())
    """

if __name__ == "__main__":
    # Запуск примеров
    print("🚀 Запуск примеров интеграции оптимизаций")
    
    # Постепенная интеграция
    asyncio.run(gradual_integration_example())
    
    # Запуск оптимизированного бота
    # asyncio.run(run_optimized_existing_bot())