# verify_cog.py
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from email.mime.text import MIMEText
from logger import main_logger as logger
from config import BotConfig as bc
from typing import Dict
import requests
import discord
import random
import json
import os


class VerifyCog(commands.Cog):

    smtp_scopes = [
        "https://www.googleapis.com/auth/gmail.send"
    ]

    TEST_CHANNEL = 1107119090541285470 # BTG server - general channel - remove after testing

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.code_length = 6 # make this configurable
        self.verification_codes: Dict[int, dict] = self.load_verification_codes() # {user_id: {verification_code: code, user_email: email, display_name: user_display_name, global_name: user_discord_name, attempts: int}}
        self.attempt_tracker: Dict[int, dict] = self.load_attempts() # {user_id: {"attempts": int, "cooldown_until": datetime}}

        self.mailgun_api_key = os.getenv('MAILGUN_API_KEY')
        self.mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        self.email_domain = os.getenv('EMAIL_DOMAIN')

    @commands.command(name="test_email")
    @commands.has_permissions(administrator=True)
    async def test_email(self, ctx: commands.Context) -> None:
        """ For testing email functionality """
        if ctx.channel.id != self.TEST_CHANNEL:
            await ctx.send("This command can only be used in the designated test channel.")
            return
        
        try:
            button_verify = VerifyButton()
            button_enter_code = EnterCodeButton()
            button_enter_code.disabled = True

            view = discord.ui.View()
            view.add_item(button_verify)
            view.add_item(button_enter_code)

            embed = discord.Embed(
                title="Email Verification Test",
                description="Greetings! I am a moderator bot from the Tarleton Engineering Discord server. To be able to interact with this server, we require that you first verify your Tarleton email address. Please verify your email by clicking the 'Enter Email' button below.",
                color=0x00ff00
            )
            embed.set_footer(text="⚠️ Warning: Abuse of this submission form will result in an immediate server ban!")

            message = await ctx.author.send(embed=embed, view=view)

            self.verification_codes[ctx.author.id] = {
                "verification_code": None,
                "user_email": None,
                "display_name": ctx.author.display_name,
                "global_name": ctx.author.name,
                "attempts": 0,
                "message_id": message.id,
                "channel_id": message.channel.id,
                "enter_code_enabled": False,
                "guild_id": ctx.author.guild.id,
                "is_verified": False
            }

        except discord.HTTPException as http_excep:
            logger.critical(f"Error: {http_excep} when sending verification DM")
            await ctx.send(f"Failed to send DM. Please ensure your DMs are open. Error: {http_excep}")

    
    @commands.command(name="notify_users")
    @commands.has_permissions(administrator=True)
    async def notify_users(self, ctx: commands.Context) -> None:
        """
            Pull the current list from verification_codes.json and parse the current guild members.
            If the user does not have a verified email on record, notify them of the new rule and
            explain the new requirement.
        """
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        for member in ctx.guild.members:
            if member.bot:
                continue

            user_verification_info = self.verification_codes.get(str(member.id))
            if not user_verification_info or not user_verification_info.get("is_verified"):
                try:
                    button_verify = VerifyButton()
                    button_enter_code = EnterCodeButton()
                    button_enter_code.disabled = True

                    view = discord.ui.View()
                    view.add_item(button_verify)
                    view.add_item(button_enter_code)

                    embed = discord.Embed(
                        title="Email Verification",
                        description="Attention: We are implementing a new rule that will require all users to have a verified Tarleton email on record before they can interact with the server. Members will have 30 days from the time of this notice to verify their Tarleton email address. If you do not provide one, all existing roles/permissions will be removed and you will be given the 'Unverified' role, where you will not be able to interact with or view channels on the server until you provide a valid email.\n\nTo start, please click the 'Enter Email' button below and follow the instructions provided to you by Rylen.\n\nIf you have since graduated and no longer have access to a valid Tarleton email, or if you encounter any issues with this form, please get in touch with an admin as soon as possible.",
                        color=0xFF0000
                    )

                    embed.set_footer(text="⚠️ Warning: Abuse of this submission form will result in an immediate server ban!")

                    message = await member.send(embed=embed, view=view)

                    self.verification_codes[member.id] = {
                        "verification_code": None,
                        "user_email": None,
                        "display_name": member.display_name,
                        "global_name": member.name,
                        "attempts": 0,
                        "message_id": message.id,
                        "channel_id": message.channel.id,
                        "enter_code_enabled": False,
                        "guild_id": member.guild.id,
                        "is_verified": False,
                    }
                    logger.info(f"User {member.name} - {member.display_name} - {member.id} has been notified")
                except discord.Forbidden:
                    logger.warning(f"Could not send DM to {member.name} - {member.display_name} - {member.id}")
                

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """ Send a verifiation button/request to new users via DM """
        try:
            unverified_role = discord.utils.get(member.guild.roles, name="Unverified")

            if unverified_role:
                await member.add_roles(unverified_role)
                logger.info(f"Added 'Unverified' role to {member.display_name}.")
            else:
                logger.warning(f"'Unverified' role not found in guild {member.guild.name}")

            button_verify = VerifyButton()
            button_enter_code = EnterCodeButton()
            button_enter_code.disabled = True

            view = discord.ui.View()
            view.add_item(button_verify)
            view.add_item(button_enter_code)

            embed = discord.Embed(
                title="Email Verification",
                description="Greetings! I am a moderator bot from the Tarleton Engineering Discord server. To be able to interact with this server, we require that you first verify your Tarleton email address. Please verify your email by clicking the 'Enter Email' button below.",
                color=0x00ff00
            )

            embed.set_footer(text="⚠️ Warning: Abuse of this submission form will result in an immediate server ban!")

            message = await member.send(embed=embed, view=view)

            self.verification_codes[member.id] = {
                "verification_code": None,
                "user_email": None,
                "display_name": member.display_name,
                "global_name": member.name,
                "attempts": 0,
                "message_id": message.id,
                "channel_id": message.channel.id,
                "enter_code_enabled": False,
                "guild_id": member.guild.id,
                "is_verified": False,
            }

        except discord.HTTPException as http_excep:
            logger.critical(f'Error: {http_excep} while trying to send email verification message.')


    async def send_verification_email(self, email: str, code: str) -> None:
        """ Send verification email to the new user """
        email_contents = f"""\
            Your verification code is: {code}
        """

        message = MIMEText(email_contents)
        message['Subject'] = "Verification Code"
        message['From'] = self.smtp_email
        message['To'] = email

        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp_server:
            smtp_server.login(self.smtp_email, self.smtp_password)
            smtp_server.sendmail(self.smtp_email, email, message.as_string())
            logger.info(f"Verification email sent to: {email}")


    async def send_email(self, email: str, code: str) -> None:
        """ Send verification email to the new user """
        email_contents = f"Your verification code is: {code}"

        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages",
                auth=("api", self.mailgun_api_key),
                data={
                    "from": f"{bc.BOT_NAME}<mailgun@{self.mailgun_domain}>",
                    "to": [email],
                    "subject": "Verification Code",
                    "text": email_contents
                }
            )
            logger.info(f"Mailgun Domain: {self.mailgun_domain}")
            logger.info(f"Mailgun API Key: {self.mailgun_api_key}")
            logger.info(f"Mailgun response: {response.status_code}: {response.text}")
            logger.info(f"Verification email successfully sent to {email}")
            return True
        except requests.exceptions.RequestException as req_excep:
            logger.warning(f"Failed to send verification email to {email}: {req_excep}")
            return False


    async def generate_verification_code(self) -> str:
        """ Generate a n-digit verification code. """
        return ''.join([str(random.randint(0, 9)) for _ in range(self.code_length)])
    

    async def check_attempts_and_cooldown(self, user_id: int) -> bool:
        """
            Check if the user has exceeded their maximum attempt limit or is in the cooldown period
            Returns True if the user is allowed to make an attempt, False otherwise
        """
        user_attempts = self.attempt_tracker.get(user_id, {"attempts": 0, "cooldown_until": datetime.min})

        if datetime.now() < user_attempts["cooldown_until"]:
            return False
        
        if user_attempts["attempts"] >= 3 and datetime.now() >= user_attempts["cooldown_until"]:
            self.attempt_tracker[user_id] = {"attempts": 0, "cooldown_until": datetime.min}

        return True
    

    async def record_attempt(self, user_id: int) -> None:
        """
            Record an attempt. If the attempt limit is reached, start a cooldown period
        """
        max_attempts = 3
        cooldown_duration = timedelta(minutes=10)

        if user_id not in self.attempt_tracker:
            self.attempt_tracker[user_id] = {"attempts": 1, "cooldown_until": datetime.min}
        else:
            self.attempt_tracker[user_id]["attempts"] += 1

            if self.attempt_tracker[user_id]["attempts"] >= max_attempts:
                self.attempt_tracker[user_id]["cooldown_until"] = datetime.now() + cooldown_duration


    def load_verification_codes(self) -> None:
        """ Load verification codes from a file. """
        try:
            with open("verification_codes.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
        
    
    def load_attempts(self) -> Dict[int, dict]:
        """ Load attempts from verification_codes per user """
        if not self.verification_codes:
            return {}
        else:
            user_attempts = {}
            for user in self.verification_codes.keys():
                
                user_attempts[user] = {
                    "attempts": self.verification_codes[user]["attempts"],
                    "cooldown_until": None
                }
            return user_attempts

    
    async def save_verification_codes(self) -> None:
        """ Save the current state of verification codes to a file. """
        logger.debug(f"Saving verification codes: {self.verification_codes}")
        with open("verification_codes.json", "w") as file:
            json.dump(self.verification_codes, file, indent=4)

    
    async def check_verification_code(self, user_id: int, code: int) -> bool:
        """ 
            Compare the user given code vs bot generated code. If correct,
            allow access and save verification status. If incorrect, log an
            attempt and check for attempt limits.
        """
        user_info = self.verification_codes.get(user_id)

        if user_info and user_info['verification_code'] == code:
            self.verification_codes[user_id]['is_verified'] = True
            self.verification_codes[user_id]['verified_at'] = datetime.now().strftime("%m-%d-%YT%H:%M:%S")
            self.attempt_tracker[user_id] = {"attempts": 0, "cooldown_until": datetime.min}
            await self.save_verification_codes()
            return True
        else:
            await self.record_attempt(user_id)
            return False
        

    async def enable_code_entry_button(self, user_id: int) -> None:
        """ 
            If valid email received, enable the secondary button for verification
            code entry
        """
        user_info = self.verification_codes.get(user_id)
        
        if user_info and user_info["message_id"] and user_info["channel_id"]:
            channel = await self.bot.fetch_channel(user_info["channel_id"])
            if channel:
                try:
                    message = await channel.fetch_message(user_info['message_id'])
                    view = discord.ui.View()
                    button_verify = VerifyButton()
                    button_enter_code = EnterCodeButton()
                    button_enter_code.disabled = False

                    view.add_item(button_verify)
                    view.add_item(button_enter_code)

                    embed = discord.Embed(
                        title="Email Verification Test",
                        description = "Email sent. Please click the 'Enter Verification Code' button below to enter/validate your code.",
                        color=0x00ff00
                    )
                    embed.set_footer(text="⚠️ Warning: Abuse of this submission form will result in an immediate server ban!")

                    await message.edit(embed=embed, view=view)
                    user_info["enter_code_enabled"] = True
                except Exception as e:
                    logger.critical(f"Error updating DM message for user {user_id}: {e}")
            else:
                logger.warning(f"Unable to locate user: {user_id}")
        else:
            logger.warning(f"Unable to validate user_info: {user_id} - {self.verification_codes[user_id]}")

    
    async def delete_verification_message(self, user_id: int) -> None:
        """ Delete the verification message for a user after successful verification or if it's no longer valid """
        user_info = self.verification_codes.get(user_id)
        if user_info and user_info.get("message_id") and user_info.get("channel_id"):
            try:
                channel = self.bot.get_channel(user_info["channel_id"])
                if channel:
                    message = await channel.fetch_message(user_info["message_id"])
                    await message.delete()
                    logger.info(f"Deleted verification message for user ID {user_id}.")
            except discord.NotFound:
                logger.warning(f"Message or channel not found for user ID {user_id}")
            except discord.Forbidden:
                logger.warning(f"Lack permissions to delete message for user ID {user_id}")
            except discord.HTTPException as e:
                logger.critical(f"HTTP exception when trying to delete message for user ID {user_id}: {str(e)}")
        else:
            logger.warning(f"No verification message found for user ID {user_id} to delete")


class VerifyButton(discord.ui.Button):

    def __init__(self) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="Enter Email")

    async def callback(self, interaction: discord.Interaction):
        """ Callback for button click - sends modal for user interaction """
        modal = EmailModal()
        await interaction.response.send_modal(modal)


class EnterCodeButton(discord.ui.Button):

    def __init__(self) -> None:
        super().__init__(style=discord.ButtonStyle.success, label="Enter Verification Code")

    async def callback(self, interaction: discord.Interaction):
        """ Callback for entering verification code button - sends modal for user interaction"""
        modal = CodeModal()
        await interaction.response.send_modal(modal)


class EmailModal(discord.ui.Modal, title="Email Verification"):

    email = discord.ui.TextInput(label="Email Address", placeholder="Enter your email here...", required=True, max_length=40)

    async def on_submit(self, interaction:discord.Interaction) -> None:
        """ Callback for Modal submission """
        cog = interaction.client.get_cog("VerifyCog")

        if not await cog.check_attempts_and_cooldown(interaction.user.id):
            await interaction.response.send_message("You have exceeded the maximum attempt limit. Please try again later.", ephemeral=True)
            return
        

        email = self.email.value
        if not email.endswith(cog.email_domain):
            cog.record_attempt(interaction.user.id)
            await interaction.response.send_message("Must be a valid Tarleton email. Please try again.", ephemeral=True)
            return


        code = await cog.generate_verification_code()

        if interaction.user.id in cog.verification_codes:
            user_entry = cog.verification_codes[interaction.user.id]
            user_entry.update({
                "verification_code": code,
                "user_email": self.email.value,
            })
            if 'attempts' in user_entry:
                user_entry.update({
                    "attempts": user_entry["attempts"] + 1
                })
        else:
            cog.verification_codes[interaction.user.id] = {
                "verification_code": code, 
                "user_email": self.email.value, 
                "display_name": interaction.user.display_name, 
                "global_name": interaction.user.name,
                "attempts": 0,
            }
        await cog.save_verification_codes()

        #await cog.send_verification_email(self.email.value, code)
        email_status = await cog.send_email(self.email.value, code)

        if email_status:
            cog.attempt_tracker[interaction.user.id] = {"attempts": 0, "cooldown_until": datetime.min}
            await cog.enable_code_entry_button(interaction.user.id)
            await interaction.response.send_message("Verification code has been sent, please check the email you provided. Click 'Enter Verification Code' button to enter the code.", ephemeral=True)
        else:
            await interaction.response.send_message("There was a problem encountered while sending the email, please try again. If the problem persists, please contact an admin.")

class CodeModal(discord.ui.Modal, title="Verification Code"):

    code = discord.ui.TextInput(label="Verification Code", placeholder="Enter verification code here...", required=True, max_length=12)

    async def on_submit(self, interaction:discord.Interaction) -> None:
        """ Callback for Code submission """
        cog = interaction.client.get_cog("VerifyCog")

        code = self.code.value
        
        if not await cog.check_verification_code(interaction.user.id, code):
            await interaction.response.send_message("The verification code you provided is incorrect. Please try again.")

            return
        
        user_data = cog.verification_codes.get(interaction.user.id)
        if user_data and "guild_id" in user_data:
            guild = cog.bot.get_guild(user_data["guild_id"])
            if guild:
                member = guild.get_member(interaction.user.id)
                if member:
                    unverified_role = discord.utils.get(guild.roles, name="Unverified")
                    verified_role = discord.utils.get(guild.roles, name="Verified")
                    if unverified_role:
                        await member.remove_roles(unverified_role)
                    if verified_role:
                        await member.add_roles(verified_role)
                    logger.info(f"{interaction.user.display_name} with ID {interaction.user.id} has successfully validated their email.")
                    await cog.delete_verification_message(interaction.user.id)
                    await interaction.response.send_message("You have successfully validated your email. You can now interact with users on the server and view/send messages in the channels.", ephemeral=True)
                else:
                    logger.warning(f"Could not find user {interaction.user.display_name} in the server. User ID: {interaction.user.id}")
                    await interaction.response.send_message("Could not find you in the server.", ephemeral=True)
            else:
                logger.warning(f"Unable to retrieve guild. User {interaction.user.name} with ID {interaction.user.id} was unable to verify their email.")
                await interaction.response.send_message("Verification process encountered an issue.", ephemeral=True)


async def setup(bot: commands.Bot):
    """ Initialize the VerifyCog and add it to the bot """
    await bot.add_cog(VerifyCog(bot))