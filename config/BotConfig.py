import os

# Name of the bot
BOT_NAME = os.getenv('BOT_NAME')

# Github Repository where source code is located
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')

# Email of bot owner - used in some header requests
EMAIL = os.getenv('EMAIL')

# Discord API Key
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')

# Directory name where cogs are stored
COGS_FOLDER = 'cogs'

# Main .env file where secrets are kept
ENV_FILE = 'cogs/bot.env'