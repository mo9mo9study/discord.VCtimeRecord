import os
from datetime import datetime, timedelta

from discord.ext import commands
import discord
from dotenv import load_dotenv
import urllib.parse
import json
import requests
from sqlalchemy import func as F, extract, and_

from .weekAggregate import Week_Aggregate
from mo9mo9db.dbtables import Studytimelogs


class Personal_DayRecord(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 603582455756095488
        self.channel_id = 829515424042450984
        self.googleApiKey = os.environ.get("FIREBASE_API_KEY")
        self.googleShortLinksPrefix = os.environ.get(
            "FIREBASE_DYNAMICLINKS_PREFIX")
        dotenv_path = os.path.join(os.getcwd(), '.env')
        load_dotenv(dotenv_path)

    def aggregate_user_record(self, member, startrange_dt,
                              endrange_dt) -> int:
        # ユーザーの勉強記録を取得
        session = Studytimelogs.session()
        startrange = startrange_dt
        endrange = endrange_dt
        obj = session.query(F.sum(Studytimelogs.studytime_min)).filter(
            Studytimelogs.member_id == member.id,
            Studytimelogs.access == "out",
            Studytimelogs.excluded_record.isnot(True),
            and_(extract('year', Studytimelogs.study_dt) == startrange.year,
                 extract('month', Studytimelogs.study_dt) == startrange.month,
                 extract('day', Studytimelogs.study_dt) >= startrange.day),
            and_(extract('year', Studytimelogs.study_dt) == endrange.year,
                 extract('month', Studytimelogs.study_dt) == endrange.month,
                 extract('day', Studytimelogs.study_dt) <= endrange.day),
            Studytimelogs.studytime_min.isnot(None)).first()
        sum_studytime = obj[0]
        if isinstance(sum_studytime, type(None)):
            sum_studytime = 0
        return sum_studytime

    def createTwitterUrlEncode(self, websiteUrl, sendContent):
        encodeContent = urllib.parse.quote(sendContent)
        twitterUrl = "https://twitter.com/share?url={}&text={}".format(
            websiteUrl, encodeContent)
        return twitterUrl

    def shorten_url(self, url, prefix, key):
        '''Firebase Dynamic Link を使って URL を短縮する'''
        baseurl = 'https://firebasedynamiclinks.googleapis.com/'
        post_url = "{}v1/shortLinks?key={}".format(baseurl, key)
        payload = {
            "dynamicLinkInfo": {
                "domainUriPrefix": prefix,
                "link": url
            },
            "suffix": {"option": "SHORT"}
        }
        headers = {'Content-type': 'application/json'}
        r = requests.post(post_url, data=json.dumps(payload), headers=headers)
        if not r.ok:
            # DBへエラー処理を追加する
            # print(str(r), file=sys.stderr)
            return None
        return json.loads(r.content)["shortLink"]

    # 週間と被るが、一旦日次分の処理を追加
    # 今後、統一していってほしい
    # 関数名がxxxになっている集計

    def aggregate_day_users_record(self, member, day) -> int:
        session = Studytimelogs.session()
        obj = session.query(F.sum(Studytimelogs.studytime_min)).filter(
            Studytimelogs.member_id == member.id,
            Studytimelogs.access == "out",
            Studytimelogs.studytime_min.isnot(None)).first()
        return int(obj[0])

    def compose_user_record(self, day, studytime):
        day_result = '''
#今日の積み上げ
-
-

#もくもくオンライン勉強会
[ {day}の勉強時間 ]
---> {totalStudyTime}
        '''.format(day=day,
                   totalStudyTime=str(Week_Aggregate(self.bot)
                                      .minutes2time(studytime))).strip()
        return day_result

    def create_twitter_embed(self, sendMessage):
        longUrl = self.createTwitterUrlEncode(
            "https://mo9mo9study.github.io/discord.web/", sendMessage)
        encodeMessage = self.shorten_url(
            longUrl, self.googleShortLinksPrefix, self.googleApiKey)
        embed = discord.Embed(title="📤積み上げツイート用",
                              description=sendMessage, color=0xFDB46C)
        embed.add_field(name="🦜下のURLから簡単に積み上げツイートが出来るよ", value=encodeMessage)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_guild(
            self.guild_id).get_channel(self.channel_id)
        await self.channel.purge()
        embed = discord.Embed(title="あなたの１日の勉強記録の集計してDMに送信します",
                              description="👇 使い方\n（超簡単）このメッセージにリアクションをするだけ‼️")
        embed.add_field(name="1⃣：",
                        value="- 今日の勉強集計",
                        inline=False)
        embed.add_field(name="2⃣：",
                        value="- 昨日の勉強集計",
                        inline=False)
        self.message = await self.channel.send(embed=embed)
        self.message_id = self.message.id
        await self.message.add_reaction("1⃣")
        await self.message.add_reaction("2⃣")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        if payload.channel_id == self.channel_id:
            embed = ""  # 行目の対策、想定しないスタンプが押された時にembedが送信されないため
            member = payload.member.guild.get_member(
                payload.member.id)  # DM用のMemberオブジェクト生成
            dm = await member.create_dm()
            today = datetime.today()
        # --------------日間集計---------------------
        if payload.message_id == self.message_id:
            select_msg = await self.channel.fetch_message(payload.message_id)
            # --------------今日のの勉強集計---------------------
            if payload.emoji.name == "1⃣":
                strtoday = today.strftime('%Y-%m-%d')
                sum_studytime = self.aggregate_user_record(
                    member, today, today)
                sendMessage = self.compose_user_record(
                    strtoday, sum_studytime)
                embed = self.create_twitter_embed(sendMessage)
            # --------------昨日の勉強集計---------------------
            elif payload.emoji.name == "2⃣":
                yesterday = today - timedelta(1)
                strday = yesterday.strftime('%Y-%m-%d')
                sum_studytime = self.aggregate_user_record(
                    member, yesterday, yesterday)
                sendMessage = self.compose_user_record(
                    strday, sum_studytime)
                embed = self.create_twitter_embed(sendMessage)
            else:
                msg = await self.channel.send("1⃣,2⃣のスタンプをクリック下さい")
                await msg.delete(delay=3)
            await select_msg.remove_reaction(payload.emoji, payload.member)
            if embed:
                await dm.send(embed=embed)


def setup(bot):
    return bot.add_cog(Personal_DayRecord(bot))
