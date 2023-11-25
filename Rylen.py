# Rylen.py
from discord.ext import commands
from logger import logger
from utility import config
import discord
import os

COGS_FOLDER = "cogs"

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

        for file_name in os.listdir(COGS_FOLDER):
            if file_name.endswith(".py"):
                cog_name = file_name[:-3]
                try:
                    await self.load_extension(f"{COGS_FOLDER}.{cog_name}")
                    logger.info(f"Loaded {cog_name}.py")
                except Exception as e:
                    logger.exception(f"Failed to load {cog_name} cog: {str(e)}")
        try:
            await self.load_extension("select_roles.select_cog")
            logger.info("Lodeaded select_cog")
        except Exception as e:
            logger.exception(f"Exception: {e}")

if __name__ == "__main__":
    bot = Rylen()
    bot.run(config.discord_api_key)