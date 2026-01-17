import time
import random
from replit import db

# Константы
ATM_MAX = 12
ATM_TIME = 600  # 10 минут в секундах

def init_db():
    """Инициализация базы данных"""
    print("📦 База данных инициализирована")

def get_patsan(user_id: int):
    """Получаем пацана из базы, создаем нового если нет"""
    key = f"user_{user_id}"
    
    if key in db:
        user = db[key]
        # Автоматическое восстановление атмосфер
        now = int(time.time())
        last = user.get("last_update", now)
        passed = now - last
        
        if passed >= ATM_TIME:
            new_atm = min(ATM_MAX, user["atm_count"] + (passed // ATM_TIME))
            if new_atm != user["atm_count"]:
                user["atm_count"] = new_atm
                user["last_update"] = now - (passed % ATM_TIME)
                db[key] = user
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
        db[key] = new_user
        return new_user

def save_patsan(user_data: dict):
    """Сохраняем пацана в базу"""
    key = f"user_{user_data['user_id']}"
    db[key] = user_data

def davka_zmiy(patsan: dict):
    """Обработка дачки коричневага"""
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
    
    save_patsan(patsan)
    
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

def sdat_zmiy(patsan: dict):
    """Сдача змия на металл"""
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
    
    save_patsan(patsan)
    
    return patsan, {
        "old_zmiy": old_zmiy,
        "total_money": total_money,
        "avtoritet_bonus": avtoritet_bonus
    }

def buy_upgrade(patsan: dict, upgrade: str):
    """Покупка улучшения"""
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
    
    save_patsan(patsan)
    
    return patsan, f"Куплено за {price}р!{effect}"

def pump_skill(patsan: dict, skill: str):
    """Прокачка скилла"""
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
