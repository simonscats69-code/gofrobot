import sqlite3

def create_tables():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE NOT NULL, username TEXT, first_name TEXT, phone TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_name TEXT NOT NULL, quantity INTEGER NOT NULL, price INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id))')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
