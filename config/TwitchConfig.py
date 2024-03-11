import os

# Retrieve your client ID from your .env
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

# Retrieve your client ID from your .env
TWITCH_SECRET = os.getenv("TWITCH_SECRET")

# Isolate Twitch cog functionality to a specific channel
TWITCH_ISOLATE = True
TWITCH_LIVE_CHANNEL_ID = 1141927486834348042 # 1123769232728002570 -> self-promotions channel

# Current list of users being tracked
TWITCH_LIVE_USERS_LIST = ['AlcAndrea']

