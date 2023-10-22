import os
import discord
import time
import logging
import settings
from typing import Optional
from random import randint

from discord.ext import tasks, commands
from discord import app_commands

# Cogs import
import cogs.common
import cogs.config_commands
import cogs.battler

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!!', intents=intents)
logger = logging.getLogger('bot')

@bot.event
async def on_ready():
	logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
	logger.info('---------------------------------------------')
	await bot.add_cog(cogs.common.Common_Cog(bot))
	await bot.add_cog(cogs.config_commands.Config_Commands_Cog(bot))
	await bot.add_cog(cogs.battler.Battler_Cog(bot))
