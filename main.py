import os
import logging
import discord
import bot
import configparser


config = configparser.ConfigParser()
config.read(os.path.dirname(__file__)+os.path.sep+'authentication.ini')

handler = logging.FileHandler(filename=os.path.dirname(__file__)+os.path.sep+'discord_py_messages.log',encoding='utf-8', mode='w')

# create logger just for bot messages

bot_log_handler = logging.StreamHandler()
bot_log_logger = logging.getLogger('bot')
bot_log_logger.setLevel(logging.DEBUG)
bot_log_logger.addHandler(bot_log_handler)
bot_log_logger.debug('Testing bot handler')

bot.bot.run(config.get("authentication","token"), log_handler=handler)
