import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import asyncio
from datetime import datetime
import json

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
intents.members = True  # Required for member scanning

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up logging to a file
logging.basicConfig(filename="bot_command_logs.txt",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Welcome channel storage
WELCOME_SETTINGS_FILE = "welcome_settings.json"


def load_welcome_settings():
    """Load welcome channel settings from file"""
    try:
        with open(WELCOME_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_welcome_settings(settings):
    """Save welcome channel settings to file"""
    try:
        with open(WELCOME_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving welcome settings: {e}")
        return False


# Load welcome settings on startup
welcome_settings = load_welcome_settings()


# Helper to log command usage
async def log_command(ctx, additional_info=""):
    user = ctx.author
    channel = ctx.channel
    command = ctx.command.name if ctx.command else "unknown"
    log_message = f"User: {user} (ID: {user.id}), Command: {command}, Channel: {channel} (ID: {channel.id})"
    if additional_info:
        log_message += f", Additional Info: {additional_info}"
    logging.info(log_message)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot is in {len(bot.guilds)} guilds")


@bot.event
async def on_member_join(member):
    """Send welcome message when a new member joins"""
    try:
        guild_id = str(member.guild.id)
        if guild_id in welcome_settings:
            channel_id = welcome_settings[guild_id].get('channel_id')
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                if channel and isinstance(channel, discord.TextChannel):
                    # Create beautiful welcome embed
                    embed = discord.Embed(
                        title="ðŸŽ‰ Welcome to the Server!",
                        description=
                        f"Hey {member.mention}! Welcome to **{member.guild.name}**!",
                        color=0x00ff56,
                        timestamp=datetime.utcnow())

                    embed.add_field(
                        name="ðŸŒŸ Getting Started",
                        value=
                        "Feel free to explore the server and introduce yourself! If you have any questions, don't hesitate to ask our friendly community members.",
                        inline=False)

                    embed.add_field(
                        name="ðŸ“Š Server Stats",
                        value=
                        f"You are member **#{len(member.guild.members)}** to join our community!",
                        inline=True)

                    embed.add_field(
                        name="ðŸ“… Account Created",
                        value=member.created_at.strftime("%B %d, %Y"),
                        inline=True)

                    # Set member avatar or default avatar
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    else:
                        embed.set_thumbnail(url=member.default_avatar.url)

                    # Set server icon if available
                    if member.guild.icon:
                        embed.set_author(
                            name=f"Welcome to {member.guild.name}",
                            icon_url=member.guild.icon.url)

                    embed.set_footer(
                        text=
                        f"Joined on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}",
                        icon_url=member.avatar.url
                        if member.avatar else member.default_avatar.url)

                    await channel.send(embed=embed)

                    # Log the welcome message
                    logging.info(
                        f"Welcome message sent for {member} (ID: {member.id}) in guild {member.guild.name}"
                    )

    except Exception as e:
        print(f"Error sending welcome message: {e}")
        logging.error(f"Error sending welcome message for {member}: {e}")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await log_command(ctx)
    channel = ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"ðŸ”’ {channel.mention} has been locked.")


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
    await ctx.send(f"ðŸ”“ {channel.mention} has been unlocked.")


# New moderation commands
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member from the server"""
    try:
        # Check if the user is trying to ban themselves
        if member == ctx.author:
            await ctx.send("âŒ You cannot ban yourself!")
            return

        # Check if the user is trying to ban the bot
        if member == bot.user:
            await ctx.send("âŒ I cannot ban myself!")
            return

        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(
                "âŒ You cannot ban someone with a higher or equal role!")
            return

        # Check if member can be banned
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(
                "âŒ I cannot ban someone with a role higher than or equal to mine!"
            )
            return

        await member.ban(reason=f"Banned by {ctx.author}: {reason}")
        await ctx.send(f"ðŸ”¨ **{member}** has been banned!\n**Reason:** {reason}"
                       )

        # Log the ban
        await log_command(ctx,
                          f"Banned {member} (ID: {member.id}) for: {reason}")

    except discord.Forbidden:
        await ctx.send("âŒ I don't have permission to ban this member!")
    except discord.HTTPException as e:
        await ctx.send(f"âŒ Failed to ban member: {str(e)}")
    except Exception as e:
        await ctx.send(f"âŒ An error occurred: {str(e)}")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("âŒ You don't have permission to ban members!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("âŒ Please mention a valid member to ban!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("âŒ Member not found!")


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_info):
    """Unban a member using their username#discriminator or user ID"""
    try:
        # Try to parse as user ID first
        if member_info.isdigit():
            user_id = int(member_info)
            user = await bot.fetch_user(user_id)
        else:
            # Try to parse as username#discriminator
            if '#' in member_info:
                username, discriminator = member_info.split('#')
                # Get banned users
                banned_users = [entry async for entry in ctx.guild.bans()]
                user = None
                for ban_entry in banned_users:
                    if ban_entry.user.name == username and ban_entry.user.discriminator == discriminator:
                        user = ban_entry.user
                        break
                if not user:
                    await ctx.send("âŒ User not found in ban list!")
                    return
            else:
                # Try to find by username only
                banned_users = [entry async for entry in ctx.guild.bans()]
                user = None
                for ban_entry in banned_users:
                    if ban_entry.user.name.lower() == member_info.lower():
                        user = ban_entry.user
                        break
                if not user:
                    await ctx.send(
                        "âŒ User not found in ban list! Use format: `username#discriminator` or user ID"
                    )
                    return

        # Unban the user
        await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
        await ctx.send(f"âœ… **{user}** has been unbanned!")

        # Log the unban
        await log_command(ctx, f"Unbanned {user} (ID: {user.id})")

    except discord.NotFound:
        await ctx.send("âŒ User is not banned or doesn't exist!")
    except discord.Forbidden:
        await ctx.send("âŒ I don't have permission to unban members!")
    except discord.HTTPException as e:
        await ctx.send(f"âŒ Failed to unban user: {str(e)}")
    except Exception as e:
        await ctx.send(f"âŒ An error occurred: {str(e)}")


@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("âŒ You don't have permission to unban members!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "âŒ Please provide a username#discriminator or user ID to unban!")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def scan_members(ctx, page: int = 1):
    """Scan and list all server members with pagination"""
    try:
        members_per_page = 20
        all_members = ctx.guild.members
        total_members = len(all_members)
        total_pages = (total_members + members_per_page -
                       1) // members_per_page

        if page < 1 or page > total_pages:
            await ctx.send(
                f"âŒ Invalid page number! Pages available: 1-{total_pages}")
            return

        start_idx = (page - 1) * members_per_page
        end_idx = min(start_idx + members_per_page, total_members)
        page_members = all_members[start_idx:end_idx]

        embed = discord.Embed(
            title=f"ðŸ“Š Server Members Scan - Page {page}/{total_pages}",
            description=
            f"Showing members {start_idx + 1}-{end_idx} of {total_members}",
            color=0x3498db,
            timestamp=datetime.utcnow())

        online_count = sum(1 for m in all_members
                           if m.status != discord.Status.offline)
        offline_count = total_members - online_count
        bot_count = sum(1 for m in all_members if m.bot)
        human_count = total_members - bot_count

        embed.add_field(
            name="ðŸ“ˆ Server Statistics",
            value=
            f"**Total:** {total_members}\n**Online:** {online_count}\n**Offline:** {offline_count}\n**Bots:** {bot_count}\n**Humans:** {human_count}",
            inline=True)

        member_list = []
        for member in page_members:
            status_emoji = {
                discord.Status.online: "ðŸŸ¢",
                discord.Status.idle: "ðŸŸ¡",
                discord.Status.dnd: "ðŸ”´",
                discord.Status.offline: "âš«"
            }.get(member.status, "âš«")

            bot_indicator = "ðŸ¤–" if member.bot else "ðŸ‘¤"
            member_info = f"{status_emoji} {bot_indicator} **{member.display_name}** ({member.name}#{member.discriminator})"

            # Add roles info if member has roles other than @everyone
            roles = [role.name for role in member.roles[1:]]  # Skip @everyone
            if roles:
                member_info += f"\n   â”” Roles: {', '.join(roles[:3])}"
                if len(roles) > 3:
                    member_info += f" (+{len(roles) - 3} more)"

            member_list.append(member_info)

        embed.add_field(name="ðŸ‘¥ Members",
                        value="\n".join(member_list)
                        if member_list else "No members found",
                        inline=False)

        embed.set_footer(
            text=f"Use !scan_members {page + 1} for next page" if page <
            total_pages else "Last page")

        await ctx.send(embed=embed)
        await log_command(ctx, f"Scanned members page {page}/{total_pages}")

    except Exception as e:
        await ctx.send(f"âŒ An error occurred while scanning members: {str(e)}")


@scan_members.error
async def scan_members_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("âŒ You don't have permission to scan server members!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("âŒ Please provide a valid page number!")


@bot.command()
@commands.has_permissions(administrator=True)
async def broadcast(ctx, *, message):
    """Send a message to all members via DM (Admin/Owner only)"""
    try:
        # Confirmation prompt
        confirm_embed = discord.Embed(
            title="ðŸ“¢ Broadcast Confirmation",
            description=
            f"Are you sure you want to send this message to **{len(ctx.guild.members)}** members?\n\n**Message:**\n{message}",
            color=0xe74c3c)
        confirm_embed.set_footer(
            text="React with âœ… to confirm or âŒ to cancel (30 seconds)")

        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction("âœ…")
        await confirm_msg.add_reaction("âŒ")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [
                "âœ…", "âŒ"
            ] and reaction.message.id == confirm_msg.id

        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                timeout=30.0,
                                                check=check)
        except asyncio.TimeoutError:
            await confirm_msg.edit(
                embed=discord.Embed(title="â° Broadcast Cancelled",
                                    description="Confirmation timed out.",
                                    color=0x95a5a6))
            return

        if str(reaction.emoji) == "âŒ":
            await confirm_msg.edit(
                embed=discord.Embed(title="âŒ Broadcast Cancelled",
                                    description="Broadcast cancelled by user.",
                                    color=0x95a5a6))
            return

        # Start broadcasting
        progress_embed = discord.Embed(
            title="ðŸ“¢ Broadcasting...",
            description=
            "Sending messages to all members. This may take a while...",
            color=0xf39c12)
        await confirm_msg.edit(embed=progress_embed)

        success_count = 0
        failed_count = 0
        total_members = len([m for m in ctx.guild.members
                             if not m.bot])  # Exclude bots

        broadcast_embed = discord.Embed(
            title=f"ðŸ“¢ Broadcast from {ctx.guild.name}",
            description=message,
            color=0x3498db,
            timestamp=datetime.utcnow())
        broadcast_embed.set_footer(
            text=f"Sent by {ctx.author}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        broadcast_embed.set_thumbnail(
            url=ctx.guild.icon.url if ctx.guild.icon else None)

        for member in ctx.guild.members:
            if member.bot or member == ctx.author:  # Skip bots and the sender
                continue

            try:
                await member.send(embed=broadcast_embed)
                success_count += 1

                # Rate limiting: wait between messages to avoid hitting Discord limits
                await asyncio.sleep(1)  # 1 second delay between DMs

            except discord.Forbidden:
                # User has DMs disabled or blocked the bot
                failed_count += 1
            except discord.HTTPException:
                # Other HTTP errors (rate limit, etc.)
                failed_count += 1
                await asyncio.sleep(2)  # Longer delay on HTTP errors
            except Exception:
                failed_count += 1

        # Final result
        result_embed = discord.Embed(
            title="ðŸ“¢ Broadcast Complete",
            color=0x27ae60 if failed_count == 0 else 0xf39c12)
        result_embed.add_field(name="âœ… Successful",
                               value=str(success_count),
                               inline=True)
        result_embed.add_field(name="âŒ Failed",
                               value=str(failed_count),
                               inline=True)
        result_embed.add_field(name="ðŸ“Š Total Attempted",
                               value=str(total_members),
                               inline=True)

        if failed_count > 0:
            result_embed.add_field(
                name="â„¹ï¸ Note",
                value=
                "Failed messages are usually due to users having DMs disabled or blocking the bot.",
                inline=False)

        await confirm_msg.edit(embed=result_embed)
        await log_command(
            ctx,
            f"Broadcast sent to {success_count}/{total_members} members. Message: {message[:100]}..."
        )

    except Exception as e:
        await ctx.send(f"âŒ An error occurred during broadcast: {str(e)}")


@broadcast.error
async def broadcast_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "âŒ You don't have permission to broadcast messages! (Administrator required)"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "âŒ Please provide a message to broadcast!\nUsage: `!broadcast <message>`"
        )


@bot.command()
@commands.has_permissions(manage_guild=True)
async def ban_list(ctx, page: int = 1):
    """List all banned users with pagination"""
    try:
        bans_per_page = 10
        banned_users = [entry async for entry in ctx.guild.bans()]
        total_bans = len(banned_users)

        if total_bans == 0:
            await ctx.send("âœ… No banned users found!")
            return

        total_pages = (total_bans + bans_per_page - 1) // bans_per_page

        if page < 1 or page > total_pages:
            await ctx.send(
                f"âŒ Invalid page number! Pages available: 1-{total_pages}")
            return

        start_idx = (page - 1) * bans_per_page
        end_idx = min(start_idx + bans_per_page, total_bans)
        page_bans = banned_users[start_idx:end_idx]

        embed = discord.Embed(
            title=f"ðŸ”¨ Banned Users - Page {page}/{total_pages}",
            description=
            f"Showing bans {start_idx + 1}-{end_idx} of {total_bans}",
            