import discord
from discord.ext import commands
from configs import colors
from utils.basecog import BaseCog
from typing import Optional
import aiomysql
import datetime

class Managecmds(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.command(name='채팅량', aliases=['채팅통계', '메시지수', '메시지량', '메시지통계', '채팅개수', '메시지개수'])
    async def _chatcount(self, ctx: commands.Context, *, member: Optional[discord.Member]=None):
        print('ds')
        if not member:
            member = ctx.author
        dt = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev = (dt - datetime.timedelta(days=1)).month
        dt = dt.replace(month=prev)

        utc = dt - datetime.timedelta(hours=9)
        
        embed = discord.Embed(title='채팅량 계산', description='{} 의 채팅량을 계산합니다. ({} 부터)\n\n'.format(member.mention, dt.strftime('%Y-%m-%d %X')), color=colors.PRIMARY)
        embed.set_footer(text='아직 계산하고 있습니다...')
        msg = await ctx.send(embed=embed)

        ls = []
        for channel in ctx.guild.text_channels:
            embed.set_footer(text='아직 계산하고 있습니다... ({} 계산 중)'.format(channel.name))
            await msg.edit(embed=embed)
            count = 0
            async for message in channel.history(limit=None, after=utc):
                if message.author.id == member.id:
                    count += 1
            ls.append(count)
            embed.description += '{}: `{}`건\n'.format(channel.mention, count)

            await msg.edit(embed=embed)
        embed.set_footer(text='계산 완료!')
        embed.description += '**\n총 메시지 수: {} 건**'.format(sum(ls))
        await msg.edit(embed=embed)
        
        
def setup(bot):
    cog = Managecmds(bot)
    bot.add_cog(cog)