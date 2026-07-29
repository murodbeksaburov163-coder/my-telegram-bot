from db import total_score


def announce_text(prize, start_time, end_time):
    return (
        "Batl boshlandi 🥳\n\n"
        f"Yutuqlar: {prize}\n\n"
        f"Boshlanish vaqti: {start_time}\n"
        f"Tugash vaqti: {end_time}\n"
    )


def announce_text_ended(prize, start_time, end_time):
    return (
        "🏁 Batl yakunlandi!\n\n"
        f"Yutuqlar: {prize}\n\n"
        f"Boshlanish vaqti: {start_time}\n"
        f"Tugash vaqti: {end_time}\n\n"
        "Natijalarni pastdagi tugma orqali ko'rishingiz mumkin."
    )


def participant_text(p, battle):
    # Ballarni hisoblash
    reactions_score = p["reactions"] * battle["points_reaction"]
    comments_score = p["comments"] * battle["points_comment"]
    stars_score = p["stars"] * battle["points_star"]
    boosts_score = p["boosts"] * battle["points_boost"]
    total = reactions_score + comments_score + stars_score + boosts_score + p["bonus"]

    return (
        f"<b>{p['seq_number']}-ishtirokchi</b>\n"
        f"👤 <b>{p['full_name']}</b>\n\n"
        f"❤️ Reaksiya: {p['reactions']}ta ({reactions_score:g} ball)\n"
        f"💬 Izoh (Comment): {p['comments']}ta ({comments_score:g} ball)\n"
        f"⭐ Stars: {p['stars']}ta ({stars_score:g} ball)\n"
        f"🚀 Boost: {p['boosts']}ta ({boosts_score:g} ball)\n"
        f"🎁 Bonus: {p['bonus']:g} ball\n\n"
        f"🏆 <b>Jami: {total:g} ball</b>"
    )



def leaderboard_text(ranked, battle):
    if not ranked:
        return "Hozircha ishtirokchilar yo'q."
    lines = ["🏆 Top ishtirokchilar:\n"]
    for i, p in enumerate(ranked[:10], start=1):
        name = p["full_name"] or (f"@{p['username']}" if p["username"] else str(p["user_id"]))
        lines.append(f"{i}. {name} — {total_score(p, battle):g} ball")
    return "\n".join(lines)
