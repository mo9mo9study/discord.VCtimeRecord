from discord.ext import commands, tasks
from datetime import datetime, date

from .weekAggregate import Week_Aggregate


class Cron_Aggregate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.week_channel_id = 683936366756888616
        self.month_channel_id = 683936646164774929
        self.post_result.start()

    # 自動集計用定期処理

    @tasks.loop(seconds=60)
    async def post_result(self):
        await self.bot.wait_until_ready()  # Botが準備状態になるまで待機
        # post_week_result
        if datetime.now().strftime('%H:%M') == "07:30":
            if date.today().weekday() == 0:
                print(f'週間集計実行日: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
                channel = self.bot.get_channel(self.week_channel_id)
                week_results = Week_Aggregate(self.bot).create_result("week")
                for week_result in week_results:
                    await channel.send(week_result)
        # post_month_result
        if datetime.now().strftime('%H:%M') == "07:35":
            if datetime.now().strftime('%d') == '01':
                print(f'月間集計実行日: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
                channel = self.bot.get_channel(self.month_channel_id)
                month_results = Week_Aggregate(self.bot).create_result("month")
                for month_result in month_results:
                    await channel.send(month_result)


def setup(bot):
    return bot.add_cog(Cron_Aggregate(bot))
