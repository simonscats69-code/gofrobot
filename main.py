import asyncio
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.commands import router as commands_router
from handlers.callbacks import router as callbacks_router
from handlers.shop import router as shop_router
from handlers.top import router as top_router
from handlers.daily import router as daily_router
from handlers.nickname_and_rademka import router as nickname_rademka_router
from handlers.specializations import router as specializations_router
from handlers.craft import router as craft_router
from handlers.achievements_progress import router as achievements_progress_router
from handlers.atm_handlers import router as atm_handlers_router  # НОВЫЙ ИМПОРТ

from database.db_manager import init_bot  # ИЗМЕНЕНО: init_db -> init_bot

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

async def main():
    await init_bot()  # ИЗМЕНЕНО: init_db -> init_bot
    print("✅ База данных инициализирована")
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем все роутеры
    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(shop_router)
    dp.include_router(top_router)
    dp.include_router(daily_router)
    dp.include_router(nickname_rademka_router)
    dp.include_router(specializations_router)
    dp.include_router(craft_router)
    dp.include_router(achievements_progress_router)
    dp.include_router(atm_handlers_router)  # НОВЫЙ РОУТЕР ДЛЯ КНОПОК АТМОСФЕР
    
    print("🤖 Бот 'Пацаны с гофроцентрала' запущен!")
    print("=" * 50)
    print("⚡ РАБОТАЕМ НА ЗАВАРВАРИВАНИЕ ДВЕНАШЕК!")
    print("=" * 50)
    print()
    print("🎉 ОБНОВЛЕНИЕ 2.0 АКТИВИРОВАНО!")
    print("=" * 50)
    print("🌳 СИСТЕМА СПЕЦИАЛИЗАЦИЙ")
    print("• 💪 Давила - мастер давления")
    print("• 🔍 Охотник - ищет двенашки")
    print("• 🛡️ Непробиваемый - железные кишки")
    print()
    print("🔨 СИСТЕМА КРАФТА")
    print("• Создавай мощные предметы")
    print("• 4 уникальных рецепта")
    print("• Шанс успеха от 70% до 100%")
    print()
    print("📈 СИСТЕМА УРОВНЕЙ")
    print("• Получай опыт за все действия")
    print("• Повышай уровень за награды")
    print("• Каждый 5 уровень +1 к атмосферам")
    print()
    print("🏆 УРОВНЕВЫЕ ДОСТИЖЕНИЯ")
    print("• Долгосрочные цели")
    print("• Множество уровней")
    print("• Большие награды")
    print()
    print("🕵️ РАЗВЕДКА РАДЁМКИ")
    print("• Узнавай точные шансы")
    print("• 5 бесплатных разведок")
    print("• Стратегическое преимущество")
    print()
    print("⭐ СИСТЕМА ЗВАНИЙ")
    print("• От Пацанчика до Царя гофры")
    print("• Уважение в сообществе")
    print("• Влияние на игровой процесс")
    print("=" * 50)
    print()
    print("👤 НОВОЕ: СИСТЕМА НИКНЕЙМА")
    print("• Первая смена ника бесплатно")
    print("• Репутация через авторитет")
    print("• Топ самых уважаемых пацанов")
    print("=" * 50)
    print()
    print("📊 База данных: асинхронный режим")
    print("🎮 Активных функций: 12+")
    print("⚙️ FSM: активирован для смены ника")
    print("🚀 Готов к работе!")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
