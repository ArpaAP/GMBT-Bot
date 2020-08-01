import aiomysql
from discord.ext import commands
from .gmbtbot import GMBTBot
import logging
from .datamgr import DataDB
from .emojictrl import Emoji

class BaseCog(commands.Cog):
    def __init__(self, bot: GMBTBot):
        self.bot = bot
        self.pool: aiomysql.Connection = bot.datas.get('pool')
        self.eventcogname = bot.datas.get('eventcogname')
        self.log: logging.Logger = bot.datas.get('log')
        self.datadb: DataDB = bot.datas.get('datadb')
        self.emj: Emoji = bot.datas.get('emj')

    def getlistener(self, name):
        listeners = self.bot.get_cog(self.eventcogname).get_listeners()
        listeners_filter = list(filter(lambda x: x[0] == name, listeners))
        if listeners_filter:
            return listeners_filter[0][1]