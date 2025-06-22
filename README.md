# Discord ChatGPT Fun Bot

A Discord bot for fun, feel-good, and inspirational commands powered by OpenAI's GPT!

## Features

- `/feelgood` — Get a 50-word, uplifting message
- `/inspo` — Get an inspirational quote
- `/bday <username>` — Send a happy birthday message with emojis
- `/joke` — Hear a random, family-friendly joke
- `/compliment <username>` — Give someone a compliment
- `/advice` — Receive wholesome advice

## Setup

### 1. Clone and Configure Environment

Clone the repo and copy `.env.example` to `.env`. Fill in your Discord token and OpenAI API key.

```sh
cp .env.example .env
# Edit .env with your credentials
```

### 2. Run With Docker Compose

Build and run the bot easily using Docker Compose:

```sh
docker compose up --build
```

- The bot will automatically restart unless stopped.
- To stop the bot, use `docker compose down`.

### 3. Alternative: Run Locally Without Docker

Install dependencies and start the bot:

```sh
pip install -r requirements.txt
python bot.py
```

### 4. Invite the Bot

Invite the bot to your Discord server with the `applications.commands` and `bot` permissions.

## Notes

- Slash commands may take a minute to sync when the bot starts.
- The bot uses the OpenAI API for all text generation.
- Make sure your environment variables are set correctly in `.env`.