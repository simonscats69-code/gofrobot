import asyncio
import os
import logging
import gc
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
from db_manager import init_db
from dotenv import load_dotenv
from handlers import router

load_dotenv()

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

async def main():
    gc.collect()
    
    try:
        logger.info("🚀 Запуск бота на bothost.ru")
        logger.info(f"📁 Рабочая директория: {os.getcwd()}")
        logger.info(f"📂 Содержимое: {os.listdir('.')}")

        await init_db()

        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            raise ValueError("BOT_TOKEN не найден в переменных окружения")

        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())

        await set_bot_commands(bot)

        dp.include_router(router)

        logger.info("Бот запускается...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)

    finally:
        gc.collect()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
