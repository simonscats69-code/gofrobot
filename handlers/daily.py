from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from db_manager import get_patsan, get_daily
from keyboards import main_keyboard, daily_keyboard

router = Router()

def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                if len(args) > 0 and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise
    return wrapper

# Комментарий: В новой системе нет ежедневных наград
# Можно либо удалить этот файл, либо оставить заглушку

@router.message(Command("daily"))
async def cmd_daily(message: types.Message):
    """В новой системе нет ежедневных наград"""
    await message.answer(
        "🎁 ЕЖЕДНЕВНЫЕ НАГРАДЫ УБРАНЫ\n\n"
        "В новой системе гофроцентрала ежедневные награды заменены на:\n"
        "• 🐍 Давку коричневага при полных 12 атмосферах\n"
        "• 🏗️ Прокачку гофры за опыт\n"
        "• ⚡ Ускорение восстановления атмосфер\n\n"
        "Жди полной зарядки атмосфер и дави змия!",
        reply_markup=main_keyboard()
    )

@ignore_not_modified_error
@router.callback_query(F.data == "daily")
async def callback_daily(callback: types.CallbackQuery):
    """Заглушка для кнопки ежедневной награды"""
    await callback.answer("В новой системе нет ежедневных наград!", show_alert=True)
