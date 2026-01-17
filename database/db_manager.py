import asyncio
import time
import random
import json
from typing import Optional, List, Dict, Any, Tuple
import aiosqlite  # Асинхронный SQLite

# Константы
ATM_MAX = 12
ATM_TIME = 600
DB_NAME = "bot_database.db"

# ==================== АСИНХРОННЫЕ ФУНКЦИИ БАЗЫ ДАННЫХ ====================

async def get_connection():
    """Создаёт асинхронное соединение с базой данных"""
    conn = await aiosqlite.connect(DB_NAME)
    conn.row_factory = aiosqlite.Row  # Чтобы получать данные как словари
    return conn

async def init_db():
    """Асинхронная инициализация базы данных: создаёт все таблицы"""
    conn = await aiosqlite.connect(DB_NAME)
    
    try:
        # 1. Таблица пользователей (для игры)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                nickname TEXT,
                avtoritet INTEGER DEFAULT 1,
                zmiy REAL DEFAULT 0.0,
                dengi INTEGER DEFAULT 100,
                last_update INTEGER,
                last_daily INTEGER DEFAULT 0,          -- НОВОЕ: последняя ежедневная награда
                atm_count INTEGER DEFAULT 12,
                skill_davka INTEGER DEFAULT 1,
                skill_zashita INTEGER DEFAULT 1,
                skill_nahodka INTEGER DEFAULT 1,
                inventory TEXT,
                upgrades TEXT,
                achievements TEXT DEFAULT '[]',        -- НОВОЕ: список достижений в JSON
                nickname_changed BOOLEAN DEFAULT FALSE, -- НОВОЕ: менял ли ник
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Таблица корзины (для магазина)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                UNIQUE(user_id, item_name)
            )
        ''')
        
        # 3. Таблица заказов (история)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                items TEXT NOT NULL,
                total INTEGER NOT NULL,
                status TEXT DEFAULT 'новый',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. НОВАЯ ТАБЛИЦА: Достижения
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # 5. НОВАЯ ТАБЛИЦА: Статистика радёмок
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS rademka_fights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                winner_id INTEGER NOT NULL,
                loser_id INTEGER NOT NULL,
                money_taken INTEGER DEFAULT 0,
                item_stolen TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаём индексы для быстрого поиска
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_cart_user_id ON cart(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rademka_winner ON rademka_fights(winner_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rademka_loser ON rademka_fights(loser_id)')
        
        await conn.commit()
        print("✅ База данных SQLite инициализирована (асинхронная версия)")
        print("✅ Добавлены поля для: ежедневных наград, достижений, смены ника")
        print("✅ Таблица для статистики радёмок создана")
        
    finally:
        await conn.close()

# ==================== ИГРОВЫЕ ФУНКЦИИ (АСИНХРОННЫЕ) ====================

async def get_patsan(user_id: int) -> Optional[Dict[str, Any]]:
    """Асинхронно получаем пацана из базы, создаём нового если нет"""
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            'SELECT * FROM users WHERE user_id = ?', 
            (user_id,)
        )
        user_row = await cursor.fetchone()
        
        if user_row:
            user = dict(user_row)
            
            # Автоматическое восстановление атмосфер
            now = int(time.time())
            last = user.get("last_update", now)
            passed = now - last
            
            if passed >= ATM_TIME:
                new_atm = min(ATM_MAX, user["atm_count"] + (passed // ATM_TIME))
                if new_atm != user["atm_count"]:
                    user["atm_count"] = new_atm
                    user["last_update"] = now - (passed % ATM_TIME)
                    await conn.execute('''
                        UPDATE users SET atm_count = ?, last_update = ? 
                        WHERE user_id = ?
                    ''', (user["atm_count"], user["last_update"], user_id))
                    await conn.commit()
            
            # Преобразуем JSON строки обратно в Python объекты
            user["inventory"] = json.loads(user["inventory"]) if user["inventory"] else []
            user["upgrades"] = json.loads(user["upgrades"]) if user["upgrades"] else {}
            user["achievements"] = json.loads(user["achievements"]) if user.get("achievements") else []
            return user
        else:
            new_user = {
                "user_id": user_id,
                "nickname": f"Пацанчик_{user_id}",
                "avtoritet": 1,
                "zmiy": 0.0,
                "dengi": 100,
                "last_update": int(time.time()),
                "last_daily": 0,
                "atm_count": 12,
                "skill_davka": 1,
                "skill_zashita": 1,
                "skill_nahodka": 1,
                "inventory": ["двенашка"],
                "upgrades": {
                    "ryazhenka": False,
                    "tea_slivoviy": False,
                    "bubbleki": False,
                    "kuryasany": False
                },
                "achievements": [],
                "nickname_changed": False
            }
            
            await conn.execute('''
                INSERT INTO users 
                (user_id, nickname, avtoritet, zmiy, dengi, last_update, 
                 last_daily, atm_count, skill_davka, skill_zashita, skill_nahodka, 
                 inventory, upgrades, achievements, nickname_changed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_user["user_id"], new_user["nickname"], new_user["avtoritet"],
                new_user["zmiy"], new_user["dengi"], new_user["last_update"],
                new_user["last_daily"], new_user["atm_count"], new_user["skill_davka"], 
                new_user["skill_zashita"], new_user["skill_nahodka"], 
                json.dumps(new_user["inventory"]), 
                json.dumps(new_user["upgrades"]),
                json.dumps(new_user["achievements"]),
                new_user["nickname_changed"]
            ))
            
            await conn.commit()
            return new_user
    finally:
        await conn.close()

async def save_patsan(user_data: Dict[str, Any]):
    """Асинхронно сохраняем пацана в базу"""
    conn = await get_connection()
    try:
        await conn.execute('''
            UPDATE users SET
                nickname = ?, avtoritet = ?, zmiy = ?, dengi = ?,
                last_update = ?, last_daily = ?, atm_count = ?, 
                skill_davka = ?, skill_zashita = ?, skill_nahodka = ?, 
                inventory = ?, upgrades = ?, achievements = ?, nickname_changed = ?
            WHERE user_id = ?
        ''', (
            user_data.get("nickname"),
            user_data.get("avtoritet", 1),
            user_data.get("zmiy", 0.0),
            user_data.get("dengi", 100),
            user_data.get("last_update", int(time.time())),
            user_data.get("last_daily", 0),
            user_data.get("atm_count", 12),
            user_data.get("skill_davka", 1),
            user_data.get("skill_zashita", 1),
            user_data.get("skill_nahodka", 1),
            json.dumps(user_data.get("inventory", [])),
            json.dumps(user_data.get("upgrades", {})),
            json.dumps(user_data.get("achievements", [])),
            user_data.get("nickname_changed", False),
            user_data["user_id"]
        ))
        await conn.commit()
    finally:
        await conn.close()

async def davka_zmiy(user_id: int) -> Tuple[Optional[Dict[str, Any]], Any]:
    """Асинхронная обработка дачки коричневага"""
    patsan = await get_patsan(user_id)
    
    base_cost = 2
    if patsan["upgrades"].get("tea_slivoviy"):
        base_cost = max(1, base_cost - 1)
    
    if patsan["atm_count"] < base_cost:
        return None, "Не хватает атмосфер в кишке!"
    
    patsan["atm_count"] -= base_cost
    
    base_grams = random.randint(200, 1500)
    skill_bonus = patsan["skill_davka"] * 100
    
    if patsan["upgrades"].get("ryazhenka"):
        base_grams = int(base_grams * 1.5)
    
    total_grams = base_grams + skill_bonus
    patsan["zmiy"] += total_grams / 1000
    
    find_chance = patsan["skill_nahodka"] * 0.05
    if patsan["upgrades"].get("bubbleki"):
        find_chance += 0.2
    
    dvenashka_found = False
    if random.random() < find_chance:
        patsan["inventory"].append("двенашка")
        dvenashka_found = True
    
    await save_patsan(patsan)
    
    # Проверка достижений после дачки
    await check_achievements(user_id, "davka", {
        "total_grams": total_grams,
        "dvenashka_found": dvenashka_found
    })
    
    if total_grams >= 1000:
        kg = total_grams // 1000
        grams = total_grams % 1000
        if grams > 0:
            weight_msg = f"{kg} килограмм и {grams} грамм"
        else:
            weight_msg = f"{kg} килограмм"
    else:
        weight_msg = f"{total_grams} грамм"
    
    return patsan, {
        "cost": base_cost,
        "weight_msg": weight_msg,
        "total_grams": total_grams,
        "dvenashka_found": dvenashka_found
    }

async def sdat_zmiy(user_id: int) -> Tuple[Optional[Dict[str, Any]], Any]:
    """Асинхронная сдача змия на металл"""
    patsan = await get_patsan(user_id)
    
    if patsan["zmiy"] <= 0:
        return None, "Нечего сдавать!"
    
    price_per_kg = 50
    total_money = int(patsan["zmiy"] * price_per_kg)
    avtoritet_bonus = patsan["avtoritet"] * 5
    total_money += avtoritet_bonus
    
    old_zmiy = patsan["zmiy"]
    patsan["dengi"] += total_money
    patsan["zmiy"] = 0
    
    await save_patsan(patsan)
    
    # Проверка достижений после сдачи
    await check_achievements(user_id, "sdat", {
        "total_money": total_money,
        "old_zmiy": old_zmiy
    })
    
    return patsan, {
        "old_zmiy": old_zmiy,
        "total_money": total_money,
        "avtoritet_bonus": avtoritet_bonus
    }

async def buy_upgrade(user_id: int, upgrade: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Асинхронная покупка улучшения"""
    patsan = await get_patsan(user_id)
    
    prices = {
        "ryazhenka": 500,
        "tea_slivoviy": 700,
        "bubbleki": 600,
        "kuryasany": 1000
    }
    
    price = prices.get(upgrade)
    if not price:
        return None, "Нет такого нагнетателя!"
    
    if patsan["upgrades"].get(upgrade):
        return None, "Уже куплено!"
    
    if patsan["dengi"] < price:
        return None, "Не хватает бабла!"
    
    effect = ""
    if upgrade == "kuryasany":
        patsan["avtoritet"] += 1
        effect = " +1 авторитет!"
    
    patsan["dengi"] -= price
    patsan["upgrades"][upgrade] = True
    
    await save_patsan(patsan)
    
    # Проверка достижений после покупки
    await check_achievements(user_id, "buy_upgrade", {
        "upgrade": upgrade,
        "price": price
    })
    
    return patsan, f"Куплено за {price}р!{effect}"

async def pump_skill(user_id: int, skill: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Асинхронная прокачка скилла"""
    patsan = await get_patsan(user_id)
    
    skill_costs = {
        "davka": 200,
        "zashita": 300,
        "nahodka": 250
    }
    
    cost = skill_costs.get(skill, 200)
    
    if patsan["dengi"] < cost:
        return None, "Не хватает бабла!"
    
    patsan["dengi"] -= cost
    patsan[f"skill_{skill}"] += 1
    
    await save_patsan(patsan)
    
    # Проверка достижений после прокачки
    await check_achievements(user_id, "pump_skill", {
        "skill": skill,
        "level": patsan[f"skill_{skill}"]
    })
    
    return patsan, f"Прокачано за {cost}р!"

# ==================== НОВЫЕ ФУНКЦИИ: ЕЖЕДНЕВНЫЕ НАГРАДЫ ====================

async def get_daily_reward(user_id: int) -> Dict[str, Any]:
    """Выдача ежедневной награды"""
    conn = await get_connection()
    try:
        # Получаем данные пользователя
        cursor = await conn.execute('''
            SELECT last_daily, nickname, achievements FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            return {"success": False, "error": "Пользователь не найден"}
        
        now = int(time.time())
        last_daily = user["last_daily"] or 0
        
        # Проверяем, можно ли получить награду
        if last_daily > 0 and now - last_daily < 86400:  # 24 часа
            wait_hours = (86400 - (now - last_daily)) // 3600
            wait_minutes = ((86400 - (now - last_daily)) % 3600) // 60
            return {
                "success": False, 
                "wait_time": f"{wait_hours}ч {wait_minutes}м",
                "next_daily": last_daily + 86400
            }
        
        # Вычисляем стрик (последовательные дни)
        achievements = json.loads(user["achievements"]) if user["achievements"] else []
        streak_key = "daily_streak"
        current_streak = 1
        
        # Ищем информацию о стрике в достижениях
        for ach in achievements:
            if ach.get("id") == streak_key:
                current_streak = ach.get("value", 1) + 1
                break
        
        # Генерируем награду
        base_reward = 100
        
        # Бонус за стрик
        if current_streak >= 7:
            base_reward *= 3
            streak_bonus = " (x3 за недельный стрик!)"
        elif current_streak >= 3:
            base_reward *= 2
            streak_bonus = " (x2 за 3-дневный стрик!)"
        else:
            streak_bonus = ""
        
        # Случайный бонус
        random_bonus = random.randint(0, 100)
        total_reward = base_reward + random_bonus
        
        # Случайный предмет
        items = ["двенашка", "атмосфера", "перчатки", "швабра", "ведро"]
        weights = [0.4, 0.3, 0.15, 0.1, 0.05]
        reward_item = random.choices(items, weights=weights, k=1)[0]
        
        # Обновляем стрик в достижениях
        streak_updated = False
        new_achievements = []
        for ach in achievements:
            if ach.get("id") == streak_key:
                ach["value"] = current_streak
                ach["last_updated"] = now
                streak_updated = True
            new_achievements.append(ach)
        
        if not streak_updated:
            new_achievements.append({
                "id": streak_key,
                "name": f"Стрик {current_streak} дней",
                "value": current_streak,
                "last_updated": now
            })
        
        # Обновляем пользователя
        await conn.execute('''
            UPDATE users SET 
                dengi = dengi + ?,
                last_daily = ?,
                inventory = json_insert(
                    COALESCE(inventory, '[]'), 
                    '$[#]', 
                    ?
                ),
                achievements = ?
            WHERE user_id = ?
        ''', (total_reward, now, reward_item, json.dumps(new_achievements), user_id))
        
        await conn.commit()
        
        # Проверяем достижения за стрик
        if current_streak == 3:
            await unlock_achievement(user_id, "streak_3", "Трёхдневный стрик", 50)
        elif current_streak == 7:
            await unlock_achievement(user_id, "streak_7", "Недельный стрик", 200)
        elif current_streak == 30:
            await unlock_achievement(user_id, "streak_30", "Месяц без пропусков", 1000)
        
        return {
            "success": True, 
            "money": total_reward,
            "item": reward_item,
            "streak": current_streak,
            "streak_bonus": streak_bonus,
            "base": base_reward,
            "random_bonus": random_bonus
        }
        
    finally:
        await conn.close()

# ==================== НОВЫЕ ФУНКЦИИ: ДОСТИЖЕНИЯ ====================

async def check_achievements(user_id: int, action: str, data: Dict[str, Any]):
    """Проверка и разблокировка достижений после различных действий"""
    
    if action == "davka":
        total_grams = data.get("total_grams", 0)
        
        if total_grams >= 1000:
            await unlock_achievement(user_id, "first_kg", "Первый килограмм", 100)
        if total_grams >= 10000:
            await unlock_achievement(user_id, "10kg", "Десять кило говна", 500)
        if total_grams >= 100000:
            await unlock_achievement(user_id, "100kg", "Центнер говна", 2000)
        
        if data.get("dvenashka_found"):
            await unlock_achievement(user_id, "first_dvenashka", "Первая двенашка", 150)
    
    elif action == "sdat":
        total_money = data.get("total_money", 0)
        
        if total_money >= 1000:
            await unlock_achievement(user_id, "1000_money", "Тыща рублей", 200)
        if total_money >= 10000:
            await unlock_achievement(user_id, "10000_money", "Десять штук", 1000)
    
    elif action == "buy_upgrade":
        upgrade = data.get("upgrade", "")
        
        if upgrade == "kuryasany":
            await unlock_achievement(user_id, "buy_kuryasany", "Курвасаны с телотинкой", 300)
        
        # Проверяем, куплены ли все улучшения
        conn = await get_connection()
        try:
            cursor = await conn.execute('''
                SELECT upgrades FROM users WHERE user_id = ?
            ''', (user_id,))
            user = await cursor.fetchone()
            
            if user and user["upgrades"]:
                upgrades = json.loads(user["upgrades"])
                all_upgrades = ["ryazhenka", "tea_slivoviy", "bubbleki", "kuryasany"]
                
                if all(upgrades.get(upg, False) for upg in all_upgrades):
                    await unlock_achievement(user_id, "all_upgrades", "Все нагнетатели", 1000)
        finally:
            await conn.close()

async def unlock_achievement(user_id: int, achievement_id: str, name: str, reward: int = 0):
    """Разблокировка достижения и выдача награды"""
    conn = await get_connection()
    try:
        # Проверяем, не разблокировано ли уже
        cursor = await conn.execute('''
            SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id))
        
        existing = await cursor.fetchone()
        
        if existing:
            return False  # Уже разблокировано
        
        # Добавляем в таблицу достижений
        await conn.execute('''
            INSERT INTO achievements (user_id, achievement_id) 
            VALUES (?, ?)
        ''', (user_id, achievement_id))
        
        # Добавляем в список достижений пользователя
        cursor = await conn.execute('''
            SELECT achievements FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        achievements = json.loads(user["achievements"]) if user and user["achievements"] else []
        
        # Проверяем, нет ли уже такого достижения в списке
        for ach in achievements:
            if ach.get("id") == achievement_id:
                return False
        
        # Добавляем новое достижение
        achievements.append({
            "id": achievement_id,
            "name": name,
            "unlocked_at": int(time.time()),
            "reward": reward
        })
        
        # Выдаём награду, если есть
        if reward > 0:
            await conn.execute('''
                UPDATE users SET 
                    dengi = dengi + ?,
                    achievements = ?
                WHERE user_id = ?
            ''', (reward, json.dumps(achievements), user_id))
        else:
            await conn.execute('''
                UPDATE users SET achievements = ? WHERE user_id = ?
            ''', (json.dumps(achievements), user_id))
        
        await conn.commit()
        return True
        
    finally:
        await conn.close()

async def get_user_achievements(user_id: int) -> List[Dict[str, Any]]:
    """Получение списка достижений пользователя"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT achievements FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        if user and user["achievements"]:
            return json.loads(user["achievements"])
        return []
    finally:
        await conn.close()

# ==================== НОВЫЕ ФУНКЦИИ: СМЕНА НИКА ====================

async def change_nickname(user_id: int, new_nickname: str) -> Tuple[bool, str]:
    """Смена ника пользователя"""
    conn = await get_connection()
    try:
        # Проверяем пользователя
        cursor = await conn.execute('''
            SELECT nickname_changed, dengi FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            return False, "Пользователь не найден"
        
        nickname_changed = user["nickname_changed"]
        current_money = user["dengi"]
        
        # Проверяем, можно ли сменить бесплатно
        if not nickname_changed:
            # Первая смена - бесплатно
            await conn.execute('''
                UPDATE users SET 
                    nickname = ?,
                    nickname_changed = TRUE
                WHERE user_id = ?
            ''', (new_nickname, user_id))
            
            await conn.commit()
            await unlock_achievement(user_id, "first_nickname", "Первая бирка", 100)
            return True, "Ник успешно изменён! (первая смена бесплатно) +100р"
        
        # Не первая смена - проверяем деньги
        cost = 5000
        if current_money < cost:
            return False, f"Не хватает {cost - current_money}р для смены ника"
        
        # Списание денег и смена ника
        await conn.execute('''
            UPDATE users SET 
                nickname = ?,
                dengi = dengi - ?
            WHERE user_id = ?
        ''', (new_nickname, cost, user_id))
        
        await conn.commit()
        return True, f"Ник изменён! Списано {cost}р"
        
    finally:
        await conn.close()

# ==================== НОВАЯ ФУНКЦИЯ: СОХРАНЕНИЕ СТАТИСТИКИ РАДЁМКИ ====================

async def save_rademka_fight(winner_id: int, loser_id: int, money_taken: int = 0, item_stolen: str = None):
    """Сохранение статистики радёмки в базу"""
    conn = await get_connection()
    try:
        await conn.execute('''
            INSERT INTO rademka_fights (winner_id, loser_id, money_taken, item_stolen)
            VALUES (?, ?, ?, ?)
        ''', (winner_id, loser_id, money_taken, item_stolen))
        await conn.commit()
    finally:
        await conn.close()

# ==================== ФУНКЦИИ ДЛЯ КОРЗИНЫ (АСИНХРОННЫЕ) ====================

async def get_cart(user_id: int) -> List[Dict[str, Any]]:
    """Асинхронно получить корзину пользователя"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT item_name, quantity, price 
            FROM cart WHERE user_id = ?
        ''', (user_id,))
        
        cart_items = []
        rows = await cursor.fetchall()
        for row in rows:
            cart_items.append(dict(row))
        
        return cart_items
    finally:
        await conn.close()

async def add_to_cart(user_id: int, item_name: str, price: int, quantity: int = 1):
    """Асинхронно добавить товар в корзину"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        existing = await cursor.fetchone()
        
        if existing:
            new_quantity = existing["quantity"] + quantity
            await conn.execute('''
                UPDATE cart SET quantity = ? 
                WHERE user_id = ? AND item_name = ?
            ''', (new_quantity, user_id, item_name))
        else:
            await conn.execute('''
                INSERT INTO cart (user_id, item_name, price, quantity)
                VALUES (?, ?, ?, ?)
            ''', (user_id, item_name, price, quantity))
        
        await conn.commit()
    finally:
        await conn.close()

async def remove_from_cart(user_id: int, item_name: str, quantity: int = 1):
    """Асинхронно удалить товар из корзины"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        existing = await cursor.fetchone()
        if not existing:
            return
        
        current_qty = existing["quantity"]
        
        if current_qty <= quantity:
            await conn.execute('''
                DELETE FROM cart 
                WHERE user_id = ? AND item_name = ?
            ''', (user_id, item_name))
        else:
            await conn.execute('''
                UPDATE cart SET quantity = ? 
                WHERE user_id = ? AND item_name = ?
            ''', (current_qty - quantity, user_id, item_name))
        
        await conn.commit()
    finally:
        await conn.close()

async def clear_cart(user_id: int):
    """Асинхронно очистить корзину пользователя"""
    conn = await get_connection()
    try:
        await conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await conn.commit()
    finally:
        await conn.close()

async def get_cart_total(user_id: int) -> int:
    """Асинхронно получить общую стоимость корзины"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT SUM(price * quantity) as total 
            FROM cart WHERE user_id = ?
        ''', (user_id,))
        
        result = await cursor.fetchone()
        return result["total"] if result and result["total"] else 0
    finally:
        await conn.close()

# ==================== ФУНКЦИИ ДЛЯ ЗАКАЗОВ ====================

async def create_order(user_id: int, items: List[Dict], total: int) -> int:
    """Асинхронно создать заказ"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            INSERT INTO orders (user_id, items, total, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(items), total, 'новый'))
        
        order_id = cursor.lastrowid
        
        await clear_cart(user_id)
        
        await conn.commit()
        return order_id
    finally:
        await conn.close()

async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """Асинхронно получить историю заказов"""
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT id, items, total, status, created_at 
            FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        
        orders = []
        rows = await cursor.fetchall()
        for row in rows:
            order = dict(row)
            order["items"] = json.loads(order["items"])
            orders.append(order)
        
        return orders
    finally:
        await conn.close()

# ==================== ФУНКЦИЯ: ТОП ИГРОКОВ ====================

async def get_top_players(limit: int = 10, sort_by: str = "avtoritet") -> List[Dict[str, Any]]:
    """
    Асинхронно получить топ игроков по выбранному критерию.
    
    Args:
        limit: Количество игроков в топе (по умолчанию 10)
        sort_by: Поле для сортировки ('avtoritet', 'dengi', 'zmiy', 'total_skill')
    
    Returns:
        Список словарей с данными игроков, включая их ранг
    """
    conn = await get_connection()
    try:
        valid_columns = ["avtoritet", "dengi", "zmiy"]
        sort_column = sort_by if sort_by in valid_columns else "avtoritet"
        
        if sort_by == "total_skill":
            query = '''
                SELECT 
                    user_id,
                    nickname, 
                    avtoritet, 
                    dengi, 
                    zmiy,
                    skill_davka, 
                    skill_zashita, 
                    skill_nahodka,
                    (skill_davka + skill_zashita + skill_nahodka) as total_skill,
                    ROW_NUMBER() OVER (ORDER BY (skill_davka + skill_zashita + skill_nahodka) DESC) as rank
                FROM users 
                ORDER BY total_skill DESC 
                LIMIT ?
            '''
            cursor = await conn.execute(query, (limit,))
        else:
            query = f'''
                SELECT 
                    user_id,
                    nickname, 
                    avtoritet, 
                    dengi, 
                    zmiy,
                    skill_davka, 
                    skill_zashita, 
                    skill_nahodka,
                    (skill_davka + skill_zashita + skill_nahodka) as total_skill,
                    ROW_NUMBER() OVER (ORDER BY {sort_column} DESC) as rank
                FROM users 
                ORDER BY {sort_column} DESC 
                LIMIT ?
            '''
            cursor = await conn.execute(query, (limit,))
        
        top_players = []
        rows = await cursor.fetchall()
        for row in rows:
            player = dict(row)
            player["zmiy_formatted"] = f"{player['zmiy']:.1f}кг"
            player["dengi_formatted"] = f"{player['dengi']}р"
            top_players.append(player)
        
        return top_players
    finally:
        await conn.close()

# ==================== КЭШИРОВАНИЕ ====================

_user_cache = {}
_cache_lock = asyncio.Lock()

async def get_patsan_cached(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение пользователя с кэшированием (TTL: 30 секунд)"""
    async with _cache_lock:
        now = time.time()
        cache_key = f"user_{user_id}"
        
        if cache_key in _user_cache:
            user, timestamp = _user_cache[cache_key]
            if now - timestamp < 30:
                return user
        
        user = await get_patsan(user_id)
        if user:
            _user_cache[cache_key] = (user, now)
        
        if len(_user_cache) > 100:
            oldest_key = min(_user_cache.items(), key=lambda x: x[1][1])[0]
            del _user_cache[oldest_key]
        
        return user

async def invalidate_user_cache(user_id: int):
    """Сбросить кэш пользователя (после обновления данных)"""
    async with _cache_lock:
        cache_key = f"user_{user_id}"
        if cache_key in _user_cache:
            del _user_cache[cache_key]
