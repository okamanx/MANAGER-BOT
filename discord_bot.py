import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

# --- Minimal Flask server for Render ---
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start the web server in a separate thread
Thread(target=run).start()
# --- End of Flask server setup ---

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

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

if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN is not set in the environment.")

bot.run(TOKEN)
