import discord
import random
import asyncio
from discord.ext import commands
from .log_tracer import LogTracer


class Client(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.satisfactory_tracer: LogTracer = kwargs.pop("satisfactory_tracer", None)
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        await self.tree.sync()
