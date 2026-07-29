import os

# Bot tokeningizni shu yerga yozing yoki muhit o'zgaruvchisi orqali bering:
#   export BOT_TOKEN="123456:ABC-DEF..."
BOT_TOKEN = os.getenv("BOT_TOKEN", "8619518195:AAFBKagDpFWgTPfhXDAt5yHwsm2M2H31dDE")

# Majburiy obuna talab qilinadigan kanal va chat (username, @ belgisisiz saqlaymiz)
REQUIRED_CHANNEL = "@K0NKURS_UZ"
REQUIRED_CHAT = "@bepul_gifts"

DB_PATH = os.getenv("DB_PATH", "konkurs_bot.db")
