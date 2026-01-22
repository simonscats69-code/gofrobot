import asyncio
import logging
import os
import time
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from db_manager import init_bot, shutdown
from dotenv import load_dotenv
from handlers import router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        print("🚀 Запуск бота на bothost.ru")
        print(f"📁 Рабочая директория: {os.getcwd()}")
        print(f"📂 Содержимое: {os.listdir('.')}")
        
        await init_bot()
        
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            return
        
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        dp.include_router(router)
        
        logger.info("Бот запускается...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        
    finally:
        await shutdown()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
