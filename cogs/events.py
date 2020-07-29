import discord
from discord.ext import commands
from configs import general, colors

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener('on_ready')
    async def on_ready(self):
        print('OK')

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

        embed = discord.Embed(title='✅ 특수방 역할을 주었습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 추가'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMATY)

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

        embed = discord.Embed(title='🔶 특수방 역할을 제거했습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 제거'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMATY)

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

        embed = discord.Embed(title='✅ 특수방 역할을 주었습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 추가'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMATY)

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

        embed = discord.Embed(title='🔶 색역할을 제거했습니다', description='{} 유저가 {} 이모지로 반응함\n{} 역할 제거'.format(member.mention, payload.emoji, role.mention), color=colors.PRIMATY)

        logch = self.bot.get_channel(general.LOG_CHANNEL_ID)
        await logch.send(embed=embed)
        print('역할 정상 제거')

def setup(bot):
    cog = Events(bot)
    bot.add_cog(cog)