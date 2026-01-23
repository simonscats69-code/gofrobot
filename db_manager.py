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
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "60"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "30"))
MAX_CACHE = int(os.getenv("MAX_CACHE_SIZE", "100"))
ATM_MAX = 12
ATM_BASE_TIME = 7200
BATCH_INT = 5

BALANCE = {
    "UNIT_SCALE": 10.0,
    "DISPLAY_DECIMALS": 1,
    "GOFRA_EXP_PER_GRAM": 0.02,
    "MIN_GOFRA_EXP": 0.8,
    "GOFRA_SOFT_CAP": 500.0,
    "GOFRA_SOFT_CAP_MULT": 0.3,
    "CABLE_MM_PER_KG": 0.2,
    "MIN_CABLE_GAIN": 0.05,
    "CABLE_CHANCE_SMALL": 0.08,
    "PVP_GOFRA_MIN": 5.0,
    "PVP_GOFRA_MAX": 12.0,
    "PVP_CABLE_GAIN": 0.2,
    "PVP_CABLE_MULT": 0.02,
    "PVP_GOFRA_MULT": 0.0005,
}

GOFRY_MM = {
    10.0: {"name": "Новая гофра", "emoji": "🆕", "min_grams": 30, "max_grams": 100, "atm_speed": 1.0},
    50.0: {"name": "Слегка разъезжена", "emoji": "🔄", "min_grams": 45, "max_grams": 120, "atm_speed": 1.1},
    150.0: {"name": "Рабочая гофра", "emoji": "⚙️", "min_grams": 60, "max_grams": 150, "atm_speed": 1.2},
    300.0: {"name": "Разъезжена хорошо", "emoji": "🔥", "min_grams": 80, "max_grams": 190, "atm_speed": 1.3},
    600.0: {"name": "Заезженная гофра", "emoji": "🏎️", "min_grams": 110, "max_grams": 250, "atm_speed": 1.4},
    1200.0: {"name": "Убитая гофра", "emoji": "💀", "min_grams": 150, "max_grams": 320, "atm_speed": 1.5},
    2500.0: {"name": "Легендарная гофра", "emoji": "👑", "min_grams": 200, "max_grams": 420, "atm_speed": 1.6},
    5000.0: {"name": "Царь-гофра", "emoji": "🐉", "min_grams": 270, "max_grams": 550, "atm_speed": 1.7},
    10000.0: {"name": "БОГ ГОФРЫ", "emoji": "👁️‍🗨️", "min_grams": 350, "max_grams": 700, "atm_speed": 1.8},
    20000.0: {"name": "ВСЕЛЕННАЯ ГОФРА", "emoji": "🌌", "min_grams": 450, "max_grams": 900, "atm_speed": 2.0},
}

def mm_to_cm(mm_value):
    return round(mm_value / BALANCE["UNIT_SCALE"], BALANCE["DISPLAY_DECIMALS"])

def cm_to_mm(cm_value):
    return cm_value * BALANCE["UNIT_SCALE"]

def format_length(mm_value):
    cm = mm_to_cm(mm_value)
    return f"{cm:.{BALANCE['DISPLAY_DECIMALS']}f} см"

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
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_connection(cls):
        async with cls._lock:
            if not cls._pool:
                logger.info(f"🔌 Создание пула соединений к БД: {DB_PATH}")
                cls._pool = await aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT)
                cls._pool.row_factory = aiosqlite.Row
                await cls._create_tables(cls._pool)
        
        return await aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False)
    
    @staticmethod
    async def _create_tables(conn=None):
        if conn is None:
            conn = await DatabaseManager.get_connection()
        
        await conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, 
                nickname TEXT DEFAULT '', 
                gofra_mm REAL DEFAULT 10.0,
                cable_mm REAL DEFAULT 10.0,
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
                created_at INTEGER DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_win ON rademka_fights(winner_id);
            CREATE INDEX IF NOT EXISTS idx_lose ON rademka_fights(loser_id);
            
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                chat_title TEXT DEFAULT '',
                chat_type TEXT DEFAULT 'group',
                is_active BOOLEAN DEFAULT TRUE,
                created_at INTEGER DEFAULT (strftime('%s','now')),
                last_activity INTEGER DEFAULT (strftime('%s','now'))
            );
            
            CREATE TABLE IF NOT EXISTS chat_stats (
                chat_id INTEGER,
                user_id INTEGER,
                total_zmiy_grams REAL DEFAULT 0.0,
                total_davki INTEGER DEFAULT 0,
                last_davka_at INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id),
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
            );
            
            CREATE TABLE IF NOT EXISTS chat_top (
                chat_id INTEGER,
                user_id INTEGER,
                total_zmiy_grams REAL DEFAULT 0.0,
                rank INTEGER DEFAULT 0,
                last_updated INTEGER DEFAULT (strftime('%s','now')),
                PRIMARY KEY (chat_id, user_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_chat_stats ON chat_stats(chat_id, total_zmiy_grams DESC);
            CREATE INDEX IF NOT EXISTS idx_chat_top ON chat_top(chat_id, rank);
        ''')
        await conn.commit()
        await conn.close()
    
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
                    
        except Exception as e:
            logger.error(f"⚠️ Бэкап не удался: {e}")

class ChatManager:
    @staticmethod
    async def register_chat(chat_id, chat_title="", chat_type="group"):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            await conn.execute('''
                INSERT OR REPLACE INTO chats 
                (chat_id, chat_title, chat_type, last_activity, is_active)
                VALUES (?,?,?,?,?)
            ''', (chat_id, chat_title, chat_type, int(time.time()), True))
            await conn.commit()
    
    @staticmethod
    async def update_chat_activity(chat_id):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            await conn.execute('''
                UPDATE chats SET last_activity = ? WHERE chat_id = ?
            ''', (int(time.time()), chat_id))
            await conn.commit()
    
    @staticmethod
    async def record_davka(chat_id, user_id, zmiy_grams):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            await conn.execute('''
                INSERT INTO chat_stats (chat_id, user_id, total_zmiy_grams, total_davki, last_davka_at)
                VALUES (?,?,?,1,?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    total_zmiy_grams = total_zmiy_grams + ?,
                    total_davki = total_davki + 1,
                    last_davka_at = ?
            ''', (chat_id, user_id, zmiy_grams, int(time.time()), zmiy_grams, int(time.time())))
            
            await conn.execute('''
                INSERT OR REPLACE INTO chat_top (chat_id, user_id, total_zmiy_grams, last_updated)
                VALUES (?,?,?,?)
            ''', (chat_id, user_id, 
                  await ChatManager.get_user_total_in_chat(chat_id, user_id),
                  int(time.time())))
            
            await conn.commit()
            await ChatManager.update_chat_ranks(chat_id)
    
    @staticmethod
    async def get_user_total_in_chat(chat_id, user_id):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            async with conn.execute('''
                SELECT total_zmiy_grams FROM chat_stats 
                WHERE chat_id = ? AND user_id = ?
            ''', (chat_id, user_id)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0.0
    
    @staticmethod
    async def update_chat_ranks(chat_id):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            async with conn.execute('''
                SELECT user_id, total_zmiy_grams FROM chat_stats
                WHERE chat_id = ?
                ORDER BY total_zmiy_grams DESC
            ''', (chat_id,)) as cursor:
                rows = await cursor.fetchall()
                
            for rank, (user_id, total_grams) in enumerate(rows, 1):
                await conn.execute('''
                    UPDATE chat_top SET rank = ?, last_updated = ?
                    WHERE chat_id = ? AND user_id = ?
                ''', (rank, int(time.time()), chat_id, user_id))
            
            await conn.commit()
    
    @staticmethod
    async def get_chat_top(chat_id, limit=10):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            async with conn.execute('''
                SELECT ct.user_id, ct.rank, ct.total_zmiy_grams, u.nickname
                FROM chat_top ct
                LEFT JOIN users u ON ct.user_id = u.user_id
                WHERE ct.chat_id = ?
                ORDER BY ct.rank
                LIMIT ?
            ''', (chat_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    @staticmethod
    async def get_chat_stats(chat_id):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            async with conn.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as total_players,
                    SUM(total_zmiy_grams) as total_zmiy_all,
                    SUM(total_davki) as total_davki_all,
                    MAX(last_davka_at) as last_activity
                FROM chat_stats 
                WHERE chat_id = ?
            ''', (chat_id,)) as cursor:
                stats = await cursor.fetchone()
            
            week_ago = int(time.time()) - 604800
            async with conn.execute('''
                SELECT COUNT(DISTINCT user_id) as active_players
                FROM chat_stats 
                WHERE chat_id = ? AND last_davka_at > ?
            ''', (chat_id, week_ago)) as cursor:
                active = await cursor.fetchone()
            
            return {
                "total_players": stats[0] if stats and stats[0] else 0,
                "total_zmiy_all": stats[1] if stats and stats[1] else 0.0,
                "total_davki_all": stats[2] if stats and stats[2] else 0,
                "last_activity": stats[3] if stats and stats[3] else 0,
                "active_players": active[0] if active and active[0] else 0
            }

class UserCache:
    def __init__(self, data, timestamp):
        self.data = data
        self.timestamp = timestamp
        self.dirty = False

class UserDataManager:
    def __init__(self):
        self._cache = {}
        self._dirty = set()
        self._lock = asyncio.Lock()
        self._save_task = None
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
    
    async def _batch_save(self, users):
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            try:
                await conn.execute("BEGIN TRANSACTION")
                for uid, d in users:
                    await conn.execute('''
                        INSERT OR REPLACE INTO users 
                        (user_id, nickname, gofra_mm, cable_mm, gofra, cable_power, zmiy_grams, 
                         last_update, last_davka, atm_count, max_atm,
                         experience, total_davki, total_zmiy_grams, nickname_changed)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        uid,
                        d.get("nickname", ""), 
                        d.get("gofra_mm", 10.0),
                        d.get("cable_mm", 10.0),
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
                        d.get("nickname_changed", False)
                    ))
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise e
    
    async def get_user(self, uid, force=False):
        now = time.time()
        
        if not force and uid in self._cache and now - self._cache[uid].timestamp < CACHE_TTL:
            self.metrics.log_cache_hit()
            return self._cache[uid].data
        
        self.metrics.log_cache_miss()
        self.metrics.log_query()
        
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('SELECT * FROM users WHERE user_id=?', (uid,)) as c:
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
            async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
                conn.row_factory = aiosqlite.Row
                placeholders = ','.join('?' * len(to_fetch))
                async with conn.execute(f'''
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
            "gofra_mm": 10.0,
            "cable_mm": 10.0,
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
        
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            await conn.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, nickname, last_update, atm_count, nickname_changed, gofra_mm, cable_mm) 
                VALUES (?,?,?,?,?,?,?)
            ''', (uid, user["nickname"], now, 12, False, 10.0, 10.0))
            await conn.commit()
        
        return user
    
    async def _process_user(self, user):
        now = time.time()
        last_update = user.get("last_update", now)
        
        gofra_mm = user.get("gofra_mm", 10.0)
        gofra_info = get_gofra_info(gofra_mm)
        atm_speed = gofra_info["atm_speed"]
        
        atm_regen_time = ATM_BASE_TIME / atm_speed
        
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
        async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(f'''
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

def get_gofra_info(gofra_value_mm):
    if gofra_value_mm >= 100000.0:
        meters = gofra_value_mm / 1000.0
        speed = 2.5 + (meters / 100) * 0.1
        weight_bonus = 1 + ((meters - 100) / 50) * 0.05
        min_grams = round(1000 * weight_bonus)
        max_grams = round(2500 * weight_bonus)
        
        return {
            "name": f"КОСМИЧЕСКАЯ ГОФРА {int(meters)}м",
            "emoji": "🚀",
            "atm_speed": round(speed, 2),
            "min_grams": min_grams,
            "max_grams": max_grams,
            "threshold": 100000.0,
            "next_threshold": gofra_value_mm + 5000.0,
            "progress": (gofra_value_mm % 5000.0) / 5000.0,
            "length_mm": gofra_value_mm,
            "length_display": f"{meters:.1f} м"
        }
    
    sorted_thresholds = sorted(GOFRY_MM.items())
    current_info = None
    
    for threshold_mm, info in sorted_thresholds:
        if gofra_value_mm >= threshold_mm:
            current_info = info.copy()
            current_info["threshold"] = threshold_mm
        else:
            break
    
    if not current_info:
        current_info = GOFRY_MM[10.0].copy()
        current_info["threshold"] = 10.0
    
    thresholds = list(GOFRY_MM.keys())
    current_index = thresholds.index(current_info["threshold"])
    
    if current_index < len(thresholds) - 1:
        next_threshold = thresholds[current_index + 1]
        current_info["next_threshold"] = next_threshold
        current_info["progress"] = (gofra_value_mm - current_info["threshold"]) / (next_threshold - current_info["threshold"]) if (next_threshold - current_info["threshold"]) > 0 else 0
    else:
        current_info["next_threshold"] = 100000.0
        current_info["progress"] = (gofra_value_mm - current_info["threshold"]) / (100000.0 - current_info["threshold"]) if (100000.0 - current_info["threshold"]) > 0 else 0
    
    current_info["length_mm"] = gofra_value_mm
    current_info["length_display"] = format_length(gofra_value_mm)
    
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

async def davka_zmiy(uid, chat_id=None):
    p = await user_manager.get_user(uid)
    
    if p.get("atm_count", 0) < 12:
        return False, None, "Нужны все 12 атмосфер! Сейчас: {}/12".format(p.get("atm_count", 0))
    
    gofra_info = get_gofra_info(p.get("gofra_mm", 10.0))
    min_grams = gofra_info["min_grams"]
    max_grams = gofra_info["max_grams"]
    
    zmiy_grams = random.randint(min_grams, max_grams)
    
    p["atm_count"] = 0
    p["last_davka"] = int(time.time())
    p["last_update"] = int(time.time())
    
    p["zmiy_grams"] = p.get("zmiy_grams", 0.0) + zmiy_grams
    p["total_zmiy_grams"] = p.get("total_zmiy_grams", 0.0) + zmiy_grams
    p["total_davki"] = p.get("total_davki", 0) + 1
    
    current_gofra_mm = p.get("gofra_mm", 10.0)
    
    base_exp_mm = zmiy_grams * BALANCE["GOFRA_EXP_PER_GRAM"]
    min_exp_mm = BALANCE["MIN_GOFRA_EXP"]
    exp_gained_mm = max(min_exp_mm, base_exp_mm)
    
    if current_gofra_mm > BALANCE["GOFRA_SOFT_CAP"]:
        over_cap = current_gofra_mm - BALANCE["GOFRA_SOFT_CAP"]
        reduction = 1.0 - (over_cap / (over_cap + 5000.0)) * 0.7
        exp_gained_mm *= max(BALANCE["GOFRA_SOFT_CAP_MULT"], reduction)
    
    exp_gained_mm = round(exp_gained_mm, 2)
    
    old_gofra_mm = current_gofra_mm
    new_gofra_mm = old_gofra_mm + exp_gained_mm
    p["gofra_mm"] = new_gofra_mm
    p["experience"] = p.get("experience", 0) + int(exp_gained_mm * 10)
    
    current_cable_mm = p.get("cable_mm", 10.0)
    cable_gain_mm = (zmiy_grams / 1000.0) * BALANCE["CABLE_MM_PER_KG"]
    
    if cable_gain_mm < BALANCE["MIN_CABLE_GAIN"]:
        if random.random() < BALANCE["CABLE_CHANCE_SMALL"]:
            cable_gain_mm = BALANCE["MIN_CABLE_GAIN"]
        else:
            cable_gain_mm = 0
    
    cable_gain_mm = round(cable_gain_mm, 2)
    old_cable_mm = current_cable_mm
    new_cable_mm = old_cable_mm + cable_gain_mm
    p["cable_mm"] = new_cable_mm
    
    p["gofra"] = int(new_gofra_mm / 10)
    p["cable_power"] = int(new_cable_mm / 5)
    
    if chat_id:
        await ChatManager.record_davka(chat_id, uid, zmiy_grams)
    
    user_manager.mark_dirty(uid)
    
    res = {
        "zmiy_grams": zmiy_grams,
        "exp_gained_mm": exp_gained_mm,
        "old_gofra_mm": old_gofra_mm,
        "new_gofra_mm": new_gofra_mm,
        "old_cable_mm": old_cable_mm,
        "new_cable_mm": new_cable_mm,
        "cable_gain_mm": cable_gain_mm,
        "gofra_up": new_gofra_mm > old_gofra_mm,
        "gofra_info": get_gofra_info(new_gofra_mm),
        "atm_speed": gofra_info["atm_speed"],
        "chat_id": chat_id
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
    base_chance = 50
    
    attacker_cable_mm = attacker.get("cable_mm", 10.0)
    defender_cable_mm = defender.get("cable_mm", 10.0)
    cable_diff_mm = attacker_cable_mm - defender_cable_mm
    base_chance += cable_diff_mm * BALANCE["PVP_CABLE_MULT"]
    
    attacker_gofra_mm = attacker.get("gofra_mm", 10.0)
    defender_gofra_mm = defender.get("gofra_mm", 10.0)
    gofra_diff_mm = attacker_gofra_mm - defender_gofra_mm
    base_chance += gofra_diff_mm * BALANCE["PVP_GOFRA_MULT"]
    
    random_factor = random.uniform(-5, 5)
    base_chance += random_factor
    
    return max(15, min(85, round(base_chance, 1)))

async def can_fight_pvp(user_id):
    async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
        hour_ago = int(time.time()) - 3600
        async with conn.execute('''
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
    async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
        async with conn.execute('SELECT * FROM users WHERE user_id=?', (uid,)) as c:
            u = await c.fetchone()
            if not u: 
                return False, "Нет юзера"

            # Убрано ограничение на смену ника
            await conn.execute('UPDATE users SET nickname=? WHERE user_id=?', (nick, uid))
            await conn.commit()
            await user_manager.get_user(uid, True)
            return True, "Ник изменён!"

async def get_top_players(limit=10, sort_by="gofra"):
    return await user_manager.get_top_fast(limit, sort_by)

async def save_rademka_fight(win, lose):
    async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False) as conn:
        await conn.execute('''
            INSERT INTO rademka_fights (winner_id, loser_id)
            VALUES (?,?)
        ''', (win, lose))
        await conn.commit()

async def get_connection():
    return await DatabaseManager.get_connection()

async def init_bot(): 
    logger.info(f"🚀 Инициализация бота | Storage: {STORAGE_DIR}")
    await DatabaseManager.get_connection()
    await user_manager.start_batch_saver()
    await DatabaseManager.create_backup()

async def shutdown(): 
    await user_manager._save_dirty()
    if DatabaseManager._pool: 
        await DatabaseManager._pool.close()
        DatabaseManager._pool = None

def calculate_atm_regen_time(user):
    gofra = user.get("gofra_mm", 10.0)
    gofra_info = get_gofra_info(gofra)
    
    base_time_per_atm = ATM_BASE_TIME / gofra_info["atm_speed"]
    
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
