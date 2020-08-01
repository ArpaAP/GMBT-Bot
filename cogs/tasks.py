import discord
from discord.ext import commands, tasks
from configs import general, colors
from configs.version import VERSION
from itertools import cycle
from utils.basecog import BaseCog
import aiomysql
import traceback

# pylint: disable=no-member

class Tasks(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.presences = cycle([
            'GMBT 커뮤니티에 오신것을 환영합니다!',
            '반드시 규칙을 읽어주세요!',
            f'GMBT 봇 - 버전 {VERSION}'
        ])
        self.update_server_user_count.start()
        self.presence_loop.start()
        self.sync_user.start()

    @tasks.loop(seconds=8)
    async def update_server_user_count(self):
        channel: discord.TextChannel = self.bot.get_channel(general.SERVER_USERCOUNT_CHANNEL_ID)
        members = self.bot.get_guild(general.MASTER_GUILD_ID).members
        count = len(list(filter(lambda x: not x.bot, members)))
        countstr = f'📊│서버 멤버수 : {count}'
        if channel.name != countstr:
            embed = discord.Embed(title='서버 멤버수 표시계를 성공적으로 업데이트했습니다', color=colors.PRIMARY)
            embed.add_field(name='기존', value=channel.name)
            embed.add_field(name='변경', value=countstr)
            await channel.edit(name=countstr)
            logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
            await logch.send(embed=embed)

    @tasks.loop(seconds=5)
    async def sync_user(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select id from userdata')
                users = cur.fetchall()
                members = self.bot.get_guild(general.MASTER_GUILD_ID).members
                dbuser_ids = set(map(lambda x: x['id'], users))
                guilduser_ids = set(map(lambda x: x.id, filter(lambda m: not m.bot, members)))
                unsynced = dbuser_ids - guilduser_ids
                for one in unsynced:
                    try:
                        await cur.execute('insert into userdata (id) values (%s)', one)
                    except:
                        traceback.print_exc()
                    else:
                        self.log.info(f'DB에 새 유저를 등록했습니다: {one}')

    @tasks.loop(seconds=8)
    async def presence_loop(self):
        await self.bot.change_presence(activity=discord.Game(next(self.presences)))

    def cog_unload(self):
        self.update_server_user_count.cancel()
        self.presence_loop.cancel()
        self.sync_user.cancel()

    @update_server_user_count.before_loop
    @presence_loop.before_loop
    @sync_user.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    cog = Tasks(bot)
    bot.add_cog(cog)