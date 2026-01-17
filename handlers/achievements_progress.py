from aiogram import Router, types, F
from database.db_manager import get_patsan_cached, get_achievement_progress
from keyboards.keyboards import main_keyboard
from keyboards.new_keyboards import achievements_progress_keyboard, back_to_profile_keyboard

router = Router()

@router.callback_query(F.data == "achievements_progress")
async def callback_achievements_progress(callback: types.CallbackQuery):
    """Прогресс по уровневым достижениям"""
    user_id = callback.from_user.id
    progress_data = await get_achievement_progress(user_id)
    
    if not progress_data:
        await callback.message.edit_text(
            "📊 <b>ПРОГРЕСС ДОСТИЖЕНИЙ</b>\n\n"
            "Пока нет прогресса по уровневым достижениям.\n"
            "Играй активно, и прогресс появится!",
            reply_markup=achievements_progress_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "<b>📊 ПРОГРЕСС ПО УРОВНЕВЫМ ДОСТИЖЕНИЯМ</b>\n\n"
    
    for ach_id, data in progress_data.items():
        text += f"<b>{data['name']}</b>\n"
        
        if data['next_level']:
            current_level = data['current_level']
            total_levels = len(data['all_levels'])
            
            text += f"Уровень: {current_level}/{total_levels}\n"
            text += f"Прогресс: {data['current_progress']:.1f}/{data['next_level']['goal']} "
            text += f"({data['progress_percent']:.1f}%)\n"
            
            # Прогресс-бар
            bars = 10
            filled = int(data['progress_percent'] / 10)
            progress_bar = "█" * filled + "░" * (bars - filled)
            text += f"[{progress_bar}]\n"
            
            text += f"Следующий уровень: <b>{data['next_level']['title']}</b>\n"
            text += f"Награда: +{data['next_level']['reward']}р, +{data['next_level']['exp']} опыта\n"
        else:
            text += f"✅ Все уровни пройдены! (Максимум)\n"
        
        text += "\n"
    
    text += "<i>Выбери достижение для подробной информации:</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=achievements_progress_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("achievement_"))
async def callback_achievement_detail(callback: types.CallbackQuery):
    """Детальная информация о достижении"""
    ach_type = callback.data.replace("achievement_", "")
    
    ach_map = {
        "zmiy_collector": {
            "name": "Коллекционер змия",
            "description": "Собери определённое количество змия",
            "levels": [
                {"goal": 10, "reward": 50, "title": "Новичок", "exp": 10},
                {"goal": 100, "reward": 300, "title": "Любитель", "exp": 50},
                {"goal": 1000, "reward": 1500, "title": "Профессионал", "exp": 200},
                {"goal": 10000, "reward": 5000, "title": "КОРОЛЬ ГОФРОЦЕНТРАЛА", "exp": 1000}
            ]
        },
        "money_maker": {
            "name": "Денежный мешок",
            "description": "Заработай много денег",
            "levels": [
                {"goal": 1000, "reward": 100, "title": "Бедолага", "exp": 10},
                {"goal": 10000, "reward": 1000, "title": "Состоятельный", "exp": 100},
                {"goal": 100000, "reward": 5000, "title": "Олигарх", "exp": 500},
                {"goal": 1000000, "reward": 25000, "title": "РОТШИЛЬД", "exp": 2500}
            ]
        },
        "rademka_king": {
            "name": "Король радёмок",
            "description": "Победи в множестве радёмок",
            "levels": [
                {"goal": 5, "reward": 200, "title": "Задира", "exp": 20},
                {"goal": 25, "reward": 1000, "title": "Гроза района", "exp": 100},
                {"goal": 100, "reward": 5000, "title": "Неприкасаемый", "exp": 500},
                {"goal": 500, "reward": 25000, "title": "ЛЕГЕНДА РАДЁМКИ", "exp": 2500}
            ]
        }
    }
    
    if ach_type not in ach_map:
        await callback.answer("Неизвестное достижение", show_alert=True)
        return
    
    ach_data = ach_map[ach_type]
    
    text = f"<b>🏆 {ach_data['name'].upper()}</b>\n\n"
    text += f"<i>{ach_data['description']}</i>\n\n"
    text += "<b>📊 Уровни:</b>\n"
    
    for i, level in enumerate(ach_data['levels'], 1):
        text += f"{i}. <b>{level['title']}</b>: {level['goal']} → +{level['reward']}р (+{level['exp']} опыта)\n"
    
    text += "\n<i>Прогресс автоматически отслеживается во время игры.</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_profile_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "achievements_progress_all")
async def callback_achievements_progress_all(callback: types.CallbackQuery):
    """Все уровневие достижения"""
    text = (
        "<b>🏆 ВСЕ УРОВНЕВЫЕ ДОСТИЖЕНИЯ</b>\n\n"
        
        "<b>🐍 Коллекционер змия</b>\n"
        "• Новичок: 10кг → +50р\n"
        "• Любитель: 100кг → +300р\n"  
        "• Профессионал: 1000кг → +1500р\n"
        "• КОРОЛЬ: 10000кг → +5000р\n\n"
        
        "<b>💰 Денежный мешок</b>\n"
        "• Бедолага: 1000р → +100р\n"
        "• Состоятельный: 10000р → +1000р\n"
        "• Олигарх: 100000р → +5000р\n"
        "• РОТШИЛЬД: 1000000р → +25000р\n\n"
        
        "<b>👊 Король радёмок</b>\n"
        "• Задира: 5 побед → +200р\n"
        "• Гроза района: 25 побед → +1000р\n"
        "• Неприкасаемый: 100 побед → +5000р\n"
        "• ЛЕГЕНДА: 500 побед → +25000р\n\n"
        
        "<i>➕ Ещё больше достижений в разработке!</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=achievements_progress_keyboard(),
        parse_mode="HTML"
    )
