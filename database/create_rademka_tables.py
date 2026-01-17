import asyncio
import aiosqlite

async def create_rademka_tables():
    """Создание таблиц для статистики радёмок"""
    conn = await aiosqlite.connect("bot_database.db")
    
    try:
        # Таблица боев радёмки
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
        
        # Индексы для быстрого поиска
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rademka_winner ON rademka_fights(winner_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rademka_loser ON rademka_fights(loser_id)')
        
        await conn.commit()
        print("✅ Таблицы для статистики радёмок созданы")
        
    except Exception as e:
        print(f"⚠️ Ошибка при создании таблиц: {e}")
        
    finally:
        await conn.close()

# Также обновляем функцию init_db в db_manager.py
async def update_init_db():
    """Обновление init_db для создания таблиц радёмок"""
    conn = await aiosqlite.connect("bot_database.db")
    
    try:
        # Создаем таблицу rademka_fights, если её нет
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
        
        # Создаем индексы
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rademka_winner ON rademka_fights(winner_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rademka_loser ON rademka_fights(loser_id)')
        
        await conn.commit()
        print("✅ Таблица rademka_fights добавлена в базу данных")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    # Создаем таблицы при запуске скрипта
    asyncio.run(create_rademka_tables())
    print("✅ Скрипт создания таблиц радёмок выполнен")
