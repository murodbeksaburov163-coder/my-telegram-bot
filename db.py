import aiosqlite
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    channel_id INTEGER PRIMARY KEY,
    title TEXT,
    username TEXT,
    owner_user_id INTEGER,
    discussion_group_id INTEGER
);

CREATE TABLE IF NOT EXISTS battles (
    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER,
    status TEXT DEFAULT 'active',      -- active | ended
    prize TEXT,
    start_time TEXT,
    end_time TEXT,
    announce_message_id INTEGER,
    points_reaction REAL DEFAULT 1,
    points_comment REAL DEFAULT 1,
    points_star REAL DEFAULT 1,
    points_boost REAL DEFAULT 5
);

CREATE TABLE IF NOT EXISTS participants (
    participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER,
    user_id INTEGER,
    full_name TEXT,
    username TEXT,
    channel_message_id INTEGER,
    seq_number INTEGER,
    reactions INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    stars INTEGER DEFAULT 0,
    boosts INTEGER DEFAULT 0,
    bonus REAL DEFAULT 0,
    UNIQUE(battle_id, user_id)
);

CREATE TABLE IF NOT EXISTS group_message_map (
    discussion_group_id INTEGER,
    group_message_id INTEGER,
    participant_id INTEGER,
    PRIMARY KEY (discussion_group_id, group_message_id)
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def add_channel(channel_id, title, username, owner_user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO channels (channel_id, title, username, owner_user_id) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(channel_id) DO UPDATE SET title=excluded.title, username=excluded.username",
            (channel_id, title, username, owner_user_id),
        )
        await db.commit()


async def set_discussion_group(channel_id, group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE channels SET discussion_group_id=? WHERE channel_id=?",
            (group_id, channel_id),
        )
        await db.commit()


async def get_channel_by_discussion_group(group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM channels WHERE discussion_group_id=?", (group_id,)
        )
        return await cur.fetchone()


async def get_user_channels(owner_user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM channels WHERE owner_user_id=?", (owner_user_id,)
        )
        return await cur.fetchall()


async def get_channel(channel_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM channels WHERE channel_id=?", (channel_id,)
        )
        return await cur.fetchone()


async def create_battle(channel_id, prize, start_time, end_time):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO battles (channel_id, prize, start_time, end_time) VALUES (?, ?, ?, ?)",
            (channel_id, prize, start_time, end_time),
        )
        await db.commit()
        return cur.lastrowid


async def set_announce_message(battle_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE battles SET announce_message_id=? WHERE battle_id=?",
            (message_id, battle_id),
        )
        await db.commit()


async def get_active_battle(channel_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM battles WHERE channel_id=? AND status='active' "
            "ORDER BY battle_id DESC LIMIT 1",
            (channel_id,),
        )
        return await cur.fetchone()


async def get_battle(battle_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM battles WHERE battle_id=?", (battle_id,)
        )
        return await cur.fetchone()


async def end_battle(battle_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE battles SET status='ended' WHERE battle_id=?", (battle_id,)
        )
        await db.commit()


async def update_points_setting(battle_id, field, value):
    assert field in ("points_reaction", "points_comment", "points_star", "points_boost")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE battles SET {field}=? WHERE battle_id=?", (value, battle_id)
        )
        await db.commit()


async def add_participant(battle_id, user_id, full_name, username, seq_number):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT OR IGNORE INTO participants "
            "(battle_id, user_id, full_name, username, seq_number) VALUES (?, ?, ?, ?, ?)",
            (battle_id, user_id, full_name, username, seq_number),
        )
        await db.commit()
        return cur.lastrowid


async def get_participant(battle_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM participants WHERE battle_id=? AND user_id=?",
            (battle_id, user_id),
        )
        return await cur.fetchone()


async def count_participants(battle_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM participants WHERE battle_id=?", (battle_id,)
        )
        row = await cur.fetchone()
        return row[0]


async def set_participant_message(participant_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE participants SET channel_message_id=? WHERE participant_id=?",
            (message_id, participant_id),
        )
        await db.commit()


async def get_participant_by_message(battle_id, channel_message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM participants WHERE battle_id=? AND channel_message_id=?",
            (battle_id, channel_message_id),
        )
        return await cur.fetchone()


async def get_participant_by_channel_message_any_battle(channel_id, channel_message_id):
    """Find participant whose post is channel_message_id, in any battle of that channel."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT p.* FROM participants p "
            "JOIN battles b ON p.battle_id = b.battle_id "
            "WHERE b.channel_id=? AND p.channel_message_id=?",
            (channel_id, channel_message_id),
        )
        return await cur.fetchone()


async def update_counter(participant_id, field, value):
    assert field in ("reactions", "comments", "stars", "boosts", "bonus")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE participants SET {field}=? WHERE participant_id=?",
            (value, participant_id),
        )
        await db.commit()


async def increment_counter(participant_id, field, delta=1):
    assert field in ("reactions", "comments", "stars", "boosts", "bonus")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE participants SET {field}={field}+? WHERE participant_id=?",
            (delta, participant_id),
        )
        await db.commit()


async def get_participant_by_id(participant_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM participants WHERE participant_id=?", (participant_id,)
        )
        return await cur.fetchone()


async def get_leaderboard(battle_id):
    battle = await get_battle(battle_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM participants WHERE battle_id=?", (battle_id,)
        )
        rows = await cur.fetchall()
    ranked = sorted(rows, key=lambda r: total_score(r, battle), reverse=True)
    return ranked


def total_score(participant_row, battle_row):
    return (
        participant_row["reactions"] * battle_row["points_reaction"]
        + participant_row["comments"] * battle_row["points_comment"]
        + participant_row["stars"] * battle_row["points_star"]
        + participant_row["boosts"] * battle_row["points_boost"]
        + participant_row["bonus"]
    )


async def map_group_message(discussion_group_id, group_message_id, participant_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO group_message_map "
            "(discussion_group_id, group_message_id, participant_id) VALUES (?, ?, ?)",
            (discussion_group_id, group_message_id, participant_id),
        )
        await db.commit()


async def get_participant_by_group_message(discussion_group_id, group_message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT participant_id FROM group_message_map "
            "WHERE discussion_group_id=? AND group_message_id=?",
            (discussion_group_id, group_message_id),
        )
        row = await cur.fetchone()
        return row["participant_id"] if row else None
