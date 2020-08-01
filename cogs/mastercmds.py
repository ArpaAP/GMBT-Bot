import discord
from discord.ext import commands
from utils import checks
import traceback
from configs import colors
from utils.basecog import BaseCog

class Mastercmds(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        for cmd in self.get_commands():
            cmd.add_check(checks.master_only)

    @commands.command(name='테스트')
    async def test(self, ctx: commands.Context):
        await ctx.send('ㅎㅇ')

    @commands.command(name='삭제')
    async def delete(self, ctx: commands.Context, count: int):
        await ctx.channel.purge(limit=count)

    @commands.command(name='eval')
    async def _eval(self, ctx: commands.Context, *, arg):
        try:
            rst = eval(arg)
        except:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{traceback.format_exc()}```\n❌ ERROR'
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n✅ SUCCESS'
        embed=discord.Embed(title='**💬 EVAL**', color=colors.PRIMARY, description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='exec')
    async def _exec(self, ctx: commands.Context, *, arg):
        try:
            rst = exec(arg)
        except:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{traceback.format_exc()}```\n❌ ERROR'
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n✅ SUCCESS'
        embed=discord.Embed(title='**💬 EXEC**', color=colors.PRIMARY, description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='await')
    async def _await(self, ctx: commands.Context, *, arg):
        try:
            rst = await eval(arg)
        except:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{traceback.format_exc()}```\n❌ ERROR'
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n✅ SUCCESS'
        embed=discord.Embed(title='**💬 AWAIT**', color=colors.PRIMARY, description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='hawait')
    async def _hawait(self, ctx: commands.Context, *, arg):
        try:
            await eval(arg)
        except:
            await ctx.send(embed=discord.Embed(title='❌ 오류', color=colors.ERROR))

def setup(bot):
    cog = Mastercmds(bot)
    bot.add_cog(cog)