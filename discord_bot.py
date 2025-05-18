import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

// ... existing code ...

# Get token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("No token found. Please set the DISCORD_TOKEN environment variable.")

bot.run(TOKEN)  # Use the token from environment variable
