import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.db_manager import init_db
import handlers

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token="YOUR_BOT_TOKEN_HERE")
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(handlers.router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
