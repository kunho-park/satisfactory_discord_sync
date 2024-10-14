import asyncio
import logging
from satisfactory import *
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
SERVER_PORT = int(os.getenv("SERVER_PORT"))  # type: ignore
LOG_PATH = os.getenv("LOG_PATH")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # type: ignore
MAX_PLAYERS = int(os.getenv("MAX_PLAYERS"))  # type: ignore
logging.getLogger("satisfactory.log_tracer").setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("satisfactory_tracer.log"), logging.StreamHandler()],
)

loop = asyncio.get_event_loop()

indent = discord.Intents.default()
indent.message_content = True
indent.guilds = True

client = Client(command_prefix="!", intents=indent)
client.loop = loop
loop.run_until_complete(client.login(DISCORD_TOKEN))


async def load_cogs():
    await client.load_extension("satisfactory.cogs.uptime")
    await client.load_extension("satisfactory.cogs.ranking")


loop.run_until_complete(load_cogs())

tracer = LogTracer(
    log_file_path=LOG_PATH,
    address=SERVER_ADDRESS,
    port=SERVER_PORT,
    loop=loop,
    client=client,
    channel=DISCORD_CHANNEL_ID,
    max_players=MAX_PLAYERS,
)
loop.create_task(tracer.start())
client.satisfactory_tracer = tracer

client.run(DISCORD_TOKEN)
