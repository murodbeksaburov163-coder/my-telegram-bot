from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📡 Kanal biriktirish", callback_data="add_channel")
    b.button(text="📋 Mening kanallarim", callback_data="my_channels")
    b.adjust(1)
    return b.as_markup()


def channels_list_kb(channels):
    b = InlineKeyboardBuilder()
    for ch in channels:
        title = ch["title"] or str(ch["channel_id"])
        b.button(text=title, callback_data=f"ch:{ch['channel_id']}")
    b.button(text="⬅️ Orqaga", callback_data="back_main")
    b.adjust(1)
    return b.as_markup()


def channel_panel_kb(channel_id, has_active_battle):
    b = InlineKeyboardBuilder()
    if has_active_battle:
        b.button(text="🏁 Battl tugatish", callback_data=f"battle_end:{channel_id}")
    else:
        b.button(text="🚀 Battl boshlash", callback_data=f"battle_start:{channel_id}")
    b.button(text="➕➖ Bonus ball", callback_data=f"bonus:{channel_id}")
    b.button(text="⚙️ Ball tizimi sozlamalari", callback_data=f"settings:{channel_id}")
    b.button(text="⬅️ Orqaga", callback_data="my_channels")
    b.adjust(1)
    return b.as_markup()


def settings_kb(channel_id):
    b = InlineKeyboardBuilder()
    b.button(text="👍 Reaksiya balli", callback_data=f"set_pt:{channel_id}:points_reaction")
    b.button(text="💬 Komment balli", callback_data=f"set_pt:{channel_id}:points_comment")
    b.button(text="⭐ Stars balli", callback_data=f"set_pt:{channel_id}:points_star")
    b.button(text="🚀 Boost balli", callback_data=f"set_pt:{channel_id}:points_boost")
    b.button(text="⬅️ Orqaga", callback_data=f"ch:{channel_id}")
    b.adjust(1)
    return b.as_markup()


def channel_post_kb(battle_id):
    b = InlineKeyboardBuilder()
    b.button(text="✅ Qo'shish", callback_data=f"join:{battle_id}")
    b.button(text="📊 Natijalar", callback_data=f"results:{battle_id}")
    b.adjust(2)
    return b.as_markup()


def channel_post_kb_ended():
    b = InlineKeyboardBuilder()
    b.button(text="🔒 Battl yakunlandi", callback_data="noop")
    return b.as_markup()


def bonus_target_kb(battle_id, participants):
    b = InlineKeyboardBuilder()
    for p in participants:
        label = f"{p['seq_number']}. {p['full_name']}"
        b.button(text=label, callback_data=f"bonus_pick:{battle_id}:{p['participant_id']}")
    b.button(text="⬅️ Orqaga", callback_data="back_main")
    b.adjust(1)
    return b.as_markup()


def bonus_amount_kb(battle_id, participant_id):
    b = InlineKeyboardBuilder()
    for val in (1, 5, 10, 20):
        b.button(text=f"+{val}", callback_data=f"bonus_apply:{participant_id}:{val}")
    for val in (1, 5, 10, 20):
        b.button(text=f"-{val}", callback_data=f"bonus_apply:{participant_id}:-{val}")
    b.adjust(4, 4)
    return b.as_markup()
