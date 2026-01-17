from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from database.db_manager import get_patsan_cached, get_craftable_items, craft_item
from keyboards.keyboards import main_keyboard, craft_keyboard, craft_items_keyboard, back_to_craft_keyboard
from keyboards.new_keyboards import craft_recipes_keyboard, craft_confirmation_keyboard

router = Router()

# Декоратор для обработки ошибки "message is not modified"
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

@router.callback_query(F.data == "craft")
async def callback_craft_menu(callback: types.CallbackQuery):
    """Меню крафта"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    crafted_count = len(patsan.get("crafted_items", []))
    
    text = (
        f"<b>🔨 КРАФТ ПРЕДМЕТОВ</b>\n\n"
        f"<i>Создавай мощные предметы из ингредиентов!</i>\n\n"
        f"📦 Инвентарь: {len(patsan.get('inventory', []))} предметов\n"
        f"🔨 Скрафчено: {crafted_count} предметов\n"
        f"💰 Деньги: {patsan['dengi']}р\n\n"
        f"<b>Выбери действие:</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=craft_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "craft_items")
async def callback_craft_items_list(callback: types.CallbackQuery):
    """Список предметов для крафта"""
    user_id = callback.from_user.id
    craftable_items = await get_craftable_items(user_id)
    
    if not craftable_items:
        await callback.message.edit_text(
            "😕 <b>НЕТ ДОСТУПНЫХ РЕЦЕПТОВ</b>\n\n"
            "У тебя пока нет нужных ингредиентов для крафта.\n"
            "Собирай двенашки, атмосферы и другие предметы!",
            reply_markup=back_to_craft_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "<b>🔨 ДОСТУПНЫЕ ДЛЯ КРАФТА:</b>\n\n"
    
    for item in craftable_items:
        status = "✅ МОЖНО" if item["can_craft"] else "❌ НЕЛЬЗЯ"
        text += f"<b>{item['name']}</b> {status}\n"
        text += f"<i>{item['description']}</i>\n"
        text += f"🎲 Шанс успеха: {int(item['success_chance'] * 100)}%\n"
        
        if not item["can_craft"] and item["missing"]:
            text += f"<code>Не хватает: {', '.join(item['missing'][:2])}</code>\n"
        
        text += "\n"
    
    text += "<i>Выбери предмет для крафта:</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=craft_items_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("craft_"))
async def callback_craft_action(callback: types.CallbackQuery):
    """Обработка действий крафта"""
    action = callback.data.replace("craft_", "")
    
    if action == "recipes":
        # Список рецептов
        await callback_craft_recipes(callback)
    elif action == "history":
        # История крафта
        await callback_craft_history(callback)
    elif action.startswith("execute_"):
        # Выполнение крафта
        recipe_id = action.replace("execute_", "")
        await callback_craft_execute(callback, recipe_id)
    elif action in ["super_dvenashka", "vechnyy_dvigatel", "tarskiy_obed", "booster_atm"]:
        # Выбор конкретного рецепта
        recipe_map = {
            "super_dvenashka": "супер_двенашка",
            "vechnyy_dvigatel": "вечный_двигатель", 
            "tarskiy_obed": "царский_обед",
            "booster_atm": "бустер_атмосфер"
        }
        recipe_id = recipe_map.get(action)
        if recipe_id:
            await callback_craft_recipe_info(callback, recipe_id)
    else:
        await callback.answer("Неизвестное действие", show_alert=True)

async def callback_craft_recipes(callback: types.CallbackQuery):
    """Список всех рецептов"""
    text = (
        "<b>📜 ВСЕ РЕЦЕПТЫ КРАФТА</b>\n\n"
        
        "<b>✨ Супер-двенашка</b>\n"
        "Ингредиенты: 3× двенашка, 500р\n"
        "Шанс: 100% | Эффект: Повышает удачу на 1 час\n\n"
        
        "<b>⚡ Вечный двигатель</b>\n"
        "Ингредиенты: 5× атмосфера, 1× энергетик\n"
        "Шанс: 80% | Эффект: Ускоряет восстановление атмосфер на 24ч\n\n"
        
        "<b>👑 Царский обед</b>\n"
        "Ингредиенты: 1× курвасаны, 1× ряженка, 300р\n"
        "Шанс: 100% | Эффект: Максимальный буст на 30 минут\n\n"
        
        "<b>🌀 Бустер атмосфер</b>\n"
        "Ингредиенты: 2× энергетик, 1× двенашка, 2000р\n"
        "Шанс: 70% | Эффект: +3 к максимальному запасу атмосфер\n\n"
        
        "<i>Собирай ингредиенты и создавай мощные предметы!</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=craft_recipes_keyboard(),
        parse_mode="HTML"
    )

async def callback_craft_history(callback: types.CallbackQuery):
    """История крафта"""
    user_id = callback.from_user.id
    patsan = await get_patsan_cached(user_id)
    
    crafted_items = patsan.get("crafted_items", [])
    
    if not crafted_items:
        await callback.message.edit_text(
            "📜 <b>ИСТОРИЯ КРАФТА</b>\n\n"
            "Пока пусто...\n"
            "Скрафть первый предмет, и история появится здесь!",
            reply_markup=back_to_craft_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "<b>📜 ИСТОРИЯ ТВОЕГО КРАФТА:</b>\n\n"
    
    import time
    from datetime import datetime
    
    # Показываем последние 10 крафтов
    for i, craft in enumerate(crafted_items[-10:], 1):
        recipe = craft.get("recipe", "неизвестно")
        item = craft.get("item", "предмет")
        craft_time = craft.get("time", 0)
        
        # Форматируем время
        if craft_time:
            time_str = datetime.fromtimestamp(craft_time).strftime("%d.%m.%Y %H:%M")
        else:
            time_str = "давно"
        
        # Эмодзи для разных предметов
        emoji = {
            "супер_двенашка": "✨",
            "вечный_двигатель": "⚙️",
            "царский_обед": "👑",
            "бустер_атмосфер": "🌀"
        }.get(item, "🔨")
        
        text += f"{i}. {emoji} <b>{item}</b>\n"
        text += f"   Рецепт: {recipe} | Время: {time_str}\n\n"
    
    text += f"<i>Всего скрафчено: {len(crafted_items)} предметов</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_craft_keyboard(),
        parse_mode="HTML"
    )

async def callback_craft_recipe_info(callback: types.CallbackQuery, recipe_id: str):
    """Информация о конкретном рецепте"""
    recipe_map = {
        "супер_двенашка": {
            "name": "✨ Супер-двенашка",
            "ingredients": "3× двенашка, 500р",
            "chance": "100%",
            "effect": "Повышает удачу на 1 час",
            "description": "Особая двенашка с усиленной энергетикой"
        },
        "вечный_двигатель": {
            "name": "⚡ Вечный двигатель",
            "ingredients": "5× атмосфера, 1× энергетик", 
            "chance": "80%",
            "effect": "Ускоряет восстановление атмосфер на 24ч",
            "description": "Мини-генератор атмосферной энергии"
        },
        "царский_обед": {
            "name": "👑 Царский обед",
            "ingredients": "1× курвасаны, 1× ряженка, 300р",
            "chance": "100%", 
            "effect": "Максимальный буст на 30 минут",
            "description": "Пиршество для настоящего пацана"
        },
        "бустер_атмосфер": {
            "name": "🌀 Бустер атмосфер",
            "ingredients": "2× энергетик, 1× двенашка, 2000р",
            "chance": "70%",
            "effect": "+3 к максимальному запасу атмосфер",
            "description": "Расширяет твои внутренние резервы"
        }
    }
    
    if recipe_id not in recipe_map:
        await callback.answer("Неизвестный рецепт", show_alert=True)
        return
    
    recipe = recipe_map[recipe_id]
    
    text = (
        f"<b>{recipe['name']}</b>\n\n"
        f"<i>{recipe['description']}</i>\n\n"
        f"<b>📦 Ингредиенты:</b>\n{recipe['ingredients']}\n\n"
        f"<b>🎲 Шанс успеха:</b> {recipe['chance']}\n\n"
        f"<b>⚡ Эффект:</b>\n{recipe['effect']}\n\n"
        f"<i>Скрафтить этот предмет?</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=craft_confirmation_keyboard(recipe_id),
        parse_mode="HTML"
    )

async def callback_craft_execute(callback: types.CallbackQuery, recipe_id: str):
    """Выполнение крафта"""
    user_id = callback.from_user.id
    
    success, message, result = await craft_item(user_id, recipe_id)
    
    if success:
        # Успешный крафт
        item_name = result.get("item", "предмет")
        duration = result.get("duration")
        
        duration_text = ""
        if duration:
            hours = duration // 3600
            if hours > 0:
                duration_text = f"\n⏱️ Действует: {hours} часов"
        
        await callback.message.edit_text(
            f"✨ <b>КРАФТ УСПЕШЕН!</b>\n\n"
            f"{message}{duration_text}\n\n"
            f"🎉 Ты создал новый предмет!\n"
            f"Проверь инвентарь, чтобы использовать его.",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Неудачный крафт
        await callback.message.edit_text(
            f"💥 <b>КРАФТ ПРОВАЛЕН</b>\n\n"
            f"{message}\n\n"
            f"Ингредиенты потеряны...\n"
            f"Попробуй снова, когда соберёшь больше!",
            reply_markup=back_to_craft_keyboard(),
            parse_mode="HTML"
        )

@ignore_not_modified_error
@router.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    from database.db_manager import get_patsan_cached
    
    patsan = await get_patsan_cached(callback.from_user.id)
    await callback.message.edit_text(
        f"Главное меню. Атмосфер в кишке: {patsan['atm_count']}/{patsan.get('max_atm', 12)}",
        reply_markup=main_keyboard()
    )
