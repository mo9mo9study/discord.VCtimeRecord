from discord.ext import commands
import discord

import config


intents = discord.Intents.all()
TOKEN = config.Token
prefix = "¥"

bot = commands.Bot(command_prefix=prefix, intents=intents)


bot.load_extension("Cogs.default")

bot.load_extension("2021-studytimeaggregate")


bot.run(TOKEN)
