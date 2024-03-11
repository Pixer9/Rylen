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
            logger.info("Lodeaded select_cog")
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


if __name__ == "__main__":
    bot = Rylen()
    print(bc.BOT_NAME)
    bot.run(token=bc.DISCORD_API_KEY)