from discord.ext import commands
from configs import masters
from . import errors

async def master_only(ctx: commands.Context):
    if ctx.author.id in masters.MASTERS:
        return True
    raise errors.NotMaster