from discord.ext import commands
import discord
import asyncio


class Week_Result(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.guild_id = 603582455756095488 #もくもくOnline勉強会
        self.channel_id = 683936366756888616 #週間勉強集計

    @commands.Cog.listener()
    async def 


def setup(bot):
    return bot.add_cog(Week_Result(bot))