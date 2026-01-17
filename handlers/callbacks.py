from aiogram import Router, types, F
from database.db_manager import (
    get_patsan,           # ← теперь асинхронная
    davka_zmiy,           # ← теперь асинхронная, сигнатура изменилась!
    sdat_zmiy,            # ← теперь асинхронная, сигнатура изменилась!
    pump_skill,           # ← теперь асинхронная, сигнатура изменилась!
    get_patsan_cached     # ← можно использовать кэшированную версию
)
from keyboards.keyboards import main_keyboard, pump_keyboard, back_keyboard

router = Router()

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    # ИСПРАВЛЕНО: добавлен await
    patsan = await get_patsan_cached(callback.from_user.id)  # Используем кэшированную версию
    await callback.message.edit_text(
        f"Главное меню. Атмосфер в кишке: {patsan['atm_count']}/12",
        reply_markup=main_keyboard()
    )

@router.callback_query(F.data == "davka")
async def callback_davka(callback: types.CallbackQuery):
    """Давка коричневага"""
    user_id = callback.from_user.id
    
    # ИСПРАВЛЕНО: новая сигнатура - передаём user_id, а не patsan
    patsan, result = await davka_zmiy(user_id)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    # Формируем сообщение о нагнетателе
    nagnetatel_msg = ""
    if patsan["upgrades"].get("ryazhenka"):
        nagnetatel_msg = "\n🥛 <i>Ряженка жмёт двенашку как надо!</i>"
    elif patsan["upgrades"].get("bubbleki"):
        nagnetatel_msg = "\n🧋 <i>Бублэки создают нужную турбулентность!</i>"
    
    dvenashka_msg = "\n🧱 Нашёл двенашку в турбулентности!" if result.get("dvenashka_found") else ""
    
    await callback.message.edit_text(
        f"<b>Заварвариваем дело...</b>{nagnetatel_msg}\n\n"
        f"🔄 Потрачено атмосфер: {result['cost']}\n"
        f"<i>\"{result['weight_msg']} говна за 25 секунд высрал я сейчас\"</i>\n\n"
        f"➕ {result['total_grams']/1000:.3f} кг коричневага{dvenashka_msg}\n"
        f"Всего змия накоплено: {patsan['zmiy']:.3f} кг\n"
        f"⚡ Осталось атмосфер: {patsan['atm_count']}/12",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "sdat")
async def callback_sdat(callback: types.CallbackQuery):
    """Сдача змия"""
    user_id = callback.from_user.id
    
    # ИСПРАВЛЕНО: новая сигнатура - передаём user_id, а не patsan
    patsan, result = await sdat_zmiy(user_id)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    await callback.message.edit_text(
        f"<b>Сдал коричневага на металлолом</b>\n\n"
        f"📦 Сдано: {result['old_zmiy']:.3f} кг змия\n"
        f"💰 Получил: {result['total_money']} руб. (включая бонус за авторитет: +{result['avtoritet_bonus']}р)\n"
        f"💸 Теперь на кармане: {patsan['dengi']} руб.\n\n"
        f"<i>Приёмщик: \"Опять эту дрянь принёс...\"</i>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "pump")
async def callback_pump(callback: types.CallbackQuery):
    """Меню прокачки"""
    # ИСПРАВЛЕНО: добавлен await
    patsan = await get_patsan_cached(callback.from_user.id)
    
    text = (
        f"<b>Прокачка скиллов:</b>\n"
        f"💰 Деньги: {patsan['dengi']} руб.\n\n"
        f"💪 <b>Давка змия</b> (+100г за уровень): {patsan['skill_davka']} ур. (200р/ур)\n"
        f"🛡️ <b>Защита атмосфер</b>: {patsan['skill_zashita']} ур. (300р/ур)\n"
        f"🔍 <b>Находка двенашек</b> (+5% шанс): {patsan['skill_nahodka']} ур. (250р/ур)\n\n"
        f"Выбери, что прокачать:"
    )
    
    await callback.message.edit_text(
        text, 
        reply_markup=pump_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("pump_"))
async def callback_pump_skill(callback: types.CallbackQuery):
    """Прокачка конкретного скилла"""
    skill = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # ИСПРАВЛЕНО: новая сигнатура - передаём user_id и skill
    patsan, result = await pump_skill(user_id, skill)
    
    if patsan is None:
        await callback.answer(result, show_alert=True)
        return
    
    await callback.answer(result, show_alert=True)
    await callback_pump(callback)  # Обновляем меню прокачки

@router.callback_query(F.data == "inventory")
async def callback_inventory(callback: types.CallbackQuery):
    """Инвентарь"""
    # ИСПРАВЛЕНО: добавлен await
    patsan = await get_patsan_cached(callback.from_user.id)
    
    inv = patsan.get("inventory", [])
    if not inv:
        inv_text = "Пусто... Только пыль и тоска"
    else:
        item_count = {}
        for item in inv:
            item_count[item] = item_count.get(item, 0) + 1
        
        inv_text = "Твои вещи:\n"
        for item, count in item_count.items():
            inv_text += f"• {item}: {count} шт.\n"
    
    text = f"<b>🎒 Твой инвентарь:</b>\n\n{inv_text}\n\n"
    text += f"🐍 Коричневагый змий: {patsan['zmiy']:.3f} кг"
    
    await callback.message.edit_text(
        text, 
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "profile")
async def callback_profile(callback: types.CallbackQuery):
    """Профиль через callback"""
    # ИСПРАВЛЕНО: добавлен await
    patsan = await get_patsan_cached(callback.from_user.id)
    
    upgrades = patsan["upgrades"]
    bought_upgrades = [k for k, v in upgrades.items() if v]
    
    upgrade_text = ""
    if bought_upgrades:
        upgrade_text = "\n<b>Нагнетатели:</b>\n" + "\n".join([f"• {upg}" for upg in bought_upgrades])
    
    await callback.message.edit_text(
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
