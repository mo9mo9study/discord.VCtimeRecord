import re
from datetime import datetime, timedelta

from discord.ext import commands
from sqlalchemy import func as F, desc
from sqlalchemy.orm import aliased

from mo9mo9db.dbtables import Studytimelogs
from mo9mo9db.dbtables import Studymembers


class AddrankroleMonthlyAggregation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.NotRecordChannels = "記録無"
        self.role_predator = 874525241949437993
        self.role_master = 874525568815755264
        self.role_diamond = 874525490742964226
        self.role_platinum = 874525823695192115
        self.role_gold = 874526111097290772
        self.role_silver = 874526164247531560
        self.role_bronze = 874526373878824980
        self.GUILD_ID = 603582455756095488
        self.LOG_CHANNEL_ID = 801060150433153054
        self.rankroles_name = ["Predator", "Master", "Diamond", "Platinum",
                               "Gold", "Silver", "Bronze"]

    @commands.Cog.listener()
    async def on_ready(self):
        self.GUILD = self.bot.get_guild(self.GUILD_ID)
        self.LOG_CHANNEL = self.GUILD.get_channel(self.LOG_CHANNEL_ID)

    def role(self, beforeroles, afterroles):
        print("tmp")

    def month_aggregate_user_record(self, member, startrange_dt) -> list:
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
            tm.member_id == member.id,
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

    async def add_rankrole(self, member, role_id):
        add_role = member.guild.get_role(role_id)
        # 勉強時間に応じたRank権限が付与されているか確認
        if add_role not in member.roles:
            remove_rankroles = []
            for role in member.roles:
                # メンバーに付与されている権限からRank権限のオブジェクトのみ抽出
                # 付与されている権限名の先頭文字にRank権限名の文字列（配列）が一致する権限が存在するか確認
                if any(list(map(
                        lambda rankrole_name: role.name.startswith(
                            rankrole_name),
                        self.rankroles_name))):
                    remove_rankroles.append(role)
            # 付与する権限以外のRank権限の剥奪
            if remove_rankroles:
                for remove_role in remove_rankroles:
                    await member.remove_roles(remove_role)
                hour_remove_rolename = list(
                    map(lambda s: s.name, remove_rankroles))
                remove_rolename = list(map(lambda s: re.sub(
                    r"\（.*\）", "", s), hour_remove_rolename))
                log_msg = f"[INFO] {member.name} から {','.join(remove_rolename)} を剥奪"  # noqa: E501
                print(log_msg)
                await self.LOG_CHANNEL.send(log_msg)
            # 勉強時間に応じたRank権限の付与
            await member.add_roles(add_role)
            log_msg = f"[INFO] {member.name} に {add_role.name} を付与"
            print(log_msg)
            await self.LOG_CHANNEL.send(log_msg)
        else:
            print(f"[DEBUG] {member.name}: 既に{add_role.name}は付与済")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if member.bot:
            return
        # VC退室時 or 勉強記録あり--->勉強記録なし
        if (after.channel is None
            or self.NotRecordChannels in after.channel.name
                and before.channel != after.channel):

            now_dt = datetime.utcnow() + timedelta(hours=9)
            channel = before.channel  # noqa: F841
            access = "out"  # noqa: F841
            # 今月勉強時間を取得
            month_results = self.month_aggregate_user_record(member, now_dt)  # noqa: E501, F841
            studytime_min = month_results[0][2]
            studytime_hour = studytime_min // 60
            print(f"[DEBUG] {member.name}: {studytime_hour} h/month")
            try:
                if 1 <= studytime_hour <= 4:
                    await self.add_rankrole(member, self.role_silver)
                elif 5 <= studytime_hour <= 14:
                    await self.add_rankrole(member, self.role_silver)
                elif 15 <= studytime_hour <= 34:
                    await self.add_rankrole(member, self.role_gold)
                elif 35 <= studytime_hour <= 74:
                    await self.add_rankrole(member, self.role_platinum)
                elif 75 <= studytime_hour <= 114:
                    await self.add_rankrole(member, self.role_diamond)
                elif 115 <= studytime_hour <= 164:
                    await self.add_rankrole(member, self.role_master)
                elif 165 <= studytime_hour:
                    await self.add_rankrole(member, self.role_predator)
            except KeyError as e:
                print(f'{member.name} : {e}')
                pass


def setup(bot):
    return bot.add_cog(AddrankroleMonthlyAggregation(bot))
