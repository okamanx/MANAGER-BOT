# Discord Server Management Bot

A simple Discord bot for server admins to lock and unlock channels. Designed for easy server moderation and management.

## Features
- **!lock**: Locks the current channel for everyone except admins (prevents @everyone from sending messages).
- **!unlock**: Unlocks the current channel for everyone (restores send message permission for @everyone).
- **Admin-only commands**: Only users with the "Manage Channels" permission can use these commands.
- **Command logging**: All admin command usage is logged to `bot_command_logs.txt`.

## Setup

1. **Clone this repository**
   ```sh
   git clone https://github.com/okamanx/dealinedcbot.git
   cd dealinedcbot
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   ```
   - Get your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).

4. **Run the bot**
   ```sh
   python discordbot/bot.py
   ```

## Usage
- In any text channel, type `!lock` to lock the channel (admin only).
- Type `!unlock` to unlock the channel (admin only).
- All command usage is logged in `bot_command_logs.txt`.

## Security Notes
- **Never share your bot token publicly.**
- Keep your `.env` file private and do not commit it to public repositories.
- Only trusted users should have the "Manage Channels" permission.

## License
MIT
