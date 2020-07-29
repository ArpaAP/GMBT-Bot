import discord
from discord.ext import commands
import os

bot = commands.Bot(command_prefix='g!')

for ext in list(filter(lambda x: x.endswith('.py'), os.listdir('./cogs'))):
    bot.load_extension('cogs.' + os.path.splitext(ext)[0])

bot.run('NjAyMDM1MDcyMTQwNTc0NzIw.XTK-2g.7lEXGOK4wWFQyFpqfVt2Qh4RIWE')