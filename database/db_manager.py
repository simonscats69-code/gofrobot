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
    # ИСПРАВЛЕНИЕ: правильное создание соединения
    conn = await aiosqlite.connect(DB_NAME)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_db():
    """Асинхронная инициализация базы данных: создаёт все таблицы"""
    # ИСПРАВЛЕНИЕ: используем отдельное соединение для инициализации
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
                atm_count INTEGER DEFAULT 12,
                skill_davka INTEGER DEFAULT 1,
                skill_zashita INTEGER DEFAULT 1,
                skill_nahodka INTEGER DEFAULT 1,
                inventory TEXT,
                upgrades TEXT,
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
        
        # Создаём индексы для быстрого поиска
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_cart_user_id ON cart(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
        
        await conn.commit()
        print("✅ База данных SQLite инициализирована (асинхронная версия)")
        
    finally:
        # Всегда закрываем соединение
        await conn.close()

# ==================== ИГРОВЫЕ ФУНКЦИИ (АСИНХРОННЫЕ) ====================

async def get_patsan(user_id: int) -> Optional[Dict[str, Any]]:
    """Асинхронно получаем пацана из базы, создаём нового если нет"""
    async with await get_connection() as conn:
        # Пытаемся найти пользователя
        cursor = await conn.execute(
            'SELECT * FROM users WHERE user_id = ?', 
            (user_id,)
        )
        user_row = await cursor.fetchone()
        
        if user_row:
            # Конвертируем Row в словарь
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
                    # Обновляем в базе
                    await conn.execute('''
                        UPDATE users SET atm_count = ?, last_update = ? 
                        WHERE user_id = ?
                    ''', (user["atm_count"], user["last_update"], user_id))
                    await conn.commit()
            
            # Преобразуем JSON строки обратно в Python объекты
            user["inventory"] = json.loads(user["inventory"]) if user["inventory"] else []
            user["upgrades"] = json.loads(user["upgrades"]) if user["upgrades"] else {}
            return user
        else:
            # Новый пацан с гофроцентрала
            new_user = {
                "user_id": user_id,
                "nickname": f"Пацанчик_{user_id}",
                "avtoritet": 1,
                "zmiy": 0.0,
                "dengi": 100,
                "last_update": int(time.time()),
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
                }
            }
            
            # Вставляем нового пользователя
            await conn.execute('''
                INSERT INTO users 
                (user_id, nickname, avtoritet, zmiy, dengi, last_update, 
                 atm_count, skill_davka, skill_zashita, skill_nahodka, inventory, upgrades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_user["user_id"], new_user["nickname"], new_user["avtoritet"],
                new_user["zmiy"], new_user["dengi"], new_user["last_update"],
                new_user["atm_count"], new_user["skill_davka"], new_user["skill_zashita"],
                new_user["skill_nahodka"], 
                json.dumps(new_user["inventory"]), 
                json.dumps(new_user["upgrades"])
            ))
            
            await conn.commit()
            return new_user

async def save_patsan(user_data: Dict[str, Any]):
    """Асинхронно сохраняем пацана в базу"""
    async with await get_connection() as conn:
        await conn.execute('''
            UPDATE users SET
                nickname = ?, avtoritet = ?, zmiy = ?, dengi = ?,
                last_update = ?, atm_count = ?, skill_davka = ?,
                skill_zashita = ?, skill_nahodka = ?, inventory = ?, upgrades = ?
            WHERE user_id = ?
        ''', (
            user_data.get("nickname"),
            user_data.get("avtoritet", 1),
            user_data.get("zmiy", 0.0),
            user_data.get("dengi", 100),
            user_data.get("last_update", int(time.time())),
            user_data.get("atm_count", 12),
            user_data.get("skill_davka", 1),
            user_data.get("skill_zashita", 1),
            user_data.get("skill_nahodka", 1),
            json.dumps(user_data.get("inventory", [])),
            json.dumps(user_data.get("upgrades", {})),
            user_data["user_id"]
        ))
        await conn.commit()

async def davka_zmiy(user_id: int) -> Tuple[Optional[Dict[str, Any]], Any]:
    """Асинхронная обработка дачки коричневага"""
    patsan = await get_patsan(user_id)
    
    # Базовый расход атмосфер
    base_cost = 2
    if patsan["upgrades"].get("tea_slivoviy"):
        base_cost = max(1, base_cost - 1)
    
    if patsan["atm_count"] < base_cost:
        return None, "Не хватает атмосфер в кишке!"
    
    patsan["atm_count"] -= base_cost
    
    # Генерируем вес змия
    base_grams = random.randint(200, 1500)
    
    # Бонус от скилла
    skill_bonus = patsan["skill_davka"] * 100
    
    # Бонус от "ряженки"
    if patsan["upgrades"].get("ryazhenka"):
        base_grams = int(base_grams * 1.5)
    
    total_grams = base_grams + skill_bonus
    
    # Добавляем змия
    patsan["zmiy"] += total_grams / 1000
    
    # Проверка на двенашку
    find_chance = patsan["skill_nahodka"] * 0.05
    if patsan["upgrades"].get("bubbleki"):
        find_chance += 0.2
    
    dvenashka_found = False
    if random.random() < find_chance:
        patsan["inventory"].append("двенашка")
        dvenashka_found = True
    
    await save_patsan(patsan)
    
    # Форматируем вес для сообщения
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
    
    # Бонус за авторитет
    avtoritet_bonus = patsan["avtoritet"] * 5
    total_money += avtoritet_bonus
    
    old_zmiy = patsan["zmiy"]
    patsan["dengi"] += total_money
    patsan["zmiy"] = 0
    
    await save_patsan(patsan)
    
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
    
    # Особый эффект для курвасанов
    effect = ""
    if upgrade == "kuryasany":
        patsan["avtoritet"] += 1
        effect = " +1 авторитет!"
    
    patsan["dengi"] -= price
    patsan["upgrades"][upgrade] = True
    
    await save_patsan(patsan)
    
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
    
    return patsan, f"Прокачано за {cost}р!"

# ==================== ФУНКЦИИ ДЛЯ КОРЗИНЫ (АСИНХРОННЫЕ) ====================

async def get_cart(user_id: int) -> List[Dict[str, Any]]:
    """Асинхронно получить корзину пользователя"""
    async with await get_connection() as conn:
        cursor = await conn.execute('''
            SELECT item_name, quantity, price 
            FROM cart WHERE user_id = ?
        ''', (user_id,))
        
        cart_items = []
        rows = await cursor.fetchall()
        for row in rows:
            cart_items.append(dict(row))
        
        return cart_items

async def add_to_cart(user_id: int, item_name: str, price: int, quantity: int = 1):
    """Асинхронно добавить товар в корзину"""
    async with await get_connection() as conn:
        # Проверяем, есть ли уже такой товар
        cursor = await conn.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        existing = await cursor.fetchone()
        
        if existing:
            # Обновляем количество
            new_quantity = existing["quantity"] + quantity
            await conn.execute('''
                UPDATE cart SET quantity = ? 
                WHERE user_id = ? AND item_name = ?
            ''', (new_quantity, user_id, item_name))
        else:
            # Добавляем новый товар
            await conn.execute('''
                INSERT INTO cart (user_id, item_name, price, quantity)
                VALUES (?, ?, ?, ?)
            ''', (user_id, item_name, price, quantity))
        
        await conn.commit()

async def remove_from_cart(user_id: int, item_name: str, quantity: int = 1):
    """Асинхронно удалить товар из корзины"""
    async with await get_connection() as conn:
        # Получаем текущее количество
        cursor = await conn.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        existing = await cursor.fetchone()
        if not existing:
            return
        
        current_qty = existing["quantity"]
        
        if current_qty <= quantity:
            # Удаляем товар полностью
            await conn.execute('''
                DELETE FROM cart 
                WHERE user_id = ? AND item_name = ?
            ''', (user_id, item_name))
        else:
            # Уменьшаем количество
            await conn.execute('''
                UPDATE cart SET quantity = ? 
                WHERE user_id = ? AND item_name = ?
            ''', (current_qty - quantity, user_id, item_name))
        
        await conn.commit()

async def clear_cart(user_id: int):
    """Асинхронно очистить корзину пользователя"""
    async with await get_connection() as conn:
        await conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await conn.commit()

async def get_cart_total(user_id: int) -> int:
    """Асинхронно получить общую стоимость корзины"""
    async with await get_connection() as conn:
        cursor = await conn.execute('''
            SELECT SUM(price * quantity) as total 
            FROM cart WHERE user_id = ?
        ''', (user_id,))
        
        result = await cursor.fetchone()
        return result["total"] if result and result["total"] else 0

# ==================== ФУНКЦИИ ДЛЯ ЗАКАЗОВ ====================

async def create_order(user_id: int, items: List[Dict], total: int) -> int:
    """Асинхронно создать заказ"""
    async with await get_connection() as conn:
        # Вставляем заказ
        cursor = await conn.execute('''
            INSERT INTO orders (user_id, items, total, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(items), total, 'новый'))
        
        order_id = cursor.lastrowid
        
        # Очищаем корзину
        await clear_cart(user_id)
        
        await conn.commit()
        return order_id

async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """Асинхронно получить историю заказов"""
    async with await get_connection() as conn:
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

# ==================== НОВАЯ ФУНКЦИЯ: ТОП ИГРОКОВ ====================

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
        # Безопасная проверка поля для сортировки (защита от SQL-инъекций)
        valid_columns = ["avtoritet", "dengi", "zmiy"]
        sort_column = sort_by if sort_by in valid_columns else "avtoritet"
        
        # Если нужен топ по скиллам, используем особый запрос
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
            # Форматируем значения для красоты
            player["zmiy_formatted"] = f"{player['zmiy']:.1f}кг"
            player["dengi_formatted"] = f"{player['dengi']}р"
            top_players.append(player)
        
        return top_players
    finally:
        await conn.close()

# ==================== КЭШИРОВАНИЕ ====================

# Простой in-memory кэш для пользователей
_user_cache = {}
_cache_lock = asyncio.Lock()

async def get_patsan_cached(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение пользователя с кэшированием (TTL: 30 секунд)"""
    async with _cache_lock:
        now = time.time()
        cache_key = f"user_{user_id}"
        
        # Проверяем кэш
        if cache_key in _user_cache:
            user, timestamp = _user_cache[cache_key]
            if now - timestamp < 30:  # Кэш живёт 30 секунд
                return user
        
        # Получаем из БД
        user = await get_patsan(user_id)
        if user:
            _user_cache[cache_key] = (user, now)
        
        # Очищаем старый кэш (больше 100 записей)
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
