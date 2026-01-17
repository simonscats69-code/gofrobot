import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импорт роутеров
from handlers.commands import router as commands_router
from handlers.callbacks import router as callbacks_router
from handlers.shop import router as shop_router

# Импорт для инициализации БД
from database.db_manager import init_db

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    # Инициализируем базу данных
    init_db()
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Подключаем роутеры
    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(shop_router)
    
    print("🤖 Бот 'Пацаны с гофроцентрала' запущен!")
    print("⚡ Работаем на заварваривание двенашек!")
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
