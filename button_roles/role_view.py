# role_view.py
from utility import utils
from utility import config
import discord

VIEW_NAME = "RoleView"

class RoleView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def handle_click(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """ Logic for role assignment when button is clicked """
        role_id = int(button.custom_id.split(":")[-1])
        role = interaction.guild.get_role(role_id)

        assert isinstance(role, discord.Role)

        current_role = None
        for user_role in interaction.user.roles:
            if user_role.id == role.id:
                current_role = user_role
                break

        if current_role is not None:
            if role.id == current_role.id:
                await interaction.user.remove_roles(current_role)
                await interaction.response.send_message(f"{current_role.name} role has been removed.", ephemeral=True)
            else:
                await interaction.response.send_message(f"You already have the role {current_role.name}. Please remove it bly clicking its associated button first.", ephemeral=True)
        else:
            roles_to_remove = []
            for user_role in interaction.user.roles:
                if user_role.is_default() or user_role.id in config.ADMIN_ROLE_IDS:
                    continue
                roles_to_remove.append(user_role)

            for user_role in roles_to_remove:
                await interaction.user.remove_roles(user_role)
            
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"You have been given the {role.name} role.", ephemeral=True)

    @discord.ui.button(label="Computer Science", emoji="", style=discord.ButtonStyle.primary, custom_id=utils.custom_id(VIEW_NAME, config.COMPUTER_SCIENCE_ROLE_ID), row=1)
    async def computer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    @discord.ui.button(label="Electrical Engineering", emoji="", style=discord.ButtonStyle.primary, custom_id=utils.custom_id(VIEW_NAME, config.ELECTRICAL_ENGINEERING_ROLE_ID), row=1)
    async def electrical_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    @discord.ui.button(label="Cybersecurity", emoji="", style=discord.ButtonStyle.danger, custom_id=utils.custom_id(VIEW_NAME, config.CYBERSECURITY_ROLE_ID), row=1)
    async def cyber_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    @discord.ui.button(label="Civil Engineering", emoji="", style=discord.ButtonStyle.primary, custom_id=utils.custom_id(VIEW_NAME, config.CIVIL_ENGINEERING_ROLE_ID), row=2)
    async def civil_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    @discord.ui.button(label="Environmental Engineering", emoji="", style=discord.ButtonStyle.success, custom_id=utils.custom_id(VIEW_NAME, config.ENV_ENGINEERING_ROLE_ID), row=2)
    async def environmental_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    @discord.ui.button(label="Mechanical Engineering", emoji="", style=discord.ButtonStyle.primary, custom_id=utils.custom_id(VIEW_NAME, config.MECH_ENGINEERING_ROLE_ID), row=2)
    async def mechanical_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    @discord.ui.button(label="Alumni", emoji="", style=discord.ButtonStyle.primary, custom_id=utils.custom_id(VIEW_NAME, config.ALUMNI_ROLE_ID), row=3)
    async def alumni_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, button)

    