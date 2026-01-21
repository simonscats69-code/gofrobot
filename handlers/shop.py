from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from database.db_manager import get_patsan, buy_upgrade
from keyboards.keyboards import shop_keyboard, main_keyboard
from keyboards.keyboards import shop_categories_keyboard

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

@router.callback_query(F.data == "shop")
async def callback_shop(callback: types.CallbackQuery):
    patsan = await get_patsan(callback.from_user.id)
    
    upgrades = patsan["upgrades"]
    
    def get_status_emoji(status):
        return "✅" if status else "❌"
    
    text = "<b>🛒 НАГНЕТАТЕЛЬНАЯ СТОЛОВАЯ</b>\n\n"
    text += "<i>Покупай питание для заварваривания двенашки</i>\n\n"
    
    items = [
        ("🥛 Ряженка", "ryazhenka", 300, "+75% давления в двенашке", upgrades.get("ryazhenka")),
        ("🍵 Чай сливовый", "tea_slivoviy", 500, "Разгоняет процесс (-2 атмосферы)", upgrades.get("tea_slivoviy")),
        ("🧋 Бублэки", "bubbleki", 800, "Турбулентность (+35% к находкам + редкие предметы)", upgrades.get("bubbleki")),
        ("🥐 Курвасаны с телотинкой", "kuryasany", 1500, "Заряд энергии (+2 авторитета)", upgrades.get("kuryasany"))
    ]
    
    for name, key, price, desc, status in items:
        status_icon = get_status_emoji(status)
        text += f"<b>{name}</b> - {price}р {status_icon}\n"
        text += f"<i>{desc}</i>\n\n"
    
    all_upgrades = ["ryazhenka", "tea_slivoviy", "bubbleki", "kuryasany"]
    bought_all = all(upgrades.get(upg, False) for upg in all_upgrades)
    
    if bought_all:
        text += "🎉 <b>У тебя все нагнетатели!</b>\n\n"
    
    text += f"💰 <b>Твои деньги:</b> {patsan['dengi']} руб.\n"
    text += f"📈 <b>Уровень:</b> {patsan.get('level', 1)}\n\n"
    
    if patsan.get('level', 1) >= 10:
        text += "🎁 <i>Уровень 10+ даёт скидку 5% на все покупки!</i>\n"
    
    await callback.message.edit_text(
        text, 
        reply_markup=shop_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: types.CallbackQuery):
    upgrade = callback.data.replace("buy_", "")
    user_id = callback.from_user.id
    
    patsan = await get_patsan(user_id)
    player_level = patsan.get('level', 1)
    discount_multiplier = 0.95 if player_level >= 10 else 1.0
    
    patsan, result = await buy_upgrade(user_id, upgrade)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    discount_text = ""
    if player_level >= 10:
        prices = {"ryazhenka": 300, "tea_slivoviy": 500, "bubbleki": 800, "kuryasany": 1500}
        original_price = prices.get(upgrade, 0)
        discounted_price = int(original_price * discount_multiplier)
        discount_text = f" (скидка {original_price - discounted_price}р за уровень {player_level})"
    
    result_with_discount = result + discount_text if discount_text else result
    
    await callback.answer(result_with_discount, show_alert=True)
    
    all_upgrades = ["ryazhenka", "tea_slivoviy", "bubbleki", "kuryasany"]
    bought_all = all(patsan["upgrades"].get(upg, False) for upg in all_upgrades)
    
    if bought_all:
        await callback.message.edit_text(
            "🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
            "Ты купил ВСЕ нагнетатели в столовой!\n"
            "🔥 <b>Теперь ты настоящий ценитель гофроцентральной кухни!</b>\n\n"
            "<i>Можешь продолжать играть с максимальными бонусами.</i>",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await callback_shop(callback)

@router.callback_query(F.data == "shop_categories")
async def callback_shop_categories(callback: types.CallbackQuery):
    text = (
        "<b>🏪 КАТЕГОРИИ МАГАЗИНА</b>\n\n"
        
        "<b>🥛 Нагнетатели (основные)</b>\n"
        "• Усиления для основных механик игры\n"
        "• Постоянные бонусы\n"
        "• Доступны сразу\n\n"
        
        "<b>⚡ Бустеры (скоро)</b>\n"
        "• Временные усиления\n"
        "• Большой эффект на короткое время\n"
        "• Для особых случаев\n\n"
        
        "<b>🔧 Инструменты (скоро)</b>\n"
        "• Полезные предметы\n"
        "• Упрощают игровой процесс\n"
        "• Помощь в сложных ситуациях\n\n"
        
        "<b>🎁 Случайные наборы (скоро)</b>\n"
        "• Наборы предметов со скидкой\n"
        "• Сюрприз каждый день\n"
        "• Ограниченное предложение\n\n"
        
        "<i>Новые категории появятся в следующих обновлениях!</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=shop_categories_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "shop_upgrades")
async def callback_shop_upgrades(callback: types.CallbackQuery):
    await callback_shop(callback)

@router.callback_query(F.data == "shop_boosters")
async def callback_shop_boosters(callback: types.CallbackQuery):
    await callback.answer("Категория 'Бустеры' появится в следующем обновлении!", show_alert=True)
    await callback_shop_categories(callback)

@router.callback_query(F.data == "shop_tools")
async def callback_shop_tools(callback: types.CallbackQuery):
    await callback.answer("Категория 'Инструменты' появится в следующем обновлении!", show_alert=True)
    await callback_shop_categories(callback)

@router.callback_query(F.data == "shop_random")
async def callback_shop_random(callback: types.CallbackQuery):
    await callback.answer("Категория 'Случайные наборы' появится в следующем обновлении!", show_alert=True)
    await callback_shop_categories(callback)

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    from database.db_manager import get_patsan_cached
    
    patsan = await get_patsan_cached(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер в кишке: {patsan['atm_count']}/{patsan.get('max_atm', 12)}",
        reply_markup=main_keyboard()
    )
