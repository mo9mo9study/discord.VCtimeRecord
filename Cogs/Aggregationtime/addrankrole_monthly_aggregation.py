from discord.ext import commands
from datetime import datetime, timedelta

from .weekAggregate import Week_Aggregate


class AddrankroleMonthlyAggregation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.role_predator = 874525241949437993
        self.role_master = 874525568815755264
        self.role_diamond = 874525490742964226
        self.role_platinum = 874525823695192115
        self.role_gold = 874526111097290772
        self.role_silver = 874526164247531560
        self.role_bronze = 874526373878824980

    def role(self, beforeroles, afterroles):
        print("tmp")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if member.bot:
            print(f'{member.name} : BOTは記録しません')
            return
        # VC退室時 or 勉強記録あり--->勉強記録なし
        if (after.channel is None
            or self.NotRecordChannels in after.channel.name
                and before.channel != after.channel):

            print("tmp")
            now_dt = datetime.utcnow() + timedelta(hours=9)
            channel = before.channel  # noqa: F841
            access = "out"  # noqa: F841
            # 今月勉強時間を取得
            month_results = Week_Aggregate(self.bot).month_aggregate_users_record(now_dt)  # noqa: E501, F841
            try:
                print("tmp")
                # メインの処理

            except KeyError as e:
                print(f'{member.name} : {e}')
                pass
