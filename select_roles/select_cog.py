from discord.ext import commands, tasks
from .select_role import SelectView
from logger import main_logger as logger
from utility import config
import discord

class SelectRoles(commands.Cog, name="Select Roles"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.roles_message.start()


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Called when the cog is loaded """
        self.bot.add_view(SelectView())


    @commands.command(name="select_roles")
    @commands.has_permissions(administrator=True)
    async def select_roles(self, ctx: commands.Context) -> None:
        """ Command to display the role selection menu """
        view = SelectView()
        embed = await self.build_embed()
        await ctx.send(embed=embed, view=view)


    @tasks.loop(hours=24)
    async def roles_message(self) -> None:
        try:
            logger.info("Updating the roles message select...")
            channel = self.bot.get_channel(config.ROLES_CHANNEL_ID)
            roles_message = None
            if channel:
                async for message in channel.history(limit=50):
                    if message.author == self.bot.user:
                        roles_message = message
                        break

            embed = await self.build_embed()

            if roles_message:
                await roles_message.edit(embed=embed, view=SelectView())
            else:
                await channel.send(embed=embed, view=SelectView())
        except Exception as e:
            logger.critical(f"Error occurred while trying to update roles message: {e}")


    async def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Choose Your Major", description="If you do not see your major or organization listed below, please contact an admin to have it added.", colour=0x4f2d7f)
        embed.add_field(name="Major Role", value="Major Roles are limited to one per user. If you are a dual major, you will need to select just one from the list as selecting additional roles will cause the current one to be removed. If you accidentally remove your major role and want to reselect it, choose a different major on the list and then reselect the desired role.", inline=False)
        embed.add_field(name="Student Org Role", value="Users may have multiple student organizational roles assigned at a time. These roles do not affect the role that is assigned based on your major. These will help students find out who is involved with what and potentially who to contact for information about the organization.", inline=False)
        embed.add_field(name="Notes", value="This role embed message resets every 24 hours. Your roles will remain unchanged, but you may notice that your selected major/org is no longer chosen in the fields below. Do not be alarmed, this is on purpose. If you encounter any bugs with the assignment, DM Kyle and let him know.", inline=False)
        embed.set_footer(text=f"{config.BOT_NAME}: Tarleton Engineering Discord Bot")
        return embed
    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(SelectRoles(bot))