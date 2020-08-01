import discord
from discord.ext import commands
from utils import progressbar
from configs import colors
from utils.basecog import BaseCog
from typing import Optional
import aiomysql
from utils.datamgr import ExpTableDBMgr
import math

class Levelingcmds(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.command(name='경험치', aliases=['레벨', 'xp', 'exp', 'level', '렙'])
    async def _exp(self, ctx: commands.Context, *, member: Optional[discord.Member]=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if not member:
                    member = ctx.author

                await cur.execute('select * from userdata where id=%s', member.id)
                data = await cur.fetchone()

                edgr = ExpTableDBMgr(self.datadb)
                nowexp = data['exp']
                level = edgr.clac_level(data['exp'])
                
                req = edgr.get_required_exp(level+1)
                accu = edgr.get_accumulate_exp(level+1)
                prev_req = edgr.get_required_exp(level)
                prev_accu = edgr.get_accumulate_exp(level)
                if req-prev_req <= 0:
                    percent = 0
                else:
                    percent = math.trunc((req-accu+nowexp)/req*1000)/10

                embed = discord.Embed(title=f'레벨 {level}', color=colors.PRIMARY)
                embed.set_author(name=f'{member.name} 님의 경험치', icon_url=member.avatar_url)
                embed.add_field(name='• 현재 경험치', value='>>> {}ㅤ **{}/{}** ({}%)\n레벨업 필요 경험치: **`{}`/`{}`**'.format(
                    progressbar.get(None, self.emj, req-accu+nowexp, req, 10),
                    format(req-accu+nowexp, ','), format(req, ','), percent, nowexp, accu
                ))
                await ctx.send(embed=embed)

def setup(bot):
    cog = Levelingcmds(bot)
    bot.add_cog(cog)