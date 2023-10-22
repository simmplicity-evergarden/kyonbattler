import os
import configparser
import logging
import json

# Setup logging
logger = logging.getLogger('bot')

config = configparser.ConfigParser(converters={'list':json.loads})
config.read(os.path.join(os.path.dirname(__file__),'settings.ini'))

# Making this a dedicated function to be manually called elsewhere rather than making 
# a custom "setter and saver" combo function
# because I can't be assed to make the logic for it
def save_settings():
	with open(os.path.join(os.path.dirname(__file__),'settings.ini'), 'w') as configfile:
		config.write(configfile)

# Appends item to config[section, setting]
# Doesn't do any type checks
def setting_list_append(section: str, setting: str, item):
	setting_val = config.getlist(section, setting)
	setting_val.append(item)
	config[section][setting] = json.dumps(setting_val)

# Removes item from config[section, setting] if item exists
# Returns if the item previously existed
def setting_list_remove(section: str, setting: str, item):
	setting_val = config.getlist(section, setting)
	if item in setting_val:
		setting_val.remove(item)
		config[section][setting] = json.dumps(setting_val)
		return True
	else:
		return False
