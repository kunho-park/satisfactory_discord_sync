import sqlite3
import aiosqlite
from hashlib import md5


def init_db():
    with sqlite3.connect("satisfactory.db") as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS servers (
            address TEXT PRIMARY KEY,
            port INTEGER,
            name TEXT,
            online BOOLEAN,
            version TEXT,
            processedTimestamp INTEGER,
            startTimestamp INTEGER
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS players (
            hash TEXT PRIMARY KEY,
            url TEXT,
            userId TEXT,
            name TEXT,
            platform TEXT,
            totalJoinTime INTEGER,
            lastJoinTimestamp INTEGER,
            joined INTEGER,
            online BOOLEAN
        )
        """
        )

        conn.commit()


async def get_server_by_address_and_port(address, port):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT * FROM servers WHERE address = ? AND port = ?", (address, port)
        )
        server = await cursor.fetchone()

    if server:
        return {
            "address": server[0],
            "port": server[1],
            "name": server[2],
            "online": bool(server[3]),
            "version": server[4],
            "processedTimestamp": server[5],
            "startTimestamp": server[6],
        }
    else:
        return None


def player_to_dict(player):
    return {
        "hash": player[0],
        "url": player[1],
        "userId": player[2],
        "name": player[3],
        "platform": player[4],
        "totalJoinTime": player[5],
        "lastJoinTimestamp": player[6],
        "joined": player[7],
        "online": bool(player[8]),
    }


async def get_player_url_and_user_id(
    url,
    userId,
):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT * FROM players WHERE userId = ? AND url = ?", (userId, url)
        )
        player = await cursor.fetchone()

    if player:
        return player_to_dict(player)
    else:
        return None


async def get_player_url_and_name(
    url,
    name,
):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT * FROM players WHERE name = ? AND url = ?", (name, url)
        )
        player = await cursor.fetchone()

    if player:
        return player_to_dict(player)
    else:
        return None


async def get_player_by_hash(
    hash,
):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute("SELECT * FROM players WHERE hash = ?", (hash,))
        player = await cursor.fetchone()

    if player:
        return player_to_dict(player)
    else:
        return None


async def save_server(data):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            """
            INSERT OR REPLACE INTO servers (address, port, name, online, version, processedTimestamp, startTimestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["address"],
                data["port"],
                data["name"],
                data["online"],
                data["version"],
                data["processedTimestamp"],
                data.get("startTimestamp", 0),
            ),
        )
        await conn.commit()


async def save_player(data):

    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            """
            INSERT OR REPLACE INTO players (hash, url, userId, name, platform, totalJoinTime, lastJoinTimestamp, joined, online)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                md5(
                    (data["url"] + data["userId"]).encode()
                ).hexdigest(),  # data["hash"],
                data["url"],
                data["userId"],
                data["name"],
                data["platform"],
                data.get("totalJoinTime", 0),
                data.get("lastJoinTimestamp", 0),
                data.get("joined", 0),
                data["online"],
            ),
        )
        await conn.commit()


async def set_all_player_offline(address):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            "UPDATE players SET online = FALSE WHERE url = ?", (address,)
        )
        await conn.commit()


async def get_online_players(address):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT * FROM players WHERE url = ? AND online = TRUE", (address,)
        )
        players = await cursor.fetchall()
        return [player_to_dict(player) for player in players] if players else []


async def rank_player_by_total_join_time(address):
    async with aiosqlite.connect("satisfactory.db") as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT * FROM players 
            WHERE url = ? 
            ORDER BY totalJoinTime DESC
            """,
            (address,),
        )
        players = await cursor.fetchall()
        return [player_to_dict(player) for player in players] if players else []


init_db()
