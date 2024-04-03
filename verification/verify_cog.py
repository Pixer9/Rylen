# verify_cog.py
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from email.mime.text import MIMEText
from logger import logger
from typing import Dict
import smtplib
import discord
import random
import json

TEST_CHANNEL = 1107119090541285470 # BTG server - general channel - remove after testing

class VerifyCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.code_length = 6 # make this configurable
        self.verification_codes = self.load_verification_codes() # {user_id: (code, email, user_display_name, user_discord_name)}
        self.attempt_tracker: Dict[int, dict] = {} # {user_id: {"attempts": int, "cooldown_until": datetime}}

        self.smtp_email = "your_email@gmail.com" # pull email from bot.env
        self.smtp_password = "your_app_password" # pull password from bot.env
        self.smtp_server = "smtp.gmail.com" # make this configurable
        self.smtp_port = 587 # make this configurable

        self.email_domain = "tarleton.edu" # make this configurable


    @commands.command(name="test_email")
    async def test_email(self, ctx: commands.Context) -> None:
        """ For testing email functionality """
        if ctx.channel.id != TEST_CHANNEL:
            await ctx.send("This command can only be used in the designated test channel.")
            return
        
        try:
            button = VerifyButton()
            view = discord.ui.View()
            view.add_item(button)

            embed = discord.Embed(
                title="Email Verification Test",
                description = "Please click the button below to proceed with email verification.",
                color=0x00ff00
            )
            embed.set_footer(text="Warning: Abuse of this submission form will result in an immediate server ban!")

            await ctx.author.send(embed=embed, view=view)

        except discord.HTTPException as http_excep:
            logger.critical(f"Error: {http_excep} when sending verification DM")
            await ctx.send(f"Failed to send DM. Please ensure your DMs are open. Error: {http_excep}")


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """ Send a verifiation button/request to new users via DM """
        try:
            button = VerifyButton()
            view = discord.ui.View()
            view.add_item(button)
            #await member.send("Welcome! Please verify your email by clicking the button below.", view=view)

            embed = discord.Embed(
                title="Email Verification",
                description="Please verify your email by clicking the button below.",
                color=0x00ff00
            )

            embed.set_footer(text="Warning: Abuse of this submission form will result in an immediate server ban!")

            await member.send(embed=embed, view=view)
        except discord.HTTPException as http_excep:
            logger.critical(f'Error: {http_excep} while trying to send email verification message.')



    async def send_verification_email(self, email: str, code: str) -> None:
        """ Send verification email to the new user """
        sender_email = self.smtp_email
        sender_password = self.smtp_password
        receiver_email = email

        message = MIMEMultipart("alternative")
        message["Subject"] = "Verification Code"
        message["From"] = sender_email
        message["To"] = receiver_email

        text = f"""\
            Your verification code is: {code}
        """

        part = MIMEText(text, "plain")
        message.attach(part)

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())


    def generate_verification_code(self) -> str:
        """ Generate a n-digit verification code. """
        return ''.join([str(random.randint(0, 9)) for _ in range(self.code_length)])
    

    def check_attempts_and_cooldown(self, user_id: int) -> bool:
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
    
    def record_attempt(self, user_id: int) -> None:
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
        
    
    def save_verification_codes(self) -> None:
        """ Save the current state of verification codes to a file. """
        with open("verification_codes.json", "w") as file:
            json.dump(self.verification_codes, file, indent=4)


class VerifyButton(discord.ui.Button):

    def __init__(self) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="Verify Email")

    async def callback(self, interaction: discord.Interaction):
        """ Callback for button click - sends modal for user interaction """
        modal = EmailModal()
        await interaction.response.send_modal(modal)


class EmailModal(discord.ui.Modal, title="Email Verification"):

    email = discord.ui.TextInput(label="Email Address", placeholder="Enter your email here...", required=True, max_length=40)

    async def on_submit(self, interaction:discord.Interaction) -> None:
        """ Callback for Modal submission """
        cog = interaction.client.get_cog("VerifyCog")

        if not cog.check_attempts_and_cooldown(interaction.user.id):
            await interaction.response.send_message("You have exceeded the maximum attempt limit. Please try again later.", ephemeral=True)
            return
        

        email = self.email.value
        if not email.endswith(cog.email_domain):
            cog.record_attempt(interaction.user.id)
            await interaction.response.send_message("Must be a valid Tarleton email. Please try again.", ephemeral=True)
            return


        code = cog.generate_verification_code()
        cog.verification_codes[interaction.user.id] = (code, self.email.value, interaction.user.name, interaction.user.display_name)
        cog.save_verification_codes()
        
        await cog.send_verification_email(self.email.value, code)

        cog.attempt_tracker[interaction.user.id] = {"attempts": 0, "cooldown_until": datetime.min}
        await interaction.response.send_message("A verification code has been sent to your email. Please enter it here.", ephemeral=True)



async def setup(bot: commands.Bot):
    """ Initialize the TwitchCog and add it to the bot """
    await bot.add_cog(VerifyCog(bot))