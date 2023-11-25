from discord.ext import commands, tasks
from logger import logger
from utility import config
from utility import utils
import discord

VIEW_NAME = "RoleView"

class Select(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Computer Science", emoji="💻", value=str(config.COMPUTER_SCIENCE_ROLE_ID), description="I have never touched grass in my life", default=False
            ),
            discord.SelectOption(
                label="Electrical Engineering", emoji="⚡", value=str(config.ELECTRICAL_ENGINEERING_ROLE_ID), description="I lick 9v batteries", default=False
            ),
            discord.SelectOption(
                label="Cybersecurity", emoji="🕵️", value=str(config.CYBERSECURITY_ROLE_ID), description="**hacker noises intensify** I'm in!", default=False
            ),
            discord.SelectOption(
                label="Civil Engineering", emoji="🏥", value=str(config.CIVIL_ENGINEERING_ROLE_ID), description="I'm not a real engineer", default=False
            ),
            discord.SelectOption(
                label="Environmental Engineering", emoji="♻️", value=str(config.ENV_ENGINEERING_ROLE_ID), description="It's not dirt, it's soil", default=False
            ),
            discord.SelectOption(
                label="Mechanical Engineering", emoji="⚙️", value=str(config.MECH_ENGINEERING_ROLE_ID), description="The engineering life chose me", default=False
            ),
            discord.SelectOption(
                label="Alumni", emoji="🎓", value=str(config.ALUMNI_ROLE_ID), description="*chuckles* I'm in danger!", default=False
            )
        ]
        super().__init__(placeholder="Select your role/major", min_values=1, max_values=None, options=options)


    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            role_id = int(self.values[0])
            role = interaction.guild.get_role(role_id)

            if role is None:
                await interaction.response.send_message("Role not found.", ephemeral=True)
                logger.error(f"Role {role} with {role_id} was not found.")
                return
            
            if role.id in config.ADMIN_ROLE_IDS:
                await interaction.response.send_message("You cannot assign the 'Admin' role.", ephemeral=True)
                return
            
            current_role = next((user_role for user_role in interaction.user.roles if user_role == role.id), None)

            if current_role is not None:
                await interaction.user.remove_roles(current_role)
                await interaction.response.send_message(f"Role {current_role.name} has been removed.", ephemeral=True)
                logger.info(f"Role {current_role.name} has been removed from {interaction.user.name}.")
            else:
                roles_to_remove = [user_role for user_role in interaction.user.roles if not user_role.is_default() and user_role.id not in config.ADMIN_ROLE_IDS and user_role.id not in config.ORG_ROLE_IDS]
                await interaction.user.remove_roles(*roles_to_remove)
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"You have been given the role {role.name} role.", ephemeral=True)
                logger.info(f"{interaction.user.name} has been given the {role.name} role.")

        except Exception as e:
            await interaction.response.send_message(f"An error has occurred, and a log has been generated for an admin. If error persists, please contact Kyle.", ephemeral=True)
            logger.exception(f"Exception: {e}")

class SelectStudentOrg(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label="Computer Society", emoji="💻", value=str(config.COMPUTER_SOCIETY_ROLE_ID), description="Hackathons, Software Engineering, Web Development", default=False
            ),
            discord.SelectOption(
                label="Mechatronics Society", emoji="🤖", value=str(config.MECHATRONICS_SOCIETY_ROLE_ID), description="Robotics, Mechatronics, Rylen go brrrr!", default=False
            ),
            discord.SelectOption(
                label="IEEE", emoji="🛰️", value=str(config.IEEE_SOCIETY_ROLE_ID), description="Network, Develop Professionally, Get Involved!", default=False
            ),
            discord.SelectOption(
                label="Society of Women Engineers", emoji="👩‍🚀", value=str(config.SWE_SOCIETY_ROLE_ID), description="Advocate change, Make an Impact, Leave Your Mark", default=False
            )
        ]
        super().__init__(placeholder="Select your student organization", min_values=1, max_values=None, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            role_id = int(self.values[0])
            role = interaction.guild.get_role(role_id)

            if role is None:
                await interaction.response.send_message("Role not found.", ephemeral=True)
                logger.error(f"Role {role} with {role.id} was not found.")
                return
            
            if role.id in config.ADMIN_ROLE_IDS:
                await interaction.response.send_message("You cannot assign the 'Admin' role.", ephemeral=True)
                return
            
            current_role = next((user_role for user_role in interaction.user.roles if user_role.id == role.id), None)

            if current_role:
                await interaction.user.remove_roles(current_role)
                await interaction.response.send_message(f"Role {current_role.name} has been removed.", ephemeral=True)
                logger.info(f"Role {current_role.name} has been removed from {interaction.user.name}")
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"You have been given the {role.name} role.", ephemeral=True)
                logger.info(f"{interaction.user.name} has been given the {role.name} role.")

        except Exception as e:
            await interaction.response.send_message(f"An error has occurred, and a log has been generated. If the error persists, please contact an Admin of the server.", ephemeral=True)
            logger.exception(f"Exception when assigning org role: {e}")

class SelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Select())
        self.add_item(SelectStudentOrg())
        