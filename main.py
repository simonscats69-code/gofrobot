import asyncio
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Импорт всех роутеров
from handlers.commands import router as commands_router
from handlers.callbacks import r as callbacks_router
from handlers.shop import router as shop_router
from handlers.daily import router as daily_router
from handlers.nickname_and_rademka import router as nickname_rademka_router
from handlers.specializations import router as specializations_router
from handlers.craft import router as craft_router
from handlers.atm_handlers import router as atm_handlers_router

from database.db_manager import init_bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден")
    sys.exit(1)

async def main():
    await init_bot()
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Все роутеры (без achievements_progress.py)
    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(shop_router)
    dp.include_router(daily_router)
    dp.include_router(nickname_rademka_router)
    dp.include_router(specializations_router)
    dp.include_router(craft_router)
    dp.include_router(atm_handlers_router)
    
    print("🤖 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
