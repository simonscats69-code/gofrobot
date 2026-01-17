import asyncio
import time
import random
import json
from typing import Optional, List, Dict, Any, Tuple
import aiosqlite

ATM_MAX = 12
ATM_TIME = 600
DB_NAME = "bot_database.db"

RANKS = {
    1: ("Пацанчик", "👶"),
    11: ("Браток", "👊"),
    51: ("Авторитет", "👑"),
    201: ("Царь гофры", "🐉"),
    501: ("Император гофроцентрала", "🏛️"),
    1001: ("БОГ ГОВНА", "💩")
}

SPECIALIZATIONS = {
    "давила": {
        "name": "Давила",
        "description": "Мастер давления коричневага",
        "requirements": {"skill_davka": 5, "zmiy": 50.0},
        "price": 1500,
        "bonuses": {
            "davka_multiplier": 1.5,
            "atm_cost_reduction": 1,
            "unlocks": ["гигантская_давка"]
        }
    },
    "охотник": {
        "name": "Охотник за двенашками",
        "description": "Находит то, что другие не видят",
        "requirements": {"skill_nahodka": 5, "inventory_contains": "двенашка"},
        "price": 1200,
        "bonuses": {
            "find_chance_bonus": 0.15,
            "rare_find_chance": 0.05,
            "unlocks": ["детектор_двенашек"]
        }
    },
    "непробиваемый": {
        "name": "Непробиваемый",
        "description": "Железные кишки и стальные нервы",
        "requirements": {"skill_zashita": 5, "avtoritet": 20},
        "price": 2000,
        "bonuses": {
            "atm_regen_bonus": 0.9,
            "rademka_defense": 0.15,
            "unlocks": ["железный_живот"]
        }
    }
}

CRAFT_RECIPES = {
    "супер_двенашка": {
        "name": "Супер-двенашка",
        "description": "Повышает удачу на 1 час",
        "ingredients": {"двенашка": 3, "деньги": 500},
        "result": {"item": "супер_двенашка", "quantity": 1, "duration": 3600},
        "success_chance": 1.0
    },
    "вечный_двигатель": {
        "name": "Вечный двигатель",
        "description": "Ускоряет восстановление атмосфер",
        "ingredients": {"атмосфера": 5, "энергетик": 1},
        "result": {"item": "вечный_двигатель", "quantity": 1, "duration": 86400},
        "success_chance": 0.8
    },
    "царский_обед": {
        "name": "Царский обед",
        "description": "Максимальный буст на 30 минут",
        "ingredients": {"курвасаны": 1, "ряженка": 1, "деньги": 300},
        "result": {"item": "царский_обед", "quantity": 1, "duration": 1800},
        "success_chance": 1.0
    },
    "бустер_атмосфер": {
        "name": "Бустер атмосфер",
        "description": "+3 к максимальному запасу атмосфер",
        "ingredients": {"энергетик": 2, "двенашка": 1, "деньги": 2000},
        "result": {"item": "буster_атмосфер", "quantity": 1},
        "success_chance": 0.7
    }
}

LEVELED_ACHIEVEMENTS = {
    "zmiy_collector": {
        "name": "Коллекционер змия",
        "levels": [
            {"goal": 10, "reward": 50, "title": "Новичок", "exp": 10},
            {"goal": 100, "reward": 300, "title": "Любитель", "exp": 50},
            {"goal": 1000, "reward": 1500, "title": "Профессионал", "exp": 200},
            {"goal": 10000, "reward": 5000, "title": "КОРОЛЬ ГОФРОЦЕНТРАЛА", "exp": 1000}
        ]
    },
    "money_maker": {
        "name": "Денежный мешок",
        "levels": [
            {"goal": 1000, "reward": 100, "title": "Бедолага", "exp": 10},
            {"goal": 10000, "reward": 1000, "title": "Состоятельный", "exp": 100},
            {"goal": 100000, "reward": 5000, "title": "Олигарх", "exp": 500},
            {"goal": 1000000, "reward": 25000, "title": "РОТШИЛЬД", "exp": 2500}
        ]
    },
    "rademka_king": {
        "name": "Король радёмок",
        "levels": [
            {"goal": 5, "reward": 200, "title": "Задира", "exp": 20},
            {"goal": 25, "reward": 1000, "title": "Гроза района", "exp": 100},
            {"goal": 100, "reward": 5000, "title": "Неприкасаемый", "exp": 500},
            {"goal": 500, "reward": 25000, "title": "ЛЕГЕНДА РАДЁМКИ", "exp": 2500}
        ]
    }
}

async def get_connection():
    conn = await aiosqlite.connect(DB_NAME)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_db():
    conn = await aiosqlite.connect(DB_NAME)
    
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                nickname TEXT,
                avtoritet INTEGER DEFAULT 1,
                zmiy REAL DEFAULT 0.0,
                dengi INTEGER DEFAULT 100,
                last_update INTEGER,
                last_daily INTEGER DEFAULT 0,
                atm_count INTEGER DEFAULT 12,
                max_atm INTEGER DEFAULT 12,
                skill_davka INTEGER DEFAULT 1,
                skill_zashita INTEGER DEFAULT 1,
                skill_nahodka INTEGER DEFAULT 1,
                specialization TEXT DEFAULT '',
                experience INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                inventory TEXT,
                upgrades TEXT,
                active_boosts TEXT DEFAULT '{}',
                achievements TEXT DEFAULT '[]',
                nickname_changed BOOLEAN DEFAULT FALSE,
                crafted_items TEXT DEFAULT '[]',
                rademka_scouts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS achievement_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                progress REAL DEFAULT 0,
                current_level INTEGER DEFAULT 0,
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS stolen_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thief_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                stolen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS craft_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id TEXT NOT NULL,
                success BOOLEAN,
                crafted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS rademka_fights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                winner_id INTEGER NOT NULL,
                loser_id INTEGER NOT NULL,
                money_taken INTEGER DEFAULT 0,
                item_stolen TEXT,
                scouted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        indexes = [
            ('idx_users_user_id', 'users(user_id)'),
            ('idx_users_specialization', 'users(specialization)'),
            ('idx_achievement_progress', 'achievement_progress(user_id, achievement_id)'),
            ('idx_stolen_items', 'stolen_items(thief_id, victim_id)'),
            ('idx_craft_history', 'craft_history(user_id)'),
            ('idx_cart_user_id', 'cart(user_id)'),
            ('idx_orders_user_id', 'orders(user_id)'),
            ('idx_rademka_winner', 'rademka_fights(winner_id)'),
            ('idx_rademka_loser', 'rademka_fights(loser_id)'),
            ('idx_rademka_scouted', 'rademka_fights(scouted)')
        ]
        
        for idx_name, idx_query in indexes:
            await conn.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_query}')
        
        await conn.commit()
        print("✅ База данных инициализирована с новыми функциями")
        print("✅ Добавлены: специализации, уровни, крафт, прогресс достижений")
        
    finally:
        await conn.close()

def get_rank(avtoritet: int) -> Tuple[str, str]:
    for threshold, (name, emoji) in sorted(RANKS.items(), reverse=True):
        if avtoritet >= threshold:
            return name, emoji
    return "Пацанчик", "👶"

def calculate_atm_regen_time(user_data: Dict[str, Any]) -> int:
    base_time = ATM_TIME
    
    if user_data.get("skill_zashita", 1) >= 10:
        base_time *= 0.9
    
    if user_data.get("specialization") == "непробиваемый":
        base_time *= 0.9
    
    boosts = user_data.get("active_boosts", {})
    if boosts.get("вечный_двигатель"):
        base_time *= 0.7
    
    return int(max(60, base_time))

def get_specialization_bonuses(specialization: str) -> Dict[str, Any]:
    spec = SPECIALIZATIONS.get(specialization, {})
    return spec.get("bonuses", {})

async def get_patsan(user_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            'SELECT * FROM users WHERE user_id = ?', 
            (user_id,)
        )
        user_row = await cursor.fetchone()
        
        if user_row:
            user = dict(user_row)
            
            now = int(time.time())
            last = user.get("last_update", now)
            passed = now - last
            
            regen_time = calculate_atm_regen_time(user)
            if passed >= regen_time:
                new_atm = min(
                    user.get("max_atm", ATM_MAX),
                    user["atm_count"] + (passed // regen_time)
                )
                if new_atm != user["atm_count"]:
                    user["atm_count"] = new_atm
                    user["last_update"] = now - (passed % regen_time)
                    await conn.execute('''
                        UPDATE users SET atm_count = ?, last_update = ? 
                        WHERE user_id = ?
                    ''', (user["atm_count"], user["last_update"], user_id))
                    await conn.commit()
            
            user["inventory"] = json.loads(user["inventory"]) if user["inventory"] else []
            user["upgrades"] = json.loads(user["upgrades"]) if user["upgrades"] else {}
            user["achievements"] = json.loads(user["achievements"]) if user.get("achievements") else []
            user["active_boosts"] = json.loads(user["active_boosts"]) if user.get("active_boosts") else {}
            user["crafted_items"] = json.loads(user["crafted_items"]) if user.get("crafted_items") else []
            
            user["rank_name"], user["rank_emoji"] = get_rank(user["avtoritet"])
            
            return user
        else:
            new_user = {
                "user_id": user_id,
                "nickname": f"Пацанчик_{user_id}",
                "avtoritet": 1,
                "zmiy": 0.0,
                "dengi": 150,
                "last_update": int(time.time()),
                "last_daily": 0,
                "atm_count": 12,
                "max_atm": 12,
                "skill_davka": 1,
                "skill_zashita": 1,
                "skill_nahodka": 1,
                "specialization": "",
                "experience": 0,
                "level": 1,
                "inventory": ["двенашка", "энергетик"],
                "upgrades": {
                    "ryazhenka": False,
                    "tea_slivoviy": False,
                    "bubbleki": False,
                    "kuryasany": False
                },
                "active_boosts": {},
                "achievements": [],
                "nickname_changed": False,
                "crafted_items": [],
                "rademka_scouts": 0,
                "rank_name": "Пацанчик",
                "rank_emoji": "👶"
            }
            
            await conn.execute('''
                INSERT INTO users 
                (user_id, nickname, avtoritet, zmiy, dengi, last_update, 
                 last_daily, atm_count, max_atm, skill_davka, skill_zashita, skill_nahodka,
                 specialization, experience, level, inventory, upgrades, active_boosts,
                 achievements, nickname_changed, crafted_items, rademka_scouts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_user["user_id"], new_user["nickname"], new_user["avtoritet"],
                new_user["zmiy"], new_user["dengi"], new_user["last_update"],
                new_user["last_daily"], new_user["atm_count"], new_user["max_atm"],
                new_user["skill_davka"], new_user["skill_zashita"], new_user["skill_nahodka"],
                new_user["specialization"], new_user["experience"], new_user["level"],
                json.dumps(new_user["inventory"]), 
                json.dumps(new_user["upgrades"]),
                json.dumps(new_user["active_boosts"]),
                json.dumps(new_user["achievements"]),
                new_user["nickname_changed"],
                json.dumps(new_user["crafted_items"]),
                new_user["rademka_scouts"]
            ))
            
            await conn.commit()
            return new_user
    finally:
        await conn.close()

async def save_patsan(user_data: Dict[str, Any]):
    conn = await get_connection()
    try:
        await conn.execute('''
            UPDATE users SET
                nickname = ?, avtoritet = ?, zmiy = ?, dengi = ?,
                last_update = ?, last_daily = ?, atm_count = ?, max_atm = ?,
                skill_davka = ?, skill_zashita = ?, skill_nahodka = ?,
                specialization = ?, experience = ?, level = ?,
                inventory = ?, upgrades = ?, active_boosts = ?,
                achievements = ?, nickname_changed = ?, crafted_items = ?,
                rademka_scouts = ?
            WHERE user_id = ?
        ''', (
            user_data.get("nickname"),
            user_data.get("avtoritet", 1),
            user_data.get("zmiy", 0.0),
            user_data.get("dengi", 150),
            user_data.get("last_update", int(time.time())),
            user_data.get("last_daily", 0),
            user_data.get("atm_count", 12),
            user_data.get("max_atm", 12),
            user_data.get("skill_davka", 1),
            user_data.get("skill_zashita", 1),
            user_data.get("skill_nahodka", 1),
            user_data.get("specialization", ""),
            user_data.get("experience", 0),
            user_data.get("level", 1),
            json.dumps(user_data.get("inventory", [])),
            json.dumps(user_data.get("upgrades", {})),
            json.dumps(user_data.get("active_boosts", {})),
            json.dumps(user_data.get("achievements", [])),
            user_data.get("nickname_changed", False),
            json.dumps(user_data.get("crafted_items", [])),
            user_data.get("rademka_scouts", 0),
            user_data["user_id"]
        ))
        await conn.commit()
    finally:
        await conn.close()

async def davka_zmiy(user_id: int) -> Tuple[Optional[Dict[str, Any]], Any]:
    patsan = await get_patsan(user_id)
    
    base_cost = 2
    
    if patsan["upgrades"].get("tea_slivoviy"):
        base_cost = max(1, base_cost - 1)
    
    bonuses = get_specialization_bonuses(patsan.get("specialization", ""))
    if bonuses.get("atm_cost_reduction"):
        base_cost = max(1, base_cost - bonuses["atm_cost_reduction"])
    
    if patsan["atm_count"] < base_cost:
        return None, "Не хватает атмосфер в кишке!"
    
    patsan["atm_count"] -= base_cost
    
    base_grams = random.randint(200, 1500)
    skill_bonus = patsan["skill_davka"] * 100
    
    multiplier = 1.0
    if patsan["upgrades"].get("ryazhenka"):
        multiplier = 1.75
    
    if bonuses.get("davka_multiplier"):
        multiplier *= bonuses["davka_multiplier"]
    
    base_grams = int(base_grams * multiplier)
    total_grams = base_grams + skill_bonus
    
    exp_gained = min(10, total_grams // 100)
    patsan["experience"] += exp_gained
    await check_level_up(patsan)
    
    patsan["zmiy"] += total_grams / 1000
    
    find_chance = patsan["skill_nahodka"] * 0.05
    
    if patsan["upgrades"].get("bubbleki"):
        find_chance += 0.35
    
    if bonuses.get("find_chance_bonus"):
        find_chance += bonuses["find_chance_bonus"]
    
    dvenashka_found = False
    rare_item_found = None
    
    if random.random() < find_chance:
        patsan["inventory"].append("двенашка")
        dvenashka_found = True
        
        if bonuses.get("rare_find_chance") and random.random() < bonuses["rare_find_chance"]:
            rare_items = ["золотая_двенашка", "кристалл_атмосферы", "секретная_схема"]
            rare_item = random.choice(rare_items)
            patsan["inventory"].append(rare_item)
            rare_item_found = rare_item
    
    await save_patsan(patsan)
    
    await update_achievement_progress(user_id, "zmiy_collector", total_grams / 1000)
    
    if total_grams >= 1000:
        kg = total_grams // 1000
        grams = total_grams % 1000
        weight_msg = f"{kg}кг {grams}г" if grams > 0 else f"{kg}кг"
    else:
        weight_msg = f"{total_grams}г"
    
    result_data = {
        "cost": base_cost,
        "weight_msg": weight_msg,
        "total_grams": total_grams,
        "dvenashka_found": dvenashka_found,
        "rare_item_found": rare_item_found,
        "exp_gained": exp_gained
    }
    
    if rare_item_found:
        result_data["rare_item"] = rare_item_found
    
    return patsan, result_data

async def buy_specialization(user_id: int, specialization: str) -> Tuple[bool, str]:
    patsan = await get_patsan(user_id)
    
    if not specialization in SPECIALIZATIONS:
        return False, "Неизвестная специализация"
    
    spec = SPECIALIZATIONS[specialization]
    
    for req_key, req_value in spec["requirements"].items():
        if req_key == "inventory_contains":
            if req_value not in patsan.get("inventory", []):
                return False, f"Нужен предмет: {req_value}"
        elif patsan.get(req_key, 0) < req_value:
            return False, f"Недостаточно {req_key}: нужно {req_value}"
    
    if patsan["dengi"] < spec["price"]:
        return False, f"Не хватает {spec['price'] - patsan['dengi']}р"
    
    if patsan.get("specialization"):
        return False, "У тебя уже есть специализация. Можно иметь только одну."
    
    patsan["dengi"] -= spec["price"]
    patsan["specialization"] = specialization
    
    await unlock_achievement(user_id, "first_specialization", "Первая специализация", 500)
    
    await save_patsan(patsan)
    return True, f"✅ Куплена специализация '{spec['name']}' за {spec['price']}р!"

async def get_available_specializations(user_id: int) -> List[Dict[str, Any]]:
    patsan = await get_patsan(user_id)
    available = []
    
    for spec_id, spec_data in SPECIALIZATIONS.items():
        meets_requirements = True
        missing = []
        
        for req_key, req_value in spec_data["requirements"].items():
            if req_key == "inventory_contains":
                if req_value not in patsan.get("inventory", []):
                    meets_requirements = False
                    missing.append(f"Предмет: {req_value}")
            elif patsan.get(req_key, 0) < req_value:
                meets_requirements = False
                missing.append(f"{req_key}: {patsan.get(req_key, 0)}/{req_value}")
        
        available.append({
            "id": spec_id,
            "name": spec_data["name"],
            "description": spec_data["description"],
            "price": spec_data["price"],
            "available": meets_requirements,
            "missing": missing,
            "bonuses": spec_data["bonuses"]
        })
    
    return available

async def craft_item(user_id: int, recipe_id: str) -> Tuple[bool, str, Dict]:
    patsan = await get_patsan(user_id)
    
    if recipe_id not in CRAFT_RECIPES:
        return False, "Неизвестный рецепт", {}
    
    recipe = CRAFT_RECIPES[recipe_id]
    
    inventory = patsan.get("inventory", [])
    inventory_count = {}
    for item in inventory:
        inventory_count[item] = inventory_count.get(item, 0) + 1
    
    missing = []
    for item_name, needed in recipe["ingredients"].items():
        if item_name == "деньги":
            if patsan["dengi"] < needed:
                missing.append(f"Деньги: {needed}р")
        elif inventory_count.get(item_name, 0) < needed:
            missing.append(f"{item_name}: {inventory_count.get(item_name, 0)}/{needed}")
    
    if missing:
        return False, f"Не хватает: {', '.join(missing)}", {}
    
    for item_name, needed in recipe["ingredients"].items():
        if item_name == "деньги":
            patsan["dengi"] -= needed
        else:
            for _ in range(needed):
                if item_name in patsan["inventory"]:
                    patsan["inventory"].remove(item_name)
    
    success = random.random() < recipe["success_chance"]
    
    if success:
        result = recipe["result"]
        
        if result.get("item"):
            patsan["inventory"].append(result["item"])
            
            if result.get("duration"):
                patsan["active_boosts"][result["item"]] = int(time.time()) + result["duration"]
        
        crafted = patsan.get("crafted_items", [])
        crafted.append({
            "recipe": recipe_id,
            "item": result.get("item", ""),
            "time": int(time.time())
        })
        patsan["crafted_items"] = crafted
        
        await unlock_achievement(user_id, "first_craft", "Первый крафт", 100)
        
        message = f"✅ Успешно скрафчено: {recipe['name']}!"
    else:
        message = f"❌ Неудачная попытка крафта {recipe['name']}... Ингредиенты потеряны."
    
    conn = await get_connection()
    try:
        await conn.execute('''
            INSERT INTO craft_history (user_id, recipe_id, success)
            VALUES (?, ?, ?)
        ''', (user_id, recipe_id, success))
        await conn.commit()
    finally:
        await conn.close()
    
    await save_patsan(patsan)
    return success, message, recipe.get("result", {})

async def get_craftable_items(user_id: int) -> List[Dict[str, Any]]:
    patsan = await get_patsan(user_id)
    inventory = patsan.get("inventory", [])
    inventory_count = {}
    
    for item in inventory:
        inventory_count[item] = inventory_count.get(item, 0) + 1
    
    craftable = []
    
    for recipe_id, recipe in CRAFT_RECIPES.items():
        can_craft = True
        missing = []
        
        for item_name, needed in recipe["ingredients"].items():
            if item_name == "деньги":
                if patsan["dengi"] < needed:
                    can_craft = False
                    missing.append(f"Деньги: {needed}р")
            elif inventory_count.get(item_name, 0) < needed:
                can_craft = False
                missing.append(f"{item_name}: {inventory_count.get(item_name, 0)}/{needed}")
        
        craftable.append({
            "id": recipe_id,
            "name": recipe["name"],
            "description": recipe["description"],
            "ingredients": recipe["ingredients"],
            "can_craft": can_craft,
            "missing": missing,
            "success_chance": recipe["success_chance"],
            "result": recipe["result"]
        })
    
    return craftable

async def sdat_zmiy(user_id: int) -> Tuple[Optional[Dict[str, Any]], Any]:
    patsan = await get_patsan(user_id)
    
    if patsan["zmiy"] <= 0:
        return None, "Нечего сдавать!"
    
    price_per_kg = 62.5
    total_money = int(patsan["zmiy"] * price_per_kg)
    
    avtoritet_bonus = patsan["avtoritet"] * 8
    total_money += avtoritet_bonus
    
    old_zmiy = patsan["zmiy"]
    patsan["dengi"] += total_money
    patsan["zmiy"] = 0
    
    exp_gained = min(20, int(total_money / 100))
    patsan["experience"] += exp_gained
    await check_level_up(patsan)
    
    await save_patsan(patsan)
    
    await update_achievement_progress(user_id, "money_maker", total_money)
    
    return patsan, {
        "old_zmiy": old_zmiy,
        "total_money": total_money,
        "avtoritet_bonus": avtoritet_bonus,
        "exp_gained": exp_gained
    }

async def buy_upgrade(user_id: int, upgrade: str) -> Tuple[Optional[Dict[str, Any]], str]:
    patsan = await get_patsan(user_id)
    
    upgrades_data = {
        "ryazhenka": {
            "price": 300,
            "effect": "+75% давления в двенашке",
            "bonus_func": None
        },
        "tea_slivoviy": {
            "price": 500,
            "effect": "-2 атмосферы на действие (мин 1)",
            "bonus_func": None
        },
        "bubbleki": {
            "price": 800,
            "effect": "+35% к шансу находок + шанс на редкий предмет",
            "bonus_func": None
        },
        "kuryasany": {
            "price": 1500,
            "effect": "+2 авторитета и временный буст",
            "bonus_func": lambda p: p.update({"avtoritet": p.get("avtoritet", 1) + 2})
        }
    }
    
    if upgrade not in upgrades_data:
        return None, "Нет такого нагнетателя!"
    
    upgrade_data = upgrades_data[upgrade]
    
    if patsan["upgrades"].get(upgrade):
        return None, "Уже куплено!"
    
    if patsan["dengi"] < upgrade_data["price"]:
        return None, f"Не хватает {upgrade_data['price'] - patsan['dengi']}р!"
    
    patsan["dengi"] -= upgrade_data["price"]
    patsan["upgrades"][upgrade] = True
    
    if upgrade_data["bonus_func"]:
        upgrade_data["bonus_func"](patsan)
    
    await save_patsan(patsan)
    
    all_upgrades = ["ryazhenka", "tea_slivoviy", "bubbleki", "kuryasany"]
    if all(patsan["upgrades"].get(upg, False) for upg in all_upgrades):
        await unlock_achievement(user_id, "all_upgrades", "Все нагнетатели", 1500)
    
    return patsan, f"✅ Куплено '{upgrade}' за {upgrade_data['price']}р! {upgrade_data['effect']}"

async def pump_skill(user_id: int, skill: str) -> Tuple[Optional[Dict[str, Any]], str]:
    patsan = await get_patsan(user_id)
    
    skill_costs = {
        "davka": 180,
        "zashita": 270,
        "nahodka": 225
    }
    
    cost = skill_costs.get(skill, 180)
    
    if patsan["dengi"] < cost:
        return None, f"Не хватает {cost - patsan['dengi']}р!"
    
    patsan["dengi"] -= cost
    
    exp_gained = cost // 10
    patsan["experience"] += exp_gained
    
    old_level = patsan[f"skill_{skill}"]
    patsan[f"skill_{skill}"] += 1
    
    await check_level_up(patsan)
    
    await save_patsan(patsan)
    
    new_level = patsan[f"skill_{skill}"]
    if new_level >= 10:
        await unlock_achievement(user_id, f"skill_{skill}_10", f"Мастер {skill}", 500)
    if new_level >= 25:
        await unlock_achievement(user_id, f"skill_{skill}_25", f"Гуру {skill}", 2000)
    
    return patsan, f"✅ Прокачано '{skill}' с {old_level} до {new_level} уровня за {cost}р! (+{exp_gained} опыта)"

async def check_level_up(user_data: Dict[str, Any]):
    current_level = user_data.get("level", 1)
    current_exp = user_data.get("experience", 0)
    
    required_exp = int(100 * (current_level ** 1.5))
    
    if current_exp >= required_exp:
        old_level = current_level
        user_data["level"] = current_level + 1
        user_data["experience"] = current_exp - required_exp
        
        level_reward = user_data["level"] * 100
        user_data["dengi"] += level_reward
        
        if user_data["level"] % 5 == 0:
            user_data["max_atm"] += 1
            user_data["atm_count"] = min(user_data["atm_count"] + 1, user_data["max_atm"])
        
        if user_data["level"] >= 10:
            await unlock_achievement(user_data["user_id"], "level_10", "10 уровень", 500)
        if user_data["level"] >= 25:
            await unlock_achievement(user_data["user_id"], "level_25", "25 уровень", 2000)
        if user_data["level"] >= 50:
            await unlock_achievement(user_data["user_id"], "level_50", "Полвека на гофре", 5000)
        
        return True, {
            "old_level": old_level,
            "new_level": user_data["level"],
            "reward": level_reward,
            "max_atm_increased": user_data["level"] % 5 == 0
        }
    
    return False, None

async def update_achievement_progress(user_id: int, achievement_id: str, progress_increment: float):
    if achievement_id not in LEVELED_ACHIEVEMENTS:
        return
    
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT progress, current_level FROM achievement_progress 
            WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id))
        
        row = await cursor.fetchone()
        
        if row:
            current_progress = row["progress"] + progress_increment
            current_level = row["current_level"]
        else:
            current_progress = progress_increment
            current_level = 0
            await conn.execute('''
                INSERT INTO achievement_progress (user_id, achievement_id, progress)
                VALUES (?, ?, ?)
            ''', (user_id, achievement_id, current_progress))
        
        achievement = LEVELED_ACHIEVEMENTS[achievement_id]
        
        if current_level < len(achievement["levels"]):
            next_level = achievement["levels"][current_level]
            
            if current_progress >= next_level["goal"]:
                patsan = await get_patsan(user_id)
                patsan["dengi"] += next_level["reward"]
                patsan["experience"] += next_level["exp"]
                
                await conn.execute('''
                    UPDATE achievement_progress 
                    SET progress = ?, current_level = ?
                    WHERE user_id = ? AND achievement_id = ?
                ''', (current_progress, current_level + 1, user_id, achievement_id))
                
                await save_patsan(patsan)
                
                achievements = patsan.get("achievements", [])
                achievements.append({
                    "id": f"{achievement_id}_level_{current_level + 1}",
                    "name": f"{achievement['name']}: {next_level['title']}",
                    "unlocked_at": int(time.time()),
                    "reward": next_level["reward"],
                    "exp": next_level["exp"]
                })
                patsan["achievements"] = achievements
                await save_patsan(patsan)
                
                return {
                    "leveled_up": True,
                    "level": current_level + 1,
                    "title": next_level["title"],
                    "reward": next_level["reward"],
                    "exp": next_level["exp"]
                }
            else:
                await conn.execute('''
                    UPDATE achievement_progress 
                    SET progress = ?
                    WHERE user_id = ? AND achievement_id = ?
                ''', (current_progress, user_id, achievement_id))
        else:
            await conn.execute('''
                UPDATE achievement_progress 
                SET progress = ?
                WHERE user_id = ? AND achievement_id = ?
            ''', (current_progress, user_id, achievement_id))
        
        await conn.commit()
        return {"leveled_up": False, "progress": current_progress}
        
    finally:
        await conn.close()

async def get_achievement_progress(user_id: int) -> Dict[str, Any]:
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT achievement_id, progress, current_level 
            FROM achievement_progress WHERE user_id = ?
        ''', (user_id,))
        
        rows = await cursor.fetchall()
        progress_data = {}
        
        for row in rows:
            ach_id = row["achievement_id"]
            if ach_id in LEVELED_ACHIEVEMENTS:
                achievement = LEVELED_ACHIEVEMENTS[ach_id]
                current_level = row["current_level"]
                current_progress = row["progress"]
                
                if current_level < len(achievement["levels"]):
                    next_level = achievement["levels"][current_level]
                    progress_percent = (current_progress / next_level["goal"]) * 100
                else:
                    next_level = None
                    progress_percent = 100
                
                progress_data[ach_id] = {
                    "name": achievement["name"],
                    "current_level": current_level,
                    "current_progress": current_progress,
                    "next_level": next_level,
                    "progress_percent": min(100, progress_percent),
                    "all_levels": achievement["levels"]
                }
        
        return progress_data
    finally:
        await conn.close()

async def rademka_scout(user_id: int, target_id: int) -> Tuple[bool, str, Dict]:
    patsan = await get_patsan(user_id)
    target = await get_patsan(target_id)
    
    if not target:
        return False, "Цель не найдена", {}
    
    if patsan["rademka_scouts"] >= 5 and patsan["dengi"] < 50:
        return False, "Нужно 50р для разведки (бесплатные разведки закончились)", {}
    
    cost = 0 if patsan["rademka_scouts"] < 5 else 50
    
    if patsan["dengi"] < cost:
        return False, f"Не хватает {cost - patsan['dengi']}р для разведки", {}
    
    base_chance = 50
    avtoritet_diff = patsan["avtoritet"] - target["avtoritet"]
    chance = base_chance + (avtoritet_diff * 5)
    
    if patsan.get("specialization") == "непробиваемый":
        chance += 5
    
    if patsan["avtoritet"] < target["avtoritet"]:
        chance += 20
    
    chance = max(10, min(95, chance))
    
    now = time.time()
    last_active = target.get("last_update", now)
    if now - last_active > 86400:
        chance += 15
    
    if cost > 0:
        patsan["dengi"] -= cost
    patsan["rademka_scouts"] += 1
    
    await save_patsan(patsan)
    
    conn = await get_connection()
    try:
        await conn.execute('''
            UPDATE rademka_fights 
            SET scouted = TRUE 
            WHERE (winner_id = ? AND loser_id = ?) 
               OR (winner_id = ? AND loser_id = ?)
        ''', (user_id, target_id, target_id, user_id))
        await conn.commit()
    finally:
        await conn.close()
    
    scout_data = {
        "chance": chance,
        "cost": cost,
        "free_scouts_left": max(0, 5 - patsan["rademka_scouts"]),
        "attacker_stats": {
            "avtoritet": patsan["avtoritet"],
            "rank": get_rank(patsan["avtoritet"])
        },
        "target_stats": {
            "avtoritet": target["avtoritet"],
            "rank": get_rank(target["avtoritet"]),
            "last_active_hours": int((now - last_active) / 3600) if last_active else "неизвестно"
        },
        "factors": [
            f"Разница в авторитете: {'+' if avtoritet_diff > 0 else ''}{avtoritet_diff * 5}%",
            "Гандикап слабого: +20%" if patsan["avtoritet"] < target["avtoritet"] else None,
            "Цель неактивна: +15%" if now - last_active > 86400 else None,
            f"Специализация: +5%" if patsan.get("specialization") == "непробиваемый" else None
        ]
    }
    
    scout_data["factors"] = [f for f in scout_data["factors"] if f]
    
    return True, f"Разведка {'бесплатная' if cost == 0 else 'за 50р'} успешна!", scout_data

async def rademka_fight_with_scout(user_id: int, target_id: int, scouted_chance: float = None) -> Dict[str, Any]:
    attacker = await get_patsan(user_id)
    target = await get_patsan(target_id)
    
    if not attacker or not target:
        return {"error": "Один из пацанов не найден"}
    
    if scouted_chance:
        chance = scouted_chance
        was_scouted = True
    else:
        base_chance = 50
        avtoritet_diff = attacker["avtoritet"] - target["avtoritet"]
        chance = base_chance + (avtoritet_diff * 5)
        
        if attacker["avtoritet"] < target["avtoritet"]:
            chance += 20
        
        chance = max(10, min(95, chance))
        was_scouted = False
    
    success = random.random() < (chance / 100)
    
    result = {
        "success": success,
        "chance": chance,
        "was_scouted": was_scouted,
        "attacker": attacker["nickname"],
        "target": target["nickname"]
    }
    
    if was_scouted:
        result["scout_bonus"] = "Точный расчёт шанса"
    
    if success:
        await update_achievement_progress(user_id, "rademka_king", 1)
    
    return result

async def get_daily_reward(user_id: int) -> Dict[str, Any]:
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT last_daily, nickname, achievements, level FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            return {"success": False, "error": "Пользователь не найден"}
        
        now = int(time.time())
        last_daily = user["last_daily"] or 0
        
        if last_daily > 0 and now - last_daily < 86400:
            wait_hours = (86400 - (now - last_daily)) // 3600
            wait_minutes = ((86400 - (now - last_daily)) % 3600) // 60
            return {
                "success": False, 
                "wait_time": f"{wait_hours}ч {wait_minutes}м",
                "next_daily": last_daily + 86400
            }
        
        player_level = user["level"] or 1
        base_reward = 100 + (player_level * 10)
        
        achievements = json.loads(user["achievements"]) if user["achievements"] else []
        streak_key = "daily_streak"
        current_streak = 1
        
        for ach in achievements:
            if ach.get("id") == streak_key:
                current_streak = ach.get("value", 1) + 1
                break
        
        streak_multiplier = 1.0
        streak_bonus_text = ""
        
        if current_streak >= 30:
            streak_multiplier = 4.0
            streak_bonus_text = " (x4 за месячный стрик!)"
            await unlock_achievement(user_id, "streak_30", "Месяц без пропусков", 1000)
        elif current_streak >= 7:
            streak_multiplier = 3.0
            streak_bonus_text = " (x3 за недельный стрик!)"
            await unlock_achievement(user_id, "streak_7", "Недельный стрик", 200)
        elif current_streak >= 3:
            streak_multiplier = 2.0
            streak_bonus_text = " (x2 за 3-дневный стрик!)"
            await unlock_achievement(user_id, "streak_3", "Трёхдневный стрик", 50)
        
        base_reward = int(base_reward * streak_multiplier)
        
        random_bonus = random.randint(0, base_reward // 10)
        total_reward = base_reward + random_bonus
        
        if player_level >= 20:
            items = ["двенашка", "атмосфера", "энергетик", "золотая_двенашка", "бустер_атмосфер"]
            weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        else:
            items = ["двенашка", "атмосфера", "энергетик", "перчатки"]
            weights = [0.4, 0.3, 0.2, 0.1]
        
        reward_item = random.choices(items, weights=weights, k=1)[0]
        
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
        
        return {
            "success": True, 
            "money": total_reward,
            "item": reward_item,
            "streak": current_streak,
            "streak_bonus": streak_bonus_text,
            "base": base_reward,
            "random_bonus": random_bonus,
            "level_multiplier": player_level
        }
        
    finally:
        await conn.close()

async def unlock_achievement(user_id: int, achievement_id: str, name: str, reward: int = 0):
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id))
        
        existing = await cursor.fetchone()
        if existing:
            return False
        
        await conn.execute('''
            INSERT INTO achievements (user_id, achievement_id) 
            VALUES (?, ?)
        ''', (user_id, achievement_id))
        
        cursor = await conn.execute('''
            SELECT achievements FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        achievements = json.loads(user["achievements"]) if user and user["achievements"] else []
        
        for ach in achievements:
            if ach.get("id") == achievement_id:
                return False
        
        achievements.append({
            "id": achievement_id,
            "name": name,
            "unlocked_at": int(time.time()),
            "reward": reward
        })
        
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

async def change_nickname(user_id: int, new_nickname: str) -> Tuple[bool, str]:
    conn = await get_connection()
    try:
        cursor = await conn.execute('''
            SELECT nickname_changed, dengi FROM users WHERE user_id = ?
        ''', (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            return False, "Пользователь не найден"
        
        nickname_changed = user["nickname_changed"]
        current_money = user["dengi"]
        
        if not nickname_changed:
            await conn.execute('''
                UPDATE users SET 
                    nickname = ?,
                    nickname_changed = TRUE
                WHERE user_id = ?
            ''', (new_nickname, user_id))
            
            await conn.commit()
            await unlock_achievement(user_id, "first_nickname", "Первая бирка", 100)
            return True, "Ник успешно изменён! (первая смена бесплатно) +100р"
        
        cost = 5000
        if current_money < cost:
            return False, f"Не хватает {cost - current_money}р для смены ника"
        
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

async def save_rademka_fight(winner_id: int, loser_id: int, money_taken: int = 0, item_stolen: str = None, scouted: bool = False):
    conn = await get_connection()
    try:
        await conn.execute('''
            INSERT INTO rademka_fights (winner_id, loser_id, money_taken, item_stolen, scouted)
            VALUES (?, ?, ?, ?, ?)
        ''', (winner_id, loser_id, money_taken, item_stolen, scouted))
        await conn.commit()
    finally:
        await conn.close()

_user_cache = {}
_cache_lock = asyncio.Lock()

async def get_patsan_cached(user_id: int) -> Optional[Dict[str, Any]]:
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
    async with _cache_lock:
        cache_key = f"user_{user_id}"
        if cache_key in _user_cache:
            del _user_cache[cache_key]

async def get_cart(user_id: int) -> List[Dict[str, Any]]:
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
    conn = await get_connection()
    try:
        await conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await conn.commit()
    finally:
        await conn.close()

async def get_cart_total(user_id: int) -> int:
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

async def create_order(user_id: int, items: List[Dict], total: int) -> int:
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

async def get_top_players(limit: int = 10, sort_by: str = "avtoritet") -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        valid_columns = ["avtoritet", "dengi", "zmiy", "level"]
        sort_column = sort_by if sort_by in valid_columns else "avtoritet"
        
        if sort_by == "total_skill":
            query = '''
                SELECT 
                    user_id,
                    nickname, 
                    avtoritet, 
                    dengi, 
                    zmiy,
                    level,
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
                    level,
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
            
            rank_name, rank_emoji = get_rank(player["avtoritet"])
            player["rank"] = f"{rank_emoji} {rank_name}"
            
            top_players.append(player)
        
        return top_players
    finally:
        await conn.close()

async def get_user_achievements(user_id: int) -> List[Dict[str, Any]]:
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
