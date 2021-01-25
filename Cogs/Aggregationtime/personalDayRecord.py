import os
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from discord.ext import commands
import discord
import asyncio
from dotenv import load_dotenv
import urllib.parse
import json
import requests

from .weekAggregate import Week_Aggregate


class Personal_DayRecord(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        dotenv_path = os.path.join(os.getcwd(), '.env')
        load_dotenv(dotenv_path)
        self.googleApiKey=os.environ.get("FIREBASE_API_KEY")
        self.googleShortLinksPrefix = os.environ.get("FIREBASE_DYNAMICLINKS_PREFIX")
        self.LOG_DIR = os.path.join("/home/centos/repos/discord.VCtimeRecord/entry_exit/", "timelog")


    def createTwitterUrlEncode(self, websiteUrl, sendContent):
        baseurl = "https://twitter.com/share"
        encodeContent = urllib.parse.quote(sendContent)
        twitterUrl = "https://twitter.com/share?url={}&text={}".format(websiteUrl, encodeContent)
        return twitterUrl


    def shorten_url(self, url, prefix, key):
        '''Firebase Dynamic Link を使って URL を短縮する'''
        post_url = 'https://firebasedynamiclinks.googleapis.com/v1/shortLinks?key=' + key
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
            print(str(r), file=sys.stderr)
            return None
        return json.loads(r.content)["shortLink"]


    #週間と被るが、一旦日次分の処理を追加
    #今後、統一していってほしい
    #関数名がxxxになっている集計
    def aggregate_day_users_record(self, name, day):
        user_log = self.LOG_DIR + '/' + name
        print(user_log)
        # ログファイルみ込み
        lines_strip = Week_Aggregate(self.bot).read_file(user_log)
        # 指定された日付の勉強ログのみ抜き出す
        study_logs = []
        for line in lines_strip:
            if day in line:
                if "Study time" in line:
                    print(line)
                    study_logs.append(line)
        # 学習ログから合計勉強時間を算出する
        sum_study_time = 0
        for log in study_logs:
            sum_study_time += int(log.split(",")[-1])
        return sum_study_time


    def compose_user_record(self, name, day, studytime):
        day_result = '''
#今日の積み上げ 
- 
-

#もくもくオンライン勉強会 
[ {day}の勉強時間 ]
---> {totalStudyTime}
#mo9mo9_{name}
        '''.format(name=name, day=day, totalStudyTime=str(Week_Aggregate(self.bot).minutes2time(studytime))).strip()
        return day_result


    def create_twitter_embed(self, sendMessage):
        longUrl = self.createTwitterUrlEncode("https://mo9mo9study.github.io/discord.web/", sendMessage)
        encodeMessage = self.shorten_url(longUrl, self.googleShortLinksPrefix , self.googleApiKey)
        #embed = discord.Embed(title="積み上げツイート用",description=sendMessage,color=0xFDB46C)
        embed = discord.Embed(title="📤積み上げツイート用",description=sendMessage,color=0xFDB46C)
        #embed.add_field(name="⬇︎下のURLから簡単に積み上げツイートが出来るよ",value=encodeMessage)
        embed.add_field(name="🦜下のURLから簡単に積み上げツイートが出来るよ",value=encodeMessage)
        return embed


    @commands.group(invoke_without_command=True)
    async def result_d(self, ctx):
        #当日分の日次集計
        if ctx.subcommand_passed is None:
            print("-----------")
            print(vars(ctx))
            print("-----------")
            name = ctx.author.name
            today = datetime.today()
            strtoday = datetime.strftime(today, '%Y-%m-%d')
            sum_study_time = self.aggregate_day_users_record(name, strtoday)
            sendMessage = self.compose_user_record(name, strtoday, sum_study_time)
            #longUrl = self.createTwitterUrlEncode("https://mo9mo9study.github.io/discord.web/", sendMessage)
            #encodeMessage = self.shorten_url(longUrl, self.googleShortLinksPrefix , self.googleApiKey)
            #embed = discord.Embed(title="積み上げツイート用",description=sendMessage,color=0xFDB46C)
            #embed.add_field(name="⬇︎下のURLから簡単に積み上げツイートが出来るよ",value=encodeMessage)
            embed = self.create_twitter_embed(sendMessage)
            sendmsg = await ctx.send(embed=embed)
            await sendmsg.add_reaction("<:otsukaresama:757813789952573520>")
        else:
            await ctx.send("[ " + ctx.subcommand_passed + " ]は無効な引数です")

    @result_d.command()
    async def ago(self, ctx):
        #前日分の日次集計
        print("-----------")
        print(vars(ctx))
        print("-----------")
        name = ctx.author.name
        today = datetime.today()
        day = today - timedelta(1)
        strday = datetime.strftime(day, '%Y-%m-%d')
        sum_study_time = self.aggregate_day_users_record(name, strday)
        sendMessage = self.compose_user_record(name, strday, sum_study_time)
        longUrl = self.createTwitterUrlEncode("https://mo9mo9study.github.io/discord.web/", sendMessage)
        encodeMessage = self.shorten_url(longUrl, self.googleShortLinksPrefix , self.googleApiKey)
        embed = discord.Embed(title="積み上げツイート用",description=sendMessage,color=0xFDB46C)
        embed.add_field(name="⬇︎下のURLから簡単に積み上げツイートが出来るよ",value=encodeMessage)
        sendmsg = await ctx.send(embed=embed)
        await sendmsg.add_reaction("<:otsukaresama:757813789952573520>")



def setup(bot):
    return bot.add_cog(Personal_DayRecord(bot))