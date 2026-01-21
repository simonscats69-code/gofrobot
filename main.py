import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from db_manager import init_bot, shutdown  # Изменено: database. удалено
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        await init_bot()
        
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            return
        
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        from handlers.commands import router as commands_router
        from handlers.callbacks import router as callbacks_router
        from handlers.daily import router as daily_router
        from handlers.nickname_and_rademka import router as nickname_router
        from handlers.shop import router as shop_router
        from handlers.top import router as top_router
        from handlers.atm_handlers import router as atm_router
        
        dp.include_router(commands_router)
        dp.include_router(callbacks_router)
        dp.include_router(daily_router)
        dp.include_router(nickname_router)
        dp.include_router(shop_router)
        dp.include_router(top_router)
        dp.include_router(atm_router)
        
        logger.info("Бот запускается...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        
    finally:
        await shutdown()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
