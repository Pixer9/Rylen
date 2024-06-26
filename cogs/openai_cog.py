# openai_cog.py
from discord.ext import commands, tasks
from logger import main_logger as logger
#from utility import config
from config import OpenAIConfig as aic, BotConfig as bc
import datetime
import discord
import openai
import csv
import os

# TODO - Clean up OpenAI commands. Parameters are passed, no reason to manually strip them from string

class OpenAICog(commands.Cog):

    chat_log_dir = aic.CHAT_LOG_DIR

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.client = openai.OpenAI(api_key=aic.OPENAI_API_KEY)
        self.model_engine = aic.DEFAULT_ENGINE
        self.temperature = aic.TEMP_DEFAULT_LIMIT
        self.persona = str(next(iter(aic.bot_personalities)))
        self.avail_personas = [persona for persona in aic.bot_personalities]
        self.conversation_memory = aic.DEFAULT_SHOULD_CACHE
        self.cache_size = aic.DEFAULT_CACHE_SIZE
        self.mention_user = aic.MENTION_USER

        self.rylen_triggers = ["Bad bot", "bad bot"]
        self.bot_name = bc.BOT_NAME
        self.csv_field_names = ["user_name", "user_id", "query_message", "response_message", "prompt_tokens", "completion_tokens", "total_tokens"]

        if not os.path.exists(self.chat_log_dir):
            os.makedirs(self.chat_log_dir)


    @commands.command(name="openai_commands")
    async def openai_commands(self, ctx: commands.Context) -> None:
        """ Display an embed that contains all available OpenAI API commands """
        try:
            embed = discord.Embed(title="OpenAI Commands", colour=0x4f2d7f)
            embed.set_footer(text=f"{self.bot_name}: Tarleton Engineering Discord Bot")

            cog = self.bot.get_cog(self.__class__.__name__)
            
            for command in cog.get_commands():
                if command.name == "openai_commands":
                    continue
                embed.add_field(name=command.name, value=command.help, inline=False)
            embed.add_field(name=f"Talk to {self.bot_name}", value=f"Just @{self.bot_name} in the 'rylens-house' channel to chat it up.", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error: {e}")
            logger.critical(f"Exception: {e}")


    @commands.command(name="temperature")
    async def temperature(self, ctx: commands.Context, temp: float) -> None:
        """
            For changing the OpenAI API temperature setting (randomness):
                '!temperature float'
        """
        message_parts = ctx.message.content.split()
        embed = discord.Embed(title="Temperature Updated", colour=0x4f2d7f)
        embed.set_footer(text=f"{self.bot_name}: Tarleton Engineering Discord Bot")
        try:
            temp = float(message_parts[1])
            if len(message_parts) < 2:
                embed.add_field(name="Invalid temperature value", value=f"Please enter a number between {aic.TEMP_LOWER_LIMIT} and {aic.TEMP_UPPER_LIMIT} after the command, ex. - '!temperature 0.7'")
            elif temp < aic.TEMP_LOWER_LIMIT or temp > aic.TEMP_UPPER_LIMIT:
                embed.add_field(name="Invalid temperature value", value=f"Float value must be between {aic.TEMP_LOWER_LIMIT} and {aic.TEMP_UPPER_LIMIT}")
            else:
                self.temperature = temp
                embed.add_field(name="Temperature changed to", value=self.temperature)
            await ctx.send(embed=embed)
        except ValueError:
            embed.add_field(name="Invalid temperature value", value="Please enter a number after the command - ex. '!temperature 0.7'")
            await ctx.send(embed=embed)


    @commands.command(name="personality")
    @commands.has_permissions(administrator=True)
    async def personality(self, ctx: commands.Context, persona: str) -> None:
        """
            For changing the persona of the bot (admins only):
                '!personality persona'
        """
        if not ctx.author.guild_permissions.kick_members:
            return
        
        embed = discord.Embed(title="Personality Updated", colour=0x4f2d7f)
        embed.set_footer(text=f"{self.bot_name}: Tarleton Engineering Discord Bot")

        if persona not in self.avail_personas:
            embed.add_field(name="Invalid persona given", value="Please choose from the available personas.", inline=False)
            embed.add_field(name="Available Personas", value=", ".join(self.avail_personas), inline=False)
        else:
            self.persona = persona
            activity_map = {
                "chad": ("watching", "Your Mom's OnlyFans"),
                "maga": ("watching", "Fox News"),
                "liberal": ("watching", "CNN"),
                "adaptive": ("watching", "The Last of Us")
            }
            activity_type, activity_name = activity_map.get(self.persona, ("listening", "Mi Gente - J Balvin, Willy William"))
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType[activity_type], name=activity_name))
            embed.add_field(name="Personality changed to", value=self.persona)
        
        await ctx.send(embed=embed)


    @commands.command(name="models")
    @commands.has_permissions(administrator=True)
    async def models(self, ctx: commands.Context) -> None:
        """
            Display a list of all available OpenAI Models (admin only)
                '!models'
        """
        if not ctx.author.guild_permissions.kick_members:
            return
        
        embed = discord.Embed(title="Available Models", colour=0x4f2d7f)
        embed.set_footer(text=f"{self.bot_name}: Tarleton Engineering Discord Bot")
        #models = openai.Model.list()
        models = self.client.models.list().data

        for index, model in enumerate(models):
            if index < 25:
                embed.add_field(name=f"Model: {model.id}", value=f"Owner is {model.owned_by}", inline=True)
            else:
                break
        await ctx.send(embed=embed)


    @commands.command(name="change_model")
    @commands.has_permissions(administrator=True)
    async def change_model(self, ctx: commands.Context, model: str) -> None:
        """
            Change the model currently being used (admin only)
                '!change_model model name'
        """
        if not ctx.author.guild_permissions.kick_members:
            return
        
        embed = discord.Embed(title="Model Update", colour=0x4f2d7f)
        embed.set_footer(text=f"{self.bot_nam}: Tarleton Engineering Discord Bot")

        #available_models = openai.Model.list()
        available_models = self.client.models.list().data
        available_models = [model.id for model in available_models]

        if model in available_models:
            previous_model = self.model_engine
            self.model_engine = model
            embed.ad_field(name="Model Change:", value=f"from {previous_model} to {self.model_engine}", inline=False)
        else:
            embed.add_field(name="Invalid model name given", value="Please choose from the available models", inline=False)
            for model in available_models:
                embed.add_field(name=f"Model: {model}", value=None, inline=True)

        await ctx.send(embed=embed)


    @commands.command(name="chat_history")
    @commands.has_permissions(administrator=True)
    async def chat_history(self, ctx: commands.Context) -> None:
        """
            For toggling the memory/cache of the bot
                '!chat_history'
        """
        if not ctx.author.guild_permissions.kick_members:
            return

        self.conversation_memory = not self.conversation_memory
        embed = discord.Embed(title="Memory Cache", colour=0x4f2d7f)
        embed.add_field(name="Remember conversation history?", value="Yes" if self.conversation_memory else "No")
        embed.set_footer(text=f"{self.bot_name}: Tarleton Engineering Discord Bot")
        await ctx.send(embed=embed)


    @commands.command(name="parameters")
    async def parameters(self, ctx: commands.Context) -> None:
        """
            Display all OpenAI API parameters currently being used:
                '!parameters'
        """
        embed = discord.Embed(title="Current OpenAI parameters for API calls", colour=0x4f2d7f)
        embed.set_footer(text=f"{self.bot_name}: Tarleton Engineering Discord Bot")
        embed.add_field(name="Model Engine: ", value=self.model_engine, inline=False)
        embed.add_field(name="Model Persona: ", value=self.persona, inline=False)
        embed.add_field(name="Tepmerature: ", value=self.temperature, inline=False)
        embed.add_field(name="Remember Chat History", value="Yes" if self.conversation_memory else "No")
        await ctx.send(embed=embed)


    @commands.command(name="image")
    @commands.has_permissions(administrator=True)
    async def image(self, ctx: commands.Context, *query) -> None:
        """
            Generate an image using the passed parameters (admin only)
                '!image_query'
        """
        if ctx.channel.id != aic.IMAGE_GENERATION_CHANNEL and not ctx.author.guild_permissions.moderate_members:
            return
        
        image_query = ' '.join(query)
        #print(f"{image_query}")
        try:
            response = self.client.images.generate(
                prompt=image_query,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
            #print(response)
            await ctx.send(image_url)
        except Exception as e:
            logger.critical(f"Exception: {e}")


    async def data_logging(self, message: discord.Message, response) -> None:
        """ Method for logging interaction data (most importantly keeps track of token usage) """

        chat_log_file = os.path.join(self.chat_log_dir, "chat-" + datetime.datetime.now().strftime("%m-%d-%y") + ".csv")
        
        try:
            with open(chat_log_file, mode='a', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=self.csv_field_names)
                writer.writerow({
                    "user_name": message.author.name,
                    "user_id": message.author.id,
                    "query_message": message.content,
                    "response_message": response.choices[0].message.content[:aic.RESPONSE_CHUNK_SIZE],
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                })
        except Exception as e:
            logger.critical(f"Error while writing to chat log file {self.csv_file_name}: {e}")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """ Main interaction method for Rylen """
        if message.author == self.bot.user or message.channel.id not in aic.BOT_ALLOWED_CHANNELS:
            return
        
        if message.attachments:
            custom_query = {"role" : "user", "content" : message.attachments[0].url}
        else:
            custom_query = {"role" : "user", "content" : message.clean_content}

        if message.content in self.rylen_triggers:
            prompt_query = aic.bot_personalities["chad"]
        elif self.bot.user.mentioned_in(message) or any(role.name == "Rylen" for role in message.role_mentions) and not message.mention_everyone:
            async with message.channel.typing():
                prompt_query = aic.bot_personalities[self.persona]
                prompt_query.append(custom_query)
                print(f"\nPrompt query before response: \n{prompt_query}")

                try:
                    response = self.client.chat.completions.create(model=self.model_engine, messages=prompt_query, temperature=self.temperature)
                    response_message = response.choices[0].message.content
                    # Discord messages limited to 2000 characters in size, break into chunks if necessary
                    response_chunks = [response_message[i:i + aic.RESPONSE_CHUNK_SIZE] for i in range(0, len(response_message), aic.RESPONSE_CHUNK_SIZE)]
                    for chunk in response_chunks:
                        if self.mention_user:
                            await message.channel.send(f"{message.author.mention} {chunk}")
                        else:
                            await message.channel.send(chunk)

                    if self.conversation_memory:
                        response_query = {"role" : "assistant", "content" : response_message}
                        aic.bot_personalities[self.persona].append(response_query)
                        if len(aic.bot_personalities[self.persona]) > self.cache_size:
                            del aic.bot_personalities[self.persona][1:3]
                    else:
                        aic.bot_personalities[self.persona].pop()
                    await self.data_logging(message, response)

                except Exception as e:
                    logger.critical(f"Error: {e}")


async def setup(bot: commands.Bot):
    """ Initialize the OpenAI cog and add it to the bot """
    await bot.add_cog(OpenAICog(bot))