import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        referrer_id INTEGER,
                        balance INTEGER DEFAULT 0,
                        stars INTEGER DEFAULT 0,
                        phone TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, referrer_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
        conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, stars, phone FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 0, None)

def update_phone_and_give_bonus(user_id, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))

    # Referrer bonus
    cursor.execute("SELECT referrer_id FROM users WHERE user_id = ? AND referrer_id IS NOT NULL", (user_id,))
    res = cursor.fetchone()
    referrer_id = None
    if res:
        referrer_id = res[0]
        cursor.execute("UPDATE users SET stars = stars + 5 WHERE user_id = ?", (referrer_id,))

    conn.commit()
    conn.close()
    return referrer_id

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL")
    active = cursor.fetchone()[0]
    conn.close()
    return total, active

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def change_user_balance(user_id, amount, b_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if b_type == "stars":
        cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, user_id))
    else:
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
