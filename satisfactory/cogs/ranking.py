from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import Client


class Ranking(commands.Cog):
    def __init__(self, bot: "Client"):
        self.bot = bot

    @commands.hybrid_command(name="ranking", description="서버 플레이 타임 랭킹 확인")
    async def ranking(self, ctx: commands.Context):
        rankStr = await self.bot.satisfactory_tracer.rank_str()

        await ctx.send(
            f"**{self.bot.satisfactory_tracer.address}:{self.bot.satisfactory_tracer.port} 플레이 타임 랭킹**\n\n{rankStr}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ranking(bot))
