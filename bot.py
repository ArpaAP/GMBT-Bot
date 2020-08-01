import discord
from discord.ext import commands
import os
from configs import datas
import aiomysql
import json
import asyncio
from utils.gmbtbot import GMBTBot
import logging
import logging.handlers
from utils.datamgr import DataDB
from utils import emojictrl
from db import exptable
import importlib

bot = GMBTBot(command_prefix='g!')

reqdirs = ['./logs', './logs/gmbt', './logs/discord']
for dit in reqdirs:
    if not os.path.isdir(dit):
        os.makedirs(dit)

logger = logging.getLogger('gmbt')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/gmbt/gmbt.log', maxBytes=datas.MAX_LOG_BYTES, backupCount=10, encoding='utf-8')
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)

dlogger = logging.getLogger('discord')
dlogger.setLevel(logging.INFO)
dhandler = logging.handlers.RotatingFileHandler(filename='./logs/discord/discord.log', maxBytes=datas.MAX_LOG_BYTES, backupCount=10, encoding='utf-8')
dformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')
dlog_streamh = logging.StreamHandler()
dhandler.setFormatter(dformatter)
dlog_streamh.setFormatter(dformatter)
dlogger.addHandler(dhandler)
dlogger.addHandler(dlog_streamh)

logger.info('========== START ==========')

with open(datas.TOKEN_FILE, 'r', encoding='utf-8') as f:
    token = f.read()
with open(datas.DBAC_FILE, 'r', encoding='utf-8') as f:
    dbac = json.load(f)

with open('./data/emojis.json', 'r', encoding='utf-8') as emojis_file:
    emojis = json.load(emojis_file)

dbkey = 'default'

async def connect_db():
    pool = await aiomysql.create_pool(
        host=dbac[dbkey]['host'],
        user=dbac[dbkey]['dbUser'],
        password=dbac[dbkey]['dbPassword'],
        db=dbac[dbkey]['dbName'],
        charset='utf8',
        autocommit=True
    )
    return pool
    
pool = asyncio.get_event_loop().run_until_complete(connect_db())

emj = emojictrl.Emoji(bot, emojis['emoji-server'], emojis['emojis'])

datadb = DataDB()

def loader(datadb: DataDB):
    datadb.load_exp_table(exptable.EXP_TABLE)

def reloader(datadb: DataDB):
    db_modules = [
        exptable
    ]
    for md in db_modules:
        importlib.reload(md)
    loader(datadb)

datadb.set_loader(loader)
datadb.set_reloader(reloader)
loader(datadb)

bot.datas['pool'] = pool
bot.datas['eventcogname'] = 'Events'
bot.datas['log'] = logger
bot.datas['datadb'] = datadb
bot.datas['emj'] = emj

for ext in list(filter(lambda x: x.endswith('.py'), os.listdir('./cogs'))):
    bot.load_extension('cogs.' + os.path.splitext(ext)[0])

bot.run(token)
