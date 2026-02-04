"""
Примеры использования всех систем оптимизации.

Этот файл содержит практические примеры того, как использовать
каждую из 8 оптимизационных систем в реальных сценариях.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Импортируем все системы оптимизации
from optimization_manager import (
    get_optimization_manager, 
    initialize_optimization, 
    get_optimization_status,
    get_performance_report,
    OptimizationLevel,
    OptimizationConfig
)
from cache_manager import (
    cache_get, cache_set, cache_exists, cache_delete,
    get_cache_stats, initialize_cache, close_cache
)
from rate_limiter import (
    check_rate_limit, is_user_blocked, get_rate_limiter,
    RateLimitConfig, get_user_stats
)
from error_handler import (
    get_error_handler, handle_bot_error, handle_errors,
    get_error_stats, get_error_history
)
from metrics_collector import (
    get_metrics_collector, measure_performance,
    get_performance_stats, get_command_stats,
    start_metrics_collection, stop_metrics_collection
)
from backup_manager import (
    create_backup, restore_backup, list_backups,
    verify_backup, get_backup_stats, cleanup_old_backups
)
from db_manager import (
    get_connection, release_connection, davka_zmiy,
    get_user_stats as db_get_user_stats
)

logger = logging.getLogger(__name__)

class OptimizationExamples:
    """Класс с примерами использования всех систем оптимизации."""
    
    def __init__(self):
        self.optimization_manager = get_optimization_manager()
    
    async def basic_optimization_example(self):
        """Базовый пример использования оптимизации."""
        print("🚀 Базовый пример оптимизации")
        
        # 1. Инициализация оптимизации
        await initialize_optimization(level=OptimizationLevel.MEDIUM)
        
        # 2. Проверка статуса
        status = get_optimization_status()
        print(f"✅ Уровень оптимизации: {status['optimization_level']}")
        print(f"✅ Активные системы: {len([s for s in status['systems'].values() if s['enabled']])}/5")
        
        # 3. Получение отчета
        report = get_performance_report(1)
        print(f"📊 Среднее время ответа: {report['performance_metrics']['response_time']['avg']:.2f}ms")
    
    async def cache_examples(self):
        """Примеры использования кэширования."""
        print("\n📦 Примеры кэширования")
        
        # 1. Инициализация кэша
        await initialize_cache()
        
        # 2. Простое кэширование данных
        cache_key = "user:123:profile"
        user_data = {"name": "John", "age": 30, "city": "Moscow"}
        
        await cache_set('user', cache_key, user_data, ttl=600)
        print(f"✅ Данные сохранены в кэш: {cache_key}")
        
        # 3. Получение данных из кэша
        cached_data = await cache_get('user', cache_key)
        print(f"✅ Данные из кэша: {cached_data}")
        
        # 4. Проверка существования
        exists = await cache_exists('user', cache_key)
        print(f"✅ Данные существуют в кэше: {exists}")
        
        # 5. Удаление из кэша
        await cache_delete('user', cache_key)
        print(f"✅ Данные удалены из кэша")
        
        # 6. Статистика кэша
        stats = get_cache_stats()
        print(f"📊 Статистика кэша: {stats}")
        
        # 7. Закрытие кэша
        await close_cache()
    
    async def rate_limiting_examples(self):
        """Примеры использования rate limiting."""
        print("\n⏰ Примеры rate limiting")
        
        # 1. Получение rate limiter
        rate_limiter = get_rate_limiter()
        
        # 2. Добавление лимитов
        rate_limiter.add_limit("command:davka", RateLimitConfig(limit=5, window_seconds=300))
        rate_limiter.add_limit("command:rademka", RateLimitConfig(limit=3, window_seconds=600))
        print("✅ Лимиты добавлены")
        
        # 3. Проверка лимитов
        user_id = 12345
        chat_id = 67890
        
        for i in range(6):
            result = await check_rate_limit(user_id, chat_id, "davka")
            print(f"Попытка {i+1}: {'✅ Разрешено' if result.allowed else f'❌ Заблокировано (осталось {result.retry_after} сек)'}")
            
            if not result.allowed:
                break
        
        # 4. Проверка блокировки пользователя
        blocked = is_user_blocked(user_id)
        print(f"🚫 Пользователь заблокирован: {blocked}")
        
        # 5. Статистика по пользователю
        user_stats = get_user_stats(user_id)
        print(f"📊 Статистика пользователя: {user_stats}")
    
    async def error_handling_examples(self):
        """Примеры использования обработки ошибок."""
        print("\n🛡️ Примеры обработки ошибок")
        
        # 1. Получение error handler
        error_handler = get_error_handler()
        
        # 2. Регистрация обработчика ошибок
        async def custom_error_handler(error_type: str, error_message: str, context: Dict[str, Any]):
            print(f"🚨 Кастомный обработчик ошибок: {error_type} - {error_message}")
            return True  # Ошибка обработана
        
        error_handler.register_handler("database_error", custom_error_handler)
        print("✅ Кастомный обработчик ошибок зарегистрирован")
        
        # 3. Пример использования декоратора
        @handle_errors("test_command")
        async def test_function():
            # Имитация ошибки
            raise ValueError("Тестовая ошибка")
        
        try:
            await test_function()
        except Exception as e:
            print(f"❌ Ошибка перехвачена: {e}")
        
        # 4. Статистика ошибок
        error_stats = get_error_stats()
        print(f"📊 Статистика ошибок: {error_stats}")
        
        # 5. История ошибок
        error_history = get_error_history(limit=5)
        print(f"📋 История ошибок: {error_history}")
    
    async def metrics_examples(self):
        """Примеры использования метрик производительности."""
        print("\n📈 Примеры метрик производительности")
        
        # 1. Запуск сбора метрик
        start_metrics_collection()
        
        # 2. Использование декоратора для измерения производительности
        @measure_performance("test_command")
        async def test_command():
            # Имитация работы
            await asyncio.sleep(0.1)
            return "Результат команды"
        
        # 3. Выполнение команды несколько раз
        for i in range(3):
            result = await test_command()
            print(f"✅ Выполнение {i+1}: {result}")
        
        # 4. Получение статистики
        performance_stats = get_performance_stats()
        print(f"📊 Статистика производительности: {performance_stats}")
        
        # 5. Статистика по командам
        command_stats = get_command_stats()
        print(f"📋 Статистика по командам: {command_stats}")
        
        # 6. Остановка сбора метрик
        stop_metrics_collection()
    
    async def database_examples(self):
        """Примеры использования оптимизированной работы с базой данных."""
        print("\n🗄️ Примеры работы с базой данных")
        
        # 1. Получение соединения из пула
        conn = await get_connection()
        
        try:
            # 2. Выполнение оптимизированного запроса
            cursor = await conn.execute("""
                SELECT u.*, 
                       COALESCE(d.total_davki, 0) as total_davki,
                       COALESCE(u.total_uletels, 0) as total_uletels
                FROM users u
                LEFT JOIN (SELECT user_id, COUNT(*) as total_davki FROM davki GROUP BY user_id) d ON u.user_id = d.user_id
                WHERE u.user_id = ?
            """, (12345,))
            
            user_data = await cursor.fetchone()
            print(f"✅ Данные пользователя: {user_data}")
            
            # 3. Использование оптимизированной функции давки
            success, patsan, result_data = await davka_zmiy(12345, 67890)
            if success:
                print(f"🐍 Давка прошла успешно: {result_data}")
            else:
                print(f"❌ Давка не удалась: {result_data}")
            
            # 4. Получение статистики пользователя
            stats = await db_get_user_stats(12345)
            print(f"📊 Статистика пользователя: {stats}")
            
        finally:
            # 5. Возврат соединения в пул
            await release_connection(conn)
    
    async def backup_examples(self):
        """Примеры использования системы резервного копирования."""
        print("\n💾 Примеры резервного копирования")
        
        # 1. Создание резервной копии
        success, backup_info = await create_backup(
            backup_type="daily",
            description="Тестовая резервная копия"
        )
        
        if success and backup_info:
            print(f"✅ Резервная копия создана: {backup_info.filename}")
            print(f"📊 Размер: {backup_info.size} байт")
            print(f"⏰ Время создания: {datetime.fromtimestamp(backup_info.created_at)}")
        else:
            print("❌ Не удалось создать резервную копию")
        
        # 2. Список резервных копий
        backups = await list_backups()
        print(f"📋 Доступные резервные копии: {len(backups)}")
        
        # 3. Проверка целостности
        if backups:
            backup_filename = backups[0].filename
            is_valid, info = await verify_backup(backup_filename)
            print(f"🔍 Проверка целостности {backup_filename}: {'✅ Валидна' if is_valid else '❌ Невалидна'}")
        
        # 4. Статистика бэкапов
        backup_stats = get_backup_stats()
        print(f"📊 Статистика бэкапов: {backup_stats}")
        
        # 5. Очистка старых бэкапов
        await cleanup_old_backups(days=7)
        print("🧹 Старые резервные копии очищены")
    
    async def advanced_optimization_example(self):
        """Продвинутый пример комплексной оптимизации."""
        print("\n🚀 Продвинутый пример комплексной оптимизации")
        
        # 1. Настройка конфигурации
        config = OptimizationConfig(
            level=OptimizationLevel.HIGH,
            cache_ttl=1200,  # 20 минут
            rate_limit_max_requests=50,
            monitoring_interval=15,
            backup_interval=1800  # 30 минут
        )
        
        # 2. Инициализация с кастомной конфигурацией
        manager = get_optimization_manager()
        manager.config = config
        await manager.initialize()
        
        # 3. Создание middleware для обработки запросов
        class OptimizedMiddleware:
            async def process_update(self, update, context):
                user_id = update.effective_user.id
                command = self._extract_command(update)
                
                # Rate limiting
                if command:
                    rate_result = await check_rate_limit(user_id, update.effective_chat.id, command)
                    if not rate_result.allowed:
                        await update.message.reply_text(f"⏰ Подождите {rate_result.retry_after} секунд")
                        return
                
                # Cache check
                if command and self._is_cacheable(command):
                    cache_key = f"command:{command}:{user_id}"
                    cached_result = await cache_get('command', cache_key)
                    if cached_result:
                        await update.message.reply_text(cached_result)
                        return
                
                # Continue processing
                context.user_data['start_time'] = datetime.now()
            
            def _extract_command(self, update):
                if update.message and update.message.text:
                    text = update.message.text.strip()
                    if text.startswith('/'):
                        return text.split()[0].lstrip('/')
                return None
            
            def _is_cacheable(self, command):
                return command in ['stats', 'help', 'info']
        
        # 4. Запуск фоновых задач
        async def background_tasks():
            while True:
                try:
                    # Мониторинг производительности
                    status = get_optimization_status()
                    metrics = status['metrics']
                    
                    if metrics['response_time']['avg'] > 1000:
                        logger.warning(f"⚠️ Высокое время ответа: {metrics['response_time']['avg']}ms")
                    
                    if metrics['cpu_usage']['current'] > 80:
                        logger.warning(f"⚠️ Высокая нагрузка CPU: {metrics['cpu_usage']['current']}%")
                    
                    # Автоматическое создание бэкапа
                    if datetime.now().hour == 2:  # В 2 часа ночи
                        await create_backup(description="Ночной бэкап")
                    
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в фоновых задачах: {e}")
                    await asyncio.sleep(60)
        
        # Запуск фоновых задач
        asyncio.create_task(background_tasks())
        
        print("✅ Комплексная оптимизация настроена")
    
    async def performance_testing_example(self):
        """Пример тестирования производительности."""
        print("\n🧪 Пример тестирования производительности")
        
        # 1. Запуск теста производительности
        async def performance_test():
            start_time = datetime.now()
            
            # Тест кэширования
            cache_times = []
            for i in range(100):
                cache_start = datetime.now()
                await cache_set('test', f'key_{i}', f'value_{i}', ttl=300)
                await cache_get('test', f'key_{i}')
                cache_end = datetime.now()
                cache_times.append((cache_end - cache_start).total_seconds() * 1000)
            
            avg_cache_time = sum(cache_times) / len(cache_times)
            print(f"📊 Среднее время операции кэша: {avg_cache_time:.2f}ms")
            
            # Тест базы данных
            db_times = []
            for i in range(50):
                db_start = datetime.now()
                conn = await get_connection()
                try:
                    cursor = await conn.execute("SELECT COUNT(*) FROM users")
                    await cursor.fetchone()
                finally:
                    await release_connection(conn)
                db_end = datetime.now()
                db_times.append((db_end - db_start).total_seconds() * 1000)
            
            avg_db_time = sum(db_times) / len(db_times)
            print(f"📊 Среднее время операции БД: {avg_db_time:.2f}ms")
            
            # Тест rate limiting
            rate_times = []
            for i in range(1000):
                rate_start = datetime.now()
                await check_rate_limit(i, i, "test")
                rate_end = datetime.now()
                rate_times.append((rate_end - rate_start).total_seconds() * 1000)
            
            avg_rate_time = sum(rate_times) / len(rate_times)
            print(f"📊 Среднее время проверки лимита: {avg_rate_time:.2f}ms")
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            print(f"⏱️ Общее время теста: {total_time:.2f} секунд")
            
            return {
                'cache_avg': avg_cache_time,
                'db_avg': avg_db_time,
                'rate_avg': avg_rate_time,
                'total': total_time
            }
        
        # 2. Запуск теста
        results = await performance_test()
        
        # 3. Анализ результатов
        if results['cache_avg'] < 10:
            print("✅ Кэширование работает отлично")
        elif results['cache_avg'] < 50:
            print("⚠️ Кэширование работает удовлетворительно")
        else:
            print("❌ Кэширование работает медленно")
        
        if results['db_avg'] < 100:
            print("✅ База данных работает отлично")
        elif results['db_avg'] < 500:
            print("⚠️ База данных работает удовлетворительно")
        else:
            print("❌ База данных работает медленно")
        
        if results['rate_avg'] < 5:
            print("✅ Rate limiting работает отлично")
        elif results['rate_avg'] < 20:
            print("⚠️ Rate limiting работает удовлетворительно")
        else:
            print("❌ Rate limiting работает медленно")
    
    async def run_all_examples(self):
        """Запуск всех примеров."""
        print("🎯 Запуск всех примеров оптимизации")
        
        try:
            # Базовые примеры
            await self.basic_optimization_example()
            await self.cache_examples()
            await self.rate_limiting_examples()
            await self.error_handling_examples()
            await self.metrics_examples()
            await self.database_examples()
            await self.backup_examples()
            
            # Продвинутые примеры
            await self.advanced_optimization_example()
            await self.performance_testing_example()
            
            print("\n🎉 Все примеры успешно выполнены!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в примерах: {e}")
            raise

async def main():
    """Главная функция для запуска примеров."""
    examples = OptimizationExamples()
    await examples.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())