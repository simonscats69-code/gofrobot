import asyncio
import logging
from typing import Callable, Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class AsyncWorker:
    def __init__(self, max_workers: int = 10):
        self.queue = asyncio.Queue()
        self.results: Dict[str, Any] = {}
        self.max_workers = max_workers
        self.workers = []
        
    async def start(self):
        """Запускаем воркеры"""
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        logger.info(f"Запущено {self.max_workers} воркеров")
    
    async def stop(self):
        """Останавливаем воркеры"""
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def _worker(self, name: str):
        """Рабочий процесс"""
        while True:
            try:
                task_id, func, args, kwargs = await self.queue.get()
                try:
                    result = await func(*args, **kwargs)
                    self.results[task_id] = ("success", result)
                except Exception as e:
                    self.results[task_id] = ("error", str(e))
                    logger.error(f"Ошибка в воркере {name}: {e}")
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Критическая ошибка воркера {name}: {e}")
    
    async def submit(self, func: Callable, *args, **kwargs) -> str:
        """Добавляем задачу в очередь и возвращаем ID"""
        task_id = f"task_{datetime.now().timestamp()}_{id(func)}"
        await self.queue.put((task_id, func, args, kwargs))
        return task_id
    
    async def get_result(self, task_id: str, timeout: float = 5.0) -> Any:
        """Получаем результат с таймаутом"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if task_id in self.results:
                status, result = self.results.pop(task_id)
                if status == "success":
                    return result
                else:
                    raise Exception(f"Ошибка выполнения: {result}")
            
            # Проверяем таймаут
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise asyncio.TimeoutError(f"Таймаут ожидания результата {task_id}")
            
            await asyncio.sleep(0.1)

# Глобальный воркер
worker = AsyncWorker()

# Функции-обертки для долгих операций
async def async_davka_zmiy(uid: int):
    """Асинхронная версия davka_zmiy через воркер"""
    from database.db_manager import davka_zmiy as original_davka
    task_id = await worker.submit(original_davka, uid)
    
    # Немедленно возвращаем промежуточный результат
    interim_result = {"status": "processing", "task_id": task_id}
    
    # В фоне ждем реальный результат
    asyncio.create_task(_wait_and_cache_result(uid, task_id, "davka"))
    
    return interim_result

async def async_sdat_zmiy(uid: int):
    """Асинхронная версия sdat_zmiy через воркер"""
    from database.db_manager import sdat_zmiy as original_sdat
    task_id = await worker.submit(original_sdat, uid)
    
    interim_result = {"status": "processing", "task_id": task_id}
    
    asyncio.create_task(_wait_and_cache_result(uid, task_id, "sdat"))
    
    return interim_result

async def _wait_and_cache_result(uid: int, task_id: str, action: str):
    """Ждем результат и кешируем его"""
    try:
        result = await worker.get_result(task_id, timeout=30.0)
        # Кешируем результат для быстрого доступа
        from cache_manager import user_cache
        if action == "davka" and result and len(result) >= 2:
            user_cache.update(uid, result[1])
    except Exception as e:
        logger.error(f"Ошибка при ожидании результата {task_id}: {e}")
