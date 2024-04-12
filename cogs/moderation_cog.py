# moderation_cog.py
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from logger import main_logger as logger
from logger import user_logger
from typing import Dict
#from utility import config
from config import ModerationConfig as mc, BotConfig as bc
import requests
import discord
import re


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.calendar_events = []
        self.last_scrape = None
        self.update_calendar.start()
        self.invites_before_join ={}
        bot.loop.create_task(self.load_invites())


    async def load_invites(self) -> Dict[str, dict]:
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invites_before_join[guild.id] = {invite.code: invite for invite in invites}
            except discord.HTTPException as http_excep:
                logger.critical(f"Failed to fetch invites for {guild.name}: {str(http_excep)}")


    @commands.command(name="information")
    async def information(self, ctx: commands.Context) -> None:
        """ For retrieving bot information related to Rylen """
        embed = discord.Embed(title="Information", description=f"Information about {bc.BOT_NAME}, libraries, and used APIs", colour=0x006400)
        embed.set_footer(text=f"{bc.BOT_NAME}: Tarleton Engineering Discord Bot")
        embed.add_field(name=f"{bc.BOT_NAME}", value=f"{bc.BOT_NAME} is an open source Discord bot created for fun by students from the Tarleton Mayfield College of Engineering. You are free to use this bot on your own server, all we ask is that you reference where bot originated.", inline=False)
        embed.add_field(name=f"{bc.BOT_NAME} Bot GitHub", value=f"{bc.GITHUB_REPOSITORY}", inline=False)
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
        embed.set_footer(text=f"{bc.BOT_NAME}: Tarleton Engineering Discord Bot")
        embed.add_field(name="!information", value=f"Information about {bc.BOT_NAME}, libraries, and used APIs", inline=False)
        embed.add_field(name="!twitch_commands", value="Shows current list of available Twitch API commands", inline=False)
        embed.add_field(name="!weather_commands", value="Shows current list of available Weather API commands", inline=False)
        embed.add_field(name="!youtube_commands", value="Shows current list of available YouTube API commands", inline=False)
        embed.add_field(name="!openai_commands", value="Shows current list of available OpenAI API commands", inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="current_invites")
    async def current_invites(self, ctx: commands.Context) -> None:
        """ Display current tracked invites to admin """
        embed = discord.Embed(title="Invites", color=0x4f2d7f)
        for guild_id, invites in self.invites_before_join.items():
            for invite_code, invite in invites.items():
                guild_name = await self.bot.fetch_guild(guild_id)
                inviter = invite.inviter
                uses = invite.uses
                embed.add_field(name=guild_name, value=f"Invite Code: {invite_code}\nInviter: {inviter}\nUses: {uses}")
        #await ctx.send(f"Current Invites: \n{self.invites_before_join}")
        await ctx.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """ Greet new members when they join """
        guild = member.guild
        guild_invites = await member.guild.invites()

        channel = discord.utils.get(guild.text_channels, name="general")
        admin_channel = member.guild.get_channel(mc.ADMIN_ONLY_CHANNEL)

        if channel is not None:
            user_logger.info(f"User {member.name} has joined the server.")
            await channel.send(f"{member.display_name} has arrived!")

        for invite in guild_invites:
            if invite.uses > self.invites_before_join[member.guild.id][invite.code].uses:
                await admin_channel.send(f"{member.name} joined by using invite {invite.code} created by {invite.inviter}")
                break
        self.invites_before_join[member.guild.id] = {invite.code: invite for invite in guild_invites}
    

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """ Keep track of when a user leaves """
        user_logger.info(f"User {member.display_name} has left the server. {member.name}")

        # Check if the member was kicked
        if isinstance(member, discord.Member) and member.guild.me.guild_permissions.view_audit_log:
            async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                if entry.target == member:
                    # Member was kicked, log and send embed
                    await self.handle_kick(member, entry.user)
                    break

    
    async def handle_kick(self, member: discord.Member, kicked_by: discord.User) -> None:
        """ Handles and reports kick event """
        user_logger.info(f"User {member.display_name} was kicked from the server by {kicked_by.display_name}")

        admin_channel = member.guild.get_channel(mc.ADMIN_ONLY_CHANNEL)

        if admin_channel:
            embed = discord.Embed(
                title="User Kicked: {member.name}",
                description=f"User {member.mention} has been kicked from the server.",
                color=discord.Color.orange()
            )

            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.add_field(name="Kicked by", value=kicked_by.mention, inline=False)

            admin_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """ Keep track of if a user gets banned """
        user_logger.info(f"User {user} has been banned from {guild}")

        admin_channel = guild.get_channel(mc.ADMIN_ONLY_CHANNEL)
    
        embed = discord.Embed(
            title=f"User Banned: {user.name}",
            description=f"User {user.mention} has been banned from the server",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        #embed.add_field(name="Banned by", value=banned_by.mention, inline=False)

        # Send notification to admin channel
        await admin_channel.send(embed=embed)

    
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite) -> None:
        """ Log the creation of an invite and relative data """
        user_logger.info(f"User {invite.inviter} created an invite at {invite.created_at} for guild {invite.guild.name}")

        # Check to see if on testing server
        if invite.guild.id == mc.TEST_SERVER:
            channel_id = mc.TEST_CHANNEL
        else:
            channel_id = mc.ADMIN_ONLY_CHANNEL

        admin_channel = invite.guild.get_channel(channel_id)
        timestamp = invite.created_at.strftime('%m-%d-%Y %H:%M:%S UTC')
        expiration_timedelta = timedelta(seconds=invite.max_age)
        expires_days = expiration_timedelta.days
        expires_hours, expires_minutes = divmod(expiration_timedelta.seconds // 60, 60)

        embed = discord.Embed(
            title=f"Invite Created by: {invite.inviter}",
            description="",
            color=discord.Color.red()
        )
        embed.add_field(name="Display Name", value=invite.inviter.display_name, inline=False)
        embed.add_field(name="Created At", value=timestamp, inline=False)
        embed.add_field(name="Expiration", value=f"{expires_days}d {expires_hours}h {expires_minutes}m", inline=False)

        self.invites_before_join[invite.guild.id] = {invite.code: invite}

        await admin_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """ Check for direct messages to the bot """
        if message.guild is not None:
            return
        
        logger.info(f"{message.author.name} sent {message.content}")


    async def add_event(self, date: str, time: str, title: str, location: str, url: str) -> None:
        """ Helper function for adding events to list of live calendar events """
        self.calendar_events.append((date, time, title, location, url))


    async def show_calendar(self) -> None:
        """ Display calenar if there are valid events available """
        if self.calendar_events:
            embed = await self.build_calendar_embed()
            channel = self.bot.get_channel(mc.CALENDAR_CHANNEL_ID)
            await channel.send(embed=embed)
        else:
            logger.error("Unable to create calendar embed. Calendar Events is empty.")
            await channel.send("Unable to create calendar embed. Calendar Events is empty.")


    async def build_calendar_embed(self) -> discord.Embed:
        """ Build the embed used for displaying the calendar events """
        embed = discord.Embed(title="Upcoming Events:", colour=0x4f2d7f, timestamp=datetime.now())
        embed.set_footer(text=f"{bc.BOT_NAME}: Tarleton Engineering Discord Bot")
        events_added = 0

        if self.calendar_events:
            for date, time, title, location, url in self.calendar_events:
                if events_added >= 5:
                    break
                embed.add_field(name=title, value=f"When: {date}\tat\t{time}\nWhere: {location}\nOfficial Calendar: {url}", inline=False)
                events_added += 1
        else:
            embed.add_field(name="There are no listed events", value="LiveWhale may be down or the server may be experiencing connectivity issues.")
        return embed
    

    @tasks.loop(hours=24)
    async def update_calendar(self) -> None:
        """ Update the posted calendar once every 24 hours """
        logger.info("Updating calendar events...")
        
        await self.scrape_events()

        calendar_message = None
        channel = self.bot.get_channel(mc.CALENDAR_CHANNEL_ID)
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
            response = requests.get(mc.TARGET_URL, timeout=3)
            response.raise_for_status()
            loaded_data = response.json()

            for event in loaded_data:
                title = event['title']
                title = title.replace("&amp;", "&")
                if re.match(r'^\d{1,2}:\d{2} [APap]\.M\. - \d{1,2}:\d{2} [APap]\.M\.$', title):
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
                    formatted_date = date.strftime("%B %d")
                    formatted_time = date.strftime("%I:%M%p").lower()
                location = event['location'] if event['location'] else "Unknown"
                url = event['url']
                self.last_scrape = datetime.now()

                await self.add_event(formatted_date, formatted_time, title, location, url)

        except requests.exceptions.RequestException as request_exc:
            logger.critical(f"Requestion Exception: {request_exc}")
        except (ValueError, KeyError) as error:
            logger.critical(f"JSON Error: {error}")
        except Exception as e:
            logger.critical(f"Error: {e}")


async def setup(bot: commands.Bot):
    """ Initialize the ModerationCog and add it to the bot """
    await bot.add_cog(ModerationCog(bot))
