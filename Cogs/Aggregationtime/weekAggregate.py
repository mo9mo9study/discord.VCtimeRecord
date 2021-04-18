import re
from datetime import datetime, timedelta, date

from discord.ext import commands
from sqlalchemy import func as F, extract, and_, desc, case
from sqlalchemy.orm import aliased

from mo9mo9db.dbtables import Studytimelogs
from mo9mo9db.dbtables import Studymembers


class Week_Aggregate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 603582455756095488  # もくもくOnline勉強会
        # self.channel_id = 683936366756888616  # 週間勉強集計
        self.channel_id = 673006702924136448  # times_supleiades
        self.MAX_SEND_MESSAGE_LENGTH = 2000

    def minutes2time(self, m):
        hour = m // 60
        minute = m % 60
        result_study_time = f"{str(hour)}時間{str(minute)}分"
        return result_study_time

    def getlastweek_days(self):
        weeknumber = [0, 1, 2, 3, 4, 5, 6]
        lastweek_days = []
        for i in weeknumber:
            lastweek_day = date.today() \
                - timedelta(days=datetime.now().weekday()) \
                + timedelta(days=i, weeks=-1)
            lastweek_days.append(lastweek_day)
        startrange_strdt = lastweek_days[0].strftime("%Y-%m-%d")
        endrange_strdt = lastweek_days[-1].strftime("%m-%d")
        desc_lastweek = f"{startrange_strdt}〜{endrange_strdt}"
        return lastweek_days, desc_lastweek

    def serialize_log(self, *args, end="\n"):
        context = "".join(map(str, args)) + end
        return context

    def construct_user_weekrecord(self,
                                  user_name,
                                  studyWeekday,
                                  sum_study_time):
        userWeekResult = self.serialize_log("Name：", user_name)
        # ex) 配列内の[04-20]月-日の文字列を[20]0埋めしない日に変換
        studyDay = []
        for item in studyWeekday:
            item_mod = re.sub(r'(^[0-9]{2})-0?([1-9]?[0-9]$)', r'\2', item)
            studyDay.append(item_mod)
        # ex) [04-20]
        userWeekResult += self.serialize_log("　勉強した日付：",
                                             str(studyDay))
        userWeekResult += self.serialize_log(
            "　合計勉強時間：",
            str(self.minutes2time(sum_study_time)))
        return userWeekResult

    def subquery(self, session, tm, ts, startrange_dt, endrange_dt,
                 str_wodfilter) -> object:
        obj = session.query(
            ts.study_dt
        ).filter(
            ts.member_id == tm.member_id,
            ts.access == "out",
            ts.excluded_record.isnot(True),
            and_(extract('year', ts.study_dt) == startrange_dt.year,
                 extract('month', ts.study_dt) == startrange_dt.month,
                 extract('day', ts.study_dt) >= startrange_dt.day),
            and_(extract('year', ts.study_dt) == endrange_dt.year,
                 extract('month', ts.study_dt) == endrange_dt.month,
                 extract('day', ts.study_dt) <= endrange_dt.day),
            ts.studytime_min.isnot(None),
            eval(str_wodfilter)
        )
        return obj

    def aggregate_users_record(self, startrange_dt,
                               endrange_dt) -> list:
        session = Studytimelogs.session()
        # メインとサブで使用するテーブルの別名
        tm, ts = aliased(Studytimelogs), aliased(Studytimelogs)
        # 1〜6,0（月〜日）の情報を取得するための動的なフィルター作成
        sub_q1 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 1")
        sub_q2 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 2")
        sub_q3 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 3")
        sub_q4 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 4")
        sub_q5 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 5")
        sub_q6 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 6")
        sub_q0 = self.subquery(session, tm, ts, startrange_dt, endrange_dt,
                               "F.date_format(ts.study_dt, '%w') == 0")
        members_weekresult = session.query(
            tm.member_id,
            Studymembers.member_name,
            F.sum(tm.studytime_min),
            case([(sub_q1.exists(), "月")], else_="x"),
            case([(sub_q2.exists(), "火")], else_="x"),
            case([(sub_q3.exists(), "水")], else_="x"),
            case([(sub_q4.exists(), "木")], else_="x"),
            case([(sub_q5.exists(), "金")], else_="x"),
            case([(sub_q6.exists(), "土")], else_="x"),
            case([(sub_q0.exists(), "日")], else_="x"),
        ).join(
            Studymembers,
            tm.member_id == Studymembers.member_id
        ).filter(
            tm.access == "out",
            tm.excluded_record.isnot(True),
            and_(extract('year', tm.study_dt) == startrange_dt.year,
                 extract('month', tm.study_dt) == startrange_dt.month,
                 extract('day', tm.study_dt) >= startrange_dt.day),
            and_(extract('year', tm.study_dt) == endrange_dt.year,
                 extract('month', tm.study_dt) == endrange_dt.month,
                 extract('day', tm.study_dt) <= endrange_dt.day),
            tm.studytime_min.isnot(None)
        ).group_by(
            tm.member_id,
            tm.guild_id,
        ).order_by(
            desc(F.sum(tm.studytime_min))
        ).all()
        return members_weekresult

#    def (self,):
#        # 勉強した曜日を取得
#        # 欲しいオブジェクト情報{ユーザーID:[月,火,水,木,金,土,日]}
#        # 別の関数(aggregate_user_record)で取得した勉強時間結果と結合する
#

    def compose_users_weekrecord(self, strtoday, days, users_log,
                                 desc_lastweek) -> str:
        code_block = "```"
        separate = "====================\n"
#        start_message = self.serialize_log("@everyone ")
        start_message = self.serialize_log("everyone ")
        start_message += code_block + "\n"
        start_message += self.serialize_log("今日の日付：", strtoday)
        start_message += self.serialize_log("先週の日付：",
                                            desc_lastweek)
        week_result = [start_message]
        for user_log in users_log:
            msglen = len(week_result[-1] + (separate + user_log))
            if msglen >= self.MAX_SEND_MESSAGE_LENGTH - len(code_block):
                week_result[-1] += code_block  # end code_block
                week_result.append(code_block)  # start code_block
            week_result[-1] += separate + user_log
        week_result[-1] += code_block  # end code_block
        return week_result

#    # ======================================================
#    # Month
#    # ======================================================
#
#    def getMonth(self, y, m):
#        if m in {1, 3, 5, 7, 8, 10, 12}:
#            return 31
#        elif m in {4, 6, 9, 11}:
#            return 30
#        elif m in {2}:
#            if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
#                return 29
#            else:
#                return 28
#        else:
#            return 0
#
#    def getLastMonthValiable(self, request):
#        thisMonth_YMFirstday = datetime(int(datetime.strftime( \
#                                           datetime.today(), '%Y')),
#                                        int(datetime.strftime(
#                                            datetime.today(), '%m')), 1)
#        lastMonth_Y = int(datetime.strftime(
#            datetime.today() - relativedelta(months=1), '%Y'))  # ex)2020
#        lastMonth_M = int(datetime.strftime(
#            datetime.today() - relativedelta(months=1), '%m'))  # ex)3
#        lastMonth_YMFirstday = date(
#            lastMonth_Y, lastMonth_M, 1)  # ex)2020-03-01
#        lastMonth_Days = self.getMonth(lastMonth_Y, lastMonth_M)
#        if request == 'thisMonth_YMFirstday':
#            return thisMonth_YMFirstday
#        if request == 'lastMonth_YMFirstday':
#            return lastMonth_YMFirstday
#        if request == 'D':
#            return lastMonth_Days
#
#    def construct_user_monthrecord(self,
#                                   user_name,
#                                   studyMonth_day,
#                                   sum_study_time):
#        userMonthResult = self.serialize_log("Name：", user_name)
#        print("(", user_name, ")", "　勉強した日付：", str(studyMonth_day))
#        userMonthResult += self.serialize_log(
#            "　合計勉強時間：",
#            str(self.minutes2time(sum_study_time)),
#            "(勉強日数：",
#            len(studyMonth_day),
#            ")")
#        return userMonthResult
#
#    def arr_monthdays(self, today):
#        days = []
#        for i in reversed(range(1, self.getLastMonthValiable('D')+1)):
#            day = self.getLastMonthValiable(
#                'thisMonth_YMFirstday') - relativedelta(days=i)
#            print(day)
#            days.append(datetime.strftime(day, '%Y-%m-%d'))
#        return days
#
#    def compose_users_monthrecord(self, strtoday, days, users_log):
#        code_block = "```"
#        separate = "====================\n"
#        #start_message = self.serialize_log("@everyone ")
#        start_message = self.serialize_log("everyone ")
#        start_message += code_block + "\n"
#        start_message += self.serialize_log("取得日：", strtoday)
#        start_message += self.serialize_log(
#            "先月の日付：",
#            self.getLastMonthValiable('lastMonth_YMFirstday'),
#            "~", days[-1])
#        month_result = [start_message]
#        for user_log in users_log:
#            msglen = len(month_result[-1] + (separate + user_log))
#            if msglen >= self.MAX_SEND_MESSAGE_LENGTH - len(code_block):
#                month_result[-1] += code_block  # end code_block
#                month_result.append(code_block)  # start code_block
#            month_result[-1] += separate + user_log
#        month_result[-1] += code_block  # end code_block
#        return month_result
#
    # ======================================================

    def create_result(self, status):
        today = datetime.today()
        strtoday = datetime.strftime(today, '%Y-%m-%d')
        if status == "week":
            days, desc_lastweek = self.getlastweek_days()
            user_records = self.aggregate_users_record(days[0],
                                                       days[-1])
            result = self.compose_users_weekrecord(
                strtoday, days, user_records, desc_lastweek)
#        if status == "month":
#            days = self.arr_monthdays(today)
#            user_records = self.aggregate_users_record(days, status)
#            result = self.compose_users_monthrecord(
#                strtoday, days, user_records)
        return result

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def admin_Week_Result(self, ctx):
        message = ctx.message
        print(f"Used Command :{ctx.invoked_with} (User){message.author.name}")
        print(f"手動週間集計実行日: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        channel = self.bot.get_channel(self.channel_id)
        week_results = self.create_result("week")
        for week_result in week_results:
            await channel.send(week_result)


def setup(bot):
    return bot.add_cog(Week_Aggregate(bot))
