from aiogram import Router, types, F
from database.db_manager import get_patsan, buy_upgrade
from keyboards.keyboards import shop_keyboard, main_keyboard

router = Router()

@router.callback_query(F.data == "shop")
async def callback_shop(callback: types.CallbackQuery):
    """Магазин нагнетательной столовой"""
    patsan = get_patsan(callback.from_user.id)
    
    upgrades = patsan["upgrades"]
    text = "<b>🍽️ Нагнетательная столовая:</b>\n\n"
    text += "<i>Покупай питание для заварваривания двенашки</i>\n\n"
    
    items = [
        ("🥛 Ряженка", "ryazhenka", 500, "+50% давления в двенашке"),
        ("🍵 Чай сливовый", "tea_slivoviy", 700, "Разгоняет процесс (-1 атмосфера)"),
        ("🧋 Бублэки", "bubbleki", 600, "Турбулентность (+20% к находкам)"),
        ("🥐 Курвасаны с телотинкой", "kuryasany", 1000, "Заряд энергии (+1 авторитет)")
    ]
    
    for name, key, price, desc in items:
        status = "✅ Куплено" if upgrades.get(key) else "❌ Нет в наличии"
        text += f"<b>{name}</b>\n{desc}\nЦена: {price}р | {status}\n\n"
    
    text += f"💰 Твои деньги: {patsan['dengi']} руб."
    
    await callback.message.edit_text(text, reply_markup=shop_keyboard())

@router.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: types.CallbackQuery):
    """Покупка нагнетателя"""
    upgrade = callback.data.replace("buy_", "")
    patsan = get_patsan(callback.from_user.id)
    patsan, result = buy_upgrade(patsan, upgrade)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    await callback.answer(result, show_alert=True)
    await callback_shop(callback)  # Обновляем магазин
