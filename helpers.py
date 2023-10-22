# Various helper functions
import discord
from settings import *
from typing import Union

# returns member object, including cache miss
async def find_member(bot: discord.Client, user_param: Union[int, discord.Member, discord.User]):
	# If user is int
	if isinstance(user_param, int):
		guild = bot.get_guild(config.getint('guild','guild_id'))
		user = guild.get_member(user_param)
		# Cache miss
		if user == None:
			user = await guild.fetch_member(user_param)
	# If already a member obj
	elif isinstance(user_param, discord.User):
		user = user_param
	# If user is discord.User
	else:
		guild = bot.get_guild(config.getint('guild','guild_id'))
		user = guild.get_member(user_param.id)
		# Cache miss
		if user == None:
			user = await guild.fetch_member(user_param.id)

	return user

# returns true if the user is either mod or admin
async def is_privileged(bot: discord.Client, user_param: Union[int, discord.Member, discord.User]):
	mod_status = await has_role(bot, config.getint('roles','mod_role'), user_param)
	mod_status = mod_status or await has_role(bot, config.getint('roles','admin_role'), user_param)
	return mod_status

# returns true if the user is simm
async def is_simm(user_param: Union[int, discord.Member, discord.User]):
	# If user is int
	if isinstance(user_param, int):
		return user_param == 1053028780383424563
	else:
		return user_param.id == 1053028780383424563

# returns true if the user is rosa
async def is_rosa(user_param: Union[int, discord.Member, discord.User]):
	# If user is int
	if isinstance(user_param, int):
		return user_param == 153857426813222912
	else:
		return user_param.id == 153857426813222912

# returns true if user is the bot
async def is_bot(bot: discord.Client, user_param: Union[int, discord.Member, discord.User]):
	if isinstance(user_param, int):
		return user_param == bot.user.id
	else:
		return user_param.id == bot.user.id

# returns true if the user has a certain role
async def has_role(bot: discord.Client, role_param: int, user_param: Union[int, discord.Member, discord.User]):
	user = await find_member(bot, user_param)

	# Check for role ID in user's roles
	return role_param in [role.id for role in user.roles]

# add user to a certain role
async def add_role(bot: discord.Client, role_param: int, user_param: Union[int, discord.Member, discord.User]):
	user = await find_member(bot, user_param)

	# Add role to user
	await user.add_roles(user.guild.get_role(role_param))

# remove user from a certain role
async def remove_role(bot: discord.Client, role_param: int, user_param: Union[int, discord.Member, discord.User]):
	user = await find_member(bot, user_param)

	# Check for role ID in 
	await user.remove_roles(user.guild.get_role(role_param))

