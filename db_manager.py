import os, time, random, json, aiosqlite
import asyncio
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def ensure_storage():
    storage_path = "storage"
    
    if not os.path.exists(storage_path):
        try:
            os.makedirs(storage_path, exist_ok=True)
            os.makedirs(os.path.join(storage_path, "backups"), exist_ok=True)
            os.makedirs(os.path.join(storage_path, "logs"), exist_ok=True)
            logger.info(f"📁 Создана папка storage")
            return storage_path
        except Exception as e:
            logger.error(f"⚠️ Ошибка создания storage: {e}")
            return "."
    
    logger.info(f"✅ Папка storage уже существует")
    return storage_path

STORAGE_DIR = ensure_storage()
DB_PATH = os.path.join(STORAGE_DIR, "bot_database.db")

DB_NAME = os.getenv("DB_NAME", DB_PATH)
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "30"))
MAX_CACHE = int(os.getenv("MAX_CACHE_SIZE", "500"))
ATM_MAX = 12
ATM_BASE_TIME = 7200
BATCH_INT = 5

GOFRY = {
    1: {"name": "Новая гофра", "emoji": "🆕", "min_grams": 50, "max_grams": 200, "atm_speed": 1.0},
    10: {"name": "Слегка разъезжена", "emoji": "🔄", "min_grams": 80, "max_grams": 300, "atm_speed": 0.9},
    25: {"name": "Рабочая гофра", "emoji": "⚙️", "min_grams": 120, "max_grams": 450, "atm_speed": 0.8},
    50: {"name": "Разъезжена хорошо", "emoji": "🔥", "min_grams": 180, "max_grams": 650, "atm_speed": 0.7},
    100: {"name": "Заезженная гофра", "emoji": "🏎️", "min_grams": 250, "max_grams": 900, "atm_speed": 0.6},
    200: {"name": "Убитая гофра", "emoji": "💀", "min_grams": 350, "max_grams": 1200, "atm_speed": 0.5},
    500: {"name": "Легендарная гофра", "emoji": "👑", "min_grams": 500, "max_grams": 1600, "atm_speed": 0.4},
    1000: {"name": "Царь-гофра", "emoji": "🐉", "min_grams": 700, "max_grams": 2000, "atm_speed": 0.3}
}

class Metrics:
    _instance = None
    
    def __init__(self):
        self.db_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.save_operations = 0
        self.start_time = time.time()
    
    @classmethod
    def get(cls):
        if not cls._instance:
            cls._instance = Metrics()
        return cls._instance
    
    def log_query(self):
        self.db_queries += 1
    
    def log_cache_hit(self):
        self.cache_hits += 1
    
    def log_cache_miss(self):
        self.cache_misses += 1
    
    def log_save(self, count=1):
        self.save_operations += count
    
    def get_stats(self):
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": uptime,
            "db_queries": self.db_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "save_operations": self.save_operations,
            "queries_per_second": self.db_queries / max(1, uptime)
        }

class DatabaseManager:
    _pool = None
    
    @classmethod
    async def get_pool(cls):
        if not cls._pool:
            logger.info(f"🔌 Подключение к БД: {DB_PATH}")
            cls._pool = await aiosqlite.connect(DB_PATH, timeout=30)
            cls._pool.row_factory = aiosqlite.Row
            await cls._create_tables()
        return cls._pool
    
    @staticmethod
    async def _create_tables():
        pool = await DatabaseManager.get_pool()
        await pool.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, 
                nickname TEXT DEFAULT '', 
                gofra INTEGER DEFAULT 1,
                cable_power INTEGER DEFAULT 1,
                zmiy_grams REAL DEFAULT 0.0,
                last_update INTEGER DEFAULT 0,
                last_davka INTEGER DEFAULT 0,
                atm_count INTEGER DEFAULT 12,
                max_atm INTEGER DEFAULT 12,
                experience INTEGER DEFAULT 0,
                total_davki INTEGER DEFAULT 0,
                total_zmiy_grams REAL DEFAULT 0.0,
                nickname_changed BOOLEAN DEFAULT FALSE
            );
            CREATE INDEX IF NOT EXISTS idx_gofra ON users(gofra DESC);
            CREATE INDEX IF NOT EXISTS idx_zmiy ON users(zmiy_grams DESC);
            
            CREATE TABLE IF NOT EXISTS rademka_fights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                winner_id INTEGER, 
                loser_id INTEGER, 
                money_taken INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_win ON rademka_fights(winner_id);
            CREATE INDEX IF NOT EXISTS idx_lose ON rademka_fights(loser_id);
        ''')
    
    @staticmethod
    async def create_backup():
        try:
            import shutil
            from datetime import datetime
            
            if not os.path.exists(DB_PATH):
                return
            
            backup_dir = os.path.join(STORAGE_DIR, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
            
            shutil.copy2(DB_PATH, backup_file)
            logger.info(f"✅ Бэкап: {os.path.basename(backup_file)}")
            
            backups = sorted([
                os.path.join(backup_dir, f) 
                for f in os.listdir(backup_dir) 
                if f.startswith("backup_") and f.endswith(".db")
            ])
            
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    os.remove(old_backup)
                    logger.debug(f"🗑️ Удалён старый бэкап: {os.path.basename(old_backup)}")
                    
        except Exception as e:
            logger.error(f"⚠️ Бэкап не удался: {e}")

class UserCache:
    def __init__(self, data, timestamp):
        self.data, self.timestamp, self.dirty = data, timestamp, False

class UserDataManager:
    def __init__(self):
        self._cache, self._dirty, self._lock, self._save_task = {}, set(), asyncio.Lock(), None
        self.metrics = Metrics.get()
    
    async def start_batch_saver(self):
        if not self._save_task:
            self._save_task = asyncio.create_task(self._save_loop())
    
    async def _save_loop(self):
        while True:
            await asyncio.sleep(BATCH_INT)
            await self._save_dirty()
    
    async def _save_dirty(self):
        async with self._lock:
            if not self._dirty:
                return
            
            to_save = [(uid, self._cache[uid].data) for uid in self._dirty 
                      if uid in self._cache and self._cache[uid].dirty]
            
            if not to_save:
                return
            
            start_time = time.time()
            try:
                await self._batch_save(to_save)
                self.metrics.log_save(len(to_save))
                logger.info(f"💾 Сохранено {len(to_save)} пользователей за {time.time()-start_time:.3f}с")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения {len(to_save)} пользователей: {e}")
                raise
    
    async def _batch_save(self, users):
        pool = await DatabaseManager.get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("BEGIN TRANSACTION")
            try:
                for uid, d in users:
                    await conn.execute('''
                        UPDATE users SET 
                            nickname=?, gofra=?, cable_power=?, zmiy_grams=?, 
                            last_update=?, last_davka=?, atm_count=?, max_atm=?,
                            experience=?, total_davki=?, total_zmiy_grams=?, nickname_changed=?
                        WHERE user_id=?
                    ''', (
                        d.get("nickname", ""), 
                        d.get("gofra", 1),
                        d.get("cable_power", 1),
                        d.get("zmiy_grams", 0.0),
                        int(time.time()),
                        d.get("last_davka", 0),
                        d.get("atm_count", 12),
                        d.get("max_atm", 12),
                        d.get("experience", 0),
                        d.get("total_davki", 0),
                        d.get("total_zmiy_grams", 0.0),
                        d.get("nickname_changed", False),
                        uid
                    ))
                await conn.execute("COMMIT")
            except Exception as e:
                await conn.execute("ROLLBACK")
                raise e
    
    async def get_user(self, uid, force=False):
        now = time.time()
        
        if not force and uid in self._cache and now - self._cache[uid].timestamp < CACHE_TTL:
            self.metrics.log_cache_hit()
            return self._cache[uid].data
        
        self.metrics.log_cache_miss()
        self.metrics.log_query()
        
        pool = await DatabaseManager.get_pool()
        async with pool.execute('SELECT * FROM users WHERE user_id=?', (uid,)) as c:
            row = await c.fetchone()
            if row: 
                user = dict(row)
                await self._process_user(user)
            else: 
                user = await self._create_user(uid)
        
        self._cache[uid] = UserCache(user, now)
        if len(self._cache) > MAX_CACHE: 
            self._clean_cache()
        return user
    
    async def get_users_batch(self, uids):
        """Получить нескольких пользователей за один запрос"""
        if not uids:
            return []
        
        now = time.time()
        result = {}
        to_fetch = []
        
        for uid in uids:
            if uid in self._cache and now - self._cache[uid].timestamp < CACHE_TTL:
                self.metrics.log_cache_hit()
                result[uid] = self._cache[uid].data
            else:
                self.metrics.log_cache_miss()
                to_fetch.append(uid)
        
        if to_fetch:
            self.metrics.log_query()
            pool = await DatabaseManager.get_pool()
            placeholders = ','.join('?' * len(to_fetch))
            async with pool.execute(f'''
                SELECT * FROM users WHERE user_id IN ({placeholders})
            ''', to_fetch) as c:
                rows = await c.fetchall()
                for row in rows:
                    user = dict(row)
                    await self._process_user(user)
                    result[user['user_id']] = user
                    self._cache[user['user_id']] = UserCache(user, now)
        
        return [result.get(uid) for uid in uids]
    
    async def _create_user(self, uid):
        now = int(time.time())
        user = {
            "user_id": uid, 
            "nickname": f"Пацанчик_{uid}", 
            "gofra": 1,
            "cable_power": 1,
            "zmiy_grams": 0.0,
            "last_update": now,
            "last_davka": 0,
            "atm_count": 12,
            "max_atm": 12,
            "experience": 0,
            "total_davki": 0,
            "total_zmiy_grams": 0.0,
            "nickname_changed": False
        }
        pool = await DatabaseManager.get_pool()
        await pool.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, nickname, last_update, atm_count, nickname_changed) 
            VALUES (?,?,?,?,?)
        ''', (uid, user["nickname"], now, 12, False))
        return user
    
    async def _process_user(self, user):
        now = time.time()
        last_update = user.get("last_update", now)
        
        gofra = user.get("gofra", 1)
        gofra_info = get_gofra_info(gofra)
        atm_speed = gofra_info["atm_speed"]
        
        atm_regen_time = ATM_BASE_TIME * atm_speed
        
        if user.get("atm_count", 12) < 12:
            time_passed = now - last_update
            if time_passed >= atm_regen_time:
                recovered = int(time_passed // atm_regen_time)
                if recovered > 0:
                    user["atm_count"] = min(12, user.get("atm_count", 0) + recovered)
                    user["last_update"] = now - (time_passed % atm_regen_time)
    
    def mark_dirty(self, uid):
        if uid in self._cache:
            self._cache[uid].dirty = True
            self._dirty.add(uid)
    
    async def save_user(self, uid):
        self.mark_dirty(uid)
        await self._save_dirty()
    
    def _clean_cache(self):
        now = time.time()
        del_ids = [uid for uid, ce in self._cache.items() if now - ce.timestamp > CACHE_TTL*2]
        for uid in del_ids: 
            del self._cache[uid]
            self._dirty.discard(uid)
        
        if len(self._cache) > MAX_CACHE:
            sorted_c = sorted(self._cache.items(), key=lambda x: x[1].timestamp)
            for uid, _ in sorted_c[:MAX_CACHE//2]: 
                del self._cache[uid]
                self._dirty.discard(uid)
    
    async def get_top_fast(self, limit=10, sort="gofra"):
        allowed_sorts = ["gofra", "cable_power", "zmiy_grams", "atm_count", 
                        "total_davki", "total_zmiy_grams", "experience"]
        
        if sort not in allowed_sorts:
            sort = "gofra"
        
        self.metrics.log_query()
        pool = await DatabaseManager.get_pool()
        async with pool.execute(f'''
            SELECT user_id, nickname, gofra, cable_power, zmiy_grams, 
                   atm_count, total_davki, total_zmiy_grams
            FROM users 
            ORDER BY {sort} DESC 
            LIMIT ?
        ''', (limit,)) as c:
            rows = await c.fetchall()
            return [dict(row) for row in rows]
    
    def get_stats(self):
        return {
            "cache_size": len(self._cache),
            "dirty_count": len(self._dirty),
            "metrics": self.metrics.get_stats()
        }

user_manager = UserDataManager()

def get_gofra_info(gofra_value):
    if gofra_value >= 10000:
        level = gofra_value // 1000
        speed = max(0.05, 0.3 - (level * 0.01))
        weight_bonus = 1 + ((level - 10) * 0.15)
        min_grams = round(700 * weight_bonus)
        max_grams = round(2000 * weight_bonus)
        
        return {
            "name": f"БОГ ГОФРЫ {level-9}",
            "emoji": "👁️‍🗨️",
            "atm_speed": round(speed, 2),
            "min_grams": min_grams,
            "max_grams": max_grams,
            "threshold": 10000,
            "next_threshold": gofra_value + 1000,
            "progress": (gofra_value % 1000) / 1000
        }
    elif gofra_value >= 1000:
        sublevel = (gofra_value - 1000) // 100
        speed = max(0.1, 0.3 - (sublevel * 0.01))
        weight_bonus = 1 + (sublevel * 0.08)
        min_grams = round(700 * weight_bonus)
        max_grams = round(2000 * weight_bonus)
        
        return {
            "name": f"Царь-гофра {sublevel+1}",
            "emoji": "🐉" + "🔥" * min(sublevel//10, 3),
            "atm_speed": round(speed, 2),
            "min_grams": min_grams,
            "max_grams": max_grams,
            "threshold": 1000,
            "next_threshold": 1000 + ((sublevel + 1) * 100),
            "progress": ((gofra_value - 1000) % 100) / 100
        }
    
    sorted_thresholds = sorted(GOFRY.items())
    current_info = None
    
    for threshold, info in sorted_thresholds:
        if gofra_value >= threshold:
            current_info = info.copy()
            current_info["threshold"] = threshold
        else:
            break
    
    if not current_info:
        current_info = GOFRY[1].copy()
        current_info["threshold"] = 1
    
    thresholds = list(GOFRY.keys())
    current_index = thresholds.index(current_info["threshold"])
    
    if current_index < len(thresholds) - 1:
        next_threshold = thresholds[current_index + 1]
        current_info["next_threshold"] = next_threshold
        current_info["progress"] = (gofra_value - current_info["threshold"]) / (next_threshold - current_info["threshold"])
    else:
        current_info["next_threshold"] = 1000
        current_info["progress"] = (gofra_value - current_info["threshold"]) / (1000 - current_info["threshold"])
    
    if "atm_speed" not in current_info:
        current_info["atm_speed"] = 1.0
    
    return current_info

async def get_patsan(uid, force=False): 
    return await user_manager.get_user(uid, force)

async def save_patsan(d): 
    uid = d.get("user_id")
    if uid: 
        if uid in user_manager._cache: 
            user_manager._cache[uid].data.update(d)
            user_manager._cache[uid].dirty = True
        await user_manager.save_user(uid)

async def davka_zmiy(uid):
    p = await user_manager.get_user(uid)
    
    if p.get("atm_count", 0) < 12:
        return False, None, "Нужны все 12 атмосфер! Сейчас: {}/12".format(p.get("atm_count", 0))
    
    gofra_info = get_gofra_info(p.get("gofra", 1))
    min_grams = gofra_info["min_grams"]
    max_grams = gofra_info["max_grams"]
    
    zmiy_grams = random.randint(min_grams, max_grams)
    
    p["atm_count"] = 0
    p["last_davka"] = int(time.time())
    p["last_update"] = int(time.time())
    
    p["zmiy_grams"] = p.get("zmiy_grams", 0.0) + zmiy_grams
    p["total_zmiy_grams"] = p.get("total_zmiy_grams", 0.0) + zmiy_grams
    p["total_davki"] = p.get("total_davki", 0) + 1
    
    exp_gained = zmiy_grams // 10
    p["experience"] = p.get("experience", 0) + exp_gained
    
    old_gofra = p.get("gofra", 1)
    new_gofra = old_gofra + exp_gained
    p["gofra"] = new_gofra
    
    cable_power_gain = zmiy_grams // 1000
    old_cable_power = p.get("cable_power", 1)
    p["cable_power"] = old_cable_power + cable_power_gain
    
    gofra_up = new_gofra > old_gofra
    
    user_manager.mark_dirty(uid)
    
    res = {
        "zmiy_grams": zmiy_grams,
        "exp_gained": exp_gained,
        "old_gofra": old_gofra,
        "new_gofra": new_gofra,
        "old_cable_power": old_cable_power,
        "new_cable_power": p["cable_power"],
        "cable_power_gain": cable_power_gain,
        "gofra_up": gofra_up,
        "gofra_info": get_gofra_info(new_gofra),
        "atm_speed": gofra_info["atm_speed"]
    }
    return True, p, res

async def uletet_zmiy(uid):
    p = await user_manager.get_user(uid)
    
    if p.get("zmiy_grams", 0) <= 0:
        return False, None, "Нечего отправлять!"
    
    zmiy_grams = p.get("zmiy_grams", 0.0)
    
    p["zmiy_grams"] = 0.0
    
    user_manager.mark_dirty(uid)
    
    res = {
        "zmiy_grams": zmiy_grams
    }
    return True, p, res

def calculate_pvp_chance(attacker, defender):
    chance = 50
    
    cable_diff = attacker.get("cable_power", 1) - defender.get("cable_power", 1)
    chance += cable_diff * 1.0
    
    gofra_diff = attacker.get("gofra", 1) - defender.get("gofra", 1)
    chance += (gofra_diff / 10) * 0.5
    
    return max(10, min(90, round(chance, 1)))

async def can_fight_pvp(user_id):
    """Проверяет, может ли пользователь участвовать в PvP"""
    pool = await get_connection()
    
    hour_ago = int(time.time()) - 3600
    async with pool.execute('''
        SELECT COUNT(*) as fight_count 
        FROM rademka_fights 
        WHERE (winner_id = ? OR loser_id = ?) 
        AND created_at > ?
    ''', (user_id, user_id, hour_ago)) as c:
        row = await c.fetchone()
        if row and row['fight_count'] >= 10:
            return False, "Лимит: 10 боёв в час"
    
    return True, "OK"

async def change_nickname(uid, nick):
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT nickname_changed FROM users WHERE user_id=?', (uid,)) as c:
        u = await c.fetchone()
        if not u: return False, "Нет юзера"
        if not u["nickname_changed"]:
            await pool.execute('UPDATE users SET nickname=?, nickname_changed=1 WHERE user_id=?', (nick, uid))
            await user_manager.get_user(uid, True)
            return True, "Ник изменён! (бесплатно)"
        else:
            return False, "Ник уже менялся! Больше нельзя."

async def get_top_players(limit=10, sort_by="gofra"):
    return await user_manager.get_top_fast(limit, sort_by)

async def save_rademka_fight(win, lose, money=0):
    pool = await DatabaseManager.get_pool()
    await pool.execute('''
        INSERT INTO rademka_fights (winner_id, loser_id, money_taken) 
        VALUES (?,?,?)
    ''', (win, lose, money))

async def get_connection():
    return await DatabaseManager.get_pool()

async def init_bot(): 
    logger.info(f"🚀 Инициализация бота | Storage: {STORAGE_DIR}")
    await DatabaseManager.get_pool()
    await user_manager.start_batch_saver()
    
    await DatabaseManager.create_backup()

async def shutdown(): 
    await user_manager._save_dirty()
    if DatabaseManager._pool: 
        await DatabaseManager._pool.close()
        DatabaseManager._pool = None

def calculate_atm_regen_time(user):
    gofra = user.get("gofra", 1)
    gofra_info = get_gofra_info(gofra)
    
    base_time_per_atm = ATM_BASE_TIME * gofra_info["atm_speed"]
    
    atm_needed = 12 - user.get("atm_count", 0)
    
    total_time = base_time_per_atm * atm_needed
    
    return {
        "per_atm": base_time_per_atm,
        "total": total_time,
        "needed": atm_needed,
        "gofra_speed": gofra_info["atm_speed"]
    }

if __name__ == "__main__":
    async def test():
        await init_bot()
        start = time.time()
        tasks = [get_patsan(i) for i in range(100)]
        await asyncio.gather(*tasks)
        print(f"100 юзеров за {time.time()-start:.2f}с")
        await shutdown()
    asyncio.run(test())

init_db = init_bot
