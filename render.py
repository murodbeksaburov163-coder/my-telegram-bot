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
    total = total_score(p, battle)
    name = p["full_name"] or (f"@{p['username']}" if p["username"] else str(p["user_id"]))
    return (
        f"{p['seq_number']}-ishtirokchi\n"
        f"{name}\n\n"
        f"Reaksiya {p['reactions']}ta ({p['reactions'] * battle['points_reaction']:g} ball)\n"
        f"Comment {p['comments']}ta ({p['comments'] * battle['points_comment']:g} ball)\n"
        f"Stars {p['stars']}ta ({p['stars'] * battle['points_star']:g} ball)\n"
        f"Boost {p['boosts']}ta ({p['boosts'] * battle['points_boost']:g} ball)\n"
        f"Bonus {p['bonus']:g} ball\n\n"
        f"Jami: {total:g} ball"
    )


def leaderboard_text(ranked, battle):
    if not ranked:
        return "Hozircha ishtirokchilar yo'q."
    lines = ["🏆 Top ishtirokchilar:\n"]
    for i, p in enumerate(ranked[:10], start=1):
        name = p["full_name"] or (f"@{p['username']}" if p["username"] else str(p["user_id"]))
        lines.append(f"{i}. {name} — {total_score(p, battle):g} ball")
    return "\n".join(lines)
