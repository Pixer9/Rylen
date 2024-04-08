# Rylen.py
from discord.ext import commands
from dotenv import load_dotenv
from typing import Union
#from utility import config
import discord
import os
 
load_dotenv('config/bot.env')

# Since contents of these files rely on bot.env, they must be imported
# after it is loaded
from config import BotConfig as bc
from logger import logger


class Rylen(commands.Bot):

    required_roles = {
        "Verified": {
            "permissions": discord.Permissions(send_messages=True, read_messages=True)
        },
        "Unverified": {
            "permissions": discord.Permissions(send_messages=False, read_messages=False)
        },
    }

    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            activity=discord.Activity(name="Vibes", type=discord.ActivityType.competing)
        )
        self.cogs_folder = bc.COGS_FOLDER
        self.cogs_dir = self.find_cogs_directory(os.getcwd())

        @self.command(name="load")
        @commands.has_permissions(administrator=True)
        async def load(ctx: commands.Context, extension_name: str) -> None:
            try:
                if '.' in extension_name:
                    await self.load_extension(extension_name)
                    await ctx.send(f"Loaded extension: {extension_name}")
                else:
                    await self.load_extension(f"cogs.{extension_name}")
                    await ctx.send(f"Loaded extension: {extension_name}")
            except commands.ExtensionAlreadyLoaded:
                await ctx.send(f"{extension_name}.py has already been loaded")
            except commands.ExtensionNotFound:
                await ctx.send(f"{extension_name}.py not found.")
            except Exception as e:
                logger.critical(f"Exception: {e} while loading cog.")


        @self.command(name="unload")
        @commands.has_permissions(administrator=True)
        async def unload(ctx: commands.Context, extension_name: str) -> None:
            try:
                if '.' in extension_name:
                    await self.unload_extension(extension_name)
                    await ctx.send(f"Unloaded extension: {extension_name}")
                else:
                    await self.unload_extension(f"cogs.{extension_name}")
                    await ctx.send(f"Unloaded extension: {extension_name}")
            except commands.ExtensionNotFound:
                await ctx.send(f"{extension_name}.py not found.")
            except Exception as e:
                logger.critical(f"Exception: {e} while unloading cog.")


        @self.command(name="reload")
        @commands.has_permissions(administrator=True)
        async def reload(ctx: commands.Context, extension_name: str) -> None:
            try:
                if '.' in extension_name:
                    await self.reload_extension(extension_name)
                    await ctx.send(f"Reloaded extension: {extension_name}")
                else:
                    await self.reload_extension(f"cogs.{extension_name}")
                    await ctx.send(f"Reloaded extension: {extension_name}")
            except commands.ExtensionNotFound:
                await ctx.send(f"{extension_name}.py not found.")
            except Exception as e:
                logger.critical(f"Exception: {e} while reloading cog.")
                

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.remove_command("help")

        logger.info(f"Logged in as {self.user.name}")
        await self.wait_until_ready()

        # For testing required role addition for verify cog
        target_guild_id = 1107119090541285467
        for guild in bot.guilds:
            if guild.id == target_guild_id:
                for role in self.required_roles.keys():
                    await self.ensure_role_exists(guild, role, self.required_roles[role]["permissions"])
                break

        for file_name in os.listdir(self.cogs_dir):
            if file_name.endswith("cog.py"):
                cog_name = file_name[:-3]
                try:
                    await self.load_extension(f"{bc.COGS_FOLDER}.{cog_name}")
                    logger.info(f"Loaded {cog_name}.py")
                except commands.ExtensionAlreadyLoaded:
                    logger.info(f"{cog_name}.py has already been loaded.")
                except commands.ExtensionNotFound:
                    logger.info(f"{cog_name}.py not found.")
                except Exception as e:
                    logger.critical(f"Failed to load {cog_name} cog: {str(e)}")
        try:
            await self.load_extension("select_roles.select_cog")
            logger.info("Loaded select_cog")
        except commands.ExtensionAlreadyLoaded:
            logger.info(f"select_cog.py already loaded.")
        except commands.ExtensionNotFound:
            logger.info(f"select_cog.py not found.")
        except Exception as e:
            logger.critical(f"Exception: {e}")

    
    def find_cogs_directory(self, start_dir: str) -> Union[str, None]:
        for dirpath, dirnames, _ in os.walk(start_dir):
            if self.cogs_folder in dirnames:
                return os.path.join(dirpath, self.cogs_folder)
        return None


    async def ensure_role_exists(self, guild: discord.Guild, role_name: str, permissions: discord.Permissions) -> None:
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try:
                await guild.create_role(name=role_name, permissions=permissions)
                logger.info(f"Created role {role_name} in guild {guild.name}")
            except discord.Forbidden:
                logger.critical(f"Lack permissions to create roles in guild {guild.name}")
            except discord.HTTPException as e:
                logger.critical(f"Failed to create role in guilde {guild.name}: {e}")


if __name__ == "__main__":
    bot = Rylen()
    bot.run(token=bc.DISCORD_API_KEY)