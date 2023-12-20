# moderation_cog.py
from discord.ext import commands, tasks
from datetime import datetime
from logger import logger
from utility import config
import requests
import discord
import re


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.calendar_events = []
        self.last_scrape = None
        self.update_calendar.start()


    @commands.command(name="information")
    async def information(self, ctx: commands.Context) -> None:
        """ For retrieving bot information related to Rylen """
        embed = discord.Embed(title="Information", description=f"Information about {config.BOT_NAME}, libraries, and used APIs", colour=0x006400)
        embed.set_footer(text=f"{config.BOT_NAME}: Tarleton Engineering Discord Bot")
        embed.add_field(name=f"{config.BOT_NAME}", value=f"{config.BOT_NAME} is an open source Discord bot created for fun by students from the Tarleton Mayfield College of Engineering. You are free to use this bot on your own server, all we ask is that you reference where bot originated.", inline=False)
        embed.add_field(name=f"{config.BOT_NAME} Bot GitHub", value=f"{config.GITHUB_REPOSITORY}", inline=False)
        embed.add_field(name="OpenAI API", value="https://openai.com/blog/openai-api - Paid Subscription Key Required", inline=False)
        embed.add_field(name="National Weather Service API", value="https://api.weather.gov/ - Public Domain", inline=False)
        embed.add_field(name="Discord API", value="https://discordpy.readthedocs.io/en/stable/api.html", inline=False)
        embed.add_field(name="Twitch API", value="https://pytwitchapi.readthedocs.io/en/stable/index.html", inline=False)
        embed.add_field(name="YouTube API", value="https://developers.google.com/youtube/v3", inline=False)
        embed.add_field(name="Geopy.py", value="https://pypi.org/projects/geopy/", inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="rylen_help")
    async def rylen_help(self, ctx: commands.Context) -> None:
        """ For displaying bot functionality/commands """
        embed = discord.Embed(title="Command Center", colour=0x4f2d7f)
        embed.set_footer(text=f"{config.BOT_NAME}: Tarleton Engineering Discord Bot")
        embed.add_field(name="!information", vaue=f"Information about {config.BOT_NAME}, libraries, and used APIs", inline=False)
        embed.add_field(name="!twitch_commands", value="Shows current list of available Twitch API commands", inline=False)
        embed.add_field(name="!weather_commands", value="Shows current list of available Weather API commands", inline=False)
        embed.add_field(name="!youtube_commands", value="Shows current list of available YouTube API commands", inline=False)
        embed.add_field(name="openai_commands", value="Shows current list of available OpenAI API commands", inline=False)
        await ctx.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """ Greet new members when they join """
        guild = member.guild
        channel = discord.utils.get(guild.text_channels, name="general")
        if channel is not None:
            logger.info(f"User {member.name} has joined the server.")
            await channel.send(f"{member.display_name} has arrived!")
    

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """ Keep track of when a user leaves """
        logger.info(f"User {member.display_name} has left the server. {member.name}")

        # Check if the member was kicked
        if isinstance(member, discord.Member) and member.guild.me.guild_permissions.view_audit_log:
            async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                if entry.target == member:
                    # Member was kicked, log and send embed
                    await self.handle_kick(member, entry.user)
                    break

    
    async def handle_kick(self, member: discord.Member, kicked_by: discord.User) -> None:
        """ Handles and reports kick event """
        logger.info(f"User {member.display_name} was kicked from the server by {kicked_by.display_name}")

        admin_channel = member.guild.get_channel(config.ADMIN_ONLY_CHANNEL)

        if admin_channel:
            embed = discord.Embed(
                title="User Kicked: {member.name}",
                description=f"User {member.mention} has been kicked from the server.",
                color=discord.Color.orange()
            )

            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="Kicked by", value=kicked_by.mention, inline=False)

            admin_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User, banned_by: discord.User) -> None:
        """ Keep track of if a user gets banned """
        logger.info(f"User {user} has been banned from {guild}")

        admin_channel = guild.get_channel(config.ADMIN_ONLY_CHANNEL)
    
        embed = discord.Embed(
            title=f"User Banned: {user.name}",
            description=f"User {user.mention} has been banned from the server",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Banned by", value=banned_by.mention, inline=False)

        # Send notification to admin channel
        await admin_channel.send(embed=embed)


    async def add_event(self, date: str, time: str, title: str, location: str, url: str) -> None:
        """ Helper function for adding events to list of live calendar events """
        self.calendar_events.append((date, time, title, location, url))


    async def show_calendar(self) -> None:
        """ Display calenar if there are valid events available """
        if self.calendar_events:
            embed = await self.build_calendar_embed()
            channel = self.bot.get_channel(config.CALENDAR_CHANNEL_ID)
            await channel.send(embed=embed)
        else:
            logger.error("Unable to create calendar embed. Calendar Events is empty.")
            await channel.send("Unable to create calendar embed. Calendar Events is empty.")


    async def build_calendar_embed(self) -> discord.Embed:
        """ Build the embed used for displaying the calendar events """
        embed = discord.Embed(title="Upcoming Events:", colour=0x4f2d7f, timestamp=datetime.now())
        embed.set_footer(text=f"{config.BOT_NAME}: Tarleton Engineering Discord Bot")
        events_added = 0

        if self.calendar_events:
            for date, time, title, location, url in self.calendar_events:
                if events_added >= 5:
                    break
                embed.add_field(name=title, value=f"When: {date}\tat\t{time}\nWhere: {location}\nOfficial Calendar: {url}", inline=False)
                events_added += 1
        else:
            embed.add_field(name="There are no listed events", value="LiveWhale may be down or there is an issue with the code. Check server status.")
        return embed
    

    @tasks.loop(hours=24)
    async def update_calendar(self) -> None:
        """ Update the posted calendar once every 24 hours """
        logger.info("Updating calendar events...")
        
        await self.scrape_events()

        calendar_message = None
        channel = self.bot.get_channel(config.CALENDAR_CHANNEL_ID)
        async for message in channel.history(limit=50):
            if message.embeds:
                if message.author == self.bot.user and message.embeds[0].title.__contains__("Upcoming Events:"):
                    calendar_message = message
                    break
        if calendar_message:
            updated_embed = await self.build_calendar_embed()
            await calendar_message.edit(embed=updated_embed)
        else:
            await self.show_calendar()
        logger.info("Calendar events successfully updated.")


    async def scrape_events(self) -> None:
        """ For scraping events off Tarleton's Official LiveWhale Calendar """
        try:
            self.calendar_events = []
            response = requests.get(config.TARGET_URL, timeout=3)
            response.raise_for_status()
            loaded_data = response.json()

            for event in loaded_data:
                title = event['title']
                title = title.replace("&amp;", "&")
                if re.match(r'^\d{1,2}:\n{2} ]APap]\.M\. - \d{1,2}:\d{2} [APap]\.M\.#', title):
                    continue
                if title == "Closed":
                    continue
                if title.lower().__contains__("grades"):
                    continue
                if event['event_types_audience']:
                    if "Students" not in event['event_types_audience']:
                        continue
                if event['event_types_campus']:
                    if "Stephenville" not in event['event_types_campus']:
                        continue
                if (event['date2_time'] or event['date_time']) and event['date']:
                    if event['date_time']:
                        formatted_time = event['date_time']
                    else:
                        formatted_time = event['date2_time']
                    formatted_date = event['date']
                else:
                    date = datetime.strptime(event['date_utc'], "%Y-%m-%d %H:%M:%S")
                    formatted_date = date.strtime("%B %d")
                    formatted_time = date.strftime("%I:%M%p").lower()
                location = event['location'] if event['location'] else "Unknown"
                url = event['url']
                self.last_scrape = datetime.now()

                await self.add_event(formatted_date, formatted_time, title, location, url)

        except requests.exceptions.RequestException as request_exc:
            logger.exception(f"Requestion Exception: {request_exc}")
        except (ValueError, KeyError) as error:
            logger.exception(f"JSON Error: {error}")
        except Exception as e:
            logger.exception(f"Error: {e}")


async def setup(bot: commands.Bot):
    """ Initialize the ModerationCog and add it to the bot """
    await bot.add_cog(ModerationCog(bot))