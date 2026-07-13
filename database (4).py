import sqlite3

DB_NAME = "bot_users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referrer_id INTEGER DEFAULT NULL,
        balance INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 0,
        phone TEXT DEFAULT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, referrer_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        if referrer_id and int(referrer_id) == int(user_id):
            referrer_id = None
        cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, stars, phone FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return res
    return (0, 0, None)

def update_phone_and_give_bonus(user_id, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))

    cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()

    if res and res[0]:
        referrer_id = res[0]
        cursor.execute("SELECT user_id, stars FROM users WHERE user_id = ?", (referrer_id,))
        ref_exists = cursor.fetchone()

        if ref_exists:
            current_stars = ref_exists[1]

            # Agar taklif qilganning joriy balli 45 dan kichik bo'lsa, unga +5 stars beramiz
            # (main.py matnida 5 stars deyilgan, shuning uchun bu yerda +5 qildim)
            if current_stars < 45:
                cursor.execute("UPDATE users SET stars = stars + 5 WHERE user_id = ?", (referrer_id,))
                conn.commit()
                conn.close()
                return referrer_id  # Bonus berilgani haqida xabar yuborish uchun ID qaytadi

    conn.commit()
    conn.close()
    return None

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(user_id) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(user_id) FROM users WHERE phone IS NOT NULL")
    active_users = cursor.fetchone()[0]
    conn.close()
    return total_users, active_users

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def change_user_balance(user_id, amount, column="stars"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if column == "stars":
        cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, user_id))
    else:
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
