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
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        logger.info(f"Запущено {self.max_workers} воркеров")
    
    async def stop(self):
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def _worker(self, name: str):
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
        task_id = f"task_{datetime.now().timestamp()}_{id(func)}"
        await self.queue.put((task_id, func, args, kwargs))
        return task_id
    
    async def get_result(self, task_id: str, timeout: float = 5.0) -> Any:
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if task_id in self.results:
                status, result = self.results.pop(task_id)
                if status == "success":
                    return result
                else:
                    raise Exception(f"Ошибка выполнения: {result}")
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise asyncio.TimeoutError(f"Таймаут ожидания результата {task_id}")
            
            await asyncio.sleep(0.1)

worker = AsyncWorker()
