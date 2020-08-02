import discord
from discord.ext import commands
from configs import colors, clac
from utils.basecog import BaseCog
from utils import checks, timedelta
from utils.converters import Date
from typing import Optional
import aiomysql
import asyncio
import datetime
import time
import math
import uuid

class Managecmds(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        for cmd in self.get_commands():
            if cmd.name == '동기화':
                cmd.add_check(checks.master_only)

    @commands.command(name='동기화')
    async def _sync_msgdb(self, ctx: commands.Context, *channels: Optional[discord.TextChannel]):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                embed = discord.Embed(
                    title='채팅량 동기화',
                    description='봇이 종료되었을때 보내진 메시지 등 봇이 기록하지 못해 누락된 메시지가 있는지 검사하고 DB에 동기화합니다.\n이 작업이 완료되는 데에 긴 시간이 소요될 수 있습니다.\n계속하시겠습니까?',
                    color=colors.PRIMARY
                )
                if channels:
                    embed.add_field(name='검사할 채널들', value=', '.join(map(lambda x: x.mention, channels)))
                else:
                    embed.add_field(name='검사할 채널들', value='모든 채널 (특정 채널들을 선택하려면 명령어 뒤에 채널 이름 또는 멘션을 나열하세요)')
                    channels = ctx.guild.text_channels
                msg = await ctx.send(embed=embed)
                emjs = [self.emj.get(ctx, 'check'), self.emj.get(ctx, 'cross')]
                for emj in emjs:
                    await msg.add_reaction(emj)
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=lambda r, u: u == ctx.author and r.message.id == msg.id and r.emoji in emjs, timeout=60)
                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reactions()
                    except:
                        pass
                else:
                    if reaction.emoji == emjs[0]:
                        await msg.clear_reactions()
                        dt = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                        prev = (dt - datetime.timedelta(days=1)).month
                        dt = dt.replace(month=prev)

                        utc = dt - datetime.timedelta(hours=9)

                        embed = discord.Embed(title='채팅량 동기화', description='채팅량을 계산합니다. ({} 부터)\n\n'.format(dt.strftime('%Y-%m-%d %X')), color=colors.PRIMARY)
                        embed.set_footer(text='아직 계산하고 있습니다...')
                        await msg.edit(embed=embed)

                        start = time.time()

                        await cur.execute('select * from messages')
                        mdb = await cur.fetchall()

                        ls = []
                        unsync = []
                        unsynccount = 0
                        for channel in channels:
                            embed.set_footer(text='아직 계산하고 있습니다... ({} 계산 중)'.format(channel.name))
                            await msg.edit(embed=embed)
                            count = 0
                            
                            async for message in channel.history(limit=None, after=utc):
                                if message.author.bot:
                                    continue
                                if not list(filter(lambda d: message.author.id == d['user'] and message.channel.id == d['channel'] and message.id == d['message'], mdb)):
                                    unsynccount += 1
                                    unsync.append(message)  
                                count += 1
                            ls.append(count)
                            embed.description += '{}: `{}`건\n'.format(channel.mention, count)

                            await msg.edit(embed=embed)

                        end = time.time()

                        embed.set_footer(text='계산 완료! ({} 초)'.format(math.trunc(end-start)))
                        embed.description += '**\n총 메시지 수: {} 건 | 누락된 메시지 수: {} 건**'.format(sum(ls), unsynccount)
                        await msg.edit(embed=embed)
                        
                        dbaddembed = discord.Embed(title='채팅량 업로드 중', color=colors.PRIMARY)
                        dbaddmsg = await ctx.send(embed=dbaddembed)

                        dbaddcount = 0

                        async def upload_db():
                            nonlocal dbaddcount
                            for m in unsync:
                                dbaddcount += 1
                                await cur.execute(
                                    'insert into messages (uuid, user, guild, channel, message, dt) values (%s, %s, %s, %s, %s, %s)',
                                    (uuid.uuid4().hex, m.author.id, m.guild.id, m.channel.id, m.id, m.created_at + datetime.timedelta(hours=9))
                                )
                        
                        uploadtask = asyncio.create_task(upload_db())

                        while not uploadtask.done():
                            dbaddembed.description = '이제 누락된 채팅량을 DB로 업로드하고 있습니다... {}/{} ({}%) 완료'.format(dbaddcount, len(unsync), round(100*(dbaddcount/len(unsync))))
                            await dbaddmsg.edit(embed=dbaddembed)
                            await asyncio.sleep(1)
                        dbaddembed.description = '이제 누락된 채팅량을 DB로 업로드하고 있습니다... {}/{} ({}%) 완료'.format(dbaddcount, len(unsync), round(100*(dbaddcount/len(unsync))))
                        await dbaddmsg.edit(embed=dbaddembed)
                        
                        await ctx.send('완료')
                        
                    else:
                        await msg.delete()

    @commands.command(name='채팅량', aliases=['채팅통계', '메시지수', '메시지량', '메시지통계', '채팅개수', '메시지개수'])
    async def _chatcount(self, ctx: commands.Context, dt: Optional[Date], member: Optional[discord.Member]=None, *channels: discord.TextChannel):
        print(dt, member, channels)
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if not member:
                    member = ctx.author
                chstr = ', '.join(map(lambda x: x.mention, channels))
                if not channels:
                    channels = ctx.guild.text_channels
                    chstr = '(모든 채널)'
                if not dt:
                    dt = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    prev = (dt - datetime.timedelta(days=1)).month
                    dt = dt.replace(month=prev)
                await cur.execute('select * from messages where date(dt) >= %s and user=%s and guild=%s', (dt, member.id, member.guild.id))
                ls = await cur.fetchall()
                ft = list(filter(lambda x: x['channel'] in map(lambda ch: ch.id, channels), ls))
                embed = discord.Embed(title='💬 채팅량', description='{} 님의 채팅량은 **`{}`**건 입니다.'.format(member.mention, len(ft)), color=colors.PRIMARY)
                embed.add_field(name='기간', value='{} 부터'.format(dt.strftime('%Y-%m-%d %X')))
                embed.add_field(name='대상 채널', value=chstr)

                await ctx.send(embed=embed)

    @commands.command(name='경고', aliases=['warn'])
    async def _warn(self, ctx: commands.Context, member: discord.Member, count: Optional[int]=1, *, reason: Optional[str]=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if reason is None:
                    reasonstr = '(없음)'
                else:
                    reasonstr = reason
                embed = discord.Embed(title='🚨 경고 부여', description='계속하시겠습니까?', color=colors.WARN)
                embed.add_field(name='대상', value=member.mention)
                embed.add_field(name='경고 횟수', value=f'{count}회')
                embed.add_field(name='이유', value=reasonstr)
                msg = await ctx.send(embed=embed)
                emjs = [self.emj.get(ctx, 'check'), self.emj.get(ctx, 'cross')]
                for emj in emjs:
                    await msg.add_reaction(emj)
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=lambda r, u: u == ctx.author and r.message.id == msg.id and r.emoji in emjs, timeout=60)
                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reactions()
                    except:
                        pass
                else:
                    if reaction.emoji == emjs[0]:
                        await cur.execute(
                            'insert into warns (uuid, user, count, reason) values (%s, %s, %s, %s)',
                            (uuid.uuid4().hex, member.id, count, reason)
                        )
                        await ctx.send(embed=discord.Embed(title='{} 경고를 부여했습니다'.format(self.emj.get('check')), color=colors.WARN))
                    else:
                        try:
                            await msg.delete()
                        except:
                            pass

    @commands.command(name='경고확인', aliases=['경고보기'])
    async def _warns(self, ctx: commands.Context, member: discord.Member):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from warns where user=%s order by `dt` desc limit 10', member.id)
                warns = await cur.fetchall()

                embed = discord.Embed(title=f'🚨 {member} 의 경고 목록', description='최근 10개까지 표시합니다.\n\n', color=colors.WARN)

                for one in warns:
                    td = datetime.datetime.now() - one['dt']
                    if td < datetime.timedelta(minutes=1):
                        pubtime = '방금'
                    else:
                        pubtime = list(timedelta.format_timedelta(td).values())[0] + ' 전'
                    embed.description += '**{}**\n>>> {}회, {}\n경고ID: {}'.format(one['reason'], one['count'], pubtime, one['uuid'])

                await ctx.send(embed=embed)

    @commands.command(name='경고삭제', aliases=['경고취소', '경고제거'])
    async def _warn_del(self, ctx: commands.Context, uuid):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from warns where uuid=%s', uuid)
                warn = await cur.fetchone()

                if not warn:
                    await ctx.send('이 ID의 경고를 찾을 수 없습니다. 경고ID가 올바른 지 확인해주세요.')

                embed = discord.Embed(title=f'🚨 경고 취소하기', description='이 경고를 취소할까요?', color=colors.WARN)

                td = datetime.datetime.now() - warn['dt']
                if td < datetime.timedelta(minutes=1):
                    pubtime = '방금'
                else:
                    pubtime = list(timedelta.format_timedelta(td).values())[0] + ' 전'

                member = ctx.guild.get_member(warn['user'])

                if not member:
                    await ctx.send('이 경고의 사용자를 찾을 수 없습니다. 유저가 서버에서 나갔을 수 있습니다.')
                
                embed.add_field(name='대상', value=member.mention)
                embed.add_field(name='이유', vaule=warn['reason'])
                embed.add_field(name='횟수', vaule=warn['count'])
                embed.add_field(name='부여한 시간', vaule=pubtime)
                
                await ctx.send(embed=embed)

                if warn['count'] == 0:
                    return

                else:
                    await ctx.send('취소할 경고 수를 입력하세요')
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content and m.content.isdecimal(), timeout=60)
                    except asyncio.TimeoutError:
                        pass
                    else:
                        after = count - int(m.content)
                        if after == 0:
                            await cur.execute('delete from warns where uuid=%s', warn['uuid'])
                        elif after > 0:
                            await cur.execute('update warns set count=%s where uuid=%s', (after, warn['uuid']))
        
def setup(bot):
    cog = Managecmds(bot)
    bot.add_cog(cog)