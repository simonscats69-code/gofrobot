import asyncio
import os
import logging
import gc
import signal
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
from db_manager import init_db, close_pool, stop_auto_backup, create_backup, start_auto_backup
from dotenv import load_dotenv
from handlers import router

load_dotenv()

# Глобальные переменные для graceful shutdown
_shutdown_event = None

def setup_logging():
    log_dir = "storage/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    try:
        import colorlog
        
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            f'%(log_color)s{log_format}',
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))
        
        log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        
        logger = colorlog.getLogger()
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        
        logging.getLogger('aiogram').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        
        logger.info(f"📝 Логирование настроено. Файл: {log_file}")
        
        return logger
        
    except ImportError:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log"), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("📝 Обычное логирование (colorlog не установлен)")
        return logger

logger = setup_logging()

async def set_bot_commands(bot: Bot):
    private_commands = [
        BotCommand(command="start", description="🚀 Начать игру"),
        BotCommand(command="davka", description="🐍 Давить коричневага"),
        BotCommand(command="uletet", description="✈️ Отправить змия"),
        BotCommand(command="profile", description="📊 Профиль игрока"),
        BotCommand(command="gofra", description="🏗️ Инфо о гофрошке"),
        BotCommand(command="cable", description="🔌 Инфо о кабеле"),
        BotCommand(command="atm", description="🌡️ Состояние атмосфер"),
        BotCommand(command="top", description="🏆 Топ игроков"),
        BotCommand(command="nickname", description="👤 Смена ника"),
        BotCommand(command="rademka", description="👊 Радёмка (PvP)"),
        BotCommand(command="help", description="🆘 Помощь"),
        BotCommand(command="version", description="🔄 Версия бота"),
        BotCommand(command="menu", description="📱 Главное меню"),
    ]
    
    group_commands = [
        BotCommand(command="start", description="🚀 Активировать в чате"),
        BotCommand(command="gdavka", description="🐍 Давить змия в чате"),
        BotCommand(command="grademka", description="👊 Радёмка в чате"),
        BotCommand(command="fight", description="⚔️ Протащить игрока (ответом)"),
        BotCommand(command="gtop", description="🏆 Топ этого чата"),
        BotCommand(command="gstats", description="📊 Статистика чата"),
        BotCommand(command="gme", description="📈 Мой вклад в чат"),
        BotCommand(command="ghelp", description="🆘 Помощь по чату"),
        BotCommand(command="gmenu", description="📱 Меню для чата"),
        BotCommand(command="davka", description="🐍 Давить (личное)"),
        BotCommand(command="profile", description="📊 Профиль (личное)"),
        BotCommand(command="top", description="🏆 Топ (личное)"),
        BotCommand(command="rademka", description="👊 Радёмка (личная)"),
    ]
    
    await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
    
    logger.info("✅ Команды бота установлены (разные для лички и групп)")

async def graceful_shutdown(signal_name: str):
    """Корректное завершение работы бота."""
    logger.info(f"🛑 Получен сигнал {signal_name}, начинаю корректное завершение...")
    
    try:
        # 1. Создаём финальный бэкап
        logger.info("💾 Создаём финальный бэкап...")
        await create_backup()
        
        # 2. Останавливаем автобэкап
        logger.info("🛑 Останавливаем автобэкап...")
        await stop_auto_backup()
        
        # 3. Закрываем пул соединений с БД
        logger.info("🔌 Закрываем соединения с базой данных...")
        await close_pool()
        
        # 4. Принудительный сборщик мусора
        gc.collect()
        
        logger.info("✅ Корректное завершение работы бота выполнено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении работы: {e}", exc_info=True)

def setup_signal_handlers(loop):
    """Настройка обработчиков сигналов."""
    global _shutdown_event
    
    _shutdown_event = asyncio.Event()
    
    def signal_handler(sig):
        logger.info(f"📡 Получен сигнал {sig.name}")
        loop.create_task(graceful_shutdown(sig.name))
        _shutdown_event.set()
    
    # Обработчики для Windows
    try:
        loop.add_signal_handler(signal.SIGTERM, lambda: signal_handler(signal.SIGTERM))
        loop.add_signal_handler(signal.SIGINT, lambda: signal_handler(signal.SIGINT))
    except (AttributeError, NotImplementedError):
        # SIGTERM/SIGINT не доступны на Windows
        pass
    
    # Добавляем обработку Ctrl+C через on_shutdown
    logger.info("✅ Обработчики сигналов настроены")

async def main():
    global _shutdown_event
    
    # Создаём event loop для shutdown
    loop = asyncio.get_running_loop()
    setup_signal_handlers(loop)
    
    gc.collect()
    
    try:
        logger.info("🚀 Запуск бота на bothost.ru")
        logger.info(f"📁 Рабочая директория: {os.getcwd()}")
        logger.info(f"📂 Содержимое: {os.listdir('.')}")

        await init_db()

        # Запускаем автобэкап
        await start_auto_backup(interval_seconds=3600)

        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            raise ValueError("BOT_TOKEN не найден в переменных окружения")

        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())

        await set_bot_commands(bot)

        dp.include_router(router)

        logger.info("Бот запускается...")
        
        # Запускаем polling с возможностью graceful shutdown
        try:
            await dp.start_polling(bot, shutdown_hook=graceful_shutdown)
        except asyncio.CancelledError:
            logger.info("⏹️ Polling отменён")
        
        # Ждём завершения если был сигнал
        if _shutdown_event and not _shutdown_event.is_set():
            await _shutdown_event.wait()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)

    finally:
        gc.collect()
        logger.info("👋 Бот полностью остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем (Ctrl+C)")
