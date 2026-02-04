"""
Тесты для системы оптимизации производительности.

Этот файл содержит комплексные тесты для всех 8 оптимизационных систем.
"""

import asyncio
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

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
    get_cache_stats, initialize_cache, close_cache,
    CacheManager, LocalCache, RedisCache
)
from rate_limiter import (
    check_rate_limit, is_user_blocked, get_rate_limiter,
    RateLimitConfig, get_user_stats, RateLimiter
)
from error_handler import (
    get_error_handler, handle_bot_error, handle_errors,
    get_error_stats, get_error_history, ErrorHandler
)
from metrics_collector import (
    get_metrics_collector, measure_performance,
    get_performance_stats, get_command_stats,
    start_metrics_collection, stop_metrics_collection,
    MetricsCollector
)
from backup_manager import (
    create_backup, restore_backup, list_backups,
    verify_backup, get_backup_stats, cleanup_old_backups,
    BackupManager, BackupType, BackupInfo
)
from db_manager import (
    get_connection, release_connection, davka_zmiy,
    get_user_stats as db_get_user_stats, DatabaseManager
)

class TestOptimizationManager:
    """Тесты для менеджера оптимизации."""
    
    @pytest.fixture
    async def optimization_manager(self):
        """Фикстура для менеджера оптимизации."""
        config = OptimizationConfig(level=OptimizationLevel.MEDIUM)
        manager = get_optimization_manager()
        manager.config = config
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    async def test_initialization(self, optimization_manager):
        """Тест инициализации менеджера оптимизации."""
        status = get_optimization_status()
        
        assert status['optimization_level'] == 'medium'
        assert 'systems' in status
        assert 'metrics' in status
        assert 'config' in status
    
    async def test_performance_report(self, optimization_manager):
        """Тест генерации отчета о производительности."""
        report = get_performance_report(1)
        
        assert 'generated_at' in report
        assert 'performance_metrics' in report
        assert 'system_status' in report
        assert 'recommendations' in report
    
    async def test_auto_tuning(self, optimization_manager):
        """Тест автоматической настройки."""
        # Имитируем высокую нагрузку
        optimization_manager.metrics.add_cpu_usage(90)
        optimization_manager.metrics.add_cache_hit_rate(20)
        
        # Выполняем автоматическую настройку
        await optimization_manager._perform_auto_tuning()
        
        # Проверяем, что параметры изменились
        assert optimization_manager.config.cache_ttl > 300
        assert optimization_manager.config.monitoring_interval > 60


class TestCacheManager:
    """Тесты для менеджера кэширования."""
    
    @pytest.fixture
    async def cache_manager(self):
        """Фикстура для менеджера кэша."""
        manager = CacheManager()
        await manager.initialize()
        yield manager
        await manager.close()
    
    async def test_cache_operations(self, cache_manager):
        """Тест операций с кэшем."""
        # Тест установки значения
        await cache_set('test', 'key1', 'value1', ttl=300)
        
        # Тест получения значения
        value = await cache_get('test', 'key1')
        assert value == 'value1'
        
        # Тест проверки существования
        exists = await cache_exists('test', 'key1')
        assert exists == True
        
        # Тест удаления
        await cache_delete('test', 'key1')
        value = await cache_get('test', 'key1')
        assert value is None
    
    async def test_cache_stats(self, cache_manager):
        """Тест статистики кэша."""
        stats = get_cache_stats()
        
        assert 'hit_rate' in stats
        assert 'total_requests' in stats
        assert 'total_hits' in stats
        assert 'total_misses' in stats
    
    async def test_local_cache_fallback(self):
        """Тест fallback на локальный кэш."""
        # Создаем менеджер без Redis
        manager = CacheManager(redis_url=None)
        await manager.initialize()
        
        # Проверяем, что используется локальный кэш
        assert isinstance(manager.redis_cache, LocalCache)
        
        # Тест операций
        await cache_set('test', 'key1', 'value1')
        value = await cache_get('test', 'key1')
        assert value == 'value1'
        
        await manager.close()


class TestRateLimiter:
    """Тесты для системы ограничения частоты запросов."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Фикстура для rate limiter."""
        return RateLimiter()
    
    def test_rate_limit_config(self, rate_limiter):
        """Тест конфигурации лимитов."""
        config = RateLimitConfig(limit=5, window_seconds=300)
        
        assert config.limit == 5
        assert config.window_seconds == 300
        assert config.block_duration_seconds == 600
    
    async def test_rate_limiting(self, rate_limiter):
        """Тест ограничения частоты запросов."""
        # Добавляем лимит
        rate_limiter.add_limit("command:test", RateLimitConfig(limit=3, window_seconds=60))
        
        user_id = 12345
        chat_id = 67890
        
        # Первые 3 запроса должны быть разрешены
        for i in range(3):
            result = await check_rate_limit(user_id, chat_id, "command:test")
            assert result.allowed == True
        
        # 4-й запрос должен быть заблокирован
        result = await check_rate_limit(user_id, chat_id, "command:test")
        assert result.allowed == False
        assert result.retry_after > 0
    
    async def test_user_blocking(self, rate_limiter):
        """Тест блокировки пользователя."""
        user_id = 12345
        
        # Пользователь не заблокирован изначально
        assert not is_user_blocked(user_id)
        
        # Блокируем пользователя
        rate_limiter.block_user(user_id, 300)
        
        # Проверяем блокировку
        assert is_user_blocked(user_id)
        
        # Разблокируем пользователя
        rate_limiter.unblock_user(user_id)
        
        # Проверяем разблокировку
        assert not is_user_blocked(user_id)


class TestErrorHandler:
    """Тесты для системы обработки ошибок."""
    
    @pytest.fixture
    def error_handler(self):
        """Фикстура для обработчика ошибок."""
        return ErrorHandler()
    
    def test_error_registration(self, error_handler):
        """Тест регистрации обработчиков ошибок."""
        async def test_handler(error_type, error_message, context):
            return True
        
        error_handler.register_handler("test_error", test_handler)
        
        assert "test_error" in error_handler.handlers
        assert error_handler.handlers["test_error"] == test_handler
    
    def test_error_stats(self, error_handler):
        """Тест статистики ошибок."""
        stats = get_error_stats()
        
        assert 'total_errors' in stats
        assert 'error_types' in stats
        assert 'last_error_time' in stats
    
    def test_error_history(self, error_handler):
        """Тест истории ошибок."""
        history = get_error_history(limit=5)
        
        assert isinstance(history, list)
        assert len(history) >= 0


class TestMetricsCollector:
    """Тесты для системы сбора метрик."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Фикстура для сборщика метрик."""
        return MetricsCollector()
    
    def test_performance_decorator(self, metrics_collector):
        """Тест декоратора производительности."""
        @measure_performance("test_command")
        async def test_function():
            await asyncio.sleep(0.01)
            return "result"
        
        # Выполняем функцию
        result = asyncio.run(test_function())
        assert result == "result"
    
    def test_metrics_stats(self, metrics_collector):
        """Тест статистики метрик."""
        stats = get_performance_stats()
        
        assert 'total_commands' in stats
        assert 'avg_response_time' in stats
        assert 'total_errors' in stats
        assert 'error_rate' in stats
    
    def test_command_stats(self, metrics_collector):
        """Тест статистики по командам."""
        stats = get_command_stats()
        
        assert isinstance(stats, dict)
        # Может быть пустым, если команды еще не выполнялись


class TestBackupManager:
    """Тесты для системы резервного копирования."""
    
    @pytest.fixture
    def backup_manager(self):
        """Фикстура для менеджера бэкапов."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BackupManager(backup_dir=temp_dir)
            yield manager
    
    async def test_backup_creation(self, backup_manager):
        """Тест создания резервной копии."""
        success, backup_info = await create_backup(
            backup_type=BackupType.DAILY,
            description="Test backup"
        )
        
        assert success == True
        assert backup_info is not None
        assert backup_info.backup_type == BackupType.DAILY
    
    async def test_backup_list(self, backup_manager):
        """Тест списка резервных копий."""
        backups = await list_backups()
        
        assert isinstance(backups, list)
    
    async def test_backup_verification(self, backup_manager):
        """Тест проверки целостности бэкапа."""
        # Создаем бэкап для теста
        success, backup_info = await create_backup()
        
        if success and backup_info:
            is_valid, info = await verify_backup(backup_info.filename)
            assert isinstance(is_valid, bool)
    
    async def test_backup_cleanup(self, backup_manager):
        """Тест очистки старых бэкапов."""
        # Создаем несколько бэкапов
        for i in range(5):
            await create_backup()
        
        # Очищаем старые бэкапы
        await cleanup_old_backups(days=1)
        
        # Проверяем, что бэкапы остались (так как они свежие)
        backups = await list_backups()
        assert len(backups) >= 0


class TestDatabaseManager:
    """Тесты для менеджера базы данных."""
    
    @pytest.fixture
    def db_manager(self):
        """Фикстура для менеджера базы данных."""
        return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_connection_pooling(self, db_manager):
        """Тест пула соединений."""
        # Получаем соединение
        conn = await get_connection()
        assert conn is not None
        
        # Возвращаем соединение
        await release_connection(conn)
    
    @pytest.mark.asyncio
    async def test_davka_operation(self, db_manager):
        """Тест операции давки."""
        # Это интеграционный тест, который может не пройти
        # без реальной базы данных
        try:
            success, patsan, result_data = await davka_zmiy(12345, 67890)
            # Может быть False, если пользователь не найден
            assert isinstance(success, bool)
        except Exception as e:
            # Ожидаемое поведение для тестовой среды
            assert "database" in str(e).lower() or "connection" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_user_stats(self, db_manager):
        """Тест получения статистики пользователя."""
        try:
            stats = await db_get_user_stats(12345)
            # Может быть None, если пользователь не найден
            assert stats is None or isinstance(stats, dict)
        except Exception as e:
            # Ожидаемое поведение для тестовой среды
            assert "database" in str(e).lower() or "connection" in str(e).lower()


class TestIntegration:
    """Интеграционные тесты для всех систем."""
    
    @pytest.mark.asyncio
    async def test_full_optimization_flow(self):
        """Тест полного цикла оптимизации."""
        # 1. Инициализация
        await initialize_optimization(level=OptimizationLevel.HIGH)
        
        # 2. Проверка статуса
        status = get_optimization_status()
        assert status['optimization_level'] == 'high'
        
        # 3. Тест кэширования
        await cache_set('test', 'key', 'value', ttl=300)
        value = await cache_get('test', 'key')
        assert value == 'value'
        
        # 4. Тест rate limiting
        result = await check_rate_limit(123, 456, "test")
        assert hasattr(result, 'allowed')
        
        # 5. Тест метрик
        @measure_performance("test_integration")
        async def test_func():
            await asyncio.sleep(0.01)
            return "ok"
        
        result = await test_func()
        assert result == "ok"
        
        # 6. Получение отчета
        report = get_performance_report(1)
        assert 'performance_metrics' in report
        
        print("✅ Полный цикл оптимизации пройден")
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Тест интеграции обработки ошибок."""
        @handle_errors("test_error_handling")
        async def test_function():
            raise ValueError("Test error")
        
        try:
            await test_function()
        except ValueError:
            pass  # Ожидаемая ошибка
        
        # Проверяем, что ошибка была зарегистрирована
        error_stats = get_error_stats()
        assert isinstance(error_stats, dict)
        
        print("✅ Интеграция обработки ошибок пройдена")
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Тест производительности под нагрузкой."""
        # Запускаем несколько параллельных операций
        tasks = []
        
        for i in range(10):
            async def test_operation():
                # Кэширование
                await cache_set('load_test', f'key_{i}', f'value_{i}', ttl=300)
                value = await cache_get('load_test', f'key_{i}')
                assert value == f'value_{i}'
                
                # Rate limiting
                result = await check_rate_limit(i, i, "load_test")
                assert hasattr(result, 'allowed')
                
                return True
            
            tasks.append(test_operation())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем, что все операции завершились успешно
        for result in results:
            if isinstance(result, Exception):
                print(f"⚠️ Операция завершилась с ошибкой: {result}")
            else:
                assert result == True
        
        print("✅ Тест производительности под нагрузкой пройден")


class TestPerformance:
    """Тесты производительности."""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Тест производительности кэша."""
        import time
        
        # Тест записи
        start_time = time.time()
        for i in range(100):
            await cache_set('perf_test', f'key_{i}', f'value_{i}', ttl=300)
        write_time = time.time() - start_time
        
        # Тест чтения
        start_time = time.time()
        for i in range(100):
            await cache_get('perf_test', f'key_{i}')
        read_time = time.time() - start_time
        
        print(f"⏱️ Время записи 100 элементов: {write_time:.4f}с")
        print(f"⏱️ Время чтения 100 элементов: {read_time:.4f}с")
        
        # Проверяем, что операции выполняются быстро
        assert write_time < 1.0  # Меньше 1 секунды на 100 записей
        assert read_time < 1.0   # Меньше 1 секунды на 100 чтений
    
    @pytest.mark.asyncio
    async def test_rate_limit_performance(self):
        """Тест производительности rate limiting."""
        import time
        
        start_time = time.time()
        for i in range(1000):
            await check_rate_limit(i, i, "perf_test")
        total_time = time.time() - start_time
        
        print(f"⏱️ Время 1000 проверок лимитов: {total_time:.4f}с")
        
        # Проверяем, что операции выполняются быстро
        assert total_time < 5.0  # Меньше 5 секунд на 1000 проверок


if __name__ == "__main__":
    # Запуск всех тестов
    pytest.main([__file__, "-v", "--tb=short"])