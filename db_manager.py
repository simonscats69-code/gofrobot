import asyncio, time, random, json, aiosqlite
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "bot_database.db")
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "30"))
MAX_CACHE = int(os.getenv("MAX_CACHE_SIZE", "500"))
ATM_MAX = 12  # Фиксировано
ATM_BASE_TIME = 86400  # 24 часа в секундах
BATCH_INT = 5

# Система гофры вместо уровней
GOFRY = {
    1: {"name": "Новая гофра", "emoji": "🆕", "atm_speed": 1.0, "min_cm": 1.0, "max_cm": 2.0},
    10: {"name": "Слегка разъезжена", "emoji": "🔄", "atm_speed": 0.9, "min_cm": 1.2, "max_cm": 2.3},
    25: {"name": "Рабочая гофра", "emoji": "⚙️", "atm_speed": 0.8, "min_cm": 1.5, "max_cm": 2.7},
    50: {"name": "Разъезжена хорошо", "emoji": "🔥", "atm_speed": 0.7, "min_cm": 1.8, "max_cm": 3.2},
    100: {"name": "Заезженная гофра", "emoji": "🏎️", "atm_speed": 0.6, "min_cm": 2.2, "max_cm": 3.8},
    200: {"name": "Убитая гофра", "emoji": "💀", "atm_speed": 0.5, "min_cm": 2.7, "max_cm": 4.5},
    500: {"name": "Легендарная гофра", "emoji": "👑", "atm_speed": 0.4, "min_cm": 3.3, "max_cm": 5.5},
    1000: {"name": "Царь-гофра", "emoji": "🐉", "atm_speed": 0.3, "min_cm": 4.0, "max_cm": 7.0}
}

class DatabaseManager:
    _pool = None
    @classmethod
    async def get_pool(cls):
        if not cls._pool:
            cls._pool = await aiosqlite.connect(DB_NAME, timeout=30)
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
                zmiy_cm REAL DEFAULT 0.0,
                dengi INTEGER DEFAULT 150,
                last_update INTEGER DEFAULT 0,
                last_davka INTEGER DEFAULT 0,
                atm_count INTEGER DEFAULT 12,
                max_atm INTEGER DEFAULT 12,
                experience INTEGER DEFAULT 0,
                total_davki INTEGER DEFAULT 0,
                total_zmiy_cm REAL DEFAULT 0.0
            );
            CREATE INDEX IF NOT EXISTS idx_gofra ON users(gofra DESC);
            CREATE INDEX IF NOT EXISTS idx_zmiy ON users(zmiy_cm DESC);
            
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

class UserCache:
    def __init__(self, data, timestamp):
        self.data, self.timestamp, self.dirty = data, timestamp, False

class UserDataManager:
    def __init__(self):
        self._cache, self._dirty, self._lock, self._save_task = {}, set(), asyncio.Lock(), None
    
    async def start_batch_saver(self):
        if not self._save_task:
            self._save_task = asyncio.create_task(self._save_loop())
    
    async def _save_loop(self):
        while True:
            await asyncio.sleep(BATCH_INT)
            await self._save_dirty()
    
    async def _save_dirty(self):
        async with self._lock:
            if not self._dirty: return
            to_save = [(uid, self._cache[uid].data) for uid in self._dirty if uid in self._cache and self._cache[uid].dirty]
            if to_save: await self._batch_save(to_save)
            self._dirty.clear()
    
    async def _batch_save(self, users):
        pool = await DatabaseManager.get_pool()
        vals = []
        for uid, d in users:
            vals.append((
                d.get("nickname", ""), 
                d.get("gofra", 1),
                d.get("zmiy_cm", 0.0),
                d.get("dengi", 150),
                int(time.time()),
                d.get("last_davka", 0),
                d.get("atm_count", 12),
                d.get("max_atm", 12),
                d.get("experience", 0),
                d.get("total_davki", 0),
                d.get("total_zmiy_cm", 0.0),
                uid
            ))
        await pool.executemany('''
            UPDATE users SET 
                nickname=?, gofra=?, zmiy_cm=?, dengi=?, 
                last_update=?, last_davka=?, atm_count=?, max_atm=?,
                experience=?, total_davki=?, total_zmiy_cm=?
            WHERE user_id=?
        ''', vals)
    
    async def get_user(self, uid, force=False):
        now = time.time()
        if not force and uid in self._cache and now - self._cache[uid].timestamp < CACHE_TTL:
            return self._cache[uid].data
        
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
    
    async def _create_user(self, uid):
        now = int(time.time())
        user = {
            "user_id": uid, 
            "nickname": f"Пацанчик_{uid}", 
            "gofra": 1,
            "zmiy_cm": 0.0,
            "dengi": 150,
            "last_update": now,
            "last_davka": 0,
            "atm_count": 12,
            "max_atm": 12,
            "experience": 0,
            "total_davki": 0,
            "total_zmiy_cm": 0.0
        }
        pool = await DatabaseManager.get_pool()
        await pool.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, nickname, last_update, atm_count) 
            VALUES (?,?,?,?)
        ''', (uid, user["nickname"], now, 12))
        return user
    
    async def _process_user(self, user):
        now = time.time()
        last_update = user.get("last_update", now)
        
        # Восстановление атмосфер в зависимости от гофры
        gofra = user.get("gofra", 1)
        gofra_info = get_gofra_info(gofra)
        atm_speed = gofra_info["atm_speed"]
        
        # Время восстановления одной атмосферы с учетом гофры
        atm_regen_time = ATM_BASE_TIME * atm_speed
        
        if user.get("atm_count", 12) < 12:
            time_passed = now - last_update
            if time_passed >= atm_regen_time:
                # Сколько атмосфер восстановилось
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
        if len(self._cache) > MAX_CACHE:
            sorted_c = sorted(self._cache.items(), key=lambda x: x[1].timestamp)
            for uid, _ in sorted_c[:MAX_CACHE//2]: 
                del self._cache[uid]
    
    async def get_top_fast(self, limit=10, sort="gofra"):
        pool = await DatabaseManager.get_pool()
        async with pool.execute(f'''
            SELECT user_id, nickname, gofra, zmiy_cm, dengi, atm_count, total_davki, total_zmiy_cm
            FROM users 
            ORDER BY {sort} DESC 
            LIMIT ?
        ''', (limit,)) as c:
            rows = await c.fetchall()
            return [dict(row) for row in rows]

user_manager = UserDataManager()

def get_gofra_info(gofra_value):
    """Получить информацию о гофре по значению"""
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
    
    # Добавляем прогресс до следующей гофры
    thresholds = list(GOFRY.keys())
    current_index = thresholds.index(current_info["threshold"])
    
    if current_index < len(thresholds) - 1:
        next_threshold = thresholds[current_index + 1]
        current_info["next_threshold"] = next_threshold
        current_info["progress"] = (gofra_value - current_info["threshold"]) / (next_threshold - current_info["threshold"])
    else:
        current_info["next_threshold"] = None
        current_info["progress"] = 1.0
    
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
    """Давка змия - можно только при полных 12 атмосферах"""
    p = await user_manager.get_user(uid)
    
    # Проверка атмосфер
    if p.get("atm_count", 0) < 12:
        return False, None, "Нужны все 12 атмосфер! Сейчас: {}/12".format(p.get("atm_count", 0))
    
    # Получаем информацию о гофре
    gofra_info = get_gofra_info(p.get("gofra", 1))
    min_cm = gofra_info["min_cm"]
    max_cm = gofra_info["max_cm"]
    
    # Генерируем длину кабеля в см
    cable_cm = round(random.uniform(min_cm, max_cm), 1)
    
    # Сбрасываем атмосферы
    p["atm_count"] = 0
    p["last_davka"] = int(time.time())
    p["last_update"] = int(time.time())
    
    # Добавляем змия
    p["zmiy_cm"] = p.get("zmiy_cm", 0.0) + cable_cm
    p["total_zmiy_cm"] = p.get("total_zmiy_cm", 0.0) + cable_cm
    p["total_davki"] = p.get("total_davki", 0) + 1
    
    # Добавляем опыт (гондра = опыт)
    exp_gained = int(cable_cm * 10)  # 1 см = 10 опыта
    p["experience"] = p.get("experience", 0) + exp_gained
    
    # Проверяем повышение гофры
    old_gofra = p.get("gofra", 1)
    new_gofra = old_gofra + exp_gained
    p["gofra"] = new_gofra
    
    gofra_up = new_gofra > old_gofra
    
    user_manager.mark_dirty(uid)
    
    res = {
        "cable_cm": cable_cm,
        "exp_gained": exp_gained,
        "old_gofra": old_gofra,
        "new_gofra": new_gofra,
        "gofra_up": gofra_up,
        "gofra_info": get_gofra_info(new_gofra),
        "atm_speed": gofra_info["atm_speed"]
    }
    return True, p, res

async def sdat_zmiy(uid):
    """Сдать змия"""
    p = await user_manager.get_user(uid)
    
    if p.get("zmiy_cm", 0) <= 0:
        return False, None, "Нечего сдавать!"
    
    zmiy_cm = p.get("zmiy_cm", 0.0)
    
    # Деньги за змия: 1 см = 100 руб + бонус за гофру
    base_money = int(zmiy_cm * 100)
    gofra_bonus = p.get("gofra", 1) * 5
    total_money = base_money + gofra_bonus
    
    p["dengi"] = p.get("dengi", 0) + total_money
    p["zmiy_cm"] = 0.0
    
    user_manager.mark_dirty(uid)
    
    res = {
        "zmiy_cm": zmiy_cm,
        "money": total_money,
        "base_money": base_money,
        "gofra_bonus": gofra_bonus
    }
    return True, p, res

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
    await DatabaseManager.get_pool()
    await user_manager.start_batch_saver()

async def shutdown(): 
    await user_manager._save_dirty()
    if DatabaseManager._pool: 
        await DatabaseManager._pool.close()
        DatabaseManager._pool = None

def calculate_atm_regen_time(user):
    """Рассчитать время восстановления атмосфер"""
    gofra = user.get("gofra", 1)
    gofra_info = get_gofra_info(gofra)
    
    # Базовое время восстановления одной атмосферы
    base_time_per_atm = ATM_BASE_TIME * gofra_info["atm_speed"]
    
    # Сколько атмосфер нужно восстановить
    atm_needed = 12 - user.get("atm_count", 0)
    
    # Общее время восстановления
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
