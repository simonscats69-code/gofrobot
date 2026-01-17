import asyncio
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импорт роутеров
from handlers.commands import router as commands_router
from handlers.callbacks import router as callbacks_router
from handlers.shop import router as shop_router

# Импорт для инициализации БД
from database.db_manager import init_db

# ========== ПРОВЕРКА ТОКЕНА ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ ОШИБКА: Переменная BOT_TOKEN не найдена!")
    print("Добавьте её в BotHost: Environment → User Variables")
    sys.exit(1)

if ":" not in BOT_TOKEN:
    print(f"❌ ОШИБКА: Неверный формат токена. Получено: '{BOT_TOKEN}'")
    print("Токен должен быть в формате: 1234567890:ABCdefGHIjklMnopQRstUvWxyz")
    sys.exit(1)

token_parts = BOT_TOKEN.split(":")
if len(token_parts) != 2 or not token_parts[0].isdigit() or len(token_parts[1]) < 30:
    print(f"❌ ОШИБКА: Токен повреждён. ID: {token_parts[0]}, ключ: {token_parts[1][:10]}...")
    sys.exit(1)

print(f"✅ Токен получен. Длина: {len(BOT_TOKEN)}, ID бота: {token_parts[0]}")
# ========== КОНЕЦ ПРОВЕРКИ ==========

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
