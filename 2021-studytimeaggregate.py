import os
from datetime import datetime, timedelta

from discord.ext import commands
import discord
from dotenv import load_dotenv
import urllib.parse
import json
import requests
from sqlalchemy import func as F
from sqlalchemy import func as F, desc

from mo9mo9db.dbtables import Studytimelogs
from mo9mo9db.dbtables import Studymembers
from sqlalchemy.orm import aliased


class Personal_2021Record(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.googleApiKey = os.environ.get("FIREBASE_API_KEY")
        self.googleShortLinksPrefix = os.environ.get(
            "FIREBASE_DYNAMICLINKS_PREFIX")

    def year2021_aggregate_user_record(self, member) -> list:
        session = Studytimelogs.session()
        monthdt_str = "2021"
        # メインとサブで使用するテーブルの別名
        tm = aliased(Studytimelogs)
        members_2021result = session.query(
            tm.member_id,
            Studymembers.member_name,
            F.sum(tm.studytime_min),
        ).join(
            Studymembers,
            tm.member_id == Studymembers.member_id
        ).filter(
            tm.member_id == member.id,
            tm.access == "out",
            tm.excluded_record.isnot(True),
            F.date_format(tm.study_dt, '%Y') == monthdt_str,
            tm.studytime_min.isnot(None)
        ).group_by(
            tm.member_id,
            tm.guild_id,
        ).order_by(
            desc(F.sum(tm.studytime_min))
        ).all()
        return members_2021result
        # 欲しいオブジェクト情報{ユーザーID,ユーザName,勉強時間}

    def createTwitterUrlEncode(self, websiteUrl, sendContent):
        encodeContent = urllib.parse.quote(sendContent)
        twitterUrl = "https://twitter.com/share?url={}&text={}".format(
            websiteUrl, encodeContent)
        return twitterUrl

    def create_twitter_embed(self, sendMessage):
        longUrl = self.createTwitterUrlEncode(
            "https://disboard.org/ja/server/603582455756095488", sendMessage)
        encodeMessage = self.shorten_url(
            longUrl, self.googleShortLinksPrefix, self.googleApiKey)
        embed = discord.Embed(title="📤積み上げツイート用",
                              description=sendMessage, color=0xFDB46C)
        embed.add_field(name="🦜下のURLから簡単に積み上げツイートが出来るよ", value=encodeMessage)
        return embed

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

    def compose_user_record(self, studytime):
        result = '''#2021年の振り返り
-
-

#もくもくオンライン勉強会
[ 2021年の総勉強時間 ]
---> {totalStudyTime} /時間
        '''.format(totalStudyTime=studytime)
        return result

    @commands.group(invoke_without_command=True)
    async def result2021(self, ctx, *args):
        member = ctx.guild.get_member(ctx.author.id)
        dm = await member.create_dm()
        results2021 = self.year2021_aggregate_user_record(member) 
        print(results2021)
        studytime_min = results2021[0][2]
        studytime_hour = studytime_min // 60
        print(f"[DEBUG] {member.name}: {studytime_hour}/h")
        sendMessage = self.compose_user_record(studytime_hour)
        embed = self.create_twitter_embed(sendMessage)
        await dm.send(embed=embed)
        await ctx.reply("あなたのdmに2021年の勉強記録を送信しました。")

def setup(bot):
    return bot.add_cog(Personal_2021Record(bot))