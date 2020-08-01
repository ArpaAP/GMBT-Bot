from discord.ext import commands

class GMBTBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datas = {}