import datetime

from discord.ext import commands
import discord
import asyncio


print('起動中...')

class Default(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('--------------------')
        print(f"BOT NAME : {self.bot.user.name}")
        print(f"BOT ID   : {str(self.bot.user.id)}")
        print(f"DATETIME : {datetime.datetime.now()}")
        print('--------------------')

def setup(bot):
    return bot.add_cog(Default(bot))
