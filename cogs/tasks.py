import discord
from discord.ext import commands, tasks
from configs import general, colors
from configs.version import VERSION
from itertools import cycle

# pylint: disable=no-member

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.presences = cycle([
            'GMBT 커뮤니티에 오신것을 환영합니다!',
            '반드시 규칙을 읽어주세요!',
            f'GMBT 봇 - 버전 {VERSION}'
        ])
        self.update_server_user_count.start()
        self.presence_loop.start()

    @tasks.loop(seconds=8)
    async def update_server_user_count(self):
        channel: discord.TextChannel = self.bot.get_channel(general.SERVER_USERCOUNT_CHANNEL_ID)
        guild = channel.guild
        members = guild.members
        count = len(list(filter(lambda x: not x.bot, members)))
        countstr = f'📊│서버 멤버수 : {count}'
        if channel.name != countstr:
            embed = discord.Embed(title='서버 멤버수 표시계를 성공적으로 업데이트했습니다', color=colors.PRIMARY)
            embed.add_field(name='기존', value=channel.name)
            embed.add_field(name='변경', value=countstr)
            await channel.edit(name=countstr)
            logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
            await logch.send(embed=embed)

    @tasks.loop(seconds=8)
    async def presence_loop(self):
        await self.bot.change_presence(activity=discord.Game(next(self.presences)))

    def cog_unload(self):
        self.update_server_user_count.cancel()
        self.presence_loop.cancel()

    @update_server_user_count.before_loop
    @presence_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    cog = Tasks(bot)
    bot.add_cog(cog)