from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from typing import Union

from discord.ext import commands
from sqlalchemy import func as F, desc, case
from sqlalchemy.orm import aliased

from mo9mo9db.dbtables import Studytimelogs
from mo9mo9db.dbtables import Studymembers


class Week_Aggregate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 603582455756095488  # もくもくOnline勉強会
        self.channel_id = 683936366756888616  # 週間勉強集計
        self.MAX_SEND_MESSAGE_LENGTH = 2000

    def minutes2time(self, m) -> str:
        hour = m // 60
        minute = m % 60
        result_study_time = f"{str(hour)}時間{str(minute)}分"
        return result_study_time

    def getlastweek_days(self) -> Union[list, str]:
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

    def serialize_log(self, *args, end="\n") -> str:
        context = "".join(map(str, args)) + end
        return context

    def subquery(self, session, tm, ts, startdt_str, enddt_str,
                 str_wodfilter) -> object:
        obj = session.query(
            ts.study_dt
        ).filter(
            ts.member_id == tm.member_id,
            ts.access == "out",
            ts.excluded_record.isnot(True),
            F.date_format(ts.study_dt, '%Y-%m-%d') >= startdt_str,
            F.date_format(ts.study_dt, '%Y-%m-%d') <= enddt_str,
            ts.studytime_min.isnot(None),
            eval(str_wodfilter)
        )
        return obj

    def week_aggregate_users_record(self, startrange_dt,
                                    endrange_dt) -> list:
        session = Studytimelogs.session()
        startdt_str = startrange_dt.strftime('%Y-%m-%d')
        enddt_str = endrange_dt.strftime('%Y-%m-%d')
        # メインとサブで使用するテーブルの別名
        tm, ts = aliased(Studytimelogs), aliased(Studytimelogs)
        # 1〜6,0（月〜日）の情報を取得するための動的なフィルター作成
        sub_q1 = self.subquery(session, tm, ts, startdt_str, enddt_str,
                               "F.date_format(ts.study_dt, '%w') == 1")
        sub_q2 = self.subquery(session, tm, ts, startdt_str, enddt_str,
                               "F.date_format(ts.study_dt, '%w') == 2")
        sub_q3 = self.subquery(session, tm, ts, startdt_str, enddt_str,
                               "F.date_format(ts.study_dt, '%w') == 3")
        sub_q4 = self.subquery(session, tm, ts, startdt_str, enddt_str,
                               "F.date_format(ts.study_dt, '%w') == 4")
        sub_q5 = self.subquery(session, tm, ts, startdt_str, enddt_str,
                               "F.date_format(ts.study_dt, '%w') == 5")
        sub_q6 = self.subquery(session, tm, ts, startdt_str, enddt_str,
                               "F.date_format(ts.study_dt, '%w') == 6")
        sub_q0 = self.subquery(session, tm, ts, startdt_str, enddt_str,
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
            F.date_format(tm.study_dt, '%Y-%m-%d') >= startdt_str,
            F.date_format(tm.study_dt, '%Y-%m-%d') <= enddt_str,
            tm.studytime_min.isnot(None)
        ).group_by(
            tm.member_id,
            tm.guild_id,
        ).order_by(
            desc(F.sum(tm.studytime_min))
        ).all()
        return members_weekresult
#       欲しいオブジェクト情報{ユーザーID,ユーザName,勉強時間,月,火,水,木,金,土,日}

    def compose_users_weekrecord(self, strtoday, days, user_records,
                                 desc_lastweek) -> list:
        code_block = "```"
        separate = "====================\n"
        start_message = self.serialize_log("@everyone ")
        # start_message = self.serialize_log("everyone ")
        start_message += code_block + "\n"
        start_message += self.serialize_log("今日の日付：", strtoday)
        start_message += self.serialize_log("先週の日付：",
                                            desc_lastweek)
        users_log = self.week_usersrecord_listtostr(user_records)
        week_result = [start_message]
        for user_log in users_log:
            msglen = len(week_result[-1] + (separate + user_log))
            if msglen >= self.MAX_SEND_MESSAGE_LENGTH - len(code_block):
                week_result[-1] += code_block  # end code_block
                week_result.append(code_block)  # start code_block
            week_result[-1] += separate + user_log
        week_result[-1] += code_block  # end code_block
        return week_result

    def week_usersrecord_listtostr(self, week_results) -> list:
        users_record = []
        for result in week_results:
            user_record = []
            studydow = []
            user_record = self.serialize_log("Name：", result[1])
            studydow.extend(result[3:])
            user_record += self.serialize_log("　勉強した曜日：",
                                              ",".join(map(str, studydow)))
            user_record += self.serialize_log("　合計勉強時間：",
                                              self.minutes2time(result[2]))
            users_record.append(user_record)
        return users_record

    # ======================================================
    # Month
    # ======================================================

    def getMonth(self, y, m) -> int:
        if m in {1, 3, 5, 7, 8, 10, 12}:
            return 31
        elif m in {4, 6, 9, 11}:
            return 30
        elif m in {2}:
            if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
                return 29
            else:
                return 28
        else:
            return 0

    def getLastMonthValiable(self, request) -> datetime:
        thisMonth_YMFirstday = datetime(int(datetime.strftime(
            datetime.today(), '%Y')),
            int(datetime.strftime(
                datetime.today(), '%m')), 1)
        lastMonth_Y = int(datetime.strftime(
            datetime.today() - relativedelta(months=1), '%Y'))  # ex)2020
        lastMonth_M = int(datetime.strftime(
            datetime.today() - relativedelta(months=1), '%m'))  # ex)3
        lastMonth_YMFirstday = date(
            lastMonth_Y, lastMonth_M, 1)  # ex)2020-03-01
        month_endday = self.getMonth(lastMonth_Y, lastMonth_M)
        lastMonth_YMEndday = date(
            lastMonth_Y, lastMonth_M, month_endday)
        if request == 'thisMonth_YMFirstday':
            return thisMonth_YMFirstday
        if request == 'lastMonth_YMFirstday':
            return lastMonth_YMFirstday
        if request == 'lastMonth_YMEndday':
            return lastMonth_YMEndday

    def month_aggregate_users_record(self, startrange_dt) -> list:
        session = Studytimelogs.session()
        monthdt_str = startrange_dt.strftime('%Y-%m')
        # メインとサブで使用するテーブルの別名
        tm = aliased(Studytimelogs)
        members_monthresult = session.query(
            tm.member_id,
            Studymembers.member_name,
            F.sum(tm.studytime_min),
        ).join(
            Studymembers,
            tm.member_id == Studymembers.member_id
        ).filter(
            tm.access == "out",
            tm.excluded_record.isnot(True),
            F.date_format(tm.study_dt, '%Y-%m') == monthdt_str,
            tm.studytime_min.isnot(None)
        ).group_by(
            tm.member_id,
            tm.guild_id,
        ).order_by(
            desc(F.sum(tm.studytime_min))
        ).all()
        return members_monthresult
        # 欲しいオブジェクト情報{ユーザーID,ユーザName,勉強時間}

    def arr_monthdays(self, today):
        lastmonth_days = []
        lastmonth_days.append(
            self.getLastMonthValiable('lastMonth_YMFirstday')
        )
        lastmonth_days.append(
            self.getLastMonthValiable('lastMonth_YMEndday')
        )
        startrange_strdt = lastmonth_days[0]
        endrange_strdt = lastmonth_days[-1]
        desc_lastmonth = f"{startrange_strdt}〜{endrange_strdt}"
        return lastmonth_days, desc_lastmonth

    def compose_users_monthrecord(self, strtoday, days, user_records,
                                  desc_lastmonth):
        code_block = "```"
        separate = "====================\n"
        start_message = self.serialize_log("@everyone ")
        # start_message = self.serialize_log("everyone ")
        start_message += code_block + "\n"
        start_message += self.serialize_log("今日の日付：", strtoday)
        start_message += self.serialize_log(
            "先月の日付：",
            desc_lastmonth)
        users_log = self.month_usersrecord_listtostr(user_records)
        month_result = [start_message]
        for user_log in users_log:
            msglen = len(month_result[-1] + (separate + user_log))
            if msglen >= self.MAX_SEND_MESSAGE_LENGTH - len(code_block):
                month_result[-1] += code_block  # end code_block
                month_result.append(code_block)  # start code_block
            month_result[-1] += separate + user_log
        month_result[-1] += code_block  # end code_block
        return month_result

    def month_usersrecord_listtostr(self, month_results) -> list:
        users_record = []
        for result in month_results:
            # result: [member_id, member_name, studytime_min]
            user_record = []
            user_record = self.serialize_log("Name：", result[1])
            user_record += self.serialize_log("　合計勉強時間：",
                                              self.minutes2time(result[2]))
            users_record.append(user_record)
#       勉強日数計算の処理が完成してないためコメント
#        userMonthResult += self.serialize_log(
#            "　合計勉強時間：",
#            str(self.minutes2time(sum_study_time)),
#            "(勉強日数：",
#            len(studyMonth_day),
#            ")")
        return users_record

    # ======================================================
    def create_result(self, status) -> list:
        today = datetime.today()
        strtoday = datetime.strftime(today, '%Y-%m-%d')
        if status == "week":
            days, desc_lastweek = self.getlastweek_days()
            user_records = self.week_aggregate_users_record(days[0],
                                                            days[-1])
            result = self.compose_users_weekrecord(
                strtoday, days, user_records, desc_lastweek)
        if status == "month":
            days, desc_lastmonth = self.arr_monthdays(today)
            user_records = self.month_aggregate_users_record(days[0])
            result = self.compose_users_monthrecord(
                strtoday, days, user_records, desc_lastmonth)
        return result

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def admin_weekresult(self, ctx):
        message = ctx.message
        print(f"Used Command :{ctx.invoked_with} (User){message.author.name}")
        print(f"手動週間集計実行日: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        channel = self.bot.get_channel(self.channel_id)
        week_results = self.create_result("week")
        for week_result in week_results:
            await channel.send(week_result)


def setup(bot):
    return bot.add_cog(Week_Aggregate(bot))
