import sqlite3

def create_tables():
    """Создает необходимые таблицы в базе данных SQLite."""
    conn = sqlite3.connect('bot_database.db')  # Файл БД появится в корне проекта
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,  # Telegram ID пользователя
            username TEXT,
            first_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица заказов (корзина)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,  # Цена за единицу в копейках/центах
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Таблицы в базе данных успешно созданы (или уже существовали).")

# Этот блок выполнится только при прямом запуске models.py
if __name__ == "__main__":
    create_tables()
