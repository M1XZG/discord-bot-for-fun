# Discord ChatGPT Fun Bot 🤖✨

A Discord bot for fun, feel-good, and inspirational commands powered by OpenAI's GPT!  
Bring positive vibes, jokes, and creative AI to your server. 🌈

---

## Table of Contents

- [Features & Commands](#features--commands)
- [How the Bot Handles Long Replies](#-how-the-bot-handles-long-replies)
- [Setup Guide](#setup-guide)
  - [1. Register Your Bot with Discord](#1-register-your-bot-with-discord)
  - [2. Get Your OpenAI API Key](#2-get-your-openai-api-key)
  - [3. Configure Your Environment](#3-configure-your-environment)
  - [4. Create the funbot Role](#4-create-the-funbot-role)
  - [5. Install Dependencies & Run](#5-install-dependencies--run)
- [Persistent Configuration: myconfig.json](#persistent-configuration-myconfigjson)
- [Admin Commands](#admin-commands)
- [Example Usage](#example-usage)
- [Tips & Notes](#tips--notes)
- [License](#license)

---

## Features & Commands

> **Note:**  
> **The bot will only respond to users who have the `funbot` role.**  
> Server owners/admins must create a role called `funbot` and assign it to any members who should be able to use the bot’s commands.  
> _If a user does not have this role, the bot will ignore their commands and let them know they are not entitled to use it._

| Command                                   | Description                                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `!funbot`                                 | List all available commands and their descriptions.                                         |
| `!botinfo`                                | Show info about this bot and important policies.                                            |
| `!advice [topic]`                         | Receive wholesome advice, optionally on a topic. 📝                                         |
| `!bday <username>`                        | Send a festive, emoji-filled happy birthday message. 🎂🎉                                    |
| `!compliment [@user] [topic]`             | Give someone (or yourself) a wholesome compliment, optionally about a topic. 🌟             |
| `!feelgood [recipient]`                   | Get a 50-word, uplifting message for yourself or someone else! 😊                           |
| `!image <description>`                    | Generate an image with DALL·E from your description. 🖼️                                    |
| `!inspo [recipient]`                      | Receive a unique, inspirational quote, optionally addressed to someone. 💡                  |
| `!joke [topic]`                           | Hear a random, family-friendly joke, or specify a topic for a themed joke! 😂               |
| `!query <your prompt>`/`!ask <your prompt>` | Ask ChatGPT anything you want! ❓                                                          |
| `!showprompts`                            | Show all prompts currently set up in the configuration. 📋                                  |
| `!games`                                  | List all available games and how to use them. 🎮                                            |

> _Note: Some admin-only or hidden commands may exist for bot management._

---

### 🎮 Games Menu (`!games`)

| Command                                   | Description                                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `!8ball <your question>`                   | Ask the Magic 8 Ball a yes/no question. 🎱                                                  |
| `!flip`                                   | Flip a coin. 🪙                                                                             |
| `!roll <number_of_dice> <dice_type>`      | Roll dice! Example: `!roll 2 20` for 2d20.<br>Supported dice types: d4, d6, d8, d10, d12, d20, d100 (default is d6). 🎲 |

> For more details on each command, type `!command` (e.g., `!joke`) or use `!games` for game

---

### 📌 How the Bot Handles Long Replies

If your reply to `!query` or `!ask` is longer than Discord's 2000-character message limit, the bot will automatically create a new thread for you in the channel.  
The full response will be posted in multiple messages within that thread, and you'll be notified in the main channel with a link to the thread.  
This keeps long answers organized and prevents cluttering the main chat.

---

## Setup Guide

### 1. Register Your Bot with Discord

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **"New Application"** and give your bot a name.
3. Go to the **"Bot"** tab, click **"Add Bot"**, and confirm.
4. Under **"Token"**, click **"Reset Token"** and copy your bot token.  
   _You’ll need this for your `.env` file!_

5. Under **"OAuth2" > "URL Generator"**, select:
   - `bot` and `applications.commands` scopes
   - Permissions: `Send Messages`, `Read Message History`, `Add Reactions`, etc.
6. Copy the generated invite link and use it to invite your bot to your server.

### 2. Get Your OpenAI API Key

1. Sign up or log in at [OpenAI Platform](https://platform.openai.com/).
2. Go to [API Keys](https://platform.openai.com/api-keys) and create a new secret key.
3. Copy your API key for your `.env` file.

### 3. Configure Your Environment

Create a `.env` file in your project directory with the following:

```
DISCORD_TOKEN=your-discord-bot-token-here
OPENAI_API_KEY=your-openai-api-key-here
ADMIN_USER_ID=your-discord-user-id-here
```

- To get your Discord user ID, enable Developer Mode in Discord (User Settings > Advanced), then right-click your username and select "Copy ID".

### 4. Create the `funbot` Role

- In your Discord server, go to **Server Settings > Roles**.
- Click **Create Role**, name it `funbot`, and save.
- Assign the `funbot` role to any members who should be able to use the bot.

### 5. Install Dependencies & Run

Install Python dependencies:

```sh
pip install -r requirements.txt
```

Run the bot:

```sh
python3 main.py
```
or, if you made it executable:
```sh
./main.py
```

---

## Persistent Configuration: `myconfig.json`

The bot uses a `myconfig.json` file to store persistent settings, such as the maximum number of tokens (response length) for each command and debugging options.

- On first run, if `myconfig.json` does not exist, the bot will automatically copy the default `config.json` to `myconfig.json`.
- All configuration changes (via admin commands) are saved to `myconfig.json`, so your settings are preserved even if you update or re-clone the repository.
- The original `config.json` serves as a template and will never be modified by the bot.

**Only the user with `ADMIN_USER_ID` can change these values using the admin commands.**

Example `config.json` (template):

```json
{
  "_info": [
    "This file stores persistent configuration for your Discord bot.",
    "The 'max_tokens' section controls the maximum number of tokens (words/characters) returned by OpenAI for each command.",
    "Increasing these values will result in longer responses, but may also increase your OpenAI API usage and costs.",
    "Only the user with ADMIN_USER_ID can change these values using the bot's admin commands.",
    "Be cautious: very high values can quickly consume your OpenAI quota or incur unexpected charges.",
    "The 'tokenuse' option enables token usage debugging. If set to true, the bot will report token usage after each ChatGPT-based command."
  ],
  "max_tokens": {
    "feelgood": 80,
    "inspo": 60,
    "bday": 90,
    "joke": 60,
    "compliment": 60,
    "advice": 60,
    "query": 750
  },
  "tokenuse": false
}
```

---

## Admin Commands

> **Only the user with the `ADMIN_USER_ID` can use these commands.**

### Prompt Management

- `!setprompt <command> <variant> <template>`  
  Set a prompt template for a command and variant (e.g., generic or targeted).

- `!showprompt <command> [variant]`  
  Show the prompt template for a command and variant.

- `!showprompts`  
  Show all prompts currently set up in the configuration.

### Token Management

- `!setmaxtokens <command> <value>`  
  Set the maximum number of tokens for a specific command.  
  Example: `!setmaxtokens query 1000`

- `!showmaxtokens`  
  Show the current max_tokens settings for all commands.

- `!settokenuse on|off`  
  Enable or disable token usage debugging. When enabled, the bot will report how many tokens were used for the prompt and reply after each ChatGPT-based command.

### Miscellaneous

- `!showconfig`  
  Show the current configuration options (excluding comments) from `myconfig.json` as a code block or in a thread if it's too long.

- `!reloadconfig`  
  Reload the configuration from `myconfig.json` (useful if you edited the file manually).

- `!adminhelp`  
  Show this list of admin commands.

**Warning:**  
Increasing max_tokens will result in longer responses and higher OpenAI API usage/costs. Use with care!

---

## Example Usage

- `!feelgood`  
  _Bot:_ “Hey [your name], you’re doing amazing! Keep shining bright like the star you are! 🌟”

- `!feelgood Alex`  
  _Bot:_ “Alex, you’re doing amazing! Keep shining bright like the star you are! 🌟”

- `!inspo`  
  _Bot:_ “The only limit to our realization of tomorrow is our doubts of today. – Addressed to you.”

- `!inspo Jamie`  
  _Bot:_ “Jamie, remember: Every day is a new beginning. 🌅”

- `!joke cats`  
  _Bot:_ “Why was the cat sitting on the computer? To keep an eye on the mouse! 🐱🖱️”

- `!compliment @micki your hair looks great`  
  _Bot:_ “@micki, your hair looks absolutely fantastic today! 💇‍♀️✨”

- `!image a robot surfing a rainbow wave`  
  _Bot:_ _[Bot posts a DALL·E generated image]_ 🌊🤖🌈

- `!ask What is the capital of France?`  
  _Bot:_ “The capital of France is Paris.”

- `!settokenuse on`  
  _Bot:_ "Token usage debugging is now ON."  
  _After each ChatGPT-based command, the bot will append token usage info to its reply._

---

## Tips & Notes

- The bot uses OpenAI’s GPT-3.5 for text and DALL·E for images.
- Make sure your API keys are kept secret and never shared publicly.
- You can run the bot on any machine with Python 3.7+.
- For more info on Discord bots: [Discord Developer Portal Docs](https://discord.com/developers/docs/intro)
- For more info on OpenAI API: [OpenAI API Docs](https://platform.openai.com/docs/)

---

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Robert McKenzie

---

## 🎉 Have fun and spread good vibes!