# weather_cog.py
from discord.ext import commands, tasks
from datetime import datetime
#from utility import config
from config import WeatherConfig as wc
from utility import forecast
from logger import logger
import discord

# TODO - have check_weather_alerts send notifications for active severe thunderstorm or tornado warning

class WeatherCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._severe_weather_alerts = []
        #self.check_weather_alerts.start()


    @commands.command(name="weather_commands")
    async def weather_commands(self, ctx: commands.Context) -> None:
        embed = discord.Embed(title="Weather Commands", colour=0x00A8F3)
        embed.set_footer(text="Information retrieved from weather.gov using publicly available API")

        cog = self.bot.get_cog(self.__class__.__name__)

        for command in cog.get_commands():
            if command.name == "weather_commands":
                continue
            embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="forecast")
    async def forecast(self, ctx: commands.Context, *args) -> None:
        """
            Retrieve and display the weather forecast from passed city, state
                '!forecast Stephenville, TX'
        """
        client_location = " ".join(args)
        daily_forecast, channel = await self.get_forecast_data(ctx, client_location, forecast.get_forecast)

        if daily_forecast:
            for data in daily_forecast[:3]:
                await self.forecast_embed(channel, client_location, data)
        else:
            await channel.send("Please input a valid location.")


    @commands.command(name="hourly")
    async def hourly(self, ctx: commands.Context, *args) -> None:
        """
            Retrieve and display hourly weather forecast from passed city, state
                '!hourly Fort Worth, TX'
        """
        client_location = " ".join(args)
        hourly_forecast, channel = await self.get_forecast_data(ctx, client_location, forecast.get_forecast_hourly)

        if hourly_forecast:
            await self.forecast_hourly_embed(channel, client_location, hourly_forecast)
        else:
            await channel.send("Please input a valid location.")


    @commands.command(name="alerts")
    async def alerts(self, ctx: commands.Context, *args) -> None:
        """
            Retrieve and display any weather alerts for the passed city, state
                '!alerts Dallas, TX'
        """
        client_location = " ".join(args)
        alerts, channel = await self.get_forecast_data(ctx, client_location, forecast.get_county_alerts)

        if alerts:
            await self.weather_alert(channel, alerts, client_location)
        else:
            await channel.send("Please enter a valid area.")


    async def get_forecast_data(self, ctx: commands.Context, location: str, fetch_function) -> None:
        """ Helper method for querying the Weather.gov API """
        channel = self.bot.get_channel(ctx.message.channel.id)
        wait = await channel.send("Pulling data.....")
        forecast_data = fetch_function(location)

        await wait.delete()
        return forecast_data, channel
    

    async def forecast_embed(self, channel, location: str, data: dict) -> None:
        """ Build the embed for displaying the weather forecast """
        embed = discord.Embed(title=data['name'], description="Forecast for " + location, colour=0x4285F4)
        embed.set_thumbnail(url=data['icon'])
        embed.set_footer(text="Information retrieved from weather.gov using publicly availabe API")
        embed.add_field(name="Weather", value=data['shortForecast'], inline=False)
        embed.add_field(name="Precipitation", value=str(data['probabilityOfPrecipitation']['value'])+"%", inline=False)
        embed.add_field(name="Temperature", value=str(data['temperature']) + " F", inline=False)
        embed.add_field(name="Wind", value=data['windSpeed'] + " " + data['windDirection'], inline=True)
        await channel.send(embed=embed)


    async def forecast_hourly_embed(self, channel, location: str, forecast: dict) -> None:
        """ Build the embed for displaying the hourly weather forecast """
        embed = discord.Embed(title="Hourly Forecast for " + location, colour=0x4285F4)
        embed.set_footer(text="Information retrieved from weather.gov using publicly available API")

        for data in forecast[:4]:
            time_str = data['startTime'][len("0000-00-00T") : len("0000-00-00T00:00")]
            time = datetime.strptime(time_str, '%H:%M').strftime('%I:%M %p')
            weather = data['shortForecast']
            temperature = str(data['temperature']) + " F"
            wind = data['windSpeed'] + " " + data['windDirection']
            precip = str(data['probabilityOfPrecipitation']['value']) + "%"
            embed.add_field(name=time, value=f"Weather: {weather}\nPrecipitation: {precip}\tTemperature: {temperature}\nWind: {wind}", inline=False)
        await channel.send(embed=embed)


    async def weather_alert(self, channel, alerts, area: str) -> None:
        """ Build the embed for displaying active weather alerts """
        embed = discord.Embed(title=f"Active weather alerts for {area}", colour=0xFF7F50)
        embed.set_footer(text="Information retrieved from weather.gov using publicly available API")

        if alerts:
            for alert in alerts[:3]:
                if alert['properties']['event'].__contains__("Warning") or alert['properties']['event'].__contains__("Tornado"):
                    embed.add_field(name=alert['properties']['headline'], value=alert['properties']['description'][:1024], inline=False)

        else:
            embed.add_field(name="No Alerts", value=f"There are currently no active weather alerts in {area}. Visit weather.gov for official information.", inline=False)
        await channel.send(embed=embed)


    @tasks.loop(minutes=1)
    async def check_weather_alerts(self) -> None:
        """ Coroutine to check for any active severe weather alerts """
        print(self._severe_weather_alerts)
        client_location = "Stepehenville, TX"
        channel = self.bot.get_channel(wc.SEVERE_WEATHER_ALERTS_CHANNEL)
        alerts = forecast.get_county_alerts(client_location)
        active_alerts = []

        if alerts:
            for alert in alerts[:3]:
                active_alert = alert['properties']['event']
                active_alerts.append(active_alert)

                if active_alert.__contains__("Severe ThunderStorm Warning") or active_alert.__contains__("Tornado Warning"):
                    if active_alert in self._severe_weather_alerts:
                        pass
                    else:
                        logger.info(f"Severe weather alert detected. Post {alert['properties']['headline']} to {wc.SEVERE_WEATHER_ALERTS_CHANNEL}")
                        self._severe_weather_alerts.append(alert['properties']['event'])
                        embed = discord.Embed(title=f"Severe Weather Alert for {client_location}", colour=0xFF7F50)
                        embed.set_footer(text="Information retrieved from weather.gov using publicly available API")
                        embed.add_field(name=alert['properties']['headline'], value=alert['properties']['description'][:1024], inline=False)
                        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    """ Initialize the WeatherCog and add it to the bot """
    await bot.add_cog(WeatherCog(bot))
