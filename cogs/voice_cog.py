from discord.ext import commands
from logger import logger
import discord


class VoiceCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    
    @commands.Command(name="join")
    async def join(self, ctx: commands.Context) -> None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            logger.info(f"Joined {channel}")
        else:
            await ctx.send("You need to be in a voice channel to use this command.")

    

    

async def setup(bot: commands.Bot):
    """ Initialize the Voice cog and add it to the bot """
    await bot.add_cog(VoiceCog(bot))