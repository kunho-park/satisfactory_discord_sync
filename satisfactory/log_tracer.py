import asyncio
import time
from datetime import datetime, timedelta
import aiofiles
import re
from .database import *
from .utils import *

import logging
import asyncio, nest_asyncio
from discord import Client
import discord, traceback
import os

nest_asyncio.apply()

logger = logging.getLogger(__name__)


class LogFileHandler:
    def __init__(self, process_callback, log_file_path, loop):
        self.process_callback = process_callback
        self.loop = loop
        self.log_file_path = log_file_path
        self.last_position = 0  # 마지막 읽은 위치 저장
        self.loop.create_task(self.process_new_lines())

    async def process_new_lines(self):
        while True:
            try:
                async with aiofiles.open(
                    self.log_file_path, mode="r", encoding="utf-8"
                ) as f:
                    await f.seek(self.last_position)
                    lines = await f.readlines()
                    self.last_position = await f.tell()
            except:
                self.last_position = 0
                logger.error(f"Log file not found: {self.log_file_path}")
                await asyncio.sleep(5)
                continue
            for line in lines:
                try:
                    await self.process_callback(line)
                except Exception as e:
                    logger.error(f"Error processing line: {line}")
                    logger.error(traceback.format_exc())

            await asyncio.sleep(0.1)


db_path = "./db.json"

logFileOpenRegex = re.compile(r"\[(.+?)\]\[.+\]Log file open, (.*)$")
logFileCommandLineRegex = re.compile(r"^LogInit: Command Line: (.*)$")
loginRequestRegex = re.compile(
    r"^\[(.+?)\]\[.+\]LogNet: Login request: .*\?Name=(.*?)? userId: (.*)?:[0-9]+ \(ForeignId=\[Type=[0-9]+ Handle=[0-9]+ RepData=\[(.*)\]\) platform: .*$"
)
joinRequestRegex = re.compile(
    r"^\[(.+?)\]\[.+\]LogNet: Join request: .*\?Name=(.*?)?\?SplitscreenCount=.*$"
)
joinSucceededRegex = re.compile(r"^\[(.+?)\]\[.+\]LogNet: Join succeeded: (.*?)?$")
connectionCloseRegex = re.compile(
    r"^\[(.+?)\]\[.+\]LogNet: UNetConnection::Close: .*, Driver: GameNetDriver .*, UniqueId: (.*)?:[0-9]+ \(ForeignId=\[Type=[0-9]+ Handle=[0-9]+ RepData=\[(.*)\]\),.*$"
)

invalid_unknown_names_and_ids = ["INVALID", "UNKNOWN"]

poll_interval = 60


class LogTracer:
    def __init__(
        self,
        log_file_path: str,
        address: str = "127.0.0.1",
        port: int = 7777,
        loop: asyncio.AbstractEventLoop = None,
        client: Client = None,
        channel: int = None,
        max_players: int = 4,
    ):
        self.log_file_path = log_file_path
        self.address = address
        self.port = port
        self.url = f"satisfactory://{self.address}:{self.port}"
        self.http_api = HttpApi(self.address, self.port)
        self.loop = loop

        self.client = client
        self.channel = channel
        self.max_players = max_players

        self.http_login_success = False

    async def start(self):
        self.channel = await self.client.fetch_channel(self.channel)
        logger.info(f"Connected Discord Channel: {self.channel}")

        await self.update_server_info()

        self.event_handler = LogFileHandler(
            self.process_callback, self.log_file_path, loop=self.loop
        )

        asyncio.create_task(self.check_server_online())

    async def process_callback(self, line):
        data = self.parse(line.strip())
        if data is not None:
            await self.process(data)

    async def uptime(self):
        server = await get_server_by_address_and_port(self.address, self.port)
        if server["online"] == False:
            return f"{format_timestamp((time.time() * 1000) - server['startTimestamp'])} 동안 오프라인"
        return f"{format_timestamp((time.time() * 1000) - server['startTimestamp'])} 동안 온라인"

    async def rank_str(self):
        rank_players = await rank_player_by_total_join_time(self.url)

        def format_number(number, length):
            if length <= 10:
                emojis = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
                if 0 <= number <= 10:
                    return emojis[number]
            else:
                return f"{number:02d}️."

        return "\n".join(
            [
                f"{format_number(idx, len(rank_players))} **{player['name']}** - {format_timestamp(player['totalJoinTime'])} ({player['joined']}회)"
                for idx, player in enumerate(rank_players, start=1)
            ]
        ).strip()

    async def update_server_info(self):
        server = await get_server_by_address_and_port(self.address, self.port)

        if server is None:
            server = {
                "address": self.address,
                "port": self.port,
                "name": "?",
                "online": False,
                "version": "?",
                "processedTimestamp": 0,
                "startTimestamp": 0,
            }
            await save_server(server)

        if self.http_login_success == False:
            try:
                await self.http_api.login(os.getenv("ADMIN_PASSWORD"))
                self.http_login_success = True
            except:
                self.http_login_success = False
                logger.error("Failed to login to the HTTP API")

        try:
            health_check_response = await self.http_api.health_check()
        except:
            health_check_response = None

        if health_check_response is not None:
            health_check = health_check_response.data["health"] == "healthy"
        else:
            health_check = False

        server_name = "?"
        server_version = "?"
        averageTickRate = "?"
        techTier = "?"
        totalGameDuration = "?"

        if health_check == False:
            if server["online"] == True:
                embed = discord.Embed(
                    title=f":robot: **{self.address}:{self.port}** 서버 꺼짐",
                    color=0xFF0000,
                )
                embed.set_footer(
                    text=f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                await self.channel.send(embed=embed)
                server["online"] = False
                await save_server(server)
                self.event_handler.last_position = 0
                server["startTimestamp"] = int(time.time() * 1000)

            logger.error(f"Probe failed for {self.address}:{self.port}")
            await set_all_player_offline(self.url)
            return
        elif server["online"] == False and health_check == True:

            probe_data = await probe(address=self.address, port=self.port, timeout=180)

            server_info = await self.http_api.query_server_state()
            server_info = server_info.data["serverGameState"]

            if probe_data is not None:
                server_name = probe_data["serverName"]
                server_version = probe_data["serverVersion"]

            if server_info is not None:
                averageTickRate = round(server_info["averageTickRate"], 2)
                techTier = server_info["techTier"]
                totalGameDuration = format_timestamp(
                    server_info["totalGameDuration"] * 1000
                )

                self.max_players = server_info["playerLimit"]

            server["startTimestamp"] = int(time.time() * 1000)

            embed = discord.Embed(
                title=f":robot: **{self.address}:{self.port}** 서버 켜짐",
                color=0x00FF00,
            )
            embed.add_field(name="서버 이름", value=server_name, inline=True)
            embed.add_field(name="서버 버전", value=server_version, inline=True)
            embed.add_field(
                name="평균 틱 레이트", value=f"{averageTickRate:.2f}", inline=True
            )
            embed.add_field(name="기술 티어", value=f"{techTier} 티어", inline=True)
            embed.add_field(name="총 게임 시간", value=totalGameDuration, inline=True)

            embed.set_footer(
                text=f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.channel.send(embed=embed)
            server["online"] = True
            await save_server(server)

        server = {
            "address": self.address,
            "port": self.port,
            "name": server_name,
            "online": True,
            "version": server_version,
            "processedTimestamp": server["processedTimestamp"],
            "startTimestamp": server["startTimestamp"],
        }
        await save_server(server)

    async def check_server_online(self):
        while True:
            try:
                await self.update_server_info()
            except Exception as e:
                logger.error(e)
            await asyncio.sleep(30)

    async def process(self, data):
        server = await get_server_by_address_and_port(self.address, self.port)
        if server is None:
            server = {
                "address": self.address,
                "port": self.port,
                "name": "?",
                "online": False,
                "version": "?",
                "processedTimestamp": 0,
                "startTimestamp": 0,
            }
            await save_server(server)

        if 1728321679054.0 >= data["timestamp"]:
            logger.debug(f"Pass / [{data['timestamp']}] Type: {data['type']}")
            return

        logger.debug(f"Process / [{data['timestamp']}] Type: {data['type']}")
        if data.get("userId") is not None:
            player = await get_player_url_and_user_id(self.url, data["userId"])
            if player is None:
                player = {
                    "url": self.url,
                    "userId": data["userId"],
                    "name": data["name"],
                    "platform": data["platform"],
                    "online": False,
                }
                await save_player(player)
                player = await get_player_url_and_user_id(self.url, data["userId"])
        elif data.get("name") is not None:
            if data["name"] in invalid_unknown_names_and_ids:
                logger.error(f"Invalid or unknown name: {data['name']}")
                return
            player = await get_player_url_and_name(self.url, data["name"])
            if player is None:
                logger.error(f"Cannot find player in the database name: {data['name']}")
                return

        if server["online"] == False:
            return

        if data["type"] == "Log file open":
            await set_all_player_offline(self.url)
        elif data["type"] == "Command line":
            pass
        elif data["type"] == "Login request":
            pass
        elif data["type"] == "Join request":
            pass
        elif data["type"] == "Join succeeded":
            player["lastJoinTimestamp"] = data["timestamp"]
            player["joined"] += 1
            player["online"] = True
            await save_player(player)
            online_players = await get_online_players(self.url)

            embed = discord.Embed(
                title=f":heavy_plus_sign: {player['name']}",
                color=0x00FF00,
            )
            embed.add_field(
                name=f"접속자 ({len(online_players)}/{self.max_players})",
                value=(
                    "\n".join(
                        [
                            f"{idx:02d}. {player['name']} ({player['platform']})"
                            for idx, player in enumerate(online_players, start=1)
                        ]
                    )
                    if len(online_players) > 0
                    else "없음"
                ),
                inline=False,
            )

            embed.set_footer(
                text=f"접속한 시간: {(datetime.fromtimestamp(data['timestamp'] / 1000) + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.channel.send(embed=embed)
        elif data["type"] == "Connection close":
            player["online"] = False

            connected_timestamp = data["timestamp"] - player["lastJoinTimestamp"]
            if connected_timestamp > 0:
                player["totalJoinTime"] += connected_timestamp
                await save_player(player)
            online_players = await get_online_players(self.url)

            embed = discord.Embed(
                title=f":heavy_minus_sign: {player['name']}",
                color=0xFF0000,
            )
            embed.add_field(
                name=f"플레이 시간",
                value=(
                    f"{format_timestamp(connected_timestamp)}"
                    if connected_timestamp > 0
                    else "?"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"총 플레이 시간",
                value=f"{format_timestamp(player['totalJoinTime'])}",
                inline=True,
            )
            embed.add_field(
                name=f"접속자 ({len(online_players)}/{self.max_players})",
                value=(
                    "\n".join(
                        [
                            f"{idx:02d}. {player['name']} ({player['platform']})"
                            for idx, player in enumerate(online_players, start=1)
                        ]
                    )
                    if len(online_players) > 0
                    else "없음"
                ),
                inline=False,
            )
            embed.set_footer(
                text=f"접속 종료 시간: {(datetime.fromtimestamp(data['timestamp'] / 1000) + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}"
            )

            await self.channel.send(embed=embed)

        if player is not None:
            await save_player(player)

        server["processedTimestamp"] = data["timestamp"]
        await save_server(server)

    @staticmethod
    def parse(line):
        pattern_matching = [
            (
                logFileOpenRegex,
                lambda m: {
                    "type": "Log file open",
                    "timestamp": parse_timestamp(m.group(1)),
                    "date": m.group(2),
                },
            ),
            (
                loginRequestRegex,
                lambda m: (
                    {
                        "type": "Login request",
                        "timestamp": parse_timestamp(m.group(1)),
                        "name": m.group(2),
                        "platform": m.group(3),
                        "userId": m.group(4),
                    }
                    if parse_timestamp(m.group(1)) is not None
                    else None
                ),
            ),
            (
                joinRequestRegex,
                lambda m: (
                    {
                        "type": "Join request",
                        "timestamp": parse_timestamp(m.group(1)),
                        "name": m.group(2),
                    }
                    if parse_timestamp(m.group(1)) is not None
                    else None
                ),
            ),
            (
                joinSucceededRegex,
                lambda m: (
                    {
                        "type": "Join succeeded",
                        "timestamp": parse_timestamp(m.group(1)),
                        "name": m.group(2),
                    }
                    if parse_timestamp(m.group(1)) is not None
                    else None
                ),
            ),
            (
                connectionCloseRegex,
                lambda m: (
                    {
                        "type": "Connection close",
                        "timestamp": parse_timestamp(m.group(1)),
                        "platform": m.group(2),
                        "userId": m.group(3),
                    }
                    if parse_timestamp(m.group(1)) is not None
                    else None
                ),
            ),
        ]

        for pattern, result_func in pattern_matching:
            match = pattern.match(line)
            if match:
                result = result_func(match)
                if result:
                    return result

        return None
