import os
import re
import magic
from datetime import datetime, timedelta, date

from discord.ext import commands
import discord
import asyncio
import dateutil
from dateutil.relativedelta import relativedelta

class Week_Aggregate(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.guild_id = 603582455756095488 #もくもくOnline勉強会
        self.channel_id = 683936366756888616 #週間勉強集計
        self.LOG_DIR = os.path.join("/home/centos/repos/discord.VCtimeRecord/entry_exit/", "timelog")
        self.MAX_SEND_MESSAGE_LENGTH = 2000


    def minutes2time(self, m):
        hour = m // 60
        minute = m % 60
        result_study_time = f"{str(hour)}時間{str(minute)}分"
        return result_study_time


    ##[検討]ここをいつ起動しても先週の月〜日を指す方法に変更するのもあり
    ## 現在は、1日前から遡って7日分取得する方法
    def arr_weekdays(self, today):
        days = []
        for i in reversed(range(1, 8)):
    #    for i in reversed(range(2, 9)): # 火曜日用
            day = today - timedelta(days=i)
            days.append(datetime.strftime(day, '%Y-%m-%d'))
        return days
    
    

    def exclude_non_txt(self, file_list):
        file_list_result = list(file_list)
        print('対象ファイル数 : ',len(file_list))
        print('--- 対象ファイルの[名前/ファイルタイプ]と[対象から除外か否か]の処理結果を出力 ---')
        for file in file_list:
            file_type = magic.from_file(file, mime=True)
            print(f'\n python-magic: {file_type} --> [file]: {file}',end='') # 確認用
            if file_type != 'text/plain':
                print('-->  [ remove ]',end='') # 確認用
                file_list_result.remove(file)
        print('\n--- (除外対象)ファイルタイプが[text/plain]でない対象 --- ')
        result = list(set(file_list) - set(file_list_result))
        for x in result:
            print(x)
        print('--- end --- ')
        return file_list_result


    def read_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        lines_strip = [line.strip() for line in lines]
        return lines_strip


    def serialize_log(self, *args, end="\n"):
        context = "".join(map(str, args)) + end
        return context


    def construct_user_weekrecord(self, user_name, studyWeekday, sum_study_time):
        userWeekResult = self.serialize_log("Name：", user_name)
        #ex) 配列内の[04-20]月-日の文字列を[20]0埋めしない日に変換
        studyDay = []
        for item in studyWeekday:
            item_mod = re.sub(r'(^[0-9]{2})-0?([1-9]?[0-9]$)',r'\2',item)
            studyDay.append(item_mod)
        #ex) [04-20]
        userWeekResult += self.serialize_log("　勉強した日付：", str(studyDay))
        userWeekResult += self.serialize_log("　合計勉強時間：", str(self.minutes2time(sum_study_time)))
        return userWeekResult


    def aggregate_users_record(self, days, status):
        """
        各ユーザーの１週間の学習時間と日数を集計する
        """
        user_list = [os.path.join(self.LOG_DIR, txt) for txt in os.listdir(self.LOG_DIR)]
        user_list = self.exclude_non_txt(user_list)
        memberStudytime = []
        users_record = []
        obj = {}
        for user_log in user_list:
            # ログファイル読み込み
            lines_strip = self.read_file(user_log)
            # １週間以内に勉強した日の学習ログのみ抜き出す
            study_logs = []
            for line in lines_strip:
                if "Study time" in line:
                    study_logs += [line for day in days if day in line]
            # 勉強した日がないユーザーは処理をスキップする
            if study_logs == []:
                print(f'{user_log}: 学習記録がありません')
                continue
            # 学習ログから勉強した日付を抜き出す
            study_days = []
            for log in study_logs:
                study_days += [day[-5:] for day in days if day in log]
            study_days = sorted(set(study_days), key=study_days.index)
            # 学習ログから合計勉強時間を算出する
            sum_study_time = 0
            for log in study_logs:
                sum_study_time += int(log.split(",")[-1])
            user_name = os.path.splitext(os.path.basename(user_log))[0]
            memberStudytime.append({"username": user_name, "studydays": study_days, "sumstudytime": sum_study_time})
        memberStudytime.sort(key=lambda x: x["sumstudytime"], reverse=True)
        for studytime in memberStudytime :
            if status == "week":
              user_record = self.construct_user_weekrecord(studytime["username"], studytime["studydays"], studytime["sumstudytime"])
            if status == "month":
              user_record = self.construct_user_monthrecord(studytime["username"], studytime["studydays"], studytime["sumstudytime"])
            users_record.append(user_record)
        print("~< ソート済整形データ >~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(memberStudytime)
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        return users_record


    def compose_users_weekrecord(self, strtoday, days, users_log):
        code_block = "```"
        separate = "====================\n"
    #    start_message = self.serialize_log("@everyone ")
        start_message = self.serialize_log("everyone ")
        start_message += code_block + "\n"
        start_message += self.serialize_log("今日の日付：", strtoday)
        start_message += self.serialize_log("先週の日付：", days[0], "~", days[-1])
        week_result = [start_message]
        for user_log in users_log:
            if len(week_result[-1] + (separate + user_log)) >= self.MAX_SEND_MESSAGE_LENGTH - len(code_block):
                week_result[-1] += code_block # end code_block
                week_result.append(code_block) # start code_block
            week_result[-1] += separate + user_log
        week_result[-1] += code_block # end code_block
        return week_result

    
    
    # ======================================================
    # Month
    # ======================================================

    def getMonth(self, y, m):
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
    
    def getLastMonthValiable(self, request):
        thisMonth_YMFirstday = datetime(int(datetime.strftime(datetime.today(),'%Y')), int(datetime.strftime(datetime.today(),'%m')), 1) #ex)2020-03
        lastMonth_Y = int(datetime.strftime(datetime.today() - relativedelta(months=1), '%Y')) #ex)2020
        lastMonth_M = int(datetime.strftime(datetime.today() - relativedelta(months=1), '%m')) #ex)3
        lastMonth_YMFirstday = date(lastMonth_Y, lastMonth_M , 1) #ex)2020-03-01
        lastMonth_Days = self.getMonth(lastMonth_Y, lastMonth_M)
        if request == 'thisMonth_YMFirstday':
            return thisMonth_YMFirstday
        if request == 'lastMonth_YMFirstday':
            return lastMonth_YMFirstday
        if request == 'D':
            return lastMonth_Days

    def construct_user_monthrecord(self, user_name, studyMonth_day, sum_study_time):
        userMonthResult = self.serialize_log("Name：", user_name)
        print("(",user_name,")","　勉強した日付：", str(studyMonth_day))
        userMonthResult += self.serialize_log("　合計勉強時間：", str(self.minutes2time(sum_study_time)),"(勉強日数：",len(studyMonth_day),")")
        return userMonthResult

    def arr_monthdays(self, today):
        days = []
        for i in reversed(range(1, self.getLastMonthValiable('D')+1)):
            day = self.getLastMonthValiable('thisMonth_YMFirstday') - relativedelta(days=i)
            print(day)
            days.append(datetime.strftime(day, '%Y-%m-%d'))
        return days

    def compose_users_monthrecord(self, strtoday, days, users_log):
        code_block = "```"
        separate = "====================\n"
    #    start_message = self.serialize_log("@everyone ")
        start_message = self.serialize_log("everyone ")
        start_message += code_block + "\n"
        start_message += self.serialize_log("取得日：", strtoday)
        start_message += self.serialize_log("先月の日付：", self.getLastMonthValiable('lastMonth_YMFirstday'),"~", days[-1])
        month_result = [start_message]
        for user_log in users_log:
            if len(month_result[-1] + (separate + user_log)) >= self.MAX_SEND_MESSAGE_LENGTH - len(code_block):
                month_result[-1] += code_block # end code_block
                month_result.append(code_block) # start code_block
            month_result[-1] += separate + user_log
        month_result[-1] += code_block # end code_block
        return month_result

    # ======================================================

    def create_result(self, status):
        today = datetime.today()
        strtoday = datetime.strftime(today, '%Y-%m-%d')
        if status == "week":
            days = self.arr_weekdays(today)
            user_records = self.aggregate_users_record(days, status)
            result = self.compose_users_weekrecord(strtoday, days, user_records)
        if status == "month":
            days = self.arr_monthdays(today) 
            user_records = self.aggregate_users_record(days, status)
            result = self.compose_users_monthrecord(strtoday, days, user_records)
        return result


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def Week_Result(self, ctx):
        message = ctx.message
        print(f"Used Command :{ctx.invoked_with} (User){message.author.name}")
        print(f"手動週間集計実行日: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        channel = self.bot.get_channel(self.channel_id)
        week_results = self.create_result("week")
        for week_result in week_results:
            await channel.send(week_result)


def setup(bot):
    return bot.add_cog(Week_Aggregate(bot))