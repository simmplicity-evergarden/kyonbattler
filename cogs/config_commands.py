from discord.ext import tasks, commands
from discord import app_commands
import configparser
import re
import os
import discord
import logging
#from random import randint
from typing import Literal
from settings import *
#from typing import Optional

logger = logging.getLogger('bot')

valid_toggles = Literal['miho_squeaks','lei_squeaks']
valid_numbers = Literal['miho_squeak_chance','lei_squeak_chance','role_squeak_chance',\
'feral_vote_requirement','feral_vote_value','paw_huff_base_chance','paw_huff_vote_value',\
'simm_huff_base_chance','simm_vote_requirement',\
'thrall_duration']

class Config_Commands_Cog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		logger.info('Loaded config_commands')

	@commands.hybrid_command(description='Modify number-based bot settings.')
	async def lb_config(self, context: commands.Context, setting_name: valid_numbers, value: int):
		# Role restriction - mods/admins
		if config.getint('roles','mod_role') not in [role.id for role in context.author.roles] \
			and  config.getint('roles','admin_role') not in [role.id for role in context.author.roles]:
			print('mod role error')

			return

		# Prevent Miho from changing their settings
		if context.author.id == 232281893696045056 and setting_name == 'miho_squeak_chance':
			await context.send(f'Miho, you can\'t change your own squeak chance! Adding +1 chance as a punishment.')
			return
		# Prevent Lei from changing their settings
		if context.author.id == 108904078351814656 and setting_name == 'lei_squeak_chance':
			await context.send(f'Lei, you can\'t change your own squeak chance! Adding +1 chance as a punishment.')
			return


		config['numbers'][setting_name] = str(value)
		save_settings()
		logger.info(f'{context.author.name} updated {setting_name} to {value}')
		await context.send(f'Updated {setting_name} to {value}', ephemeral=True)

	@commands.hybrid_command(description='Modify toggle-based bot settings.')
	async def lb_toggle(self, context: commands.Context, setting_name: valid_toggles, value: Literal['True','False']):
		# Role restriction - mods/admins
		if config.getint('roles','mod_role') not in [role.id for role in context.author.roles] \
			and  config.getint('roles','admin_role') not in [role.id for role in context.author.roles]:
			print('mod role error')
			return

		# Prevent Miho from changing their settings
		if context.author.id == 232281893696045056 and setting_name == 'miho_squeaks':
			await context.send(f'Miho, you can\'t change your own squeak chance! Adding +1% chance as a punishment.')
			return
		# Prevent Lei from changing their settings
		if context.author.id == 108904078351814656 and setting_name == 'lei_squeaks':
			await context.send(f'Lei, you can\'t change your own squeak chance! Adding +1 chance as a punishment.')
			return


		config['toggles'][setting_name] = str(value)
		save_settings()
		logger.info(f'{context.author.name} updated {setting_name} to {value}')
		await context.send(f'Updated {setting_name} to {value}', ephemeral=True)

	@commands.hybrid_command(description='Print current bot settings.')
	async def lb_print(self, context: commands.Context):
		# Role restriction - mods/admins
		if config.getint('roles','mod_role') not in [role.id for role in context.author.roles] \
			and  config.getint('roles','admin_role') not in [role.id for role in context.author.roles]:
			return

		# Print toggle-settings
		response = "Toggles:\n"
		for key in config['toggles'].keys():
			response += f'> **{key}:** {config["toggles"][key]}\n'

		# Print number-settings
		response += "Numbers:\n"
		for key in config['numbers'].keys():
			# Prevent Miho from changing their settings
			if context.author.id == 232281893696045056 and key == 'miho_squeak_chance':
				response += f'> **{key}:** <:rosasmug:1049703628639834163>\n'
				continue

			# Prevent Lei from changing their settings
			if context.author.id == 108904078351814656 and key == 'lei_squeak_chance':
				response += f'> **{key}:** <:rosasmug:1049703628639834163>\n'
				continue

			response += f'> **{key}:** {config["numbers"][key]}\n'

		await context.send(response, ephemeral=True)
