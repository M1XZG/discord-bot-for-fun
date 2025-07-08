# Installation Guide

## Prerequisites

- Python 3.10 or higher
- Discord Bot Token ([How to get one](https://discord.com/developers/docs/getting-started))
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/M1XZG/discord-bot-for-fun.git
cd discord-bot-for-fun
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Configure the Bot

The bot will automatically create configuration files on first run:
- `myconfig.json` - Main configuration
- `my_fishing_game_config.json` - Fishing game settings

### 6. Run the Bot

```bash
python main.py
```

## Docker Installation (Alternative)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## Inviting the Bot to Your Server

1. Go to your [Discord Application](https://discord.com/developers/applications)
2. Select your bot application
3. Go to OAuth2 → URL Generator
4. Select scopes: `bot`, `applications.commands`
5. Select permissions:
   - Send Messages
   - Send Messages in Threads
   - Create Public Threads
   - Manage Threads
   - Embed Links
   - Attach Files
   - Read Message History
   - Use External Emojis
   - Add Reactions
6. Copy the generated URL and visit it to invite the bot

## Verifying Installation

Once the bot is running and invited:

1. Check bot status with `!botinfo`
2. Test AI features with `!joke`
3. Try the fishing game with `!fish`

## Next Steps

- [Configure your bot](CONFIGURATION.md)
- [Learn all commands](COMMANDS.md)
- [Set up admin features](ADMIN-GUIDE.md)