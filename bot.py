import discord
from discord.ext import commands
import os
from configs import datas

bot = commands.Bot(command_prefix='g!')
with open(datas.TOKEN_FILE, 'r', encoding='utf-8') as f:
    token = f.read()

for ext in list(filter(lambda x: x.endswith('.py'), os.listdir('./cogs'))):
    bot.load_extension('cogs.' + os.path.splitext(ext)[0])

bot.run(token)