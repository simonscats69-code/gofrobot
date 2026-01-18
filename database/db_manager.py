import asyncio
import time
import random
import json
import sqlite3
from typing import Optional, List, Dict, Any, Tuple, Set
from contextlib import asynccontextmanager
from collections import defaultdict
import aiosqlite
import logging

logger = logging.getLogger(__name__)

ATM_MAX = 12
ATM_TIME = 600
DB_NAME = "bot_database.db"
CACHE_TTL = 30
MAX_CACHE_SIZE = 500
BATCH_SAVE_INTERVAL = 5

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

class DatabaseManager:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            cls._pool = await aiosqlite.connect(DB_NAME, timeout=30, isolation_level=None)
            cls._pool.row_factory = aiosqlite.Row
            
            await cls._pool.execute("PRAGMA journal_mode = WAL")
            await cls._pool.execute("PRAGMA synchronous = NORMAL")
            await cls._pool.execute("PRAGMA cache_size = -10000")
            await cls._pool.execute("PRAGMA foreign_keys = ON")
            await cls._pool.execute("PRAGMA temp_store = MEMORY")
            
            await cls._instance._create_tables()
        
        return cls._pool
    
    @staticmethod
    async def _create_tables():
        pool = await DatabaseManager.get_pool()
        
        async with pool.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                nickname TEXT NOT NULL DEFAULT '',
                avtoritet INTEGER DEFAULT 1,
                zmiy REAL DEFAULT 0.0,
                dengi INTEGER DEFAULT 150,
                last_update INTEGER DEFAULT 0,
                last_daily INTEGER DEFAULT 0,
                atm_count INTEGER DEFAULT 12,
                max_atm INTEGER DEFAULT 12,
                skill_davka INTEGER DEFAULT 1,
                skill_zashita INTEGER DEFAULT 1,
                skill_nahodka INTEGER DEFAULT 1,
                specialization TEXT DEFAULT '',
                experience INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                inventory TEXT DEFAULT '[]',
                upgrades TEXT DEFAULT '{}',
                active_boosts TEXT DEFAULT '{}',
                achievements TEXT DEFAULT '[]',
                crafted_items TEXT DEFAULT '[]',
                rademka_scouts INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                dirty_flag INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_users_avtoritet ON users(avtoritet DESC);
            CREATE INDEX IF NOT EXISTS idx_users_dengi ON users(dengi DESC);
            CREATE INDEX IF NOT EXISTS idx_users_level ON users(level DESC);
            CREATE INDEX IF NOT EXISTS idx_users_updated ON users(last_update);
            
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at INTEGER,
                progress REAL DEFAULT 0,
                level INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, achievement_id)
            );
            
            CREATE TABLE IF NOT EXISTS active_boosts_cache (
                user_id INTEGER PRIMARY KEY,
                boosts_json TEXT DEFAULT '{}',
                expires_at INTEGER DEFAULT 0
            );
            
            CREATE VIEW IF NOT EXISTS leaderboard_view AS
            SELECT 
                user_id,
                nickname,
                avtoritet,
                dengi,
                zmiy,
                level,
                (skill_davka + skill_zashita + skill_nahodka) as total_skill,
                ROW_NUMBER() OVER (ORDER BY avtoritet DESC) as rank
            FROM users;
            
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER,
                item_id TEXT,
                quantity INTEGER DEFAULT 1,
                price INTEGER,
                added_at INTEGER DEFAULT (strftime('%s', 'now')),
                PRIMARY KEY (user_id, item_id)
            ) WITHOUT ROWID;
            
            CREATE TABLE IF NOT EXISTS craft_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id TEXT NOT NULL,
                success BOOLEAN,
                crafted_at INTEGER DEFAULT (strftime('%s', 'now'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_craft_user ON craft_history(user_id, crafted_at DESC);
            
            CREATE TABLE IF NOT EXISTS rademka_fights (
                winner_id INTEGER NOT NULL,
                loser_id INTEGER NOT NULL,
                money_taken INTEGER DEFAULT 0,
                item_stolen TEXT,
                scouted BOOLEAN DEFAULT FALSE,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_rademka_winner ON rademka_fights(winner_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_rademka_loser ON rademka_fights(loser_id, created_at DESC);
            
            CREATE TABLE IF NOT EXISTS achievement_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                progress REAL DEFAULT 0,
                current_level INTEGER DEFAULT 0,
                UNIQUE(user_id, achievement_id)
            );
            
            CREATE TABLE IF NOT EXISTS stolen_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thief_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                stolen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                items TEXT NOT NULL,
                total INTEGER NOT NULL,
                status TEXT DEFAULT 'новый',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            );
        '''):
            pass
        
        logger.info("Таблицы созданы")
    
    @asynccontextmanager
    async def transaction(self):
        pool = await self.get_pool()
        try:
            await pool.execute("BEGIN IMMEDIATE")
            yield pool
            await pool.commit()
        except Exception as e:
            await pool.rollback()
            raise e

class UserCache:
    def __init__(self, data: Dict[str, Any], timestamp: float):
        self.data = data
        self.timestamp = timestamp
        self.dirty = False

class UserDataManager:
    def __init__(self):
        self._cache: Dict[int, UserCache] = {}
        self._dirty_users: Set[int] = set()
        self._batch_lock = asyncio.Lock()
        self._save_task = None
        self._db = DatabaseManager()
    
    async def start_batch_saver(self):
        if self._save_task is None:
            self._save_task = asyncio.create_task(self._batch_save_loop())
    
    async def stop_batch_saver(self):
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass
            self._save_task = None
    
    async def _batch_save_loop(self):
        while True:
            try:
                await asyncio.sleep(BATCH_SAVE_INTERVAL)
                await self._save_dirty_users()
            except asyncio.CancelledError:
                await self._save_dirty_users()
                raise
            except Exception as e:
                logger.error(f"Ошибка сохранения: {e}")
    
    async def _save_dirty_users(self):
        async with self._batch_lock:
            if not self._dirty_users:
                return
            
            users_to_save = []
            user_ids = list(self._dirty_users)
            
            for user_id in user_ids:
                if user_id in self._cache:
                    cache_entry = self._cache[user_id]
                    if cache_entry.dirty:
                        users_to_save.append((user_id, cache_entry.data))
                        cache_entry.dirty = False
            
            if users_to_save:
                await self._batch_save_users(users_to_save)
            
            self._dirty_users.clear()
    
    async def _batch_save_users(self, users_data: List[Tuple[int, Dict]]):
        pool = await self._db.get_pool()
        
        values = []
        now = int(time.time())
        
        for user_id, data in users_data:
            values.append((
                data.get("nickname", ""),
                data.get("avtoritet", 1),
                data.get("zmiy", 0.0),
                data.get("dengi", 150),
                now,
                data.get("last_daily", 0),
                data.get("atm_count", 12),
                data.get("max_atm", 12),
                data.get("skill_davka", 1),
                data.get("skill_zashita", 1),
                data.get("skill_nahodka", 1),
                data.get("specialization", ""),
                data.get("experience", 0),
                data.get("level", 1),
                json.dumps(data.get("inventory", [])),
                json.dumps(data.get("upgrades", {})),
                json.dumps(data.get("active_boosts", {})),
                json.dumps(data.get("achievements", [])),
                json.dumps(data.get("crafted_items", [])),
                data.get("rademka_scouts", 0),
                user_id
            ))
        
        await pool.executemany('''
            UPDATE users SET 
                nickname = ?, avtoritet = ?, zmiy = ?, dengi = ?,
                last_update = ?, last_daily = ?, atm_count = ?, max_atm = ?,
                skill_davka = ?, skill_zashita = ?, skill_nahodka = ?,
                specialization = ?, experience = ?, level = ?,
                inventory = ?, upgrades = ?, active_boosts = ?,
                achievements = ?, crafted_items = ?, rademka_scouts = ?
            WHERE user_id = ?
        ''', values)
    
    async def get_user(self, user_id: int, force_fresh: bool = False) -> Optional[Dict[str, Any]]:
        now = time.time()
        
        if not force_fresh and user_id in self._cache:
            cache_entry = self._cache[user_id]
            if now - cache_entry.timestamp < CACHE_TTL:
                return cache_entry.data
        
        pool = await self._db.get_pool()
        
        async with pool.execute('''
            SELECT 
                u.*,
                COALESCE(ab.boosts_json, '{}') as cached_boosts,
                COALESCE(
                    (SELECT json_group_array(achievement_id) 
                     FROM user_achievements ua 
                     WHERE ua.user_id = u.user_id),
                    '[]'
                ) as achievement_ids
            FROM users u
            LEFT JOIN active_boosts_cache ab ON u.user_id = ab.user_id
            WHERE u.user_id = ?
        ''', (user_id,)) as cursor:
            row = await cursor.fetchone()
            
            if row:
                user = dict(row)
                await self._post_process_user(user)
                
                self._cache[user_id] = UserCache(
                    data=user,
                    timestamp=now
                )
                
                if len(self._cache) > MAX_CACHE_SIZE:
                    self._clean_old_cache()
                
                return user
            else:
                return await self._create_new_user(user_id)
    
    async def _create_new_user(self, user_id: int) -> Dict[str, Any]:
        now = int(time.time())
        new_user = {
            "user_id": user_id,
            "nickname": f"Пацанчик_{user_id}",
            "avtoritet": 1,
            "zmiy": 0.0,
            "dengi": 150,
            "last_update": now,
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
            "upgrades": {},
            "active_boosts": {},
            "achievements": [],
            "crafted_items": [],
            "rademka_scouts": 0,
            "rank_name": "Пацанчик",
            "rank_emoji": "👶",
            "cached_boosts": {},
            "achievement_ids": []
        }
        
        pool = await self._db.get_pool()
        
        async with pool.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, nickname, last_update, inventory, upgrades, active_boosts, achievements)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            new_user["nickname"],
            now,
            json.dumps(new_user["inventory"]),
            json.dumps(new_user["upgrades"]),
            json.dumps(new_user["active_boosts"]),
            json.dumps(new_user["achievements"])
        )):
            pass
        
        self._cache[user_id] = UserCache(
            data=new_user,
            timestamp=time.time()
        )
        
        return new_user
    
    async def _post_process_user(self, user: Dict[str, Any]):
        now = time.time()
        last_update = user.get("last_update", now)
        passed = now - last_update
        
        if passed >= ATM_TIME:
            max_atm = user.get("max_atm", ATM_MAX)
            current_atm = user.get("atm_count", 0)
            regen_count = passed // ATM_TIME
            
            if regen_count > 0:
                new_atm = min(max_atm, current_atm + regen_count)
                user["atm_count"] = new_atm
                user["last_update"] = now - (passed % ATM_TIME)
        
        json_fields = ["inventory", "upgrades", "active_boosts", "achievements", "crafted_items"]
        
        for field in json_fields:
            value = user.get(field)
            if isinstance(value, str):
                try:
                    if value:
                        user[field] = json.loads(value)
                    else:
                        user[field] = [] if field in ["inventory", "achievements", "crafted_items"] else {}
                except:
                    user[field] = [] if field in ["inventory", "achievements", "crafted_items"] else {}
        
        user["rank_name"], user["rank_emoji"] = get_rank(user.get("avtoritet", 1))
    
    def mark_dirty(self, user_id: int):
        if user_id in self._cache:
            self._cache[user_id].dirty = True
            self._dirty_users.add(user_id)
    
    async def save_user(self, user_id: int):
        if user_id in self._cache:
            self.mark_dirty(user_id)
            await self._save_dirty_users()
    
    def _clean_old_cache(self):
        now = time.time()
        to_delete = []
        
        for user_id, cache_entry in self._cache.items():
            if now - cache_entry.timestamp > CACHE_TTL * 2:
                to_delete.append(user_id)
        
        for user_id in to_delete:
            del self._cache[user_id]
        
        if len(self._cache) > MAX_CACHE_SIZE:
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1].timestamp)
            for user_id, _ in sorted_items[:MAX_CACHE_SIZE // 2]:
                del self._cache[user_id]
    
    async def get_top_players_fast(self, limit: int = 10, sort_by: str = "avtoritet") -> List[Dict]:
        pool = await self._db.get_pool()
        
        valid_columns = ["avtoritet", "dengi", "zmiy", "level", "total_skill"]
        if sort_by not in valid_columns:
            sort_by = "avtoritet"
        
        query = f'''
            SELECT * FROM leaderboard_view 
            ORDER BY {sort_by} DESC 
            LIMIT ?
        '''
        
        async with pool.execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

user_manager = UserDataManager()

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
    
    if isinstance(boosts, str):
        try:
            boosts = json.loads(boosts) if boosts else {}
        except:
            boosts = {}
    
    if isinstance(boosts, dict) and boosts.get("вечный_двигатель"):
        base_time *= 0.7
    
    return int(max(60, base_time))

def get_specialization_bonuses(specialization: str) -> Dict[str, Any]:
    spec = SPECIALIZATIONS.get(specialization, {})
    return spec.get("bonuses", {})

async def get_patsan(user_id: int) -> Optional[Dict[str, Any]]:
    return await user_manager.get_user(user_id)

async def save_patsan(user_data: Dict[str, Any]):
    user_id = user_data.get("user_id")
    if user_id:
        if user_id in user_manager._cache:
            user_manager._cache[user_id].data.update(user_data)
            user_manager._cache[user_id].dirty = True
        await user_manager.save_user(user_id)

async def davka_zmiy(user_id: int) -> Tuple[Optional[Dict[str, Any]], Any]:
    patsan = await user_manager.get_user(user_id)
    
    base_cost = 2
    
    if patsan["upgrades"].get("tea_slivoviy"):
        base_cost = max(1, base_cost - 1)
    
    bonuses = get_specialization_bonuses(patsan.get("specialization", ""))
    if bonuses.get("atm_cost_reduction"):
        base_cost = max(1, base_cost - bonuses["atm_cost_reduction"])
    
    if patsan["atm_count"] < base_cost:
        return None, "Не хватает атмосфер!"
    
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
    
    user_manager.mark_dirty(user_id)
    
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
    patsan = await user_manager.get_user(user_id)
    
    if specialization not in SPECIALIZATIONS:
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
        return False, "У тебя уже есть специализация"
    
    patsan["dengi"] -= spec["price"]
    patsan["specialization"] = specialization
    
    await unlock_achievement(user_id, "first_specialization", "Первая специализация", 500)
    
    user_manager.mark_dirty(user_id)
    return True, f"✅ Куплена специализация '{spec['name']}' за {spec['price']}р!"

async def get_available_specializations(user_id: int) -> List[Dict[str, Any]]:
    patsan = await user_manager.get_user(user_id)
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
    patsan = await user_manager.get_user(user_id)
    
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
        message = f"❌ Неудачная попытка крафта {recipe['name']}"
    
    pool = await DatabaseManager().get_pool()
    try:
        await pool.execute('''
            INSERT INTO craft_history (user_id, recipe_id, success)
            VALUES (?, ?, ?)
        ''', (user_id, recipe_id, success))
    finally:
        pass
    
    user_manager.mark_dirty(user_id)
    return success, message, recipe.get("result", {})

async def get_craftable_items(user_id: int) -> List[Dict[str, Any]]:
    patsan = await user_manager.get_user(user_id)
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
    patsan = await user_manager.get_user(user_id)
    
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
    
    user_manager.mark_dirty(user_id)
    
    await update_achievement_progress(user_id, "money_maker", total_money)
    
    return patsan, {
        "old_zmiy": old_zmiy,
        "total_money": total_money,
        "avtoritet_bonus": avtoritet_bonus,
        "exp_gained": exp_gained
    }

async def buy_upgrade(user_id: int, upgrade: str) -> Tuple[Optional[Dict[str, Any]], str]:
    patsan = await user_manager.get_user(user_id)
    
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
    
    user_manager.mark_dirty(user_id)
    
    all_upgrades = ["ryazhenka", "tea_slivoviy", "bubbleki", "kuryasany"]
    if all(patsan["upgrades"].get(upg, False) for upg in all_upgrades):
        await unlock_achievement(user_id, "all_upgrades", "Все нагнетатели", 1500)
    
    return patsan, f"✅ Куплено '{upgrade}' за {upgrade_data['price']}р! {upgrade_data['effect']}"

async def pump_skill(user_id: int, skill: str) -> Tuple[Optional[Dict[str, Any]], str]:
    patsan = await user_manager.get_user(user_id)
    
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
    
    user_manager.mark_dirty(user_id)
    
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
    
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT progress, current_level FROM achievement_progress 
            WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id)) as cursor:
            row = await cursor.fetchone()
            
            if row:
                current_progress = row["progress"] + progress_increment
                current_level = row["current_level"]
            else:
                current_progress = progress_increment
                current_level = 0
                await pool.execute('''
                    INSERT INTO achievement_progress (user_id, achievement_id, progress)
                    VALUES (?, ?, ?)
                ''', (user_id, achievement_id, current_progress))
        
        achievement = LEVELED_ACHIEVEMENTS[achievement_id]
        
        if current_level < len(achievement["levels"]):
            next_level = achievement["levels"][current_level]
            
            if current_progress >= next_level["goal"]:
                patsan = await user_manager.get_user(user_id)
                patsan["dengi"] += next_level["reward"]
                patsan["experience"] += next_level["exp"]
                
                await pool.execute('''
                    UPDATE achievement_progress 
                    SET progress = ?, current_level = ?
                    WHERE user_id = ? AND achievement_id = ?
                ''', (current_progress, current_level + 1, user_id, achievement_id))
                
                user_manager.mark_dirty(user_id)
                
                achievements = patsan.get("achievements", [])
                achievements.append({
                    "id": f"{achievement_id}_level_{current_level + 1}",
                    "name": f"{achievement['name']}: {next_level['title']}",
                    "unlocked_at": int(time.time()),
                    "reward": next_level["reward"],
                    "exp": next_level["exp"]
                })
                patsan["achievements"] = achievements
                user_manager.mark_dirty(user_id)
                
                return {
                    "leveled_up": True,
                    "level": current_level + 1,
                    "title": next_level["title"],
                    "reward": next_level["reward"],
                    "exp": next_level["exp"]
                }
            else:
                await pool.execute('''
                    UPDATE achievement_progress 
                    SET progress = ?
                    WHERE user_id = ? AND achievement_id = ?
                ''', (current_progress, user_id, achievement_id))
        else:
            await pool.execute('''
                UPDATE achievement_progress 
                SET progress = ?
                WHERE user_id = ? AND achievement_id = ?
            ''', (current_progress, user_id, achievement_id))
        
        return {"leveled_up": False, "progress": current_progress}
        
    finally:
        pass

async def get_achievement_progress(user_id: int) -> Dict[str, Any]:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT achievement_id, progress, current_level 
            FROM achievement_progress WHERE user_id = ?
        ''', (user_id,)) as cursor:
            
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
        pass

async def rademka_scout(user_id: int, target_id: int) -> Tuple[bool, str, Dict]:
    patsan = await user_manager.get_user(user_id)
    target = await user_manager.get_user(target_id)
    
    if not target:
        return False, "Цель не найдена", {}
    
    if patsan["rademka_scouts"] >= 5 and patsan["dengi"] < 50:
        return False, "Нужно 50р для разведки", {}
    
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
    
    user_manager.mark_dirty(user_id)
    
    pool = await DatabaseManager().get_pool()
    try:
        await pool.execute('''
            UPDATE rademka_fights 
            SET scouted = TRUE 
            WHERE (winner_id = ? AND loser_id = ?) 
               OR (winner_id = ? AND loser_id = ?)
        ''', (user_id, target_id, target_id, user_id))
    finally:
        pass
    
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
    attacker = await user_manager.get_user(user_id)
    target = await user_manager.get_user(target_id)
    
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
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT last_daily, nickname, achievements, level FROM users WHERE user_id = ?
        ''', (user_id,)) as cursor:
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
            
            await pool.execute('''
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
            
            patsan = await user_manager.get_user(user_id, force_fresh=True)
            
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
        pass

async def unlock_achievement(user_id: int, achievement_id: str, name: str, reward: int = 0):
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id)) as cursor:
            
            existing = await cursor.fetchone()
            if existing:
                return False
        
        await pool.execute('''
            INSERT INTO achievements (user_id, achievement_id) 
            VALUES (?, ?)
        ''', (user_id, achievement_id))
        
        async with pool.execute('''
            SELECT achievements FROM users WHERE user_id = ?
        ''', (user_id,)) as cursor:
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
                await pool.execute('''
                    UPDATE users SET 
                        dengi = dengi + ?,
                        achievements = ?
                    WHERE user_id = ?
                ''', (reward, json.dumps(achievements), user_id))
            else:
                await pool.execute('''
                    UPDATE users SET achievements = ? WHERE user_id = ?
                ''', (json.dumps(achievements), user_id))
            
            patsan = await user_manager.get_user(user_id, force_fresh=True)
            
            return True
            
    finally:
        pass

async def change_nickname(user_id: int, new_nickname: str) -> Tuple[bool, str]:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT nickname_changed, dengi FROM users WHERE user_id = ?
        ''', (user_id,)) as cursor:
            user = await cursor.fetchone()
            
            if not user:
                return False, "Пользователь не найден"
            
            nickname_changed = user["nickname_changed"]
            current_money = user["dengi"]
            
            if not nickname_changed:
                await pool.execute('''
                    UPDATE users SET 
                        nickname = ?,
                        nickname_changed = TRUE
                    WHERE user_id = ?
                ''', (new_nickname, user_id))
                
                await unlock_achievement(user_id, "first_nickname", "Первая бирка", 100)
                patsan = await user_manager.get_user(user_id, force_fresh=True)
                return True, "Ник успешно изменён! (первая смена бесплатно) +100р"
            
            cost = 5000
            if current_money < cost:
                return False, f"Не хватает {cost - current_money}р для смены ника"
            
            await pool.execute('''
                UPDATE users SET 
                    nickname = ?,
                    dengi = dengi - ?
                WHERE user_id = ?
            ''', (new_nickname, cost, user_id))
            
            patsan = await user_manager.get_user(user_id, force_fresh=True)
            return True, f"Ник изменён! Списано {cost}р"
            
    finally:
        pass

async def save_rademka_fight(winner_id: int, loser_id: int, money_taken: int = 0, item_stolen: str = None, scouted: bool = False):
    pool = await DatabaseManager().get_pool()
    try:
        await pool.execute('''
            INSERT INTO rademka_fights (winner_id, loser_id, money_taken, item_stolen, scouted)
            VALUES (?, ?, ?, ?, ?)
        ''', (winner_id, loser_id, money_taken, item_stolen, scouted))
    finally:
        pass

async def get_patsan_cached(user_id: int) -> Optional[Dict[str, Any]]:
    return await user_manager.get_user(user_id)

async def invalidate_user_cache(user_id: int):
    if user_id in user_manager._cache:
        del user_manager._cache[user_id]

async def get_cart(user_id: int) -> List[Dict[str, Any]]:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT item_id as item_name, quantity, price 
            FROM cart WHERE user_id = ?
        ''', (user_id,)) as cursor:
            
            rows = await cursor.fetchall()
            cart_items = []
            for row in rows:
                cart_items.append(dict(row))
            
            return cart_items
    finally:
        pass

async def add_to_cart(user_id: int, item_name: str, price: int, quantity: int = 1):
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND item_id = ?
        ''', (user_id, item_name)) as cursor:
            
            existing = await cursor.fetchone()
            
            if existing:
                new_quantity = existing["quantity"] + quantity
                await pool.execute('''
                    UPDATE cart SET quantity = ? 
                    WHERE user_id = ? AND item_id = ?
                ''', (new_quantity, user_id, item_name))
            else:
                await pool.execute('''
                    INSERT INTO cart (user_id, item_id, price, quantity)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, item_name, price, quantity))
    finally:
        pass

async def remove_from_cart(user_id: int, item_name: str, quantity: int = 1):
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND item_id = ?
        ''', (user_id, item_name)) as cursor:
            
            existing = await cursor.fetchone()
            if not existing:
                return
            
            current_qty = existing["quantity"]
            
            if current_qty <= quantity:
                await pool.execute('''
                    DELETE FROM cart 
                    WHERE user_id = ? AND item_id = ?
                ''', (user_id, item_name))
            else:
                await pool.execute('''
                    UPDATE cart SET quantity = ? 
                    WHERE user_id = ? AND item_id = ?
                ''', (current_qty - quantity, user_id, item_name))
    finally:
        pass

async def clear_cart(user_id: int):
    pool = await DatabaseManager().get_pool()
    try:
        await pool.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    finally:
        pass

async def get_cart_total(user_id: int) -> int:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT SUM(price * quantity) as total 
            FROM cart WHERE user_id = ?
        ''', (user_id,)) as cursor:
            
            result = await cursor.fetchone()
            return result["total"] if result and result["total"] else 0
    finally:
        pass

async def create_order(user_id: int, items: List[Dict], total: int) -> int:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            INSERT INTO orders (user_id, items, total, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(items), total, 'новый')) as cursor:
            
            order_id = cursor.lastrowid
            
            await clear_cart(user_id)
            
            return order_id
    finally:
        pass

async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT id, items, total, status, created_at 
            FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            
            orders = []
            rows = await cursor.fetchall()
            for row in rows:
                order = dict(row)
                order["items"] = json.loads(order["items"])
                orders.append(order)
            
            return orders
    finally:
        pass

async def get_top_players(limit: int = 10, sort_by: str = "avtoritet") -> List[Dict[str, Any]]:
    return await user_manager.get_top_players_fast(limit, sort_by)

async def get_user_achievements(user_id: int) -> List[Dict[str, Any]]:
    pool = await DatabaseManager().get_pool()
    try:
        async with pool.execute('''
            SELECT achievements FROM users WHERE user_id = ?
        ''', (user_id,)) as cursor:
            user = await cursor.fetchone()
            
            if user and user["achievements"]:
                return json.loads(user["achievements"])
            return []
    finally:
        pass

_top_cache = {}
_top_cache_time = {}

async def get_top_players_cached(limit: int = 10, sort_by: str = "avtoritet"):
    cache_key = f"{limit}_{sort_by}"
    now = time.time()
    
    if cache_key in _top_cache:
        if now - _top_cache_time.get(cache_key, 0) < 30:
            return _top_cache[cache_key]
    
    top = await user_manager.get_top_players_fast(limit, sort_by)
    _top_cache[cache_key] = top
    _top_cache_time[cache_key] = now
    
    if len(_top_cache) > 20:
        oldest = min(_top_cache_time.items(), key=lambda x: x[1])[0]
        del _top_cache[oldest]
        del _top_cache_time[oldest]
    
    return top

async def init_bot():
    await DatabaseManager().get_pool()
    await user_manager.start_batch_saver()
    logger.info("Бот инициализирован")

async def shutdown_bot():
    await user_manager.stop_batch_saver()
    await user_manager._save_dirty_users()
    
    if DatabaseManager._pool:
        await DatabaseManager._pool.close()
        DatabaseManager._pool = None
    
    logger.info("Бот завершил работу")

async def _clean_expired_boosts():
    while True:
        try:
            pool = await DatabaseManager().get_pool()
            now = int(time.time())
            await pool.execute(
                "DELETE FROM active_boosts_cache WHERE expires_at < ?",
                (now,)
            )
        except Exception as e:
            logger.error(f"Ошибка очистки бустов: {e}")
        await asyncio.sleep(3600)

async def start_background_tasks():
    asyncio.create_task(_clean_expired_boosts())

if __name__ == "__main__":
    import asyncio
    
    async def test():
        await init_bot()
        
        start = time.time()
        
        tasks = []
        for i in range(100):
            tasks.append(get_patsan(i))
        
        results = await asyncio.gather(*tasks)
        print(f"Загружено 100 пользователей за {time.time() - start:.2f}с")
        
        await shutdown_bot()
    
    asyncio.run(test())
