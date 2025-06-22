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

1. Clone the repo and copy `.env.example` to `.env`. Fill in your Discord token and OpenAI API key.
2. Build and run with Docker:

   ```sh
   docker build -t discord-fun-bot .
   docker run --env-file .env discord-fun-bot
   ```

   Or run locally:

   ```sh
   pip install -r requirements.txt
   python bot.py
   ```

3. Invite the bot to your Discord server with appropriate permissions (applications.commands).

## Notes

- Slash commands may take a minute to sync when the bot starts.
- The bot uses the OpenAI API for all text generation.