# twitch_cog.py
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from typing import Dict
from twitchAPI.helper import first
from logger import logger
#from utility import config
from config import TwitchConfig as tc
import discord

class TwitchCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.twitch = Twitch(tc.TWITCH_CLIENT_ID, tc.TWITCH_SECRET)
        self.notified_live: Dict[str, list] = {}
        self.twitch_users_to_watch = tc.TWITCH_LIVE_USERS_LIST
        #self.check_twitch_streams.start()


    @commands.command(name="twitch_commands")
    async def twitch_commands(self, ctx: commands.Context) -> None:
        """ Display an embed that contains all available Twitch bot commands """
        if ctx.channel.id != tc.TWITCH_LIVE_CHANNEL_ID:
            return
        
        embed = discord.Embed(title="Twitch Commands", colour=0x9146FF)
        embed.set_footer(text="Information retreived using publicly available Twitch API")

        cog = self.bot.get_cog(self.__class__.__name__)

        for command in cog.get_commands():
            if command.name == "twitch_commands":
                continue
            embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="live_twitch")
    async def live_twitch(self, ctx: commands.Context) -> None:
        """
            Get a list of all live Twitch streams of user added accounts
                '!live_twitch'
        """
        if ctx.channel.id != tc.TWITCH_LIVE_CHANNEL_ID:
            return
        
        if self.notified_live:
            for user, details in self.notified_live.items():
                embed = discord.Embed(title="Twitch Live Streams", description=None, colour=0x9146FF)
                embed.set_footer(text="Information retrieved using publicly available Twitch API")
                game, title, stream_url, thumbnail_url = details
                embed.set_thumbnail(url=thumbnail_url)
                embed.add_field(name="User", value=user, inline=False)
                embed.add_field(name="Game", value=game, inline=False)
                embed.add_field(name="Title", value=title, inline=False)
                embed.add_field(name="Stream URL", value=stream_url, inline=False)
                await ctx.send(embed=embed)
        else:
            await ctx.send("There are no live Twitch stream at this time.")


    @commands.command(name="add_twitch")
    async def add_twitch(self, ctx: commands.Context) -> None:
        """
            Add your Twitch account to the Live Watch List for livestream notifications
                '!add_twitch twitchUsername'
        """
        if ctx.channel.id != tc.TWITCH_LIVE_CHANNEL_ID:
            return
        
        message = ctx.message.content[len("!add_twitch") + 1:]
        message_parts = message.split()
        twitch_user = message_parts[0]

        try:
            user_data = await first(self.twitch.get_users(logins=[twitch_user]))
            if user_data is None:
                await ctx.send(f"Unable to locate user {twitch_user}. Check spelling and try again.")
                return
            
            twitch_user = user_data.display_name
            print(f"https://www.twitch.tv/{twitch_user}")
            if twitch_user in self.twitch_users_to_watch:
                await ctx.send(f"User {twitch_user} is already in the list of Twitch users.")
            else:
                self.twitch_users_to_watch.append(twitch_user)
                await ctx.send(f"Successfully added {user_data.display_name} to list of Twitch users.")
        except Exception as e:
            await ctx.send(f"Unable to locate user {twitch_user}. Check spelling and try again.")
            logger.critical(f"Error occurred while trying to add Twitch user: {e}")


    @commands.command(name="list_twitch")
    async def list_twitch(self, ctx: commands.Context) -> None:
        """
            Display a list of all Twitch users being watched for live notifications
                '!list_twitch'
        """
        if ctx.channel.id != tc.TWITCH_LIVE_CHANNEL_ID:
            return
        
        embed = discord.Embed(title="Twitch Account Watch List", colour=0x9146FF)
        embed.set_footer(text="Information retrieved using publicly available Twitch API")

        if self.twitch_users_to_watch:
            for user in self.twitch_users_to_watch:
                embed.add_field(name=user, value="https://www.twitch.tc/{user}", inline=False)
        else:
            await ctx.send("There are no users on the live watch list.")
        await ctx.send(embed=embed)


    @commands.command(name="twitch_search")
    async def twitch_search(self, ctx: commands.Context) -> None:
        """ Manually search specific Twitch users """
        pass


    @tasks.loop(minutes=5)
    async def check_twitch_streams(self) -> None:
        """ Check for live Twitch streams """
        await self.authenticate_twitch()

        for user in self.twitch_users_to_watch:
            user_data = await first(self.twitch.get_users(logins=[user]))
            user_id = user_data.id

            stream_info = await first(self.twitch.get_streams(user_id=[user_id], stream_type='live'))
            if stream_info:
                logger.info(f"User name: {user}\tUser ID: {user_id}\tis LIVE")
                game = stream_info.game_name
                title = stream_info.title
                stream_url = f"https://www.twitch.tv/{user}"

                if user not in self.notified_live:
                    self.notified_live[user] = [game, title, stream_url, stream_info.thumbnail_url]
                    channel = self.bot.get_channel(tc.TWITCH_LIVE_CHANNEL_ID)
                    await channel.send(f"{user} is love on Twitch playing {game}: {title}\n{stream_url}")
            if stream_info is None and user in self.notified_live:
                del self.notified_live[user]
        

    async def authenticate_twitch(self) -> None:
        """ Authenticate the Twitch App """
        await self.twitch.authenticate_app([])


async def setup(bot: commands.Bot):
    """ Initialize the TwitchCog and add it to the bot """
    await bot.add_cog(TwitchCog(bot))