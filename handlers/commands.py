from aiogram import Router, types
from aiogram.filters import Command
from database.db_manager import get_patsan  # Теперь асинхронная функция
from keyboards.keyboards import main_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    # ДОБАВЛЯЕМ await!
    patsan = await get_patsan(message.from_user.id)
    
    await message.answer(
        f"<b>Ну чё, пацан?</b> 👊\n"
        f"Добро пожаловать на гофроцентрал.\n"
        f"У тебя в кишке {patsan['atm_count']}/12 атмосфер.\n"
        f"Иди заварваривай коричневага, а то старшие придут и спросят.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Обработчик команды /profile"""
    # ДОБАВЛЯЕМ await!
    patsan = await get_patsan(message.from_user.id)
    
    upgrades = patsan["upgrades"]
    bought_upgrades = [k for k, v in upgrades.items() if v]
    
    upgrade_text = ""
    if bought_upgrades:
        upgrade_text = "\n<b>Нагнетатели:</b>\n" + "\n".join([f"• {upg}" for upg in bought_upgrades])
    
    await message.answer(
        f"<b>📊 Профиль пацана:</b>\n\n"
        f"👤 {patsan['nickname']}\n"
        f"⭐ Авторитет: {patsan['avtoritet']}\n"
        f"🌀 Атмосферы: {patsan['atm_count']}/12\n"
        f"🐍 Коричневаг: {patsan['zmiy']:.3f} кг\n"
        f"💰 Деньги: {patsan['dengi']} руб.\n\n"
        f"<b>Скиллы:</b>\n"
        f"💪 Давка: {patsan['skill_davka']}\n"
        f"🛡️ Защита: {patsan['skill_zashita']}\n"
        f"🔍 Находка: {patsan['skill_nahodka']}"
        f"{upgrade_text}",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )
