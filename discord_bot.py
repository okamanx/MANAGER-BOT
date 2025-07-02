import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from google import genai
import logging

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
TOKEN = "MTM4OTg5NDE2MzQxNTE3MTA4Mw.GZGpKV.hkWWbPBsSsHzLvHZgsPwP3YOaOlCPxY31vOrS8"
GEMINI_API_KEY = "AIzaSyAA3kTzkmS7aNtexQV8QpS2-zKgpPdpTOc"

client = genai.Client(api_key=GEMINI_API_KEY)

# Set up logging to a file
logging.basicConfig(
    filename="bot_command_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Helper to log command usage
async def log_command(ctx):
    user = ctx.author
    channel = ctx.channel
    command = ctx.command.name if ctx.command else "unknown"
    logging.info(f"User: {user} (ID: {user.id}), Command: {command}, Channel: {channel} (ID: {channel.id})")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await log_command(ctx)
    channel = ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔒 {channel.mention} has been locked.")

@lock.error
async def lock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await log_command(ctx)
    channel = ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔓 {channel.mention} has been unlocked.")

@bot.command()
async def chat(ctx, *, message: str):
    await log_command(ctx)
    """Chat with the bot using Gemini API."""
    try:
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=message
        )
        reply = response.text.strip() if getattr(response, 'text', None) else str(response)
        await ctx.send(f"{ctx.author.mention} {reply}")
    except Exception as e:
        await ctx.send(f"Sorry {ctx.author.mention}, I couldn't process your request. Error: {e}")

if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN is not set in the environment.")
bot.run(TOKEN) 
