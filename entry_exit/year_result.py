# import mimetypes
import magic
import os
import sys
import setting
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import re

from pprint import pprint
import urllib.parse
import json
import requests

import discord
from discord.ext import tasks, commands

client = discord.Client()
bot = commands.Bot(command_prefix='¥')
TOKEN = setting.dToken
SERVER = setting.dServer
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timelog")
USER_SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "userSettings")
MAX_SEND_MESSAGE_LENGTH = 2000


def getMonth(y, m):
    if m in {1, 3, 5, 7, 8, 10, 12}:
        return 31
    elif m in {4, 6, 9, 11}:
        return 30
    elif m in 2:
        if y % 4 in 0 and y % 100 != 0 or y % 400:
            return 29
        else:
            return 28
    else:
        return 0


#50行目に関してはpost_result.pyの方にも移植したい
def minutes2time(m):
    hour = m // 60
    minute = m % 60
    result_study_time = f"{hour:,}時間{minute}分"
    return result_study_time


def compose_user_record(name, day, studytime):
    day_result = '''
#もくもくオンライン勉強会 
#2021年の抱負 
- 

====================
#2020年の振り返り と一言 
- 

あなたの2020年総勉強時間は、
--->[ {totalStudyTime} ]
    '''.format(name=name, day=day, totalStudyTime=str(minutes2time(studytime))).strip()
    return day_result


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines_strip = [line.strip() for line in lines]
    return lines_strip


#週間と被るが、一旦日次分の処理を追加
#今後、統一していってほしい
#関数名がxxxになっている集計
def xxx(name, day):
    user_log = LOG_DIR + '/' + name
    # ログファイル読み込み
    lines_strip = read_file(user_log)
    # 指定された日付の勉強ログのみ抜き出す
    study_logs = []
    for line in lines_strip:
        if day in line:
            if "Study time" in line:
                #print(line)
                study_logs.append(line)
    # 学習ログから合計勉強時間を算出する
    sum_study_time = 0
    for log in study_logs:
        sum_study_time += int(log.split(",")[-1])
    return sum_study_time



#==========
# result_d
#==========
googleShortLinksPrefix = setting.dFirebaseshortLinksPrefix
googleApiKey = setting.dFirebaseAipkey

def createTwitterUrlEncode(websiteUrl, sendContent):
    baseurl = "https://twitter.com/share"
    encodeContent = urllib.parse.quote(sendContent)
    twitterUrl = "https://twitter.com/share?url={}&text={}".format(websiteUrl, encodeContent)
    return twitterUrl


def shorten_url(url, prefix, key):
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


#日付を2020で固定してある
@bot.group(invoke_without_command=True)
async def result_y(ctx):
    #2020年一年間の総勉強時間集計
    print("-----------")
    pprint(vars(ctx))
    print("===========")
    if ctx.subcommand_passed is None:
        name = ctx.author.name
        today = datetime.today()
        #strtoday = datetime.strftime(today, '%Y')
        #sum_study_time = xxx(name, strtoday)
        sum_study_time = xxx(name, "2020")
        #sendMessage = compose_user_record(name, strtoday, sum_study_time)
        sendMessage = compose_user_record(name, "2020", sum_study_time)
        longUrl = createTwitterUrlEncode("https://mo9mo9study.github.io/discord.web/", sendMessage)
        encodeMessage = shorten_url(longUrl, googleShortLinksPrefix , googleApiKey)
        embed = discord.Embed(title="積み上げツイート用",description=sendMessage,color=0xFDB46C)
        embed.add_field(name="⬇︎下のURLから簡単に積み上げツイートが出来るよ",value=encodeMessage)
        await ctx.send(embed=embed)
    else:
        await ctx.send("[ " + ctx.subcommand_passed + " ]は無効な引数です")

#@result_d.command()
#async def ago(ctx):
#    #前日分の日次集計
#    print("-----------")
#    pprint(vars(ctx))
#    print("===========")
#    name = ctx.author.name
#    today = datetime.today()
#    day = today - timedelta(1)
#    print("day :", day)
#    strday = datetime.strftime(day, '%Y-%m-%d')
#    print("strday :",strday)
#    sum_study_time = xxx(name, strday)
#    sendMessage = compose_user_record(name, strday, sum_study_time)
#    longUrl = createTwitterUrlEncode("https://mo9mo9study.github.io/discord.web/", sendMessage)
#    encodeMessage = shorten_url(longUrl, googleShortLinksPrefix , googleApiKey)
#    embed = discord.Embed(title="積み上げツイート用",description=sendMessage,color=0xFDB46C)
#    embed.add_field(name="⬇︎下のURLから簡単に積み上げツイートが出来るよ",value=encodeMessage)
#    await ctx.send(embed=embed)
#


@bot.event
async def on_ready():
    print('Online')


bot.run(TOKEN)