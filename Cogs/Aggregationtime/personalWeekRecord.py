from datetime import date, datetime, timedelta
import re

import discord
from discord.ext import commands
from tqdm import tqdm
from sqlalchemy import func as F

from .weekAggregate import Week_Aggregate
from .personalDayRecord import Personal_DayRecord
from mo9mo9db.dbtables import Studytimelogs


class Personal_WeekRecord(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 603582455756095488
        self.channel_id = 828645803131404410  # times_supleiades

    # 先週の月〜日までの日付を取得
    def getlastweek_days(self):
        weeknumber = [0, 1, 2, 3, 4, 5, 6]
        lastweek_days = []
        for i in weeknumber:
            lastweek_day = date.today()
            - timedelta(days=datetime.now().weekday()) + \
                timedelta(days=i, weeks=-1)
            lastweek_days.append(lastweek_day.strftime("%Y-%m-%d"))
        lastsunday = datetime.now().strptime(
            lastweek_days[-1], "%Y-%m-%d").strftime("%m-%d")
        desc_lastweek = f"{lastweek_days[0]}〜{lastsunday}"
        return lastweek_days, desc_lastweek

    # 今週の月〜今日までの日付を取得
    def getweek_days(self):
        # 月曜(0)から今日の曜日までの曜日を示す数字を配列に格納
        weeknumber = list(range(date.today().weekday() + 1))
        week_days = []
        for i in weeknumber:
            week_day = date.today()
            - timedelta(days=datetime.now().weekday()) + timedelta(days=i)
            week_days.append(week_day.strftime("%Y-%m-%d"))
        now_date = datetime.now().strftime("%m-%d")
        desc_week = f"{week_days[0]}〜{now_date}"
        return week_days, desc_week

    def format_userrecord(self, member, day, studytime, title):
        totalStudyTime = str(Week_Aggregate(
            self.bot).minutes2time(studytime)).strip()
        # DBからテンプレートテキストを取得して置換する処理に変更する
        week_result = f'''
#{title}
-
-

#もくもくオンライン勉強会
[ {day}の勉強時間 ]
---> {totalStudyTime}
#mo9mo9_{member.id}
        '''
        return week_result

    def aggregate_user_record(self, member, week_days) -> int:
        # ユーザーの勉強記録を取得
        session = Studytimelogs.session()
        obj = session.query(F.sum(Studytimelogs.studytime_min)).filter(
            Studytimelogs.member_id == member.id,
            Studytimelogs.access == "out",
            Studytimelogs.studytime_min.isnot(None)).first()
        return obj[0]

    def addembed_studytimebar(self, embed, targettime, weekstudymtime):
        weekstudyhtime = int(weekstudymtime) // 60
        if weekstudyhtime > int(targettime):  # 勉強時間/目標時間が100%を超えた場合の処理
            bar = str(tqdm(
                initial=weekstudyhtime,
                total=weekstudyhtime,
                ncols=77, desc="[達成度]",
                bar_format="""
{desc}{percentage:3.0f}%|{bar}|
--->現在の積み上げ：{n}h
--->週の目標時間　：{total}h
"""
            ))
            # 文字列の末尾の目標時間を以下の変数で置換
            bar = re.sub(rf"{str(weekstudyhtime)}h$",
                         f"{str(targettime)}h", bar)
        else:  # 勉強時間/目標時間が100%未満の場合の処理
            bar = str(tqdm(
                initial=weekstudyhtime,
                total=int(targettime),
                ncols=77, desc="[達成度]",
                bar_format="""
{desc}{percentage:3.0f}%|{bar}|
--->現在の積み上げ：{n}h
--->週の目標時間　：{total}h
"""
            ))
        bar = bar.replace(" ", "", 2)
        bar = bar.replace(" ", "----")
        embed.add_field(
            name=f"📊目標設定( {targettime}時間 )", value=bar, inline=False)
        return embed

    def strfembed(self, str):
        embed = discord.Embed(title=str)
        return embed

# ----------------------------------------------------------------

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_guild(
            self.guild_id).get_channel(self.channel_id)
        # await self.channel.purge()
        embed = discord.Embed(title="あなたの今週の勉強記録の集計を出力します",
                              description="- 集計結果をDMに送ります")
        embed.add_field(name=" 👇 使い方",
                        value="（超簡単）このメッセージにリアクションをするだけ‼️ ")
        self.message = await self.channel.send(embed=embed)
        self.message_id = self.message.id
        await self.message.add_reaction("🛎️")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        print(payload.channel_id)
        if payload.channel_id == self.channel_id:
            member = payload.member.guild.get_member(
                payload.member.id)  # DM用のMemberオブジェクト生成
            dm = await member.create_dm()
        # --------------今週〜今日までの週間集計---------------------
        if payload.message_id == self.message_id:
            week_days, desc_week = self.getweek_days()
            sum_studytime = self.aggregate_user_record(member, week_days)
            sendmessage = self.format_userrecord(
                member, desc_week, sum_studytime, "今週の振り返り")
            embed = Personal_DayRecord(
                self.bot).create_twitter_embed(sendmessage)
            # embed不足
            # embed = self.addembed_studytimebar(embed, args[0], sum_studytime)
            await dm.send(embed=embed)
            # --------------DBerror処理--------------
            # else:
            #    msg = await self.channel.send("今週の勉強記録が見つかりませんでした")
            #    await self.time_sleep(msg)


# ----------------------------------------------------------------
#
#    @commands.group(invoke_without_command=True)
#    async def result_w(self, ctx, *args):
#        if ctx.subcommand_passed is None:
#            week_days, desc_week = self.getweek_days()
#            sum_studytime = self.aggregate_user_record(member, week_days)
#            sendmessage = self.format_userrecord(username,
#                                desc_week, sum_studytime, "今週の振り返り")
#            print(sendmessage)
#            embed = Personal_DayRecord(self.bot)
#                .create_twitter_embed(sendmessage)
#            print(args)
#            if args: # タプルが空かどうか判定
#                if args[0].isdigit(): # 以下、目標時間の引数（int）がある場合
#                    embed = self.addembed_studytimebar(embed,
#                                                       args[0],
#                                                       sum_studytime)
#                    sendmsg = await ctx.channel.send(embed=embed)
# await sendmsg.add_reaction("<:otsukaresama:757813789952573520>")
#                else: # 引数が数字でない場合
#                    await ctx.channel.send(embed=
#                        self.strfembed(f"""
# [ {args[0]} ]は無効な引数です。数字を指定してください
# """))
#            else: # 引数が含まれていない場合
#                sendmsg = await ctx.channel.send(embed=embed)
# await sendmsg.add_reaction("<:otsukaresama:757813789952573520>")
#        else:
#            await ctx.send("[ " + ctx.subcommand_passed + " ]は無効な引数です")
#
#    @result_w.command()
#    async def ago(self, ctx, *args):
#        member = ctx.author.name
#        lastweek_days, desc_lastweek = self.getlastweek_days()
#        sum_studytime = self.aggregate_user_record(username, lastweek_days)
#        sendmessage = self.format_userrecord(username,
#                            desc_lastweek, sum_studytime, "先週の振り返り")
#        print(sendmessage)
#        embed = Personal_DayRecord(self.bot).create_twitter_embed(sendmessage)
#        if args: # タプルが空かどうか判定
#            if args[0].isdigit(): # 以下、目標時間の引数（int）がある場合
#                embed = self.addembed_studytimebar(embed,
#                                                   args[0],
#                                                   sum_studytime)
#                sendmsg = await ctx.channel.send(embed=embed)
#                await sendmsg.add_reaction("<:otsukaresama:757813789952573520>")  # noqa: E501
#            else: # 引数が数字でない場合
#                await ctx.channel.send(embed=
#                    self.strfembed(f"""
# [ {args[0]} ]は無効な引数です。数字を指定してください
# """))
#        else: # 引数が含まれていない場合
#            sendmsg = await ctx.channel.send(embed=embed)
#            await sendmsg.add_reaction("<:otsukaresama:757813789952573520>")


def setup(bot):
    return bot.add_cog(Personal_WeekRecord(bot))
