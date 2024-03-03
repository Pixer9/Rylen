from discord.ext import commands
from logger import logger
from utility import config
import datetime
import discord
import json
import os

class AdminCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.command(name="admin_commands")
    @commands.has_permissions(administrator=True)
    async def admin_commands(self, ctx: commands.Context) -> None:
        """
            Display all active administrator commands
                '!admin_commands'
        """
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You do not have permission to use this command.")
            return
        try:
            embed = discord.Embed(title="List of all available admin commands:", colour=0x4f2d7f)
            embed.set_footer(text=f"{config.BOT_NAME}: Tarleton Engineering Discord Bot")

            cog = self.bot.get_cog(self.__class__.__name__)

            for command in cog.get_commands():
                if command.name == "admin_commands":
                    continue
                embed.add_field(name=command.name, value=command.help, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except Exception as e:
            logger.critical(f"Error occurred while generating list of admin commands: {e}")


    @commands.command(name="active_bans")
    @commands.has_permissions(administrator=True)
    async def active_bans(self, ctx: commands.Context) -> None:
        """
            Display all active bans on the server
                '!active_bans'
        """
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        guild = ctx.guild
        bans = await guild.bans()

        if not bans:
            await ctx.send("There are no active bans on this server.")
        else:
            ban_list = "\n".join([f"{ban.user.name}#{ban.user.discriminator} ({ban.user.id})" for ban in bans])
            await ctx.send(f"List of banned users:\n{ban_list}")


    @commands.command(name="active_timeouts")
    @commands.has_permissions(administrator=True)
    async def active_timeouts(self, ctx: commands.Context) -> None:
        """
            Display active timeouts on the server:
                '!active_timeouts'
        """
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            server = ctx.guild
            embed = discord.Embed(title="Users in Timeout", colour=0x4f2d7f)
            embed.set_footer(text=f"{config.BOT_NAME}: Tarleton Engineering Discord Bot")
            timeout_members_found = False
            field_count = 0
            async for member in server.fetch_members(limit=None):
                if member.is_timed_out and member.timed_out_until is not None:
                    if field_count < 25:
                        embed.add_field(name=member.display_name, value=f"Timeout expires (UTC): {member.timed_out_until}", inline=True)
                        field_count += 1
                        timeout_members_found = True
                    else:
                        break

            if not timeout_members_found:
                embed.add_field(name=None, value="No users found in timeout.", inline=True)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except Exception as e:
            logger.critical(f"Error occurred while pulling list of timedout members: {e}")


    @commands.command(name="estimate_prune")
    @commands.has_permissions(administrator=True)
    async def estimate_prune(self, ctx: commands.Context, days: int, roles: discord.Role=[]) -> None:
        """
            Returns the number of users who have not logged in within the specified time:
                '!estimate_prune days(required) roles(optional)'
        """
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            guild = ctx.guild
            estimated_number = await guild.estimate_pruned_members(days=days, roles=roles)
            if estimated_number > 0:
                await ctx.send(f"{estimated_number} users have not logged on in the last {days} days and would be pruned.")
            else:
                await ctx.send(f"No users have been inactive within {days} days.")
        except discord.Forbidden:
            logger.critical("You do not have permission to use this command.")
            ctx.send("You do not have permission to use this command.")
        except TypeError:
            logger.critical("Days must be a vaid integer.")
            ctx.send("Days must be a valid integer.")
        except ValueError as ve:
            logger.critical(f"Value error: {ve}")
            ctx.send(f"Value Error: {ve}")
        except discord.HTTPException as he:
            logger.critical(f"HTTP Exception: {he}")
            ctx.send(f"HTTP Exception: {he}")
        except Exception as e:
            logger.critical(f"Error occurred while generating estimated prune list: {e}")
            ctx.send(f"Error occurred while generating estimated prune list: {e}")


    @commands.command(name="prune")
    @commands.has_permissions(administrator=True)
    async def prune(self, ctx: commands.Context, days: int, reason: str=None, roles: discord.Role=[]) -> None:
        """
            Removes users who have not logged in within the specified number of days:
                '!prune days(required) reason(optional) roles(optional)
        """
        if not ctx.author.guild_permissions.kick_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            guild = ctx.guild
            amount_pruned = await guild.prune_members(days=days, roles=roles, reason=reason)
            if amount_pruned > 0:
                await ctx.send(f"{amount_pruned} users have not logged on in the last {days} and have been pruned.")
                logger.info(f"{amount_pruned} users have been pruned by {ctx.author.name}")
            else:
                await ctx.send(f"No users have been inactive within {days} days.")
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except TypeError:
            await ctx.send("Days must be a valid integer.")
        except discord.HTTPException as he:
            await ctx.send(f"HTTP Exception: {he}")
        except Exception as e:
            logger.critical(f"Error occurred while pruning members: {e}")


    @commands.command(name="ban")
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx: commands.Context, user: discord.Member, reason: str=None) -> None:
        """
            Ban the specified user
                '!ban user(required) reason(optional)'
        """
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            _user = None
            for member in ctx.guild.members:
                if member.name == user.name:
                    _user = member
                    break
            if _user is not None:
                await _user.ban(reason=reason)
                await ctx.send(f"{_user.name} has been banned. Reason: {reason}.")
                logger.info(f"{ctx.author.name} has banned {_user.name}.")
            else:
                await ctx.send("User not found.")
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except Exception as e:
            logger.critical(f"Error occurred while trying to ban member {user.name}: {e}")


    @commands.command(name="unban")
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx: commands.Context, user: discord.Member, reason: str=None) -> None:
        """
            Unban the specificed user:
                '!unban user(required) reason(optional)'
        """
        if not ctx.author.guild_permissions.ban_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            banned_users = await ctx.guild.bans()
            user_to_unban = next((ban_entry.user for ban_entry in banned_users if ban_entry.user.name == user.name), None)

            if user_to_unban is not None:
                await ctx.guild.unban(user_to_unban, reason=reason)
                await ctx.send(f"{user_to_unban.name} has been unbanned.")
                logger.info(f"{ctx.author.name} has unbanned {user_to_unban.name}.")
            else:
                await ctx.send("User not found in the ban list.")
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except Exception as e:
            logger.critical(f"Error occurred while trying to unban user: {e}")


    @commands.command(name="kick")
    @commands.has_permissions(administrator=True)
    async def kick(self, ctx: commands.Context, user: discord.Member, reason: str=None) -> None:
        """
            Kick the specified user from the server:
                '!kick user(required) reason(optional)'
        """
        if not ctx.author.guild_permissions.kick_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            _user = None
            for member in ctx.guild.members:
                if member.name == user.name:
                    _user = member
                    break

            if _user is not None:
                await _user.kick(reason=reason)
                await ctx.send(f"{_user.name} has been kicked from the server.")
                logger.info(f"{ctx.author.name} has kicked user {_user.name} from the server.")
            else:
                await ctx.send("User not found.")
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except Exception as e:
            logger.critical(f"Error occurred while trying to kick member: {e}")


    @commands.command(name="timeout")
    @commands.has_permissions(administrator=True)
    async def timeout(self, ctx: commands.Context, user: discord.Member, duration: int, reason: str=None) -> None:
        """
            Timeout the specified user for a specific duration in minutes:
                '!timeout user(required) duration(required) reason(optional)'
        """
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You do not have permisson to use this command.")
            return
        
        try:
            _user = None
            for member in ctx.guild.members:
                if member.name == user.name:
                    _user = member
                    break

            if _user is not None:
                current_time = datetime.datetime.now().astimezone()
                timeout = datetime.timedelta(minutes=duration)

                await _user.timeout(current_time + timeout, reason=reason)
                await ctx.send(f"{_user.name} has been put in timeout for {duration} minutes. Until {current_time + timeout}")

                logger.info(f"{ctx.author.name} has put {_user.name} in timeout for {duration} minutes.")
            else:
                await ctx.send("User not found.")
        except discord.Forbidden:
            await ctx.send("You do not have permission to use this command.")
        except Exception as e:
            logger.critical(f"Error occurred while trying to put member in timeout: {e}")


    @commands.command(name="untimeout")
    @commands.has_permissions(administrator=True)
    async def untimeout(self, ctx: commands.Context, user: discord.Member) -> None:
        """
            Remove the timeout of a user:
                '!untimeout user(required)'
        """
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            _user = None
            for member in ctx.guild.members:
                if member.name == user.name:
                    _user = member
                    break
            
            if _user is not None:
                #await _user.timeout(until=None)
                await _user.edit(timed_out_until=None)
                await ctx.send(f"{_user.name} has had their timeout removed.")
                logger.info(f"{ctx.author.name} has removed user {_user.name} from timeout.")
            else:
                await ctx.send("User not found.")
        except Exception as e:
            logger.error(f"Error occurred while trying to remove user from timeout: {e}")


    @commands.command(name="retrieve_message_data")
    @commands.has_permissions(administrator=True)
    async def retrieve_message_data(self, ctx: commands.Context, channel_id: int, message_id: int) -> None:
        """
            Retrieve all pertinent data on a specific message and write it to file:
                '!retrieve_message_data channel_id(required) message_id(required)'
        """
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("You do not have permission to use this command.")
            return
        
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send("Channel not found.")
                return
            
            message = await channel.fetch_message(message_id)
            if not message:
                await ctx.send("Message not found.")
                return
            
            message_data = {
                "message_id": message.id,
                "content": message.content,
                "is_embed": bool(message.embeds),
                "embed_content": [],
                "author": {
                    "id": message.author.id,
                    "name": message.author.name,
                    "discriminator": message.author.discriminator
                },
                "timestamp": message.created_at.isoformat(),
                "emojis_data": {}
            }

            if message.embeds:
                embed = message.embeds[0]
                embed_data = {
                    "title": embed.title,
                    "type": embed.type,
                    "description": embed.description,
                    "url": embed.url,
                    "colour": str(embed.colour) if embed.colour else None,
                    "image": str(embed.image.url) if embed.image else None,
                    "thumbnail": str(embed.thumbnail.url) if embed.thumbnail else None,
                    "fields": [{"name": field.name, "value": field.value} for field in embed.fields],
                    "footer": {
                        "text": embed.footer.text if embed.footer else None,
                        "icon_url": str(embed.footer.icon.url) if embed.footer and embed.footer.icon_url else None
                    },
                    "timestamp": embed.timestamp.isoformat() if embed.timestamp else None
                }
                message_data["embed_content"].append(embed_data)

            for reaction in message.reactions:
                async for user in reaction.users():
                    emoji_str = str(reaction.emoji)
                    if emoji_str not in message_data["emojis_data"]:
                        message_data["emojis_data"][emoji_str] = []
                    message_data["emojis_data"][emoji_str].append(str(user.id))

            file_name = "message_data.json"
            with open(file_name, mode='a') as f:
                json.dump(message_data, f, indent=4)

            await ctx.send(file=discord.File(file_name))
            os.remove(file_name)

        except discord.NotFound:
            await ctx.send("Message not found.")
        except Exception as e:
            logger.critical(f"Error occurred while parsing desired message: {e}")


    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        else:
            await ctx.send(f"Error occured: {error}")


async def setup(bot: commands.Bot):
    """ Initalize AdminCog an add it to the bot """
    await bot.add_cog(AdminCog(bot))