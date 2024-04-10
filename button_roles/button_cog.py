# button_cog.py
from discord.ext import commands, tasks
from .role_view import RoleView
from utility import config
from logger import main_logger as logger

class ButtonRoles(commands.Cog, name="Button Roles"):
    """ Creates buttons that assign roles """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        #self.roles_message.start()

    @commands.Cog.listenere()
    async def on_ready(self) -> None:
        """ Called when the cog is loaded """
        self.bot.add_view(RoleView())

    @tasks.loop(hours=24)
    async def roles_message(self) -> None:
        try:
            channel = self.bot.get_channel(config.ROLES_CHANNEL_ID)
            roles_message = None
            if channel:
                async for message in channel.history(limit=50):
                    if message.author == self.bot.user:
                        roles_message = message
                        break
            
            if roles_message:
                await roles_message.edit(view=RoleView())
            else:
                await channel.send("Choose your role below:", view=RoleView())
        except Exception as e:
            logger.error(f"Error encountered while generating button roles: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ButtonRoles(bot))