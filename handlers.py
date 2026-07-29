import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

import db
import keyboards as kb
import render
from states import AddChannel, StartBattle, SettingsFSM
from config import REQUIRED_CHANNEL, REQUIRED_CHAT

router = Router()

SETTING_LABELS = {
    "points_reaction": "Reaksiya",
    "points_comment": "Komment",
    "points_star": "Stars",
    "points_boost": "Boost",
}


# ---------------------------------------------------------------------------
# Asosiy menyu
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Salom! 👋\nKanalingizdagi konkurs/battl jarayonini boshqarish uchun bot.\n\n"
        "Boshlash uchun kanalingizni biriktiring:",
        reply_markup=kb.main_menu_kb(),
    )


@router.callback_query(F.data == "back_main")
async def back_main(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.message.edit_text("Bosh menyu:", reply_markup=kb.main_menu_kb())
    await cq.answer()


# ---------------------------------------------------------------------------
# Kanal biriktirish
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "add_channel")
async def add_channel_start(cq: CallbackQuery, state: FSMContext):
    await state.set_state(AddChannel.waiting_forward)
    await cq.message.edit_text(
        "Kanalingizdan istalgan postni shu botga forward qiling.\n\n"
        "⚠️ Diqqat: bot avval kanalda ADMIN etib qo'yilgan bo'lishi kerak "
        "(xabar yuborish va tahrirlash huquqlari bilan)."
    )
    await cq.answer()


@router.message(AddChannel.waiting_forward)
async def add_channel_forward(message: Message, state: FSMContext, bot: Bot):
    origin = message.forward_origin
    if not origin or origin.type != "channel":
        await message.answer("Bu kanal posti emas. Iltimos, kanalingizdan postni forward qiling.")
        return

    channel_chat = origin.chat
    channel_id = channel_chat.id

    try:
        bot_member = await bot.get_chat_member(channel_id, bot.id)
    except TelegramBadRequest:
        await message.answer("Bot bu kanalda topilmadi. Avval botni kanalga admin qilib qo'shing.")
        return

    if bot_member.status != "administrator":
        await message.answer("Bot bu kanalda hali admin emas. Admin qilib, qayta urinib ko'ring.")
        return

    try:
        user_member = await bot.get_chat_member(channel_id, message.from_user.id)
    except TelegramBadRequest:
        user_member = None

    if not user_member or user_member.status not in ("administrator", "creator"):
        await message.answer("Siz bu kanalda admin emassiz, shuning uchun uni biriktira olmaysiz.")
        return

    await db.add_channel(
        channel_id, channel_chat.title, channel_chat.username, message.from_user.id
    )
    await state.clear()
    await message.answer(
        f"✅ «{channel_chat.title}» kanali muvaffaqiyatli biriktirildi!",
        reply_markup=kb.main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Mening kanallarim / boshqaruv paneli
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "my_channels")
async def my_channels(cq: CallbackQuery):
    channels = await db.get_user_channels(cq.from_user.id)
    if not channels:
        await cq.answer("Sizda hali biriktirilgan kanal yo'q.", show_alert=True)
        return
    await cq.message.edit_text("Kanalingizni tanlang:", reply_markup=kb.channels_list_kb(channels))
    await cq.answer()


@router.callback_query(F.data.startswith("ch:"))
async def channel_panel(cq: CallbackQuery):
    channel_id = int(cq.data.split(":")[1])
    battle = await db.get_active_battle(channel_id)
    await cq.message.edit_text(
        "Kanal boshqaruv paneli:",
        reply_markup=kb.channel_panel_kb(channel_id, has_active_battle=bool(battle)),
    )
    await cq.answer()


# ---------------------------------------------------------------------------
# Battl boshlash
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("battle_start:"))
async def battle_start(cq: CallbackQuery, state: FSMContext):
    channel_id = int(cq.data.split(":")[1])
    existing = await db.get_active_battle(channel_id)
    if existing:
        await cq.answer("Bu kanalda allaqachon faol battl bor.", show_alert=True)
        return
    await state.update_data(channel_id=channel_id)
    await state.set_state(StartBattle.waiting_prize)
    await cq.message.edit_text("Yutuqlar matnini yuboring (masalan: 1-o'rin 50000, 2-o'rin 30000...):")
    await cq.answer()


@router.message(StartBattle.waiting_prize)
async def battle_prize_entered(message: Message, state: FSMContext):
    await state.update_data(prize=message.text)
    await state.set_state(StartBattle.waiting_end_time)
    await message.answer("Tugash vaqtini yozing (masalan: 05.08.2026 20:00), yoki \"yo'q\" deb yozing:")


@router.message(StartBattle.waiting_end_time)
async def battle_end_time_entered(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    channel_id = data["channel_id"]
    prize = data["prize"]
    end_time = message.text
    start_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    battle_id = await db.create_battle(channel_id, prize, start_time, end_time)

    text = render.announce_text(prize, start_time, end_time)
    sent = await bot.send_message(channel_id, text, reply_markup=kb.channel_post_kb(battle_id))
    await db.set_announce_message(battle_id, sent.message_id)

    await state.clear()
    await message.answer("✅ Battl kanalda e'lon qilindi!", reply_markup=kb.main_menu_kb())


@router.callback_query(F.data.startswith("battle_end:"))
async def battle_end(cq: CallbackQuery, bot: Bot):
    channel_id = int(cq.data.split(":")[1])
    battle = await db.get_active_battle(channel_id)
    if not battle:
        await cq.answer("Faol battl topilmadi.", show_alert=True)
        return

    await db.end_battle(battle["battle_id"])
    text = render.announce_text_ended(battle["prize"], battle["start_time"], battle["end_time"])
    try:
        await bot.edit_message_text(
            text,
            chat_id=channel_id,
            message_id=battle["announce_message_id"],
            reply_markup=kb.channel_post_kb(battle["battle_id"]),
        )
    except TelegramBadRequest:
        pass

    await cq.message.edit_text(
        "🏁 Battl tugatildi.", reply_markup=kb.channel_panel_kb(channel_id, has_active_battle=False)
    )
    await cq.answer()


# ---------------------------------------------------------------------------
# Ball tizimi sozlamalari
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("settings:"))
async def settings_menu(cq: CallbackQuery):
    channel_id = int(cq.data.split(":")[1])
    await cq.message.edit_text(
        "Har bir harakat uchun necha ball berilishini sozlang:",
        reply_markup=kb.settings_kb(channel_id),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("set_pt:"))
async def settings_pick_field(cq: CallbackQuery, state: FSMContext):
    _, channel_id, field = cq.data.split(":")
    battle = await db.get_active_battle(int(channel_id))
    if not battle:
        await cq.answer(
            "Sozlamalar faqat faol battl paytida o'zgartiriladi. Avval battl boshlang.",
            show_alert=True,
        )
        return
    await state.update_data(battle_id=battle["battle_id"], field=field, channel_id=channel_id)
    await state.set_state(SettingsFSM.waiting_value)
    await cq.message.edit_text(f"{SETTING_LABELS[field]} uchun necha ball berilsin? (raqam kiriting)")
    await cq.answer()


@router.message(SettingsFSM.waiting_value)
async def settings_value_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting (masalan: 1 yoki 0.5).")
        return
    await db.update_points_setting(data["battle_id"], data["field"], value)
    await state.clear()
    await message.answer(
        f"✅ {SETTING_LABELS[data['field']]} balli {value:g} qilib belgilandi.",
        reply_markup=kb.main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Bonus ball
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("bonus:"))
async def bonus_menu(cq: CallbackQuery):
    channel_id = int(cq.data.split(":")[1])
    battle = await db.get_active_battle(channel_id)
    if not battle:
        await cq.answer("Faol battl topilmadi.", show_alert=True)
        return
    ranked = await db.get_leaderboard(battle["battle_id"])
    if not ranked:
        await cq.answer("Hozircha ishtirokchilar yo'q.", show_alert=True)
        return
    await cq.message.edit_text(
        "Bonus ball berish uchun ishtirokchini tanlang:",
        reply_markup=kb.bonus_target_kb(battle["battle_id"], ranked),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("bonus_pick:"))
async def bonus_pick(cq: CallbackQuery):
    _, battle_id, participant_id = cq.data.split(":")
    await cq.message.edit_text(
        "Necha ball qo'shamiz yoki ayiramiz?",
        reply_markup=kb.bonus_amount_kb(int(battle_id), int(participant_id)),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("bonus_apply:"))
async def bonus_apply(cq: CallbackQuery, bot: Bot):
    _, participant_id, amount = cq.data.split(":")
    participant_id = int(participant_id)
    amount = float(amount)

    await db.increment_counter(participant_id, "bonus", amount)
    p = await db.get_participant_by_id(participant_id)
    battle = await db.get_battle(p["battle_id"])
    await refresh_participant_message(bot, p, battle)

    await cq.answer(f"Bonus {amount:g} ball qo'llandi.", show_alert=True)
    await cq.message.edit_text("✅ Bonus ball qo'llandi.", reply_markup=kb.main_menu_kb())


# ---------------------------------------------------------------------------
# Kanaldagi "Qo'shish" / "Natijalar" tugmalari (barcha foydalanuvchilar uchun)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("join:"))
async def join_battle(cq: CallbackQuery, bot: Bot):
    battle_id = int(cq.data.split(":")[1])
    battle = await db.get_battle(battle_id)
    if not battle or battle["status"] != "active":
        await cq.answer("Battl faol emas.", show_alert=True)
        return

    # Majburiy obuna tekshiruvi
    for chat_username in (REQUIRED_CHANNEL, REQUIRED_CHAT):
        try:
            member = await bot.get_chat_member(chat_username, cq.from_user.id)
            if member.status in ("left", "kicked"):
                raise ValueError
        except Exception:
            await cq.answer(
                f"Ishtirok etish uchun avval {REQUIRED_CHANNEL} va {REQUIRED_CHAT}ga "
                f"obuna bo'ling, so'ng qayta bosing.",
                show_alert=True,
            )
            return

    existing = await db.get_participant(battle_id, cq.from_user.id)
    if existing and existing["channel_message_id"]:
        await cq.answer("Siz allaqachon ishtirok etyapsiz!", show_alert=True)
        return

    seq = (await db.count_participants(battle_id)) + 1
    full_name = cq.from_user.full_name
    username = cq.from_user.username
    await db.add_participant(battle_id, cq.from_user.id, full_name, username, seq)
    p = await db.get_participant(battle_id, cq.from_user.id)

    text = render.participant_text(p, battle)
    sent = await bot.send_message(battle["channel_id"], text)
    await db.set_participant_message(p["participant_id"], sent.message_id)

    await cq.answer("✅ Siz battlga muvaffaqiyatli qo'shildingiz!", show_alert=True)


@router.callback_query(F.data.startswith("results:"))
async def show_results(cq: CallbackQuery, bot: Bot):
    battle_id = int(cq.data.split(":")[1])
    battle = await db.get_battle(battle_id)
    ranked = await db.get_leaderboard(battle_id)
    text = render.leaderboard_text(ranked, battle)

    try:
        await bot.send_message(cq.from_user.id, text)
        await cq.answer("Natijalar shaxsiy xabarlarga yuborildi.")
    except TelegramForbiddenError:
        short = text[:190]
        await cq.answer(short, show_alert=True)


@router.callback_query(F.data == "noop")
async def noop(cq: CallbackQuery):
    await cq.answer()


# ---------------------------------------------------------------------------
# Avtomatik hisoblash: reaksiya + stars (message_reaction_count)
# ---------------------------------------------------------------------------

async def refresh_participant_message(bot: Bot, p, battle):
    text = render.participant_text(p, battle)
    try:
        await bot.edit_message_text(text, chat_id=battle["channel_id"], message_id=p["channel_message_id"])
    except TelegramBadRequest:
        pass


@router.message_reaction_count()
async def on_reaction_count(update, bot: Bot):
    channel_id = update.chat.id
    message_id = update.message_id
    p = await db.get_participant_by_channel_message_any_battle(channel_id, message_id)
    if not p:
        return

    reactions_total = 0
    stars_total = 0
    for rc in update.reactions:
        if rc.type.type == "paid":
            stars_total += rc.total_count
        else:
            reactions_total += rc.total_count

    await db.update_counter(p["participant_id"], "reactions", reactions_total)
    await db.update_counter(p["participant_id"], "stars", stars_total)

    p = await db.get_participant_by_id(p["participant_id"])
    battle = await db.get_battle(p["battle_id"])
    await refresh_participant_message(bot, p, battle)


# ---------------------------------------------------------------------------
# Avtomatik hisoblash: boost
# ---------------------------------------------------------------------------

@router.chat_boost()
async def on_chat_boost(update, bot: Bot):
    channel_id = update.chat.id
    source = update.boost.source
    user = getattr(source, "user", None)
    if not user:
        return
    battle = await db.get_active_battle(channel_id)
    if not battle:
        return
    p = await db.get_participant(battle["battle_id"], user.id)
    if not p or not p["channel_message_id"]:
        return
    await db.increment_counter(p["participant_id"], "boosts", 1)
    p = await db.get_participant_by_id(p["participant_id"])
    await refresh_participant_message(bot, p, battle)


@router.removed_chat_boost()
async def on_chat_boost_removed(update, bot: Bot):
    channel_id = update.chat.id
    source = update.source
    user = getattr(source, "user", None)
    if not user:
        return
    battle = await db.get_active_battle(channel_id)
    if not battle:
        return
    p = await db.get_participant(battle["battle_id"], user.id)
    if not p or not p["channel_message_id"] or p["boosts"] <= 0:
        return
    await db.increment_counter(p["participant_id"], "boosts", -1)
    p = await db.get_participant_by_id(p["participant_id"])
    await refresh_participant_message(bot, p, battle)


# ---------------------------------------------------------------------------
# Avtomatik hisoblash: komment (bog'langan muhokama guruhi orqali)
# ---------------------------------------------------------------------------

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def on_group_message(message: Message, bot: Bot):
    # 1) Kanal postining guruhga avtomatik forward qilingan nusxasini aniqlaymiz
    if message.is_automatic_forward and message.forward_origin and message.forward_origin.type == "channel":
        await db.set_discussion_group(message.forward_origin.chat.id, message.chat.id)
        p = await db.get_participant_by_channel_message_any_battle(
            message.forward_origin.chat.id, message.forward_origin.message_id
        )
        if p:
            await db.map_group_message(message.chat.id, message.message_id, p["participant_id"])
        return

    # 2) Ishtirokchi postiga yozilgan izoh (reply)
    if message.reply_to_message:
        participant_id = await db.get_participant_by_group_message(
            message.chat.id, message.reply_to_message.message_id
        )
        if participant_id:
            await db.increment_counter(participant_id, "comments", 1)
            p = await db.get_participant_by_id(participant_id)
            battle = await db.get_battle(p["battle_id"])
            await refresh_participant_message(bot, p, battle)
