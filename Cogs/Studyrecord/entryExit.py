import os
import sys
from datetime import datetime, timedelta

from discord.ext import commands, tasks
import discord
import asyncio

class ENTRY_EXIT(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 603582455756095488 #もくもくOnline勉強会
        self.channel_id = 618081921611726851 #勉強記録
        self.pretime_dict = {}
        self.logsPath = "/home/centos/repos/discord.VCtimeRecord/entry_exit/timelog/"
        self.NotRecordChannels = "時間記録無"

    async def writeLog(time,name,m,mdta=''):
        print(f'{name} : <ログの書き込み>')
        if not os.path.isdir(self.logsPath):
            os.mkdir(self.logsPath)
        filePath = f'{self.logsPath}{name}'
        if os.path.isfile(filePath):
            with open(filePath, "a", encoding="utf-8") as f:
                f.write(str(time) + ',' + name + ',' + m + ',' + mdta + '\n')
        else:
            with open(filePath, "w", encoding="utf-8") as f:
                f.write(str(time) + ',' + name + ',' + m + ',' + mdta + '\n')

    def splitTime(name):
        print(f'{name} : <ログの読み込み>')
        filePath = f'{self.logsPath}{name}'
        with open(filePath) as f:
            arrAlllog = f.readlines()
            strReadlog = arrAlllog[-1]
            arrSplitlog = strReadlog.split(',')
            result = arrSplitlog[0]
            dtResult = datetime.strptime(result, '%Y-%m-%d %H:%M:%S.%f')
            return dtResult

    @commands.Cog.listener()
    async def on_voice_state_update(member, before, after):
        # 原因がわからず、入室時に二度処理が走っているため。入室後に走るイベントをretunする処理追加
        if before.channel == after.channel:
            return
        print(f"[{datetime.now()}]{member.name} : ステータスが変更されました (before){before.channel}/(after){after.channel}")
        if member.bot:
            print(f'{member.name} : BOTは記録しません')
            return
        if member.guild.id == self.guild_id and (before.channel != after.channel):
            now = datetime.utcnow() + timedelta(hours=9)
            alert_channel = client.get_channel(self.channel_id)
            # VC入室時 or 勉強記録なし--->勉強記録あり
            if before.channel is None or self.NotRecordChannels in before.channel.name and before.channel != after.channel:
                print(f'{member.name} : 入室時の処理')
                self.pretime_dict['beforetime'] = datetime.now()
                msg = f'{now:%m/%d %H:%M} 　 {member.name}   joined the  {after.channel.name}'
                #writeLog(datetime.now(),member.name,msg)
                if  self.NotRecordChannels in after.channel.name:
                    print(f'{member.name} : self.NotRecordChannels リストに記載されているので記録しません')
                    return
                #await alert_channel.send(msg)
            # VC退室時 or 勉強記録あり--->勉強記録なし
            elif after.channel is None or self.NotRecordChannels in after.channel.name and before.channel != after.channel:
                print(f'{member.name} : 退室時の処理')
                if self.NotRecordChannels in before.channel.name:
                    print(f'{member.name} : self.NotRecordChannels リストに記載されているので記録しません')
                    return
                msg = f'[{now:%m/%d %H:%M} ]  {member.name}  joined  {before.channel.name} '
                dtBeforetime = splitTime(member.name)
                try:
                    duration_time = dtBeforetime - datetime.now()
                    duration_time_adjust = int(duration_time.total_seconds()) * -1
                    print(f"dutation_time_adjust: {duration_time_adjust}")
                    if duration_time_adjust >= 60:
                        print(f'{member.name} : 60sec以上')
                        minute_duration_time_adjust = int(duration_time_adjust) // 60
                        msg = "-->[" + member.name + "]   Study time： " + str(minute_duration_time_adjust) + "/分"
                        #writeLog(datetime.now(),member.name,msg,str(minute_duration_time_adjust)) #不要になる予定
                        if duration_time_adjust >= 300:
                            entry_date = date(dtBeforetime.year, dtBeforetime.month, dtBeforetime.day)
                            print(f"entry_date: {entry_date}")
                            exit_date = date.today()
                            print(f"exit_date: {exit_date}")
                            if entry_date != exit_date: # 日付を跨いだ時の処理
                                # 入室時から23:59:59までの経過時間を算出
                                agoday_studytime = int((dtBeforetime - datetime(entry_date.year, entry_date.month, entry_date.day, 23, 59, 59)).total_seconds() * -1) // 60
                                result_studytimes = [agoday_studytime]
                                # 00:00:00から退室時までの経過時間を算出
                                day_studytime = int((datetime.combine(date.today(), time(0,0)) - datetime.now()).total_seconds()) * -1 // 60
                                result_studytimes.append(day_studytime) 
                                print(f"list:{result_studytimes}")
                                for result_time in result_studytimes:
                                    #writeLog(datetime.now(),member.name,msg,str(result_time))
                                    print(f"書き込みログ：{datetime.now()},{member.name},{msg},{str(result_time)}")

                            print(f'{member.name} : 退室ログをDiscordに出力')
                            #await alert_channel.send(msg)
                except KeyError:
                    print(f'{member.name} : except')
                    pass


def setup(bot):
    return bot.add_cog(ENTRY_EXIT(bot))