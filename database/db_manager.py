import sqlite3
import time
import random
import json
from typing import Optional, List, Dict, Any

ATM_MAX = 12
ATM_TIME = 600

DB_NAME = "bot_database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            UNIQUE(user_id, item_name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            total INTEGER NOT NULL,
            status TEXT DEFAULT 'новый',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных SQLite инициализирована")

def get_patsan(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_row = cursor.fetchone()
    
    if user_row:
        user = dict(user_row)
        
        now = int(time.time())
        last = user.get("last_update", now)
        passed = now - last
        
        if passed >= ATM_TIME:
            new_atm = min(ATM_MAX, user["atm_count"] + (passed // ATM_TIME))
            if new_atm != user["atm_count"]:
                user["atm_count"] = new_atm
                user["last_update"] = now - (passed % ATM_TIME)
                cursor.execute('''
                    UPDATE users SET atm_count = ?, last_update = ? 
                    WHERE user_id = ?
                ''', (user["atm_count"], user["last_update"], user_id))
                conn.commit()
        
        conn.close()
        
        user["inventory"] = json.loads(user["inventory"]) if user["inventory"] else []
        user["upgrades"] = json.loads(user["upgrades"]) if user["upgrades"] else {}
        return user
    else:
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
        
        cursor.execute('''
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
        
        conn.commit()
        conn.close()
        return new_user

def save_patsan(user_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
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
    
    conn.commit()
    conn.close()

def davka_zmiy(patsan: dict):
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
    
    save_patsan(patsan)
    
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

def sdat_zmiy(patsan: dict):
    if patsan["zmiy"] <= 0:
        return None, "Нечего сдавать!"
    
    price_per_kg = 50
    total_money = int(patsan["zmiy"] * price_per_kg)
    
    avtoritet_bonus = patsan["avtoritet"] * 5
    total_money += avtoritet_bonus
    
    old_zmiy = patsan["zmiy"]
    patsan["dengi"] += total_money
    patsan["zmiy"] = 0
    
    save_patsan(patsan)
    
    return patsan, {
        "old_zmiy": old_zmiy,
        "total_money": total_money,
        "avtoritet_bonus": avtoritet_bonus
    }

def buy_upgrade(patsan: dict, upgrade: str):
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
    
    save_patsan(patsan)
    
    return patsan, f"Куплено за {price}р!{effect}"

def pump_skill(patsan: dict, skill: str):
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
    
    save_patsan(patsan)
    
    return patsan, f"Прокачано за {cost}р!"

def get_cart(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT item_name, quantity, price 
        FROM cart WHERE user_id = ?
    ''', (user_id,))
    
    cart_items = []
    for row in cursor.fetchall():
        cart_items.append(dict(row))
    
    conn.close()
    return cart_items

def add_to_cart(user_id: int, item_name: str, price: int, quantity: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT quantity FROM cart 
        WHERE user_id = ? AND item_name = ?
    ''', (user_id, item_name))
    
    existing = cursor.fetchone()
    
    if existing:
        new_quantity = existing["quantity"] + quantity
        cursor.execute('''
            UPDATE cart SET quantity = ? 
            WHERE user_id = ? AND item_name = ?
        ''', (new_quantity, user_id, item_name))
    else:
        cursor.execute('''
            INSERT INTO cart (user_id, item_name, price, quantity)
            VALUES (?, ?, ?, ?)
        ''', (user_id, item_name, price, quantity))
    
    conn.commit()
    conn.close()

def remove_from_cart(user_id: int, item_name: str, quantity: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT quantity FROM cart 
        WHERE user_id = ? AND item_name = ?
    ''', (user_id, item_name))
    
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return
    
    current_qty = existing["quantity"]
    
    if current_qty <= quantity:
        cursor.execute('''
            DELETE FROM cart 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
    else:
        cursor.execute('''
            UPDATE cart SET quantity = ? 
            WHERE user_id = ? AND item_name = ?
        ''', (current_qty - quantity, user_id, item_name))
    
    conn.commit()
    conn.close()

def clear_cart(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_cart_total(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT SUM(price * quantity) as total 
        FROM cart WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result["total"] if result["total"] else 0

def create_order(user_id: int, items: List[Dict], total: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO orders (user_id, items, total, status)
        VALUES (?, ?, ?, ?)
    ''', (user_id, json.dumps(items), total, 'новый'))
    
    order_id = cursor.lastrowid
    
    clear_cart(user_id)
    
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, items, total, status, created_at 
        FROM orders WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    
    orders = []
    for row in cursor.fetchall():
        order = dict(row)
        order["items"] = json.loads(order["items"])
        orders.append(order)
    
    conn.close()
    return orders
