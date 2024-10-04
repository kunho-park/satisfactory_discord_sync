from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import Client


class Uptime(commands.Cog):
    def __init__(self, bot: "Client"):
        self.bot = bot

    @commands.hybrid_command(name="uptime", description="서버 운영 시간 확인")
    async def uptime(self, ctx: commands.Context):
        uptimeStr = await self.bot.satisfactory_tracer.uptime()
        await ctx.send(f"**Uptime**: {uptimeStr}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Uptime(bot))
