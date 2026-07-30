import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# Token va boshqa sozlamalar
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Render beradigan URL
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = f"/bot/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# Portni Render avtomatik beradi yoki 10000 ishlatiladi
PORT = int(os.getenv("PORT", 10000))


async def on_startup(bot: Bot):
  # Bot ishga tushganda webhook'ni o'rnatish
  await bot.set_webhook(WEBHOOK_URL)


async def handle_webhook(request: web.Request):
  try:
    data = await request.json()
    # aiogram 3 uchun to'g'ri validatsiya qilib uzatish
    update = types.Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
  except Exception as e:
    logging.error(f"Webhook error: {e}")
  return web.Response()


async def handle_root(request: web.Request):
  # Render va UptimeRobot uchun 200 OK qaytarish
  return web.Response(text="Bot is running!")


async def main():
  # aiogram voqealarini ulash
  dp.startup.register(on_startup)

  # aiohttp ilovasini yaratish
  app = web.Application()
  app.router.add_get("/", handle_root)
  app.router.add_post(WEBHOOK_PATH, handle_webhook)

  # Serverni ishga tushirish
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", PORT)
  await site.start()

  # Bot to'xtaguncha ishni ushlab turish
  await asyncio.Event().wait()


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())
    
