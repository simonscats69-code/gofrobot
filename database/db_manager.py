import asyncio, time, random, json, aiosqlite
from typing import Optional, List, Dict, Any

ATM_MAX, ATM_TIME, DB_NAME = 12, 600, "bot_database.db"
CACHE_TTL, MAX_CACHE, BATCH_INT = 30, 500, 5

RANKS = {1:("👶","Пацанчик"), 11:("👊","Браток"), 51:("👑","Авторитет"), 
         201:("🐉","Царь гофры"), 501:("🏛️","Император"), 1001:("💩","БОГ ГОВНА")}

SPECS = {
    "davila": {"name":"Давила", "description":"Мастер давления", "req":{"skill_davka":5,"zmiy":50.0},
               "price":1500, "bon":{"davka_mul":1.5, "atm_red":1}},
    "ohotnik": {"name":"Охотник", "description":"Находит двенашки", "req":{"skill_nahodka":5,"inv_contains":"двенашка"},
                "price":1200, "bon":{"find_chance":0.15, "rare_chance":0.05}},
    "neprobivaemy": {"name":"Непробиваемый", "description":"Железные кишки", "req":{"skill_zashita":5,"avtoritet":20},
                      "price":2000, "bon":{"atm_regen":0.9, "rad_def":0.15}}
}

CRAFT = {
    "супер_двенашка": {"name":"Супер-двенашка", "description":"Удача +1ч", "ing":{"двенашка":3,"деньги":500},
                       "res":{"item":"супер_двенашка","dur":3600}, "chance":1.0},
    "вечный_двигатель": {"name":"Вечный двигатель", "description":"Восстановление атмосфер", "ing":{"атмосфера":5,"энергетик":1},
                         "res":{"item":"вечный_двигатель","dur":86400}, "chance":0.8},
    "царский_обед": {"name":"Царский обед", "description":"Макс буст 30м", "ing":{"курвасаны":1,"ряженка":1,"деньги":300},
                     "res":{"item":"царский_обед","dur":1800}, "chance":1.0},
    "бустер_атмосфер": {"name":"Бустер атмосфер", "description":"+3 к макс атмосферам", "ing":{"энергетик":2,"двенашка":1,"деньги":2000},
                        "res":{"item":"бустер_атмосфер"}, "chance":0.7}
}

ACH_LEVELS = {
    "zmiy_collector": {"name":"Коллекционер змия", "lvls":[(10,50,"Новичок",10),(100,300,"Любитель",50),
                                                          (1000,1500,"Профессионал",200),(10000,5000,"КОРОЛЬ",1000)]},
    "money_maker": {"name":"Денежный мешок", "lvls":[(1000,100,"Бедолага",10),(10000,1000,"Состоятельный",100),
                                                    (100000,5000,"Олигарх",500),(1000000,25000,"РОТШИЛЬД",2500)]},
    "rademka_king": {"name":"Король радёмок", "lvls":[(5,200,"Задира",20),(25,1000,"Гроза района",100),
                                                     (100,5000,"Неприкасаемый",500),(500,25000,"ЛЕГЕНДА",2500)]}
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
                user_id INTEGER PRIMARY KEY, nickname TEXT DEFAULT '', avtoritet INTEGER DEFAULT 1,
                zmiy REAL DEFAULT 0.0, dengi INTEGER DEFAULT 150, last_update INTEGER DEFAULT 0,
                last_daily INTEGER DEFAULT 0, atm_count INTEGER DEFAULT 12, max_atm INTEGER DEFAULT 12,
                skill_davka INTEGER DEFAULT 1, skill_zashita INTEGER DEFAULT 1, skill_nahodka INTEGER DEFAULT 1,
                specialization TEXT DEFAULT '', experience INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
                inventory TEXT DEFAULT '[]', upgrades TEXT DEFAULT '{}', active_boosts TEXT DEFAULT '{}',
                achievements TEXT DEFAULT '[]', crafted_items TEXT DEFAULT '[]', rademka_scouts INTEGER DEFAULT 0,
                nickname_changed BOOLEAN DEFAULT FALSE
            );
            CREATE INDEX IF NOT EXISTS idx_av ON users(avtoritet DESC);
            CREATE INDEX IF NOT EXISTS idx_money ON users(dengi DESC);
            CREATE INDEX IF NOT EXISTS idx_lvl ON users(level DESC);
            
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER, achievement_id TEXT, progress REAL DEFAULT 0,
                level INTEGER DEFAULT 0, PRIMARY KEY (user_id, achievement_id)
            );
            
            CREATE TABLE IF NOT EXISTS rademka_fights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                winner_id INTEGER, loser_id INTEGER, money_taken INTEGER DEFAULT 0,
                item_stolen TEXT, scouted BOOLEAN DEFAULT FALSE, created_at INTEGER DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_win ON rademka_fights(winner_id);
            CREATE INDEX IF NOT EXISTS idx_lose ON rademka_fights(loser_id);
            
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER, achievement_id TEXT, 
                unlocked_at INTEGER DEFAULT (strftime('%s','now')),
                PRIMARY KEY (user_id, achievement_id)
            );
            
            CREATE TABLE IF NOT EXISTS craft_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, recipe_id TEXT, success BOOLEAN,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            );
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
            vals.append((d.get("nickname",""), d.get("avtoritet",1), d.get("zmiy",0.0), d.get("dengi",150),
                        int(time.time()), d.get("last_daily",0), d.get("atm_count",12), d.get("max_atm",12),
                        d.get("skill_davka",1), d.get("skill_zashita",1), d.get("skill_nahodka",1),
                        d.get("specialization",""), d.get("experience",0), d.get("level",1),
                        json.dumps(d.get("inventory",[])), json.dumps(d.get("upgrades",{})),
                        json.dumps(d.get("active_boosts",{})), json.dumps(d.get("achievements",[])),
                        json.dumps(d.get("crafted_items",[])), d.get("rademka_scouts",0), 
                        d.get("nickname_changed", False), uid))
        await pool.executemany('''
            UPDATE users SET nickname=?, avtoritet=?, zmiy=?, dengi=?, last_update=?, last_daily=?,
            atm_count=?, max_atm=?, skill_davka=?, skill_zashita=?, skill_nahodka=?, specialization=?,
            experience=?, level=?, inventory=?, upgrades=?, active_boosts=?, achievements=?,
            crafted_items=?, rademka_scouts=?, nickname_changed=? WHERE user_id=?
        ''', vals)
    
    async def get_user(self, uid, force=False):
        now = time.time()
        if not force and uid in self._cache and now - self._cache[uid].timestamp < CACHE_TTL:
            return self._cache[uid].data
        
        pool = await DatabaseManager.get_pool()
        async with pool.execute('SELECT * FROM users WHERE user_id=?', (uid,)) as c:
            row = await c.fetchone()
            if row: user = dict(row); await self._process_user(user)
            else: user = await self._create_user(uid)
        
        self._cache[uid] = UserCache(user, now)
        if len(self._cache) > MAX_CACHE: self._clean_cache()
        return user
    
    async def _create_user(self, uid):
        now = int(time.time())
        user = {
            "user_id": uid, "nickname": f"Пацанчик_{uid}", "avtoritet": 1, "zmiy": 0.0, "dengi": 150,
            "last_update": now, "last_daily": 0, "atm_count": 12, "max_atm": 12, "skill_davka": 1,
            "skill_zashita": 1, "skill_nahodka": 1, "specialization": "", "experience": 0, "level": 1,
            "inventory": ["двенашка", "энергетик"], "upgrades": {}, "active_boosts": {},
            "achievements": [], "crafted_items": [], "rademka_scouts": 0, "nickname_changed": False
        }
        pool = await DatabaseManager.get_pool()
        await pool.execute('INSERT OR IGNORE INTO users (user_id, nickname, last_update, inventory) VALUES (?,?,?,?)',
                          (uid, user["nickname"], now, json.dumps(user["inventory"])))
        return user
    
    async def _process_user(self, user):
        now = time.time()
        passed = now - user.get("last_update", now)
        if passed >= ATM_TIME:
            max_a, cur_a = user.get("max_atm", ATM_MAX), user.get("atm_count", 0)
            regen = passed // ATM_TIME
            if regen > 0:
                user["atm_count"] = min(max_a, cur_a + regen)
                user["last_update"] = now - (passed % ATM_TIME)
        
        for field in ["inventory","upgrades","active_boosts","achievements","crafted_items"]:
            val = user.get(field)
            if isinstance(val, str):
                try: user[field] = json.loads(val) if val else ([] if field in ["inventory","achievements","crafted_items"] else {})
                except: user[field] = [] if field in ["inventory","achievements","crafted_items"] else {}
        
        av = user.get("avtoritet", 1)
        rank_name, rank_emoji = get_rank(av)
        user.update({"rank_emoji": rank_emoji, "rank_name": rank_name})
    
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
        for uid in del_ids: del self._cache[uid]
        if len(self._cache) > MAX_CACHE:
            sorted_c = sorted(self._cache.items(), key=lambda x: x[1].timestamp)
            for uid, _ in sorted_c[:MAX_CACHE//2]: del self._cache[uid]
    
    async def get_top_fast(self, limit=10, sort="avtoritet"):
        pool = await DatabaseManager.get_pool()
        async with pool.execute(f'SELECT * FROM users ORDER BY {sort} DESC LIMIT ?', (limit,)) as c:
            rows = await c.fetchall()
            result = []
            for row in rows:
                user = dict(row)
                await self._process_user(user)
                result.append(user)
            return result

user_manager = UserDataManager()

def get_rank(av):
    for threshold, (emoji, name) in sorted(RANKS.items()):
        if av >= threshold:
            return name, emoji
    return "Пацанчик", "👶"

async def get_patsan(uid): return await user_manager.get_user(uid)
async def get_patsan_cached(uid): return await user_manager.get_user(uid)
async def save_patsan(d): 
    uid = d.get("user_id")
    if uid: 
        if uid in user_manager._cache: user_manager._cache[uid].data.update(d); user_manager._cache[uid].dirty = True
        await user_manager.save_user(uid)

async def davka_zmiy(uid):
    p = await user_manager.get_user(uid)
    cost = 2
    if p.get("upgrades",{}).get("tea_slivoviy"): cost = max(1, cost-1)
    bon = SPECS.get(p.get("specialization",""),{}).get("bon",{})
    if bon.get("atm_red"): cost = max(1, cost-bon["atm_red"])
    
    if p.get("atm_count",0) < cost: return None, "Не хватает атмосфер!"
    p["atm_count"] = p.get("atm_count",0) - cost
    
    base = random.randint(200,1500) + p.get("skill_davka",1)*100
    mul = 1.0
    if p.get("upgrades",{}).get("ryazhenka"): mul = 1.75
    if bon.get("davka_mul"): mul *= bon["davka_mul"]
    total = int(base * mul)
    
    exp = min(10, total//100)
    p["experience"] = p.get("experience",0) + exp
    await check_lvl(p)
    p["zmiy"] = p.get("zmiy",0.0) + total/1000
    
    chance = p.get("skill_nahodka",1)*0.05
    if p.get("upgrades",{}).get("bubbleki"): chance += 0.35
    if bon.get("find_chance"): chance += bon["find_chance"]
    
    found, rare = False, None
    if random.random() < chance:
        if "inventory" not in p: p["inventory"] = []
        p["inventory"].append("двенашка")
        found = True
        if bon.get("rare_chance") and random.random() < bon["rare_chance"]:
            rare = random.choice(["золотая_двенашка","кристалл_атмосферы","секретная_схема"])
            p["inventory"].append(rare)
    
    user_manager.mark_dirty(uid)
    await upd_ach(uid, "zmiy_collector", total/1000)
    
    kg, g = total//1000, total%1000
    w = f"{kg}кг {g}г" if g else f"{kg}кг"
    res = {"cost":cost, "weight":w, "wm":w, "total_grams":total, "dvenashka_found":found, "rare_item_found":rare, "exp_gained":exp}
    return p, res

async def buy_spec(uid, spec):
    p = await user_manager.get_user(uid)
    if spec not in SPECS: return False, "Нет такой спецы"
    s = SPECS[spec]
    for k,v in s.get("req",{}).items():
        if k == "inv_contains":
            if v not in p.get("inventory",[]): return False, f"Нужен: {v}"
        elif p.get(k,0) < v: return False, f"Недостаточно {k}: {v}"
    if p.get("dengi",0) < s.get("price",0): return False, f"Не хватает {s['price']-p['dengi']}р"
    if p.get("specialization"): return False, "Уже есть спеца"
    p["dengi"] = p.get("dengi",0) - s["price"]
    p["specialization"] = spec
    await unlock_ach(uid, "first_spec", "Первая специализация", 500)
    user_manager.mark_dirty(uid)
    return True, f"✅ Куплена '{s['name']}' за {s['price']}р!"

async def get_available_specs(uid):
    p = await user_manager.get_user(uid)
    avail = []
    for sid, s in SPECS.items():
        ok, miss = True, []
        for k,v in s.get("req",{}).items():
            if k == "inv_contains":
                if v not in p.get("inventory",[]): ok=False; miss.append(f"Предмет: {v}")
            elif p.get(k,0) < v: ok=False; miss.append(f"{k}: {p.get(k,0)}/{v}")
        avail.append({"id":sid, "name":s.get("name",""), "description":s.get("description",""), "price":s.get("price",0),
                      "available":ok, "missing":miss, "bon":s.get("bon",{})})
    return avail

async def craft_item(uid, rid):
    p = await user_manager.get_user(uid)
    if rid not in CRAFT: return False, "Нет рецепта", {}
    r = CRAFT[rid]
    inv = p.get("inventory",[])
    cnt = {i:inv.count(i) for i in set(inv)}
    miss = []
    for itm, need in r.get("ing",{}).items():
        if itm == "деньги":
            if p.get("dengi",0) < need: miss.append(f"Деньги: {need}р")
        elif cnt.get(itm,0) < need: miss.append(f"{itm}: {cnt.get(itm,0)}/{need}")
    if miss: return False, f"Не хватает: {', '.join(miss)}", {}
    
    for itm, need in r.get("ing",{}).items():
        if itm == "деньги": 
            p["dengi"] = p.get("dengi",0) - need
        else:
            for _ in range(need): 
                if itm in p.get("inventory",[]): 
                    p["inventory"].remove(itm)
    
    ok = random.random() < r.get("chance",0)
    if ok:
        res = r.get("res",{})
        if res.get("item"): 
            if "inventory" not in p: p["inventory"] = []
            p["inventory"].append(res["item"])
            if res.get("dur"): 
                if "active_boosts" not in p: p["active_boosts"] = {}
                p["active_boosts"][res["item"]] = int(time.time()) + res["dur"]
        crafted = p.get("crafted_items",[])
        crafted.append({"recipe":rid, "item":res.get("item",""), "time":int(time.time())})
        p["crafted_items"] = crafted
        await unlock_ach(uid, "first_craft", "Первый крафт", 100)
        msg = f"✅ Успешно: {r['name']}!"
    else: 
        msg = f"❌ Неудача: {r['name']}"
    
    pool = await DatabaseManager.get_pool()
    await pool.execute('INSERT INTO craft_history (user_id, recipe_id, success) VALUES (?,?,?)', (uid,rid,ok))
    user_manager.mark_dirty(uid)
    return ok, msg, r.get("res",{})

async def get_craftable(uid):
    p = await user_manager.get_user(uid)
    inv = p.get("inventory",[])
    cnt = {i:inv.count(i) for i in set(inv)}
    craftable = []
    for rid, r in CRAFT.items():
        ok, miss = True, []
        for itm, need in r.get("ing",{}).items():
            if itm == "деньги":
                if p.get("dengi",0) < need: ok=False; miss.append(f"Деньги: {need}р")
            elif cnt.get(itm,0) < need: ok=False; miss.append(f"{itm}: {cnt.get(itm,0)}/{need}")
        craftable.append({"id":rid, "name":r.get("name",""), "description":r.get("description",""), "ing":r.get("ing",{}),
                          "can_craft":ok, "missing":miss, "success_chance":r.get("chance",0), "res":r.get("res",{})})
    return craftable

async def sdat_zmiy(uid):
    p = await user_manager.get_user(uid)
    if p.get("zmiy",0) <= 0: return None, "Нечего сдавать!"
    money = int(p["zmiy"] * 62.5) + p.get("avtoritet",1)*8
    old = p["zmiy"]
    p["dengi"] = p.get("dengi",0) + money
    p["zmiy"] = 0
    exp = min(20, money//100)
    p["experience"] = p.get("experience",0) + exp
    await check_lvl(p)
    user_manager.mark_dirty(uid)
    await upd_ach(uid, "money_maker", money)
    res = {"old":old, "oz":old, "tm":money, "money":money, "avtoritet_bonus":p.get("avtoritet",1)*8, "exp_gained":exp}
    return p, res

async def buy_upgrade(uid, upg):
    p = await user_manager.get_user(uid)
    prices = {"ryazhenka":300, "tea_slivoviy":500, "bubbleki":800, "kuryasany":1500}
    if upg not in prices: return None, "Нет такого"
    if p.get("upgrades",{}).get(upg): return None, "Уже куплено"
    price = prices[upg]
    if p.get("dengi",0) < price: return None, f"Не хватает {price-p['dengi']}р"
    p["dengi"] = p.get("dengi",0) - price
    if "upgrades" not in p: p["upgrades"] = {}
    p["upgrades"][upg] = True
    if upg == "kuryasany": 
        p["avtoritet"] = p.get("avtoritet",1) + 2
    user_manager.mark_dirty(uid)
    all_upg = ["ryazhenka","tea_slivoviy","bubbleki","kuryasany"]
    if all(p.get("upgrades",{}).get(u,False) for u in all_upg):
        await unlock_ach(uid, "all_upg", "Все нагнетатели", 1500)
    return p, f"✅ Куплено '{upg}' за {price}р!"

async def pump_skill(uid, skill):
    p = await user_manager.get_user(uid)
    prices = {"davka":180, "zashita":270, "nahodka":225}
    cost = prices.get(skill,180)
    if p.get("dengi",0) < cost: return None, f"Не хватает {cost-p['dengi']}р"
    p["dengi"] = p.get("dengi",0) - cost
    exp = cost//10
    p["experience"] = p.get("experience",0) + exp
    old = p.get(f"skill_{skill}",1)
    p[f"skill_{skill}"] = old + 1
    await check_lvl(p)
    user_manager.mark_dirty(uid)
    new = p[f"skill_{skill}"]
    if new >= 10: await unlock_ach(uid, f"skill_{skill}_10", f"Мастер {skill}", 500)
    if new >= 25: await unlock_ach(uid, f"skill_{skill}_25", f"Гуру {skill}", 2000)
    return p, f"✅ Прокачано '{skill}' {old}→{new} за {cost}р! (+{exp} опыта)"

async def check_lvl(u):
    cur, exp = u.get("level",1), u.get("experience",0)
    need = int(100 * (cur**1.5))
    if exp >= need:
        old = cur
        u["level"] = cur+1
        u["experience"] = exp-need
        rew = u["level"]*100
        u["dengi"] = u.get("dengi",0) + rew
        if u["level"] % 5 == 0:
            u["max_atm"] = u.get("max_atm",12) + 1
            u["atm_count"] = min(u.get("atm_count",0)+1, u["max_atm"])
        if u["level"] >= 10: await unlock_ach(u.get("user_id"), "lvl_10", "10 уровень", 500)
        if u["level"] >= 25: await unlock_ach(u.get("user_id"), "lvl_25", "25 уровень", 2000)
        if u["level"] >= 50: await unlock_ach(u.get("user_id"), "lvl_50", "Полвека", 5000)
        return True, {"old":old, "new":u["level"], "rew":rew, "atm_inc":u["level"]%5==0}
    return False, None

async def upd_ach(uid, aid, inc):
    if aid not in ACH_LEVELS: return {"lvled":False}
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT progress,level FROM user_achievements WHERE user_id=? AND achievement_id=?', (uid,aid)) as c:
        row = await c.fetchone()
        if row: prog, lvl = row["progress"]+inc, row["level"]
        else: 
            prog, lvl = inc, 0
            await pool.execute('INSERT INTO user_achievements (user_id,achievement_id,progress) VALUES (?,?,?)', (uid,aid,prog))
    
    ach = ACH_LEVELS[aid]
    if lvl < len(ach.get("lvls",[])):
        goal, rew, title, exp = ach["lvls"][lvl]
        if prog >= goal:
            p = await user_manager.get_user(uid)
            p["dengi"] = p.get("dengi",0) + rew
            p["experience"] = p.get("experience",0) + exp
            await pool.execute('UPDATE user_achievements SET progress=?,level=? WHERE user_id=? AND achievement_id=?', 
                              (prog, lvl+1, uid, aid))
            user_manager.mark_dirty(uid)
            ach_list = p.get("achievements",[])
            ach_list.append({"id":f"{aid}_lvl_{lvl+1}", "name":f"{ach['name']}: {title}",
                            "unlocked":int(time.time()), "rew":rew, "exp":exp})
            p["achievements"] = ach_list
            user_manager.mark_dirty(uid)
            return {"lvled":True, "lvl":lvl+1, "title":title, "rew":rew, "exp":exp}
        else:
            await pool.execute('UPDATE user_achievements SET progress=? WHERE user_id=? AND achievement_id=?', (prog, uid, aid))
    else:
        await pool.execute('UPDATE user_achievements SET progress=? WHERE user_id=? AND achievement_id=?', (prog, uid, aid))
    return {"lvled":False, "prog":prog}

async def get_ach_progress(uid):
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT achievement_id,progress,level FROM user_achievements WHERE user_id=?', (uid,)) as c:
        rows = await c.fetchall()
        res = {}
        for r in rows:
            aid = r["achievement_id"]
            if aid in ACH_LEVELS:
                ach = ACH_LEVELS[aid]
                lvl, prog = r["level"], r["progress"]
                if lvl < len(ach.get("lvls",[])):
                    goal, _, title, _ = ach["lvls"][lvl]
                    perc = min(100, (prog/goal)*100) if goal>0 else 0
                else: 
                    goal, title, perc = None, "Макс", 100
                res[aid] = {"name":ach.get("name",""), "current_level":lvl, "current_progress":prog, 
                           "next_level":goal, "progress_percent":perc, "title":title}
        return res

async def rademka_scout(uid, tid):
    p = await user_manager.get_user(uid)
    t = await user_manager.get_user(tid)
    if not t: return False, "Нет цели", {}
    cost = 0 if p.get("rademka_scouts",0) < 5 else 50
    if p.get("dengi",0) < cost: return False, f"Не хватает {cost-p['dengi']}р", {}
    
    base = 50
    diff = p.get("avtoritet",1) - t.get("avtoritet",1)
    chance = base + (diff*5)
    if p.get("specialization") == "neprobivaemy": chance += 5
    if p.get("avtoritet",1) < t.get("avtoritet",1): chance += 20
    chance = max(10, min(95, chance))
    
    now = time.time()
    last = t.get("last_update",now)
    if now - last > 86400: chance += 15
    
    if cost > 0: 
        p["dengi"] = p.get("dengi",0) - cost
    p["rademka_scouts"] = p.get("rademka_scouts",0) + 1
    user_manager.mark_dirty(uid)
    
    pool = await DatabaseManager.get_pool()
    await pool.execute('UPDATE rademka_fights SET scouted=1 WHERE (winner_id=? AND loser_id=?) OR (winner_id=? AND loser_id=?)', 
                      (uid,tid,tid,uid))
    
    factors = [f"Разница авторитета: {'+' if diff>0 else ''}{diff*5}%"]
    if p.get("avtoritet",1) < t.get("avtoritet",1): factors.append("Гандикап слабого: +20%")
    if now - last > 86400: factors.append("Цель неактивна: +15%")
    if p.get("specialization") == "neprobivaemy": factors.append("Специализация: +5%")
    
    return True, f"Разведка {'бесплатная' if cost==0 else 'за 50р'} успешна!", {
        "chance":int(chance), "cost":cost, "free_scouts_left":max(0,5-p.get("rademka_scouts",0)),
        "attacker_stats":{"avtoritet":p.get("avtoritet",1),"rank":get_rank(p.get("avtoritet",1))},
        "target_stats":{"avtoritet":t.get("avtoritet",1),"rank":get_rank(t.get("avtoritet",1)),
                       "last_active_hours":int((now-last)/3600) if last else 0},
        "factors":factors
    }

async def get_daily(uid):
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT last_daily,level,dengi,nickname FROM users WHERE user_id=?', (uid,)) as c:
        u = await c.fetchone()
        now = int(time.time())
        if not u: return {"ok":False, "error":"Нет юзера"}
        last = u["last_daily"] or 0
        if last > 0 and now - last < 86400:
            wait = 86400 - (now - last)
            h = wait//3600
            m = (wait%3600)//60
            return {"ok":False, "wait":f"{h}ч {m}м", "next":last+86400}
        
        lvl = u["level"] or 1
        base = 100 + lvl*10
        streak = 1
        mul = 1.0
        if streak >= 30: mul = 4.0
        elif streak >= 7: mul = 3.0
        elif streak >= 3: mul = 2.0
        
        base = int(base * mul)
        bonus = random.randint(0, base//10)
        total = base + bonus
        items = ["двенашка","атмосфера","энергетик","золотая_двенашка","бустер_атмосфер"] if lvl>=20 else ["двенашка","атмосфера","энергетик","перчатки"]
        weights = [0.3,0.25,0.2,0.15,0.1] if lvl>=20 else [0.4,0.3,0.2,0.1]
        item = random.choices(items, weights=weights, k=1)[0]
        
        await pool.execute('UPDATE users SET dengi=dengi+?, last_daily=?, inventory=json_insert(COALESCE(inventory,"[]"), "$[#]", ?) WHERE user_id=?',
                          (total, now, item, uid))
        
        p = await user_manager.get_user(uid, True)
        return {"ok":True, "money":total, "item":item, "streak":streak, "base":base, "bonus":bonus, "lvl":lvl}

async def unlock_ach(uid, aid, name, rew=0):
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT 1 FROM achievements WHERE user_id=? AND achievement_id=?', (uid,aid)) as c:
        if await c.fetchone(): return False
    await pool.execute('INSERT INTO achievements (user_id, achievement_id) VALUES (?,?)', (uid,aid))
    async with pool.execute('SELECT achievements,dengi FROM users WHERE user_id=?', (uid,)) as c:
        u = await c.fetchone()
        ach = json.loads(u["achievements"]) if u and u["achievements"] else []
        for a in ach:
            if a.get("id") == aid: return False
        ach.append({"id":aid, "name":name, "unlocked":int(time.time()), "rew":rew})
        if rew > 0:
            await pool.execute('UPDATE users SET dengi=dengi+?, achievements=? WHERE user_id=?', (rew, json.dumps(ach), uid))
        else:
            await pool.execute('UPDATE users SET achievements=? WHERE user_id=?', (json.dumps(ach), uid))
        await user_manager.get_user(uid, True)
        return True

async def change_nick(uid, nick):
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT nickname_changed,dengi FROM users WHERE user_id=?', (uid,)) as c:
        u = await c.fetchone()
        cost = 5000
        if not u: return False, "Нет юзера"
        if not u["nickname_changed"]:
            await pool.execute('UPDATE users SET nickname=?, nickname_changed=1 WHERE user_id=?', (nick, uid))
            await unlock_ach(uid, "first_nick", "Первая бирка", 100)
            await user_manager.get_user(uid, True)
            return True, "Ник изменён! (бесплатно) +100р"
        if u["dengi"] < cost: return False, f"Не хватает {cost-u['dengi']}р"
        await pool.execute('UPDATE users SET nickname=?, dengi=dengi-? WHERE user_id=?', (nick, cost, uid))
        await user_manager.get_user(uid, True)
        return True, f"Ник изменён! -{cost}р"

async def save_rademka(win, lose, money=0, item=None, scout=False):
    pool = await DatabaseManager.get_pool()
    await pool.execute('INSERT INTO rademka_fights (winner_id,loser_id,money_taken,item_stolen,scouted) VALUES (?,?,?,?,?)',
                      (win, lose, money, item, scout))

async def get_top_players(limit=10, sort="avtoritet"):
    return await user_manager.get_top_fast(limit, sort)

async def get_user_achievements(uid):
    pool = await DatabaseManager.get_pool()
    async with pool.execute('SELECT achievements FROM users WHERE user_id=?', (uid,)) as c:
        u = await c.fetchone()
        return json.loads(u["achievements"]) if u and u["achievements"] else []

async def init_bot(): 
    await DatabaseManager.get_pool()
    await user_manager.start_batch_saver()

async def shutdown(): 
    await user_manager._save_dirty()
    if DatabaseManager._pool: 
        await DatabaseManager._pool.close()
        DatabaseManager._pool = None

async def get_craftable_items(uid): return await get_craftable(uid)
async def get_available_specializations(uid): return await get_available_specs(uid)
async def buy_specialization(uid, spec): return await buy_spec(uid, spec)
async def get_achievement_progress(uid): return await get_ach_progress(uid)
async def get_daily_reward(uid): return await get_daily(uid)
async def unlock_achievement(uid, aid, name, rew=0): return await unlock_ach(uid, aid, name, rew)
async def change_nickname(uid, nick): return await change_nick(uid, nick)
async def get_top(limit=10, sort="avtoritet"): return await get_top_players(limit, sort)
async def get_connection(): return await DatabaseManager.get_pool()
async def save_rademka_fight(win, lose, money=0, item=None, scout=False): return await save_rademka(win, lose, money, item, scout)
async def check_level_up(user): return await check_lvl(user)

def calculate_atm_regen_time(user):
    base_time = 600
    if user.get("skill_zashita", 1) >= 10: base_time *= 0.9
    if user.get("specialization") == "neprobivaemy": base_time *= 0.9
    boosts = user.get("active_boosts", {})
    if isinstance(boosts, dict) and "вечный_двигатель" in boosts: base_time *= 0.7
    elif isinstance(boosts, str) and "вечный_двигатель" in boosts: base_time *= 0.7
    return int(max(60, base_time))

def get_specialization_bonuses(spec): return SPECS.get(spec, {}).get("bon", {})

if __name__ == "__main__":
    async def test():
        await init_bot()
        start = time.time()
        tasks = [get_patsan(i) for i in range(100)]
        await asyncio.gather(*tasks)
        print(f"100 юзеров за {time.time()-start:.2f}с")
        await shutdown()
    asyncio.run(test())
