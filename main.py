import asyncio
import logging
import os
import urllib.parse
from datetime import datetime

import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ============================================================
#                       SOZLAMALAR (CONFIG)
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8762594173:AAGSAsdbNU1XziBj_fbGHUuStBMjbFAqGD4")
# Render'dan admin ID ni o'qish
ADMIN_IDS = [int(i.strip()) for i in os.environ.get("ADMIN_IDS", "8597455078").split(",") if i.strip().isdigit()]
BOT_USERNAME = "bepul_gifts_bot"
SUPPORT_ADMIN_USERNAME = os.environ.get("SUPPORT_ADMIN_USERNAME", "DlKTATOR_UZ")
DATABASE_URL = os.environ.get("DATABASE_URL")


# Neon.tech (yoki boshqa Postgres) ulanish satri. Render'da Environment
# Variables bo'limiga DATABASE_URL nomi bilan qo'shiladi.
# Masalan: postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require
DATABASE_URL = os.environ.get("DATABASE_URL", "")

STARS_PER_REFERRAL = 5
MAX_REWARDED_REFERRALS = 9  # Shundan keyin referal stars bermaydi (foydalanuvchiga bildirilmaydi)

# Majburiy obuna kanallari.
# Ochiq kanal/guruh uchun: "chat": "@username"
# Yopiq (private) kanal uchun: "chat": raqamli chat_id (masalan -1001234567890)
#   Bot o'sha kanalga ADMIN qilib qo'yilishi shart, aks holda obuna va
#   "kanaldan chiqib ketish" tekshiruvlari ishlamaydi.
MANDATORY_CHANNELS = [
    {"title": "𝙰𝚜𝚝𝚛𝚘 𝙺𝚘𝚗𝚔𝚞𝚛𝚜", "chat": "@K0NKURS_UZ", "url": "https://t.me/K0NKURS_UZ"},
    {"title": "𝐄𝐯𝐢𝐥 𝐆𝐢𝐟𝐭𝐬🎁", "chat": "@gifts_evil", "url": "https://t.me/gifts_evil"},
    {"title": "𝙰𝚜𝚝𝚛𝚘 𝙺𝚘𝚗𝚔𝚞𝚛𝚜 𝚌𝚑𝚊𝚝", "chat": "@REAK_CHAT", "url": "https://t.me/REAK_CHAT"},
    {"title": "𝐄𝐯𝐢𝐥 𝐆𝐢𝐟𝐭𝐬 💝 𝐜𝐡𝐚𝐭", "chat": "@VZ_REAK_CHATl", "url": "https://t.me/VZ_REAK_CHATl"},
    {"title": "𝓜𝔂 𝓵𝓲𝓯𝓮 🤴🏻", "chat": "-1002161734168", "url": "https://telegram.me/+Ims0V4GEanI4MWYy"},
]

PAYMENT_CHANNEL_TITLE = "Bepul Gifts Toʻlov kanali"
PAYMENT_CHANNEL_URL = "https://t.me/bepul_gifts"

PREMIUM_PLANS = [
    ("1 oylik", 1, 150),
    ("3 oylik", 3, 450),
    ("6 oylik", 6, 900),
    ("12 oylik", 12, 1800),
]

GIFT_ITEMS = [
    ("🧸💝 4 tasi", 50),
    ("🌹🎁 4 tasi", 80),
    ("🎂💐🚀 3 tasi", 120),
    ("🏆💎💍 Donasi", 95),
]

# "Boshqa" bo'limi — balansga aloqasi yo'q, hammasi admin profiliga yo'naltiradi
JONLI_OVOZ_ITEMS = [(10, 5), (20, 14), (30, 25), (40, 38), (50, 55)]
CAMENT_REAKSIYA_ITEMS = [(10, 10), (15, 15), (25, 30), (35, 40), (50, 60)]
OBUNACHI_GARAND_ITEMS = [(40, 15), (80, 25), (120, 50)]

TG_OBUNACHI_ITEMS = [
    ("0 kun", "1500 so'm"),
    ("30 kun", "7000 so'm"),
    ("90 kun", "20000 so'm"),
    ("150 kun", "40000 so'm"),
    ("360 kun", "55000 so'm"),
]
TG_REAKSIYA_ITEMS = [
    ("Oddiy reaksiya - 1000 tasi", "1000 so'm"),
    ("Bepul oddiy reaksiya usuli", "5000 so'm"),
    ("Premium reaksiya - 1000 tasi", "5000 so'm"),
]
TG_PROSMOTR_ITEMS = [("Cheksiz prosmotr usuli", "5000 so'm")]

RULES_TEXT = (
    "Bot qoidalari 📜\n"
    "🛑 Siz chaqirgan doʻstingiz majburiy kanallardan chiqib ketmasligi kerak. "
    "Agar chiqib ketsa, bu jarimaga olib keladi.\n"
    "🚫 Multi-accountdan koʻp foydalanish hisob bloklanishigacha olib kelishi mumkin.\n"
    "⁉️ Bot bergan giftni sotib starsga aylantirish mumkinmi? 🤔\n\n"
    "Yoʻq, afsuski, bot tomonidan kiritilgan giftlarni biz taqsimlay olmaymiz 😔. "
    "Chunki baza giftlar sotib olinib boʻlingan, bot ularni avto xadiya qiladi 🎁🤖.\n\n"
    "Ularni \"stars\"ga oʻzgartirish iloji yoʻq, chunki haqiqiy boʻlishi uchun "
    "oldindan sotib olingan va bot sizga taqdim etadi 🎁.\n\n"
    "Agar sotish uchun olmoqchi boʻlsangiz, balans 0ga tenglashtirishingiz va "
    "Adminga murojaat qilishingiz kerak 📩. Men Admin bot hisobingizni giftga "
    "qarab yechib beradi, ammo 50 starsga 50 starslik savdo chegirma boʻlmaydi 🚫💸."
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

pool: asyncpg.Pool | None = None  # on_startup ichida to'ldiriladi


# ============================================================
#                          FSM HOLATLARI
# ============================================================

class SupportStates(StatesGroup):
    waiting_message = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_info_user_id = State()
    waiting_balance_user_id = State()
    waiting_balance_amount = State()


# ============================================================
#                    BAZA (POSTGRESQL / NEON)
# ============================================================

async def db_connect() -> None:
    global pool
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL topilmadi! Render'da Environment Variables bo'limiga "
            "Neon.tech ulanish satrini DATABASE_URL nomi bilan qo'shing."
        )
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)


async def db_init() -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                referrer_id BIGINT,
                referral_count INTEGER DEFAULT 0,
                rewarded_referrals INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                is_registered INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                user_id BIGINT,
                chat_id BIGINT,
                PRIMARY KEY (user_id, chat_id)
            )
        """)


async def db_get_user(user_id: int) -> asyncpg.Record | None:
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)


async def db_create_user(user_id: int, username: str | None, full_name: str, referrer_id: int | None) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, username, full_name, referrer_id) VALUES ($1, $2, $3, $4) "
            "ON CONFLICT (user_id) DO NOTHING",
            user_id, username, full_name, referrer_id,
        )


async def db_set_phone_and_register(user_id: int, phone: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET phone = $1, is_registered = 1 WHERE user_id = $2", phone, user_id
        )


async def db_register_referral_success(referrer_id: int) -> None:
    """Referal to'liq ro'yxatdan o'tganda chaqiriladi.
    referral_count doim oshadi, ammo stars faqat birinchi
    MAX_REWARDED_REFERRALS tagacha beriladi (foydalanuvchiga bildirilmaydi)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT rewarded_referrals FROM users WHERE user_id = $1", referrer_id
        )
        if row is None:
            return
        await conn.execute(
            "UPDATE users SET referral_count = referral_count + 1 WHERE user_id = $1", referrer_id
        )
        if row["rewarded_referrals"] < MAX_REWARDED_REFERRALS:
            await conn.execute(
                "UPDATE users SET balance = balance + $1, rewarded_referrals = rewarded_referrals + 1 "
                "WHERE user_id = $2",
                STARS_PER_REFERRAL, referrer_id,
            )


async def db_change_balance(user_id: int, amount: int) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE users SET balance = balance + $1 WHERE user_id = $2 RETURNING balance",
            amount, user_id,
        )
        return row["balance"] if row else 0


async def db_top_by_balance(limit: int = 20) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT user_id, username, full_name, balance FROM users "
            "WHERE is_registered = 1 ORDER BY balance DESC LIMIT $1",
            limit,
        )

async def db_add_join_request(user_id: int, chat_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO join_requests (user_id, chat_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id, chat_id
        )

async def db_check_join_request(user_id: int, chat_id: int) -> bool:
    async with pool.acquire() as conn:
        res = await conn.fetchval(
            "SELECT 1 FROM join_requests WHERE user_id = $1 AND chat_id = $2", user_id, chat_id
        )
        return res is not None

async def db_referrals_of(user_id: int) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT user_id, username, full_name FROM users "
            "WHERE referrer_id = $1 AND is_registered = 1",
            user_id,
        )


async def db_stats() -> dict:
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        registered = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_registered = 1")
        return {"total": total, "registered": registered}


async def db_all_registered_ids() -> list[int]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users WHERE is_registered = 1")
        return [r["user_id"] for r in rows]


# ============================================================
#                        YORDAMCHI FUNKSIYALAR
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_deeplink(text: str) -> str:
    return f"https://t.me/{SUPPORT_ADMIN_USERNAME}?text={urllib.parse.quote(text)}"


def user_mention(row: asyncpg.Record) -> str:
    if row["username"]:
        return f"@{row['username']}"
    return row["full_name"] or f"ID {row['user_id']}"


# ============================================================
#                        KLAVIATURALAR
# ============================================================

def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="⭐ STARS ISHLASH"), KeyboardButton(text="Boshqa")],
        [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="📜 Bot qoidalari")],
        [KeyboardButton(text="💳 Toʻlov kanali"), KeyboardButton(text="✉️ Murojaat")],
    ]
    if is_admin(user_id):
        rows.append([KeyboardButton(text="🛠 Admin paneli")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def subscription_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=ch["title"], url=ch["url"])] for ch in MANDATORY_CHANNELS]
    rows.append([InlineKeyboardButton(text="✅ Tekshirdim", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stars_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    share_text = f"Bepul sovgʻa yutish uchun botga qoʻshiling! 🎁\n{ref_link}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Doʻstlarni taklif qilish", switch_inline_query=share_text)],
            [
                InlineKeyboardButton(text="💎 Premium olish", callback_data="menu:premium"),
                InlineKeyboardButton(text="🎁 Gift olish", callback_data="menu:gift"),
            ],
            [InlineKeyboardButton(text="💳 Toʻlovlar kanali", callback_data="menu:tolov")],
            [InlineKeyboardButton(text="📋 Mening referallarim", callback_data="menu:referrals")],
        ]
    )


def premium_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{label} - {price} stars", callback_data=f"premium:{months}:{price}")]
        for label, months, price in PREMIUM_PLANS
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:stars")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def gift_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{label} - {price} stars", callback_data=f"gift:{i}:{price}")]
        for i, (label, price) in enumerate(GIFT_ITEMS)
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:stars")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tolov_kanali_keyboard(back_target: str = "menu:stars") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=PAYMENT_CHANNEL_TITLE, url=PAYMENT_CHANNEL_URL)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_target)],
        ]
    )


def boshqa_root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Jonli ovoz, cament, obunachi", callback_data="boshqa:jonli")],
            [InlineKeyboardButton(text="Nakrutka xizmati", callback_data="boshqa:nakrutka")],
        ]
    )


def jonli_root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Batl uchun jonli ovoz", callback_data="jonli:ovoz")],
            [InlineKeyboardButton(text="Batl uchun cament va reaksiya", callback_data="jonli:cament")],
            [InlineKeyboardButton(text="Kanal uchun jonli obunachi", callback_data="jonli:obunachi")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="boshqa:root")],
        ]
    )


def nakrutka_root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Telegram obunachi", callback_data="nakrutka:obunachi")],
            [InlineKeyboardButton(text="Telegram reaksiya", callback_data="nakrutka:reaksiya")],
            [InlineKeyboardButton(text="Cheksiz prosmotr", callback_data="nakrutka:prosmotr")],
        ]
    )


def price_url_keyboard(items, back_callback, extra_label=None, prefix_text="Xizmat") -> InlineKeyboardMarkup:
    rows = []
    for label, price in items:
        text = f"{label} - {price}"
        deeplink_text = f"Salom! Men \"{prefix_text}: {label} ({price})\" xizmatidan foydalanmoqchiman."
        rows.append([InlineKeyboardButton(text=text, url=admin_deeplink(deeplink_text))])
    if extra_label:
        deeplink_text = f"Salom! Men \"{prefix_text}\" boʻyicha miqdorni oʻzim aytmoqchiman."
        rows.append([InlineKeyboardButton(text=extra_label, url=admin_deeplink(deeplink_text))])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def murojaat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data="support:write")],
            [InlineKeyboardButton(text="🤝 Homiy boʻlish", url=f"https://t.me/{SUPPORT_ADMIN_USERNAME}")],
        ]
    )


def reyting_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="close_msg")]]
    )


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
                InlineKeyboardButton(text="📢 Hammaga xabar yuborish", callback_data="admin:broadcast"),
            ],
            [InlineKeyboardButton(text="👤 Foydalanuvchi haqida maʼlumotlar", callback_data="admin:info")],
            [InlineKeyboardButton(text="💰 Foydalanuvchilar balans boshqarish", callback_data="admin:balance")],
        ]
    )


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="admin:broadcast_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:broadcast_cancel"),
            ]
        ]
    )


def balance_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Qoʻshish", callback_data="admin:bal_add"),
                InlineKeyboardButton(text="➖ Ayirish", callback_data="admin:bal_sub"),
            ]
        ]
    )


# ============================================================
#                    OBUNA TEKSHIRISH LOGIKASI
# ============================================================

async def get_unsubscribed_channels(user_id: int) -> list[dict]:
    not_subscribed = []
    for ch in MANDATORY_CHANNELS:
        try:
            # Agar chat_id raqamli (shaxsiy kanal) bo'lsa, bazadan tekshiramiz
            if str(ch["chat"]).startswith("-100"):
                chat_id = int(ch["chat"])
                if not await db_check_join_request(user_id, chat_id):
                    not_subscribed.append(ch)
            else:
                # Oddiy kanal bo'lsa, statusini tekshiramiz
                member = await bot.get_chat_member(chat_id=ch["chat"], user_id=user_id)
                if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                    not_subscribed.append(ch)
        except Exception as e:
            logging.warning("Kanal tekshirishda xatolik (%s): %s", ch["chat"], e)
            not_subscribed.append(ch)
    return not_subscribed

@router.chat_join_request()
async def on_join_request(update: aiogram.types.ChatJoinRequest) -> None:
    await db_add_join_request(update.from_user.id, update.chat.id)
    logging.info(f"Yangi so'rov: {update.from_user.id} foydalanuvchidan, kanal: {update.chat.id}")

# ============================================================
#                      START / ROʻYXATDAN OʻTISH
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    referrer_id = None
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].removeprefix("ref_"))
            if ref_id != user_id:
                referrer_id = ref_id
        except ValueError:
            pass

    existing = await db_get_user(user_id)
    if existing is None:
        await db_create_user(user_id, username, full_name, referrer_id)

    if existing and existing["is_registered"]:
        await message.answer(
            f"Xush kelibsiz, {full_name}! 👋", reply_markup=main_menu_keyboard(user_id)
        )
        return

    await message.answer(
        f"Assalomu alaykum, @{username or full_name}, siz majburiy kanallarga obuna boʻling 👇",
        reply_markup=subscription_keyboard(),
    )


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    not_subscribed = await get_unsubscribed_channels(user_id)

    if not_subscribed:
        await callback.answer("❗️ Siz hali barcha kanallarga aʼzo boʻlmadingiz!", show_alert=True)
        return

    user = await db_get_user(user_id)
    if user and user["is_registered"]:
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi!", reply_markup=main_menu_keyboard(user_id))
        return

    await callback.message.delete()
    await callback.message.answer(
        "✅ Obuna tasdiqlandi!\n\nEndi roʻyxatdan oʻtish uchun telefon raqamingizni yuboring.\n"
        "⚠️ Faqat <b>Oʻzbekiston (+998)</b> raqamlari qabul qilinadi.",
        reply_markup=phone_request_keyboard(),
    )


@router.message(F.contact)
async def handle_contact(message: Message) -> None:
    user_id = message.from_user.id

    if message.contact.user_id != user_id:
        await message.answer("⚠️ Iltimos, faqat oʻzingizning raqamingizni yuboring.")
        return

    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    if not phone.startswith("+998") or len(phone) != 13:
        await message.answer(
            "❌ Faqat Oʻzbekiston Respublikasi raqamlari (+998) bilan roʻyxatdan oʻtish mumkin. "
            "Iltimos, qaytadan urinib koʻring.",
            reply_markup=phone_request_keyboard(),
        )
        return

    not_subscribed = await get_unsubscribed_channels(user_id)
    if not_subscribed:
        await message.answer(
            "❗️ Roʻyxatdan oʻtishdan oldin barcha kanallarga aʼzo boʻling.",
            reply_markup=subscription_keyboard(),
        )
        return

    user = await db_get_user(user_id)
    was_registered = bool(user and user["is_registered"])

    await db_set_phone_and_register(user_id, phone)

    if not was_registered and user and user["referrer_id"]:
        await db_register_referral_success(user["referrer_id"])

    await message.answer("✅ Roʻyxatdan muvaffaqiyatli oʻtdingiz!", reply_markup=main_menu_keyboard(user_id))


# ============================================================
#                        STARS ISHLASH
# ============================================================

def _stars_text(user: asyncpg.Record) -> str:
    mention = f"@{user['username']}" if user["username"] else user["full_name"]
    return (
        f"Assalomu alaykum, {mention}\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"⭐ Balans: <b>{user['balance']}</b> stars\n"
        f"👥 Referal: <b>{user['referral_count']}</b>\n\n"
        f"Har bitta referal +{STARS_PER_REFERRAL} stars"
    )


@router.message(F.text == "⭐ STARS ISHLASH")
async def stars_ishlash(message: Message) -> None:
    user = await db_get_user(message.from_user.id)
    await message.answer(_stars_text(user), reply_markup=stars_menu_keyboard(message.from_user.id))


@router.callback_query(F.data == "menu:stars")
async def cb_menu_stars(callback: CallbackQuery) -> None:
    user = await db_get_user(callback.from_user.id)
    await callback.message.edit_text(_stars_text(user), reply_markup=stars_menu_keyboard(callback.from_user.id))


@router.callback_query(F.data == "menu:premium")
async def cb_menu_premium(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=premium_keyboard())


@router.callback_query(F.data == "menu:gift")
async def cb_menu_gift(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=gift_keyboard())


@router.callback_query(F.data == "menu:tolov")
async def cb_menu_tolov(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Bot giftlarni avto toʻlaydi", reply_markup=tolov_kanali_keyboard("menu:stars")
    )


@router.callback_query(F.data == "menu:referrals")
async def cb_menu_referrals(callback: CallbackQuery) -> None:
    refs = await db_referrals_of(callback.from_user.id)
    if not refs:
        text = "📋 Sizda hozircha toʻliq roʻyxatdan oʻtgan referallar yoʻq."
    else:
        lines = ["📋 <b>Mening referallarim</b>\n"]
        for i, r in enumerate(refs, start=1):
            name = f"@{r['username']}" if r["username"] else (r["full_name"] or f"ID {r['user_id']}")
            lines.append(f"{i}. {name}")
        text = "\n".join(lines)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:stars")]]
    )
    await callback.message.edit_text(text, reply_markup=kb)


# ---------------------- Premium / Gift sotib olish ----------------------

@router.callback_query(F.data.startswith("premium:"))
async def cb_buy_premium(callback: CallbackQuery) -> None:
    _, months, price = callback.data.split(":")
    price = int(price)
    await process_purchase(callback, item_name=f"Premium {months} oylik", price=price)


@router.callback_query(F.data.startswith("gift:"))
async def cb_buy_gift(callback: CallbackQuery) -> None:
    _, idx, price = callback.data.split(":")
    price = int(price)
    label = GIFT_ITEMS[int(idx)][0]
    await process_purchase(callback, item_name=f"Gift: {label}", price=price)


async def process_purchase(callback: CallbackQuery, item_name: str, price: int) -> None:
    user = await db_get_user(callback.from_user.id)
    if user["balance"] < price:
        await callback.answer(
            f"⚠️ Sizda yetarli yulduz yo'q! Kerak: {price}, Sizda: {user['balance']}", show_alert=True
        )
        return

    await db_change_balance(user["user_id"], -price)
    await callback.answer("✅ Xarid muvaffaqiyatli amalga oshirildi!", show_alert=True)

    mention = f"@{user['username']}" if user["username"] else user["full_name"]
    admin_text = (
        f"💸 <b>Balansdan yechildi</b>\n\n"
        f"👤 {mention} (ID: <code>{user['user_id']}</code>)\n"
        f"🛒 Xarid: {item_name}\n"
        f"💰 Narx: {price} stars\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            logging.warning("Adminga xabar yuborilmadi: %s", e)


# ============================================================
#                          BOSHQA BOʻLIMI
# ============================================================

@router.message(F.text == "Boshqa")
async def boshqa_root(message: Message) -> None:
    await message.answer(
        "Sizga qiziqarli narlarni arzon narxda taqdim etaman!", reply_markup=boshqa_root_keyboard()
    )


@router.callback_query(F.data == "boshqa:root")
async def cb_boshqa_root(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Sizga qiziqarli narlarni arzon narxda taqdim etaman!", reply_markup=boshqa_root_keyboard()
    )


@router.callback_query(F.data == "boshqa:jonli")
async def cb_boshqa_jonli(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=jonli_root_keyboard())


@router.callback_query(F.data == "boshqa:nakrutka")
async def cb_boshqa_nakrutka(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=nakrutka_root_keyboard())


@router.callback_query(F.data == "jonli:ovoz")
async def cb_jonli_ovoz(callback: CallbackQuery) -> None:
    kb = price_url_keyboard(
        JONLI_OVOZ_ITEMS, "boshqa:jonli", extra_label="✍️ Miqdorni oʻzingiz kiriting",
        prefix_text="Batl uchun jonli ovoz",
    )
    await callback.message.edit_text(
        "Keraklisini tanlang! Narx majburiy obuna borligi bilan oʻzgarishi mumkin", reply_markup=kb
    )


@router.callback_query(F.data == "jonli:cament")
async def cb_jonli_cament(callback: CallbackQuery) -> None:
    kb = price_url_keyboard(
        CAMENT_REAKSIYA_ITEMS, "boshqa:jonli", extra_label="✍️ Oʻzim yozaman",
        prefix_text="Batl uchun cament va reaksiya",
    )
    await callback.message.edit_text(
        "Keraklisini tanlang! Majburiy obuna kanallari soniga qarab narx oʻzgarishi mumkin!",
        reply_markup=kb,
    )


@router.callback_query(F.data == "jonli:obunachi")
async def cb_jonli_obunachi(callback: CallbackQuery) -> None:
    kb = price_url_keyboard(
        [(f"Garand {n}ta", p) for n, p in OBUNACHI_GARAND_ITEMS],
        "boshqa:jonli", extra_label="✍️ Oʻzim yozaman",
        prefix_text="Kanal uchun jonli obunachi",
    )
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=kb)


@router.callback_query(F.data == "nakrutka:obunachi")
async def cb_nakrutka_obunachi(callback: CallbackQuery) -> None:
    kb = price_url_keyboard(TG_OBUNACHI_ITEMS, "boshqa:nakrutka", prefix_text="Telegram obunachi (1000 tasi)")
    await callback.message.edit_text("Keraklisini tanlang! (1000 tasi uchun narx)", reply_markup=kb)


@router.callback_query(F.data == "nakrutka:reaksiya")
async def cb_nakrutka_reaksiya(callback: CallbackQuery) -> None:
    kb = price_url_keyboard(TG_REAKSIYA_ITEMS, "boshqa:nakrutka", prefix_text="Telegram reaksiya")
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=kb)


@router.callback_query(F.data == "nakrutka:prosmotr")
async def cb_nakrutka_prosmotr(callback: CallbackQuery) -> None:
    kb = price_url_keyboard(TG_PROSMOTR_ITEMS, "boshqa:nakrutka", prefix_text="Cheksiz prosmotr")
    await callback.message.edit_text("Keraklisini tanlang!", reply_markup=kb)


# ============================================================
#                            REYTING
# ============================================================

@router.message(F.text == "🏆 Reyting")
async def reyting(message: Message) -> None:
    top = await db_top_by_balance(20)
    lines = [
        "Har juma kuni top 3ta oʻrin egalari taqdirlanadi!\n",
        "🏆 Konkurs Reytingi (Top 20)\n",
    ]
    if not top:
        lines.append("Hozircha reyting boʻsh.")
    else:
        for i, row in enumerate(top, start=1):
            name = f"@{row['username']}" if row["username"] else "Anonim foydalanuvchi"
            lines.append(f"{i}. {name} — {row['balance']} stars")
    lines.append("\n🎁 Eng koʻp referal yigʻgan ishtirokchi taqdirlanadi!")
    await message.answer("\n".join(lines), reply_markup=reyting_keyboard())


@router.callback_query(F.data == "close_msg")
async def cb_close_msg(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer()


# ============================================================
#                       BOT QOIDALARI / TOʻLOV
# ============================================================

@router.message(F.text == "📜 Bot qoidalari")
async def qoidalar(message: Message) -> None:
    await message.answer(RULES_TEXT)


@router.message(F.text == "💳 Toʻlov kanali")
async def tolov_kanali_reply(message: Message) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=PAYMENT_CHANNEL_TITLE, url=PAYMENT_CHANNEL_URL)]]
    )
    await message.answer("Bot giftlarni avto toʻlaydi", reply_markup=kb)


# ============================================================
#                            MUROJAAT
# ============================================================

@router.message(F.text == "✉️ Murojaat")
async def murojaat(message: Message) -> None:
    await message.answer("Keraklisini tanlang!", reply_markup=murojaat_keyboard())


@router.callback_query(F.data == "support:write")
async def cb_support_write(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportStates.waiting_message)
    await callback.message.edit_text("✍️ Xabaringizni yozib yuboring, u to'g'ridan-to'g'ri adminga yetadi.")


@router.message(SupportStates.waiting_message)
async def support_message_received(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    mention = f"@{user.username}" if user.username else user.full_name
    header = f"✉️ <b>Yangi murojaat</b>\n👤 {mention}\n🆔 ID: <code>{user.id}</code>\n\n"
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, header)
            await bot.copy_message(admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            logging.warning("Murojaat adminga yuborilmadi: %s", e)
    await message.answer("✅ Xabaringiz adminga yuborildi!", reply_markup=main_menu_keyboard(user.id))


# ============================================================
#               REFERAL KANALDAN CHIQIB KETSA / BLOK QILSA
# ============================================================

def _channel_matches(chat_username: str | None, chat_id: int) -> bool:
    for ch in MANDATORY_CHANNELS:
        target = ch["chat"]
        if isinstance(target, str) and target.startswith("@"):
            if chat_username and target[1:].lower() == chat_username.lower():
                return True
        else:
            if str(target) == str(chat_id):
                return True
    return False


async def warn_referrer_if_needed(user_id: int) -> None:
    user = await db_get_user(user_id)
    if not user or not user["referrer_id"]:
        return
    mention = f"@{user['username']}" if user["username"] else (user["full_name"] or f"ID {user['user_id']}")
    text = (
        f"Siz taklif qilgan doʻstingiz {mention} majburiy kanallarni tark etdi, "
        f"agar bunday holat yana takrorlansa hisobingizga jarima berilishi hattoki "
        f"balansingiz muzlatib qoʻyilishi mumkin."
    )
    try:
        await bot.send_message(user["referrer_id"], text)
    except Exception as e:
        logging.warning("Referrerga ogohlantirish yuborilmadi: %s", e)


@router.chat_member()
async def on_chat_member_update(update: ChatMemberUpdated) -> None:
    if not _channel_matches(update.chat.username, update.chat.id):
        return
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    left_statuses = (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
    if old_status not in left_statuses and new_status in left_statuses:
        await warn_referrer_if_needed(update.new_chat_member.user.id)


@router.my_chat_member()
async def on_bot_blocked(update: ChatMemberUpdated) -> None:
    if update.chat.type != "private":
        return
    if update.new_chat_member.user.id != bot.id:
        return
    if update.new_chat_member.status in (ChatMemberStatus.KICKED, ChatMemberStatus.LEFT):
        await warn_referrer_if_needed(update.chat.id)


# ============================================================
#                          ADMIN PANELI
# ============================================================

@router.message(F.text == "🛠 Admin paneli")
async def admin_panel(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Admin paneli", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    s = await db_stats()
    await callback.message.edit_text(
        f"📊 <b>Statistika</b>\n\nJami foydalanuvchi: {s['total']}\n"
        f"Toʻliq roʻyxatdan oʻtganlar: {s['registered']}",
        reply_markup=admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text("📢 Yubormoqchi boʻlgan xabarni yozing yoki forward qiling.")


@router.message(AdminStates.waiting_broadcast)
async def admin_broadcast_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await message.answer("Yuborishni tasdiqlaysizmi?", reply_markup=broadcast_confirm_keyboard())


@router.callback_query(F.data == "admin:broadcast_confirm")
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    data = await state.get_data()
    await state.clear()
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")
    if not chat_id or not message_id:
        await callback.message.edit_text("❌ Xatolik: xabar topilmadi.")
        return

    sent, failed = 0, 0
    for uid in await db_all_registered_ids():
        try:
            await bot.copy_message(uid, from_chat_id=chat_id, message_id=message_id)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.edit_text(f"✅ Yuborildi: {sent} ta\n❌ Yetkazilmadi: {failed} ta")


@router.callback_query(F.data == "admin:broadcast_cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin:info")
async def cb_admin_info(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.set_state(AdminStates.waiting_info_user_id)
    await callback.message.edit_text("👤 Foydalanuvchi ID raqamini kiriting:")


@router.message(AdminStates.waiting_info_user_id)
async def admin_info_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Notoʻgʻri ID format.")
        return

    user = await db_get_user(target_id)
    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        return

    refs = await db_referrals_of(target_id)
    ref_lines = "\n".join(f"— {user_mention(r)}" for r in refs) or "yoʻq"

    text = (
        f"👤 <b>Foydalanuvchi maʼlumotlari</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"👤 Username: {'@' + user['username'] if user['username'] else '—'}\n"
        f"📱 Telefon: {user['phone'] or '—'}\n"
        f"⭐ Balans: {user['balance']}\n"
        f"👥 Referal soni: {user['referral_count']}\n\n"
        f"📋 Toʻliq roʻyxatdan oʻtishiga sabab boʻlgan foydalanuvchilar:\n{ref_lines}"
    )
    await message.answer(text, reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin:balance")
async def cb_admin_balance(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.set_state(AdminStates.waiting_balance_user_id)
    await callback.message.edit_text("💰 Foydalanuvchi ID raqamini kiriting:")


@router.message(AdminStates.waiting_balance_user_id)
async def admin_balance_user_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Notoʻgʻri ID format.")
        return

    user = await db_get_user(target_id)
    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        return

    await state.update_data(target_id=target_id)
    await message.answer(
        f"Foydalanuvchi: {user_mention(user)}\nHozirgi balans: {user['balance']} stars\n\nAmalni tanlang:",
        reply_markup=balance_action_keyboard(),
    )


@router.callback_query(F.data.in_(["admin:bal_add", "admin:bal_sub"]))
async def cb_admin_balance_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    sign = 1 if callback.data == "admin:bal_add" else -1
    await state.update_data(sign=sign)
    await state.set_state(AdminStates.waiting_balance_amount)
    await callback.message.edit_text("Miqdorni kiriting (raqam):")


@router.message(AdminStates.waiting_balance_amount)
async def admin_balance_amount_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    target_id = data.get("target_id")
    sign = data.get("sign", 1)
    await state.clear()

    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Notoʻgʻri miqdor.")
        return

    new_balance = await db_change_balance(target_id, sign * amount)
    user = await db_get_user(target_id)

    await message.answer(
        f"✅ Yangilandi. {user_mention(user)} balansi: {new_balance} stars",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
    try:
        action_word = "qoʻshildi" if sign > 0 else "ayirildi"
        await bot.send_message(
            target_id, f"ℹ️ Balansingizga {amount} stars {action_word}. Joriy balans: {new_balance}"
        )
    except Exception as e:
        logging.warning("Foydalanuvchiga xabar yuborilmadi: %s", e)


# ============================================================
#                    RENDER UCHUN WEBHOOK SERVER
# ============================================================

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
BASE_WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", 10000))


async def on_startup(app: web.Application) -> None:
    await db_connect()
    await db_init()
    if BASE_WEBHOOK_URL:
        webhook_url = BASE_WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logging.info("Webhook o'rnatildi: %s", webhook_url)
    else:
        logging.warning("RENDER_EXTERNAL_URL topilmadi — webhook o'rnatilmadi.")


async def on_shutdown(app: web.Application) -> None:
    if pool is not None:
        await pool.close()


async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="Bot ishlayapti ✅")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health_check)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_shutdown)
    return app


if __name__ == "__main__":
    web.run_app(build_app(), host="0.0.0.0", port=PORT)
