import discord
from discord.ext import commands
from configs import general, colors, clac, masters
from configs.version import VERSION
from utils import errors
from utils.basecog import BaseCog
import traceback
import aiomysql
import uuid
import datetime

class Events(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.cooldown = {}

    @commands.Cog.listener('on_warn')
    async def on_warn(self, member: discord.Member):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
                warncount = await cur.execute('select uuid from warns where user=%s', member.id)
                roles = list(filter(lambda a: a is not None, map(member.guild.get_role, general.WARN_ROLES)))

                

                if warncount >= general.ROLE_GIVE_WARN_COUNT:
                    await member.add_roles(*roles)
                else:
                    await member.remove_roles(*roles)

    @commands.Cog.listener('on_message')
    async def insert_message(self, message: discord.Message):
        if member.guild.id != general.MASTER_GUILD_ID:
            return
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if message.author.bot:
                    return
                if message.channel.id not in clac.CHAT_COUNT_CHANNELS:
                    return
                await cur.execute('insert into messages (uuid, user, guild, channel, message) values (%s, %s, %s, %s, %s)', (uuid.uuid4().hex, message.author.id, message.guild.id, message.channel.id, message.id))

    @commands.Cog.listener('on_message')
    async def give_exp(self, message: discord.Message):
        if member.guild.id != general.MASTER_GUILD_ID:
            return
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                cld = 60
                now = datetime.datetime.now()
                cooldown: datetime.datetime = self.cooldown.get(message.author.id)
                if cooldown is None:
                    pass
                elif cooldown + datetime.timedelta(seconds=60) <= now:
                    pass
                else:
                    return
                self.cooldown[message.author.id] = now
                await cur.execute('update userdata set exp=exp+1 where id=%s', message.author.id)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        err = [line.rstrip() for line in tb]
        errstr = '\n'.join(err)
        if isinstance(error, errors.NotMaster):
            await ctx.send('그 명령어는 개발자만 사용할 수 있다 애송아.')
        elif isinstance(error, commands.MissingPermissions):
            if 'administrator' in error.missing_perms:
                await ctx.send('그 명령어는 서버 관리자만 사용할 수 있습니다 ㅋ')
        else:
            print(errstr)

    @commands.Cog.listener('on_ready')
    async def on_ready(self):
        print('OK')
        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
        embed = discord.Embed(description='**ALL DONE, BOOTED SUCCESSFULLY**', color=colors.PRIMARY)
        embed.set_footer(text=f'모든 준비 완료, 성공적으로 부팅했습니다 - 버전 {VERSION}')
        await logch.send(embed=embed)

    @commands.Cog.listener('on_member_join')
    async def member_join(self, member: discord.Member):
        if member.guild.id != general.MASTER_GUILD_ID:
            return
        channel = self.bot.get_channel(general.IO_CHANNEL)
        embed = discord.Embed(title=f'{member.name}, 안녕하세요!', color=colors.PRIMARY)
        if member.bot:
            embed.description = f'{member.name} 봇이 **GMBT 커뮤니티** 서버에 들어왔습니다!'
        else:
            embed.description = f'{member.name} 님 안녕하세요, **GMBT 커뮤니티** 에 오신것을 환영합니다!'
        count = len(list(filter(lambda x: not x.bot, member.guild.members)))

        await member.add_roles(*map(member.guild.get_role, general.JOIN_ROLES))

        embed.set_footer(text=f'현재 멤버 수: {count}명')
        await channel.send(embed=embed)

    @commands.Cog.listener('on_member_join')
    async def create_data_on_member_join(self, member: discord.Member):
        if member.guild.id != general.MASTER_GUILD_ID:
            return
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if not member.bot:
                    if await cur.execute('select id from userdata where id=%s', member.id) == 0:
                        await cur.execute('insert into userdata (id) values (%s)', member.id)
                        self.log.info(f'DB에 새 유저를 등록했습니다: {member.id}')

    @commands.Cog.listener('on_member_remove')
    async def member_remove(self, member: discord.Member):
        if member.guild.id != general.MASTER_GUILD_ID:
            return
        channel = self.bot.get_channel(general.IO_CHANNEL)
        embed = discord.Embed(title=f'{member.name}, 안녕히가세요-', color=colors.PRIMARY)
        if member.bot:
            embed.description = f'{member.name} 봇이 서버를 떠났습니다.'
        else:
            embed.description = f'{member.name} 님이 서버를 떠났습니다.'
        count = len(list(filter(lambda x: not x.bot, member.guild.members)))
        embed.set_footer(text=f'현재 멤버 수: {count}명')
        await channel.send(embed=embed)

    @commands.Cog.listener('on_raw_reaction_add')
    async def special_channel_role_give(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return
        if payload.guild_id != general.MASTER_GUILD_ID:
            return
        if payload.channel_id != general.SPECIAL_CHANNEL_ROLE_CHANNEL_ID:
            return
        if payload.message_id != general.SPECIAL_CHANNEL_MSG_ID:
            return
        
        if payload.emoji.is_custom_emoji():
            role_id = general.SPECIAL_ROLE_REACTION.get(payload.emoji.id)
        elif payload.emoji.is_unicode_emoji():
            role_id = general.SPECIAL_ROLE_REACTION.get(str(payload.emoji))
        if role_id is None:
            return
        
        member: discord.Member = payload.member
        guild: discord.Guild = member.guild

        role = guild.get_role(role_id)
        await member.add_roles(role, reason='특수방 입장에서 정상적으로 역할을 주었습니다.')

        embed = discord.Embed(title='✅ 특수방 역할을 주었습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 추가'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMARY)

        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
        await logch.send(embed=embed)
        print('역할 정상 추가')

    @commands.Cog.listener('on_raw_reaction_remove')
    async def special_channel_role_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id != general.MASTER_GUILD_ID:
            return
        if payload.channel_id != general.SPECIAL_CHANNEL_ROLE_CHANNEL_ID:
            return
        if payload.message_id != general.SPECIAL_CHANNEL_MSG_ID:
            return
        
        if payload.emoji.is_custom_emoji():
            role_id = general.SPECIAL_ROLE_REACTION.get(payload.emoji.id)
        elif payload.emoji.is_unicode_emoji():
            role_id = general.SPECIAL_ROLE_REACTION.get(str(payload.emoji))
        if role_id is None:
            return

        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        member: discord.Member = guild.get_member(payload.user_id)

        if member.bot:
            return

        role: discord.Role = guild.get_role(role_id)
        await member.remove_roles(role, reason='특수방 입장에서 정상적으로 역할을 제거했습니다.')

        embed = discord.Embed(title='🔶 특수방 역할을 제거했습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 제거'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMARY)

        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
        await logch.send(embed=embed)
        print('역할 정상 제거')



    @commands.Cog.listener('on_raw_reaction_add')
    async def color_role_give(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return
        if payload.guild_id != general.MASTER_GUILD_ID:
            return
        if payload.channel_id != general.COLOR_ROLE_CHANNEL_ID:
            return
        if payload.message_id != general.COLOR_MSG_ID:
            return
        
        if payload.emoji.is_custom_emoji():
            role_id = general.COLOR_ROLE_REACTION.get(payload.emoji.id)
        elif payload.emoji.is_unicode_emoji():
            role_id = general.COLOR_ROLE_REACTION.get(str(payload.emoji))
        if role_id is None:
            return
        
        member: discord.Member = payload.member
        guild: discord.Guild = member.guild

        role = guild.get_role(role_id)
        await member.add_roles(role, reason='특수방 입장에서 정상적으로 역할을 주었습니다.')

        embed = discord.Embed(title='✅ 특수방 역할을 주었습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 추가'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMARY)

        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
        await logch.send(embed=embed)
        print('역할 정상 추가')

    @commands.Cog.listener('on_raw_reaction_remove')
    async def color_role_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id != general.MASTER_GUILD_ID:
            return
        if payload.channel_id != general.COLOR_ROLE_CHANNEL_ID:
            return
        if payload.message_id != general.COLOR_MSG_ID:
            return
        
        if payload.emoji.is_custom_emoji():
            role_id = general.COLOR_ROLE_REACTION.get(payload.emoji.id)
        elif payload.emoji.is_unicode_emoji():
            role_id = general.COLOR_ROLE_REACTION.get(str(payload.emoji))
        if role_id is None:
            return

        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        member: discord.Member = guild.get_member(payload.user_id)

        if member.bot:
            return

        role = guild.get_role(role_id)
        await member.remove_roles(role, reason='특수방 입장에서 정상적으로 역할을 제거했습니다.')

        embed = discord.Embed(title='🔶 색역할을 제거했습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 제거'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMARY)

        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
        await logch.send(embed=embed)
        print('역할 정상 제거')

def setup(bot):
    cog = Events(bot)
    bot.add_cog(cog)