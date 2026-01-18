import time
import logging
from typing import Dict, Any
from datetime import datetime

class CallbackMonitor:
    def __init__(self):
        self.callback_times: Dict[str, list] = {}
        self.slow_threshold = 2.0  # 2 секунды
        self.error_count = 0
    
    def start_callback(self, callback_data: str):
        return {
            "data": callback_data,
            "start_time": time.time(),
            "start_datetime": datetime.now().isoformat()
        }
    
    def end_callback(self, start_info: Dict[str, Any], success: bool = True, error: str = ""):
        duration = time.time() - start_info["start_time"]
        callback_data = start_info["data"]
        
        # Логируем медленные callback'и
        if duration > self.slow_threshold:
            logging.warning(
                f"Медленный callback: {callback_data} - {duration:.2f} сек"
            )
        
        # Собираем статистику
        if callback_data not in self.callback_times:
            self.callback_times[callback_data] = []
        
        self.callback_times[callback_data].append(duration)
        
        # Оставляем только последние 100 записей
        if len(self.callback_times[callback_data]) > 100:
            self.callback_times[callback_data] = self.callback_times[callback_data][-100:]
        
        if not success:
            self.error_count += 1
            logging.error(f"Ошибка callback {callback_data}: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        for callback_data, times in self.callback_times.items():
            if times:
                stats[callback_data] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "slow_count": len([t for t in times if t > self.slow_threshold])
                }
        return stats

# Глобальный монитор
monitor = CallbackMonitor()
