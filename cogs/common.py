from discord.ext import tasks, commands
from discord import app_commands
import re
import os
import discord
import logging
from settings import *

logger = logging.getLogger('bot')

class Common_Cog(commands.Cog):

	def __init__(self, bot):
		logger.info('Loaded Common')

	# Sync commands
	@commands.command(description='Sync bot commands w/ server')
	async def sync(self, context: commands.Context):
		synced = await context.bot.tree.sync()
		await context.send(f'Sync\'d {len(synced)} commands to current guild.', ephemeral=True)
