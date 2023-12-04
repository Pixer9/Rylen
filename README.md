# Rylen
Discord chat bot that utilizes OpenAI API, Weather API, Twitch API, and YouTube API to delivered tailored responses to user queries.

OpenAI allows for image generation based on prompt query and development of customized 'personalities' for tailored responses.

Weather API allows for users to request the hourly weather forecast, 3-day forecast, or any active alerts that may exist within the passed query (e.g. Dallas, TX). Functionality also exists to turn on active scanning of the API,
where the bot will query the weather.gov API every 'x' minutes looking for active severe weather alerts. If an active severe weather alert is found (e.g. Severe Thunderstorm Warning or Tornado Warning), it will immediately send
a message embed to a pre-designated channel alerting the server of the alert.

Twitch API allows for users to add their Twitch usernames to a 'watch list', where the bot will actively scan this list every so often to see if that user is currently live. If the user it live, it will generate and send a chat
message embed to the pre-designated channel alerting the server that a user has gone live. It will provide details such as when the user went live, what activity the user is participating in, and a link to their live feed.

YouTube API allows for users to perform YouTube searches from within Discord. Users can search for specific channels or videos, and a message embed is then generated and sent to the channel in which the command was invoked containing 
a list of up to 3 items located from the search parameters. 

!==================== IMPORTANT =========================!

Upon installation, the config.py will need to be configured before the bot can be run. The config.py contains important information such as:

- Channel and Role IDs specific to the Discord Guild
- API keys/client secrets for all the necessary APIs
- OpenAI model configurations such as:
  - Bot personalities
  - Model engine
  - Model temperature bounds
  - 
