import discord
from discord.ext import commands
import datetime

class Date(commands.Converter):
    async def convert(self, ctx, arg):
        try:
            dt = datetime.datetime.strptime(arg, '%Y%m%d')
        except:
            return None
        else:
            return dt