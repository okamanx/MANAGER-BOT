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

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

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

# Get token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("No token found. Please set the DISCORD_TOKEN environment variable.")

bot.run(TOKEN)
