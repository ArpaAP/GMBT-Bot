import discord
from discord.ext import commands
from configs import colors, clac
from utils.basecog import BaseCog
from utils import checks
from db import help
from typing import Optional
import aiomysql
import asyncio
import datetime
import time
import math
import uuid

class Maincmds(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.command(name='도움', aliases=['도움말'])
    async def _help(self, ctx: commands.Context):
        embed = discord.Embed(title='📃 GMBT 봇 전체 명령어', description='(소괄호)는 필수 입력, [대괄호]는 선택 입력입니다. *별표는 여러번 입력할 수 있는 부분입니다.\n\n', color=colors.PRIMARY)
        for name, value in help.gethelps():
            embed.add_field(
                name='🔸' + name,
                value=value.format(p=self.prefix),
                inline=False
            )
        
        if ctx.channel.type != discord.ChannelType.private:
            msg, sending = await asyncio.gather(
                ctx.author.send(embed=embed),
                ctx.send(embed=discord.Embed(title='{} 도움말을 전송하고 있습니다...'.format(self.emj.get(ctx, 'loading')), color=colors.PRIMARY))
            )
            await sending.edit(embed=discord.Embed(title='{} 도움말을 전송했습니다!'.format(self.emj.get(ctx, 'check')), description=f'**[DM 메시지]({msg.jump_url})**를 확인하세요!', color=colors.SUCCESS))
        else:
            msg = await ctx.author.send(embed=embed)
        
def setup(bot):
    cog = Maincmds(bot)
    bot.add_cog(cog)