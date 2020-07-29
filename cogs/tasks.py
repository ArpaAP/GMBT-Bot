import discord
from discord.ext import commands, tasks
from configs import general, colors

# pylint: disable=no-member

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.update_server_user_count.start()

    @tasks.loop(seconds=8)
    async def update_server_user_count(self):
        channel: discord.TextChannel = self.bot.get_channel(general.SERVER_USERCOUNT_CHANNEL_ID)
        guild = channel.guild
        members = guild.members
        count = len(list(filter(lambda x: not x.bot, members)))
        channel.edit(name=f'📊│서버 멤버수 : {count}')

    def cog_unload(self):
        self.update_server_user_count.cancel()

    @update_server_user_count.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    cog = Tasks(bot)
    bot.add_cog(cog)