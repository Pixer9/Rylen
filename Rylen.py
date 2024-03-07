# Rylen.py
from discord.ext import commands
from logger import logger
from utility import config
import discord
import os


class Rylen(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            activity=discord.Activity(name="Vibes", type=discord.ActivityType.competing)
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.remove_command("help")

        logger.info(f"Logged in as {self.user.name}")
        await self.wait_until_ready()

        for file_name in os.listdir(config.COGS_FOLDER):
            if file_name.endswith(".py"):
                cog_name = file_name[:-3]
                try:
                    await self.load_extension(f"{config.COGS_FOLDER}.{cog_name}")
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

    
    @commands.Cog.listener()
    @commands.has_permissions(administrator=True)
    async def load(self, ctx: commands.Context, extension_name: str) -> None:
        try:
            await self.load_extension(f"cogs.{extension_name}")
            await ctx.send(f"Loaded extension: {extension_name}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"{extension_name}.py has already been loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"{extension_name}.py not found.")
        except Exception as e:
            logger.critical(f"Exception: {e} while loading cog.")

    
    @commands.Cog.listener()
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx: commands.Context, extension_name: str) -> None:
        try:
            await self.unload_extension(f"cogs.{extension_name}")
            await ctx.send(f"Unloaded extension: {extension_name}")
        except commands.ExtensionNotFound:
            await ctx.send(f"{extension_name}.py not found.")
        except Exception as e:
            logger.critical(f"Exception: {e} while unloading cog.")

    
    @commands.Cog.listener()
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx: commands.Context, extension_name: str) -> None:
        try:
            await self.reload_extension(f"cogs.{extension_name}")
            await ctx.send(f"Reloaded extension: {extension_name}")
        except commands.ExtensionNotFound:
            await ctx.send(f"{extension_name}.py not found.")
        except Exception as e:
            logger.critical(f"Exception: {e} while reloading cog.")


if __name__ == "__main__":
    bot = Rylen()
    bot.run(token=config.DISCORD_API_KEY)