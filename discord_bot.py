import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
from flask import Flask
import threading
from datetime import datetime

# Load environment variables
load_dotenv()

# Debug logging for token
TOKEN = os.getenv('DISCORD_TOKEN')
print("Token exists:", bool(TOKEN))
print("Token length:", len(TOKEN) if TOKEN else 0)
print("Token first few chars:", TOKEN[:10] + "..." if TOKEN else "None")

if not TOKEN:
    raise ValueError("No token found. Please set the DISCORD_TOKEN environment variable.")

# Initialize Flask app
app = Flask(__name__)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  # Enable guild (server) intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Load or initialize tournament data
DATA_FILE = "tourney_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"slots": 0, "teams": [], "confirmed": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

@tasks.loop(minutes=10)
async def heartbeat():
    """Send a heartbeat message every 10 minutes to the botlogs channel"""
    try:
        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Find the botlogs channel in all servers the bot is in
        for guild in bot.guilds:
            botlogs_channel = discord.utils.get(guild.channels, name="botlogs")
            if botlogs_channel:
                await botlogs_channel.send(f"🤖 Bot is alive! Heartbeat at {current_time}")
                print(f"Sent heartbeat to {guild.name} - {botlogs_channel.name}")
    except Exception as e:
        print(f"Error in heartbeat: {e}")

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    # Start the heartbeat task
    heartbeat.start()
    print("Heartbeat task started")

@bot.command()
@commands.has_permissions(administrator=True)
async def setslots(ctx, number: int):
    data["slots"] = number
    save_data(data)
    await ctx.send(f"Tournament slots set to {number}.")

@bot.command()
async def register(ctx, team_name: str, *players):
    if len(data["teams"]) >= data["slots"]:
        await ctx.send("All slots are full.")
        return

    for team in data["teams"]:
        if team_name.lower() == team["team_name"].lower():
            await ctx.send("This team name is already registered.")
            return

    team = {
        "team_name": team_name,
        "players": list(players),
        "captain_id": ctx.author.id
    }
    data["teams"].append(team)
    save_data(data)
    await ctx.send(f"Team '{team_name}' registered with players: {', '.join(players)}")

@bot.command()
async def confirm(ctx):
    for team in data["teams"]:
        if team["captain_id"] == ctx.author.id:
            if team["team_name"] in data["confirmed"]:
                await ctx.send("Your team is already confirmed.")
                return
            data["confirmed"].append(team["team_name"])
            save_data(data)
            await ctx.send(f"Team '{team['team_name']}' confirmed.")
            return
    await ctx.send("You don't have a registered team.")

@bot.command()
async def slots(ctx):
    filled = len(data["teams"])
    total = data["slots"]
    await ctx.send(f"{filled}/{total} slots filled.")

@bot.command()
@commands.has_permissions(administrator=True)
async def teams(ctx):
    if not data["teams"]:
        await ctx.send("No teams registered yet.")
        return
    msg = "Registered Teams:\n"
    for team in data["teams"]:
        msg += f"- {team['team_name']}: {', '.join(team['players'])}\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    global data
    data = {"slots": 0, "teams": [], "confirmed": []}
    save_data(data)
    await ctx.send("Tournament data has been reset.")

# Flask routes
@app.route('/')
def home():
    return "Discord Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    bot.run(TOKEN)

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Run the Flask app in the main thread
    run_web()
