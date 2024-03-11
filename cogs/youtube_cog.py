# youtube_cog.py
from googleapiclient.discovery import build
from discord.ext import commands, tasks
#from utility import config
from config import YouTubeConfig as ytc
import discord

class YouTubeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.youtube = build('youtube', 'v3', developerKey=ytc.YOUTUBE_API_KEY)

    @commands.command(name="youtube_commands")
    async def youtube_commands(self, ctx: commands.Context) -> None:
        """ Display an embed that contains all available YouTube bot commands """
        embed = discord.Embed(title="YouTube Commands", colour=0xFF0000)
        embed.set_footer(text="Information retrieved from YouTube using publicly available API")
        embed.add_field(name="!youtube_search [query_parameters]", value="Search YouTube for the given query parameters and return the top two results.", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="youtube_search")
    async def youtube_search(self, ctx: commands.Context, *query) -> None:
        """ Search YouTube API given user query parameters """
        search_query = ' '.join(query)
        request = self.youtube.search().list(
            part='snippet',
            videoSyndicated='any',
            channelType='any',
            videoCaption='any',
            q=search_query,
            type='video',
            maxResults=2
        )
        response = request.execute()
        videos = response.get('items', [])

        if videos:
            for video in videos:
                video_id = video['id']['videoId']
                video_title = video['snippet']['title']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                await ctx.send(f"{video_title}: {video_url}")
        else:
            await ctx.send("No videos found.")

async def setup(bot: commands.Bot):
    """ Initialize the YouTubeCog and add it toe the bot """
    await bot.add_cog(YouTubeCog(bot))
