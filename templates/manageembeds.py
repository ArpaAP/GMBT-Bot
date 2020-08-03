from utils.basecog import BaseCog
from utils.pager import Pager
from utils import timedelta
from configs import colors
import datetime
import discord

def warns_embed(cog: BaseCog, pgr: Pager, *, member: discord.Member, mode='default'):
    warns = pgr.get_thispage()
    embed = discord.Embed(title=f'🚨 {member} 의 경고 목록', description='', color=colors.WARN)

    for idx, one in enumerate(warns, 1):
        td = datetime.datetime.now() - one['dt']
        if td < datetime.timedelta(minutes=1):
            pubtime = '방금'
        else:
            pubtime = list(timedelta.format_timedelta(td).values())[0] + ' 전'
        bymem = member.guild.get_member(one['byuser'])
        if bymem:
            bystr = f', By {bymem.mention}'
        else:
            bystr = f', By (알수없는 유저)'
        if mode == 'select':
            embed.description += '{}. **{}**\n> {}{}\n'.format(idx, one['reason'], pubtime, bystr)
        else:
            embed.description += '**{}**\n> {}{}\n'.format(one['reason'], pubtime, bystr)
    embed.set_footer(text='❌: 경고 취소하기')

    return embed