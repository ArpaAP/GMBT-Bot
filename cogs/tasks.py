import discord
from discord.ext import commands, tasks
from configs import general, colors
from configs.version import VERSION
from itertools import cycle
from utils.basecog import BaseCog
import aiomysql
import datetime
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
        self.release_jail.start()

    @tasks.loop(seconds=8)
    async def update_server_user_count(self):
        try:
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
        except:
            traceback.print_exc()

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
        try:
            await self.bot.change_presence(activity=discord.Game(next(self.presences)))
        except:
            traceback.print_exc()

    @tasks.loop(seconds=3)
    async def nick_pin(self):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute('select * from nickpin')
                    pins = await cur.fetchall()
                    for one in pins:
                        await self.bot.get_guild(one['guild']).get_member(one['member']).edit(nick=one['value'])
        except:
            traceback.print_exc()


    @tasks.loop(seconds=5)
    async def release_jail(self):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute('select * from `release_timer` where DATE_ADD(dt, INTERVAL `minutes` MINUTE) <= %s', (datetime.datetime.now()))
                    rs = await cur.fetchall()
                    guild = self.bot.get_guild(general.MASTER_GUILD_ID)
                    roles = list(map(guild.get_role, general.WARN_ROLES))
                    target = list(map(lambda x: guild.get_member(x['user']), rs))
                    for one in rs:
                        await guild.get_member(one['user']).remove_roles(*roles)
                        await cur.execute('delete from `release_timer` where uuid=%s', one['uuid'])
                    if rs:
                        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
                        embed = discord.Embed(title='정해진 시간이 되어 유저가 석방되었습니다', color=colors.PRIMARY)
                        embed.add_field(name='석방 유저', value=', '.join(map(lambda x: x.mention, target)))
                        await logch.send(embed=embed)
        except:
            traceback.print_exc()

    def cog_unload(self):
        self.update_server_user_count.cancel()
        self.presence_loop.cancel()
        self.sync_user.cancel()
        self.release_jail.cancel()

    @release_jail.before_loop
    @update_server_user_count.before_loop
    @presence_loop.before_loop
    @sync_user.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    cog = Tasks(bot)
    bot.add_cog(cog)
