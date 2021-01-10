from discord.ext import commands
import discord
import asyncio

import config


intents = discord.Intents.all()
TOKEN = config.dToken
prefix = "¥"

bot = commands.Bot(command_prefix=prefix,help_command=None,intents=intents)


bot.load_extension("Cogs.default")

bot.load_extension("Cogs.Studyrecord.entryExit")


bot.run(TOKEN)