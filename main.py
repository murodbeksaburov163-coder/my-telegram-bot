import telebot
from telebot import types
import time
import sqlite3
import html
from flask import Flask, request
from database import init_db, add_user, get_user, update_phone_and_give_bonus, get_stats, get_all_users, change_user_balance, DB_NAME

# 🛠 BOT TOKENINI SHU YERGA YOZING:
TOKEN = "8762594173:AAFtqn2ryWSKPlsbAmAG88JTxvKu8EWH58g"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

ADMIN_ID = 8597455078
ADMIN_USERNAME = "ADMlNlSTRATOR_UZ"
PAY_CHANNEL_NAME = "bepul_gifts"

ADMIN_LINK = f'<a href="https://t.me/{ADMIN_USERNAME}">@{ADMIN_USERNAME}</a>'
PAY_CHANNEL_LINK = f'<a href="https://t.me/{PAY_CHANNEL_NAME}">@{PAY_CHANNEL_NAME}</a>'

# 📢 OMMAVIY KANALLAR VA GURUHLAR RO'YXATI (Yangi qo'shilgan chatlar bilan birga)
CHANNELS = [
    "@K0NKURS_UZ",
    "@gifts_evil",
    "@VZ_REAK_CHATl",  # Evil Gifts 💝 chat
    "@REAK_CHAT"       # Astro Konkurs chat
]

# 🔒 FAQAT BITTA SHAXSIY KANAL QOLDI
PRIVATE_CHANNEL_LINK = "https://t.me/+IwLGet4hlQk1YTBi"  # My Life

CARD_INFO = "💳 <code>5614 6887 0422 6686</code>\n👤 <b>Sohibi:</b> Q.Doniyor"

GIFTS = {
    "gift_1": {"name": "🧸💖 (4tasi )", "price": 50},
    "gift_2": {"name": "🎁🌹(4tasi ) ", "price": 65},
    "gift_3": {"name": "💐🎂🚀🍾 (2tasi ) ", "price": 85},
    "gift_4": {"name": "🏆💎💍( 1tasi ) ", "price": 90}
}

PREMIUMS = {
    "prem_1": {"name": "Telegram Premium (1 Oylik)", "price": 150},
    "prem_3": {"name": "Telegram Premium (3 Oylik)", "price": 350},
    "prem_12": {"name": "Telegram Premium (12 Oylik)", "price": 990}
}

def clean_html(text):
    if not text:
        return ""
    return html.escape(str(text))

def get_user_referrals(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, phone FROM users WHERE referrer_id = ?", (user_id,))
    refs = cursor.fetchall()
    conn.close()
    return refs

def get_top_referrals():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, stars FROM users WHERE phone IS NOT NULL ORDER BY stars DESC LIMIT 20")
    top_list = cursor.fetchall()
    conn.close()

    text = "🏆 <b>Konkurs Reytingi (Top 20)</b>\n\n"
    if not top_list:
        text += "Hech kim hali ro'yxatda yo'q."
    else:
        for i, (u_id, stars) in enumerate(top_list, 1):
            try:
                chat = bot.get_chat(u_id)
                name = chat.first_name if chat.first_name else "Foydalanuvchi"
            except:
                name = f"User {u_id}"

            safe_name = clean_html(name)
            text += f"{i}. {safe_name} — <b>{stars} stars</b>\n"

    text += "\n🎁 <b>Eng ko'p referal yig'gan ishtirokchi taqdirlanadi!</b>"
    return text

def get_main_menu(user_id, balance, stars):
    text = (
        "👑 <b>Eng tezkor va ishonchli xizmatlardan foydalaning</b>\n\n"
        "🔍 <b>ID:</b> <code>{user_id}</code>\n"
        "📊 <b>Xisobingiz:</b> {balance} som\n\n"
        "🤝 <b>Referal bonus:</b> {stars} stars\n\n"
        "🔗 <code>https://t.me/bepul_gifts_bot?start={user_id}</code>\n"
        "⭐️ Quyidagi havolani do'stlaringizga ulashing va har bir do'stingiz uchun <b>5 stars</b> bonus olasiz."
    ).format(user_id=user_id, balance=balance, stars=stars)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton(text="🏆 Konkursda ishtirok etish", callback_data="btn_konkurs"))
    markup.row(types.InlineKeyboardButton(text="💖 Gift olish", callback_data="btn_gift_olish"), types.InlineKeyboardButton(text="⭐️ Premium olish", callback_data="btn_premium_olish"))
    markup.row(types.InlineKeyboardButton(text="📱 Raqam olish", callback_data="btn_raqam_olish"), types.InlineKeyboardButton(text="💼 Xisob toldirish", callback_data="btn_pay"))
    markup.row(types.InlineKeyboardButton(text="💰 Stars yechish", callback_data="btn_withdraw"), types.InlineKeyboardButton(text="🌐 SMM xizmatlari", callback_data="btn_smm"))
    markup.row(types.InlineKeyboardButton(text="👥 Referallarim", callback_data="btn_my_referrals"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="statistika"))
    markup.row(types.InlineKeyboardButton(text="👤 Admin", callback_data="admin_info"), types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh"))

    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton(text="⚙️ Admin Panel (Yashirin)", callback_data="admin_panel"))

    return text, markup

def check_sub(user_id):
    is_sub = True
    for channel in CHANNELS:
        # Username formatini to'g'rilash (agar boshida @ bo'lmasa avtomatik qo'shiladi)
        ch_username = channel if channel.startswith("@") else f"@{channel}"
        try:
            status = bot.get_chat_member(ch_username, user_id).status
            if status in ['left', 'kicked']:
                is_sub = False
                break
        except:
            is_sub = False
            break

    if not is_sub:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()

        if res and res[0]:
            referrer_id = res[0]
            try:
                chat = bot.get_chat(user_id)
                friend_name = chat.first_name if chat.first_name else f"ID: {user_id}"

                warn_text = (
                    f"⚠️ <b>OGOHLANTIRISH!</b>\n\n"
                    f"Siz taklif qilgan do'stingiz <b>{clean_html(friend_name)}</b> kanallarni tark etdi! "
                    f"Agar bu holat takrorlansa, jarima ball beriladi yoki balansingiz muzlatilishi mumkin!"
                )
                bot.send_message(referrer_id, warn_text)

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET referrer_id = NULL WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
            except:
                pass

    return is_sub

def get_sub_keyboard():
    markup = types.InlineKeyboardMarkup()
    # 4 ta ommaviy kanal va guruhlar tugmasi
    markup.add(types.InlineKeyboardButton(text="🌌 Astro Konkurs", url="https://t.me/K0NKURS_UZ"))
    markup.add(types.InlineKeyboardButton(text="🧸 Evil Gifts", url="https://t.me/gifts_evil"))
    markup.add(types.InlineKeyboardButton(text="💝 𝐄𝐯𝐢𝐥 𝐆𝐢𝐟𝐭𝐬 chat", url="https://t.me/VZ_REAK_CHATl"))
    markup.add(types.InlineKeyboardButton(text="🚀 𝙰𝚜𝚝𝚛𝚘 𝙺𝚘𝚗𝚔𝚞𝚛𝚜 chat", url="https://t.me/REAK_CHAT"))

    # 1 ta qolgan shaxsiy kanal tugmasi
    markup.add(types.InlineKeyboardButton(text="🇲🇾 🇱🇮🇫🇪 🤴🏻 (Shaxsiy)", url=PRIVATE_CHANNEL_LINK))

    markup.add(types.InlineKeyboardButton(text=" obuna boldim ✅ ", callback_data="check_subscription"))
    return markup


@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split()[1:] if len(message.text.split()) > 1 else None
    referrer_id = int(args[0]) if args and args[0].isdigit() else None

    add_user(user_id, referrer_id)

    if not check_sub(user_id):
        bot.send_message(message.chat.id, "⚠️ <b>Botdan foydalanish uchun hamkor kanallarimizga obuna bo'ling!</b>", reply_markup=get_sub_keyboard())
        return

    balance, stars, phone = get_user(user_id)
    if not phone:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
        bot.send_message(message.chat.id, "👋 <b>Xush kelibsiz!</b> Botdan to'liq foydalanish uchun pastdagi tugma orqali telefon raqamingizni yuboring:", reply_markup=markup)
        return

    text, reply_markup = get_main_menu(user_id, balance, stars)
    bot.send_message(message.chat.id, text, reply_markup=reply_markup)

    markup_gift = types.InlineKeyboardMarkup()
    btn_gift = types.InlineKeyboardButton(
        text="Giftni olish 🧸",
        url="https://t.me/AnonimStars_Bot?start=7888928851"
    )
    markup_gift.add(btn_gift)

    bot.send_message(
        chat_id=message.chat.id,
        text="Tabriklayman siz gift yutdingiz 🥳",
        reply_markup=markup_gift
    )


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
        if phone.startswith("+998") or phone.startswith("998") or phone.startswith("+"):
            referrer_id = update_phone_and_give_bonus(user_id, phone)

            if referrer_id:
                try:
                    bot.send_message(referrer_id, f"🔔 <b>Yangi referal!</b> Havolangiz orqali yangi foydalanuvchi ro'yxatdan o'tdi. Sizga <b>+5 stars</b> berildi! 🎉")
                except:
                    pass

            balance, stars, _ = get_user(user_id)
            text, reply_markup = get_main_menu(user_id, balance, stars)
            bot.send_message(message.chat.id, "✅ <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>", reply_markup=types.ReplyKeyboardRemove())
            bot.send_message(message.chat.id, text, reply_markup=reply_markup)
        else:
            bot.send_message(message.chat.id, "❌ <b>Kechirasiz, botdan faqat O'zbekiston raqamlari (+998) orqali ro'yxatdan o'tish mumkin!</b>")

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription_callback(call):
    user_id = call.from_user.id
    if check_sub(user_id):
             try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
             except Exception:
                pass
             balance, stars, phone = get_user(user_id)
             if not phone:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add(types.KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
                bot.send_message(call.message.chat.id, "✅ Kanallarga obuna bo'lindi. Endi telefon raqamingizni yuboring:", reply_markup=markup)
             else:
                text, reply_markup = get_main_menu(user_id, balance, stars)
                bot.send_message(call.message.chat.id, text, reply_markup=reply_markup)
    else:
        bot.answer_callback_query(call.id, "❌ Hali hamma kanallarga obuna bo'lmagansiz!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_'))
def buttons_handler(call):
    user_id = call.from_user.id
    action = call.data
    balance, stars, phone = get_user(user_id)

    back_markup = types.InlineKeyboardMarkup()
    back_markup.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_menu"))

    if action == "btn_konkurs":
        text = get_top_referrals()
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_markup)

    elif action == "btn_my_referrals":
        refs = get_user_referrals(user_id)
        text = "👥 <b>Siz taklif qilgan do'stlaringiz ro'yxati:</b>\n\n"
        if not refs:
            text += "Siz hali hech kimni taklif qilmagansiz."
        else:
            text += f"Jami chaqirilganlar: <b>{len(refs)} ta</b>\n\n"
            for i, (ref_id, ref_phone) in enumerate(refs, 1):
                status = "✅ Tasdiqlangan" if ref_phone else "⏳ Raqam kutilmoqda"
                try:
                    chat = bot.get_chat(ref_id)
                    r_name = chat.first_name if chat.first_name else f"Foydalanuvchi"
                except:
                    r_name = f"User {ref_id}"
                text += f"{i}. {clean_html(r_name)} ({status})\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_markup)

    elif action == "btn_gift_olish":
        text = (
            "💖 <b>Gift do'koni</b>\n\n"
            "⚠️ <b>Diqqat:</b> Birinchi buyurtma narxi kamida <b>50 stars</b> bo'lishi shart!\n"
            "Kerakli sovg'ani tanlang:\n\n"
            "Sizning balansingiz: <b>{0} stars</b>"
        ).format(stars)

        gift_markup = types.InlineKeyboardMarkup(row_width=1)
        for g_id, g_info in GIFTS.items():
            gift_markup.add(types.InlineKeyboardButton(text=f"{g_info['name']} — {g_info['price']} stars", callback_data=f"buy_gift_{g_id}"))
        gift_markup.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_menu"))

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=gift_markup)

    elif action == "btn_premium_olish":
        text = f"⭐️ <b>Telegram Premium sotib olish</b>\n\nSizning balansingiz: <b>{stars} stars</b>\n\nKerakli muddatni tanlang (Adminga so'rov yuboriladi):"
        prem_markup = types.InlineKeyboardMarkup(row_width=1)
        for p_id, p_info in PREMIUMS.items():
            prem_markup.add(types.InlineKeyboardButton(text=f"{p_info['name']} — {p_info['price']} stars", callback_data=f"buy_prem_{p_id}"))
        prem_markup.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=prem_markup)

    elif action == "btn_raqam_olish":
        text = f"📱 <b>Anonim virtual raqamlar olish</b>\n\n🇺🇿 O'zbekiston raqami narxi: <b>120 stars</b>\n\nSizning balansingiz: <b>{stars} stars</b>"
        num_markup = types.InlineKeyboardMarkup(row_width=1)
        num_markup.add(types.InlineKeyboardButton(text="🇺🇿 O'zbekiston raqamini olish (120 stars)", callback_data="buy_raqam_uzb"))
        num_markup.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=num_markup)

    elif action == "btn_pay":
        text = (
            f"💼 <b>Xisobni to'ldirish</b>\n\n"
            f"Hisobingizni to'ldirish uchun pastdagi kartaga pul o'tkazing va chekni adminga {ADMIN_LINK} yuboring:\n\n"
            f"{CARD_INFO}\n\n"
            f"To'lovlar kanali: {PAY_CHANNEL_LINK}"
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_markup)

    elif action == "btn_smm":
        text = "🌐 <b>SMM Xizmatlari</b>\n\nTelegram kanal va guruhlarga odam qo'shish, ko'rishlar sonini oshirish xizmatlari tez orada ishga tushadi."
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_markup)

# Admin tasdiqlash xaridlari
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def order_request_callback(call):
    user_id = call.from_user.id
    data = call.data
    balance, stars, phone = get_user(user_id)

    item_name = ""
    item_price = 0
    item_type = ""

    if data.startswith("buy_gift_"):
        g_id = data.replace("buy_gift_", "")
        if g_id in GIFTS:
            item_name = GIFTS[g_id]["name"]
            item_price = GIFTS[g_id]["price"]
            item_type = "Gift"

    elif data.startswith("buy_prem_"):
        p_id = data.replace("buy_prem_", "")
        if p_id in PREMIUMS:
            item_name = PREMIUMS[p_id]["name"]
            item_price = PREMIUMS[p_id]["price"]
            item_type = "Premium"

    elif data == "buy_raqam_uzb":
        item_name = "O'zbekiston virtual raqami"
        item_price = 120
        item_type = "Raqam"

    if item_price == 0:
        bot.answer_callback_query(call.id, "Xatolik yuz berdi!", show_alert=True)
        return

    if stars < item_price:
        bot.answer_callback_query(call.id, f"❌ Mablag' yetarli emas! Sizga yana {item_price - stars} stars kerak.", show_alert=True)
        return

    buyer_name = clean_html(call.from_user.first_name)
    buyer_user = f"@{call.from_user.username}" if call.from_user.username else "Yo'q"

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.row(
        types.InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"approve_{user_id}_{item_price}_{item_type}"),
        types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}_{item_price}")
    )

    admin_msg = (
        f"🔔 <b>Yangi xarid so'rovi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {buyer_name} ({buyer_user})\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"📦 <b>Turi:</b> {item_type}\n"
        f"🛍 <b>Mahsulot:</b> {item_name}\n"
        f"💰 <b>Narxi:</b> {item_price} stars\n\n"
        f"Xaridni tasdiqlaysizmi?"
    )

    try:
        bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)
        bot.answer_callback_query(call.id, "✅ So'rovingiz adminga yuborildi. Tasdiqlanishini kuting!", show_alert=True)

        back_markup = types.InlineKeyboardMarkup()
        back_markup.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_menu"))
        bot.edit_message_text("⏳ <b>Buyurtmangiz ko'rib chiqilmoqda...</b> Admin tasdiqlashi bilan hisobingizdan stars yechiladi.", call.message.chat.id, call.message.message_id, reply_markup=back_markup)
    except:
        bot.answer_callback_query(call.id, "❌ Adminga so'rov yuborishda xatolik.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def admin_decision_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    data_parts = call.data.split('_')
    action = data_parts[0]
    target_user_id = int(data_parts[1])
    item_price = int(data_parts[2])

    if action == "approve":
        item_type = data_parts[3]
        _, current_stars, _ = get_user(target_user_id)

        if current_stars >= item_price:
            change_user_balance(target_user_id, -item_price, "stars")
            bot.edit_message_text(call.message.text + "\n\n✅ <b>Qabul qilindi va Stars yechildi!</b>", call.message.chat.id, call.message.message_id, reply_markup=None)
            try:
                bot.send_message(target_user_id, f"🎉 <b>Ajoyib xushxabar!</b> Admin buyurtmangizni tasdiqladi. Hisobingizdan <b>{item_price} stars</b> yechildi. Yaqin orada xizmat yetkaziladi!")
            except:
                pass
        else:
            bot.edit_message_text(call.message.text + "\n\n❌ <b>Xatolik: Foydalanuvchida stars yetarli emas!</b>", call.message.chat.id, call.message.message_id, reply_markup=None)

    elif action == "reject":
        bot.edit_message_text(call.message.text + "\n\n❌ <b>Buyurtma rad etildi!</b>", call.message.chat.id, call.message.message_id, reply_markup=None)
        try:
            bot.send_message(target_user_id, f"❌ <b>Sizning buyurtmangiz admin tomonidan rad etildi.</b> Stars hisobingizdan yechilmadi.")
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu_callback(call):
    user_id = call.from_user.id
    balance, stars, _ = get_user(user_id)
    text, reply_markup = get_main_menu(user_id, balance, stars)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=reply_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'refresh')
def refresh_cmd(call):
    user_id = call.from_user.id
    if not check_sub(user_id):
        bot.send_message(call.message.chat.id, "⚠️ Obuna to'xtatilgan!", reply_markup=get_sub_keyboard())
        return
    balance, stars, _ = get_user(user_id)
    text, reply_markup = get_main_menu(user_id, balance, stars)
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=reply_markup)
    except:
        pass
    bot.answer_callback_query(call.id, "Yangilandi ✅")

@bot.callback_query_handler(func=lambda call: call.data == 'statistika')
def statistika_callback(call):
    bot.answer_callback_query(call.id)
    total, active = get_stats()
    bot.send_message(call.message.chat.id, f"📊 <b>Bot statistikasi:</b>\n\n👥 <b>Umumiy a'zolar:</b> {total} ta\n✅ <b>Raqam tasdiqlaganlar:</b> {active} ta")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_info')
def admin_info_callback(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="✍️ Adminga xabar yozish", callback_data="write_to_admin"))
    markup.add(types.InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_menu"))

    bot.edit_message_text(
        f"👤 <b>Bosh Admin:</b> {ADMIN_LINK}\n"
        f"🆔 <b>Admin ID:</b> <code>{ADMIN_ID}</code>\n"
        f"💳 <b>To'lov kanali:</b> {PAY_CHANNEL_LINK}\n\n"
        f"Adminga to'g'ridan-to'g'ri bot orqali xabar yuborish uchun pastdagi tugmani bosing:",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "write_to_admin")
def write_to_admin_callback(call):
    msg = bot.send_message(call.message.chat.id, "📝 <b>Adminga yubormoqchi bo'lgan matningizni yozing:</b>\n\n<i>(Xabar matnini kiritsangiz, u adminga yetkaziladi)</i>")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"

    safe_name = clean_html(name)
    safe_username = clean_html(username)
    safe_msg = clean_html(message.text)

    admin_text = (
        f"📩 <b>Yangi xabar keldi!</b>\n\n"
        f"👤 <b>Kimdan:</b> {safe_name}\n"
        f"🌐 <b>Username:</b> {safe_username}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        f"💬 <b>Xabar matni:</b>\n{safe_msg}"
    )

    try:
        bot.send_message(ADMIN_ID, admin_text)
        bot.send_message(message.chat.id, "✅ <b>Xabaringiz adminga muvaffqiyatli yuborildi!</b>")
    except:
        bot.send_message(message.chat.id, "❌ <b>Xabarni yuborishda xatolik yuz berdi.</b>")

    balance, stars, _ = get_user(user_id)
    text, reply_markup = get_main_menu(user_id, balance, stars)
    bot.send_message(message.chat.id, text, reply_markup=reply_markup)

# 👑 ADMIN PANEL FUNKSIYALARI

@bot.callback_query_handler(func=lambda call: call.data == 'admin_panel' and call.from_user.id == ADMIN_ID)
def admin_panel_callback(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="📢 Hammaga Xabar Yuborish", callback_data="adm_send_post"))
    markup.add(types.InlineKeyboardButton(text="✍️ Foydalanuvchi Tekshirish / Balans", callback_data="adm_change_bal"))
    markup.add(types.InlineKeyboardButton(text="⬅️ Chiqish", callback_data="back_to_menu"))
    bot.edit_message_text("🛠 <b>Bosh Admin boshqaruv paneli:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'adm_send_post' and call.from_user.id == ADMIN_ID)
def adm_send_post_callback(call):
    msg = bot.send_message(call.message.chat.id, "📢 Bot a'zolariga yubormoqchi bo'lgan xabaringizni yuboring:")
    bot.register_next_step_handler(msg, send_marketing_post)

def send_marketing_post(message):
    users = get_all_users()
    bot.send_message(ADMIN_ID, f"🚀 Xabar yuborish boshlandi. Jami: {len(users)} ta...")

    count = 0
    for u_id in users:
        try:
            bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Reklama yakunlandi. {count} ta odamga yetib bordi.")

@bot.callback_query_handler(func=lambda call: call.data == 'adm_change_bal' and call.from_user.id == ADMIN_ID)
def adm_change_bal_callback(call):
    msg = bot.send_message(call.message.chat.id, "Balansni o'zgartirish formatini tanlang:\n\nFormat: <code>ID Turi Miqdori</code>\n\n<b>Masalan:</b>\n• Stars qo'shish: <code>8597455078 stars 50</code>\n• Stars ayirish: <code>8597455078 stars -30</code>\n• So'm qo'shish: <code>8597455078 balance 15000</code>\n• So'm ayirish: <code>8597455078 balance -10000</code>")
    bot.register_next_step_handler(msg, process_change_bal)

def process_change_bal(message):
    try:
        u_id, b_type, amount = message.text.split()
        u_id = int(u_id)
        amount = int(amount)

        if b_type not in ["stars", "balance"]:
            bot.send_message(ADMIN_ID, "❌ Xatolik! Turi faqat <code>stars</code> yoki <code>balance</code> bo'lishi kerak.")
            return

        change_user_balance(u_id, amount, b_type)

        refs = get_user_referrals(u_id)
        ref_text = f"\n\n👥 <b>Ushbu foydalanuvchi chaqirgan referallar (Jami: {len(refs)} ta):</b>\n"
        if refs:
            for i, (r_id, r_phone) in enumerate(refs[:15], 1):
                status = "✅ Tasdiqlangan" if r_phone else "⏳ Raqamsiz"
                ref_text += f"{i}. ID: <code>{r_id}</code> ({status})\n"
        else:
            ref_text += "Hech kimni chaqirmagan."

        bot.send_message(ADMIN_ID, f"✅ Foydalanuvchi ({u_id}) '{b_type}' balansi {amount:+} ga o'zgartirildi.{ref_text}")

        unit = "stars" if b_type == "stars" else "som"
        bot.send_message(u_id, f"🔔 Admin balansingizni o'zgartirdi: <b>{amount:+} {unit}</b>!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Xatolik! Format xato yoki foydalanuvchi bazada yo'q. Xato: {e}")


# =========================================================
# WEBHOOK BOSHQARUV TIZIMI (PYTHONANYWHERE UCHUN)
# =========================================================

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        try:
            bot.process_new_updates([update])
        except Exception as e:
            import traceback
            print("XATO process_new_updates ichida:", e)
            traceback.print_exc()
        return "!", 200
    return "Noto'g'ri so'rov turi", 403