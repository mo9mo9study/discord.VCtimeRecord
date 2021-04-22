from datetime import datetime

from discord.ext import commands

from .weekAggregate import Week_Aggregate


class Month_Aggregate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 603582455756095488  # もくもくOnline勉強会
        # self.channel_id = 683936646164774929 #月間勉強集計
        self.channel_id = 673006702924136448  # times_supleiades
        self.MAX_SEND_MESSAGE_LENGTH = 2000

    @commands.command()
    # @commands.has_permissions(administrator=True)
    async def admin_monthresult(self, ctx):
        message = ctx.message
        print(f"Used Command :{ctx.invoked_with} (User){message.author.name}")
        print(f'手動月間集計実行日: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        channel = self.bot.get_channel(self.channel_id)
        month_results = Week_Aggregate(self.bot).create_result("month")
        for month_result in month_results:
            await channel.send(month_result)


def setup(bot):
    return bot.add_cog(Month_Aggregate(bot))
