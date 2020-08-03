import discord
from discord.ext import commands
from configs import colors, clac, masters
from utils.basecog import BaseCog
from utils import checks, timedelta, emojibuttons, event_waiter
from utils.converters import Date
from utils.pager import Pager
from typing import Optional
import aiomysql
import asyncio
import datetime
import time
import math
import uuid
from templates import manageembeds

class Managecmds(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        for cmd in self.get_commands():
            if cmd.name in ['동기화', '경고', '경고삭제']:
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
    async def _warn(self, ctx: commands.Context, member: Optional[discord.Member]=None, *, reason: Optional[str]=None):
        if not member:
            await self._warns(ctx)
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if reason is None:
                    reasonstr = '(없음)'
                else:
                    reasonstr = reason
                embed = discord.Embed(title='🚨 경고 부여', description='계속하시겠습니까?', color=colors.WARN)
                embed.add_field(name='대상', value=member.mention)
                embed.add_field(name='사유', value=reasonstr)
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
                            'insert into warns (uuid, user, reason, byuser) values (%s, %s, %s, %s)',
                            (uuid.uuid4().hex, member.id, reason, ctx.author.id)
                        )
                        await ctx.send(embed=discord.Embed(title='{} 경고를 부여했습니다'.format(self.emj.get(ctx, 'check')), color=colors.WARN))
                        lsnr = self.getlistener('on_warn')
                        await lsnr(member)
                    else:
                        try:
                            await msg.delete()
                        except:
                            pass

    @commands.command(name='경고확인', aliases=['경고보기', '경고목록', '경고들', '내경고'])
    async def _warns(self, ctx: commands.Context, member: Optional[discord.Member]=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if not member:
                    member = ctx.author

                if await cur.execute('select * from warns where user=%s order by `dt` desc limit 10', member.id) == 0:
                    await ctx.send(f'{member} 가 받은 경고가 하나도 없습니다! 👍')
                    return

                warns = await cur.fetchall()
                pgr = Pager(warns, 5)
                msg = await ctx.send(embed=manageembeds.warns_embed(self, pgr, member=member))

                ismaster = ctx.author.id in masters.MASTERS
                if ismaster:
                    extemjs = ['❌']
                else:
                    extemjs = []
                emjs = emojibuttons.PageButton.emojis + extemjs
                async def addreaction(m):
                    if len(pgr.pages()) == 0:
                        return
                    elif len(pgr.pages()) <= 1:
                        for emj in extemjs:
                            await m.add_reaction(emj)
                    else:
                        for emj in emjs:
                            await m.add_reaction(emj)
                await addreaction(msg)

                def check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60*5)
                    except asyncio.TimeoutError:
                        try:
                            await msg.clear_reactions()
                        except:
                            pass
                    else:
                        if reaction.emoji in extemjs:
                            if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                                await msg.edit(embed=manageembeds.warns_embed(self, pgr, member=member, mode='select'))
                            else:
                                results = await asyncio.gather(
                                    msg.delete(),
                                    ctx.send(embed=manageembeds.warns_embed(self, pgr, member=member, mode='select'))
                                )
                                msg = results[1]
                                await addreaction(msg)
                                reaction.message = msg

                        if reaction.emoji == '❌' and ismaster:
                            allcancel = ['모두', '전부']
                            itemidxmsg = await ctx.send(embed=discord.Embed(
                                title='🚨 경고 취소하기 - 취소할 경고 선택',
                                description='취소할 경고의 번째수를 입력해주세요. (모두 취소하려면 `전부` 또는 `모두` 입력)\n위 메시지에 경고 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                                color=colors.WARN
                            ))
                            await itemidxmsg.add_reaction('❌')
                            canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.bot, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                            indextask = asyncio.create_task(event_waiter.wait_for_message(self.bot, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal() or m.content in allcancel))
                            task = await event_waiter.wait_for_first(canceltask, indextask)
                            await itemidxmsg.delete()

                            if task == indextask:
                                idxtaskrst = indextask.result()
                                if idxtaskrst.content in allcancel:
                                    await cur.execute('delete from warns where user=%s', member.id)
                                    lsnr = self.getlistener('on_warn')
                                    await lsnr(member)
                                else:
                                    idx = int(idxtaskrst.content)
                                    if 1 <= idx <= len(pgr.get_thispage()):
                                        delwarn = pgr.get_thispage()[idx-1]
                                        await cur.execute('delete from warns where uuid=%s', delwarn['uuid'])
                                        await ctx.send(embed=discord.Embed(title='{} 경고를 풀었습니다!'.format(self.emj.get(ctx, 'check')), color=colors.SUCCESS))
                                        lsnr = self.getlistener('on_warn')
                                        await lsnr(ctx.guild.get_member(delwarn['user']))
                                    else:
                                        embed = discord.Embed(title='❓ 경고 번째수가 올바르지 않습니다!', description='위 메시지에 경고 앞마다 번호가 붙어 있습니다.', color=colors.ERROR)
                                        embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                        await ctx.send(embed=embed, delete_after=7)
                        
                        if await cur.execute('select * from warns where user=%s order by `dt` desc limit 10', member.id) == 0:
                            await msg.edit(content=f'{member} 가 받은 경고가 하나도 없습니다! 👍', embed=None)
                            try:
                                await msg.clear_reactions()
                            except:
                                pass
                            return
                        else:
                            pgr.set_obj(await cur.fetchall())

                        do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr, double=5)
                        if asyncio.iscoroutine(do):
                            await asyncio.gather(do,
                                msg.edit(embed=manageembeds.warns_embed(self, pgr, member=member)),
                            )
        
def setup(bot):
    cog = Managecmds(bot)
    bot.add_cog(cog)