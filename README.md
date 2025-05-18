# Discord Tournament Bot

A Discord bot that helps manage tournament registrations and team confirmations. The bot runs as a web service on Render's free tier.

## Features

- Tournament slot management
- Team registration with player lists
- Team confirmation system
- Admin commands for tournament management
- Web service integration for continuous uptime

## Commands

### Admin Commands
- `!setslots <number>` - Set the number of available tournament slots (Admin only)
- `!teams` - List all registered teams (Admin only)
- `!reset` - Reset all tournament data (Admin only)

### User Commands
- `!register <team_name> <player1> <player2> ...` - Register a team with players
- `!confirm` - Confirm your team's participation
- `!slots` - Check available tournament slots

## Setup

### Prerequisites
- Python 3.8 or higher
- A Discord bot token
- A Render account

### Local Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Discord token:
   ```
   DISCORD_TOKEN=your_token_here
   ```
4. Run the bot:
   ```bash
   python discord_bot.py
   ```

### Render Deployment

1. Create a new Web Service on Render
2. Connect your repository
3. Configure the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn discord_bot:app`
4. Add environment variable:
   - Key: `DISCORD_TOKEN`
   - Value: Your Discord bot token
5. Deploy!

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Enable "Message Content Intent" under Privileged Gateway Intents
5. Copy the bot token
6. Add the bot to your server using the OAuth2 URL generator

## Web Endpoints

- `/` - Main page showing bot status
- `/health` - Health check endpoint

## Data Storage

The bot stores tournament data in a JSON file (`tourney_data.json`) with the following structure:
```json
{
    "slots": 0,
    "teams": [],
    "confirmed": []
}
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License. 
