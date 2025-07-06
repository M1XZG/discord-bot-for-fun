# Discord ChatGPT Fun Bot 🤖✨

A Discord bot for fun, feel-good, and inspirational commands powered by OpenAI's GPT!  
Bring positive vibes, jokes, and creative AI to your server. 🌈

---

## Table of Contents

- [Features & Commands](#features--commands)
- [Games Menu (`!games`)](#games-menu-games)
- [Fishing Game Commands (`!fish`, `!fishlist`, `!fishinfo`)](#fishing-game-commands-fish-fishlist-fishinfo)
- [Conversational Chat Commands](#conversational-chat-commands)
- [Server Information Commands](#server-information-commands)
- [How the Bot Handles Long Replies](#how-the-bot-handles-long-replies)
- [Setup Guide](#setup-guide)
  - [1. Register Your Bot with Discord](#1-register-your-bot-with-discord)
  - [2. Get Your OpenAI API Key](#2-get-your-openai-api-key)
  - [3. Configure Your Environment](#3-configure-your-environment)
  - [4. Create the `funbot` Role](#4-create-the-funbot-role)
  - [5. Install Dependencies & Run](#5-install-dependencies--run)
- [Persistent Configuration: `myconfig.json`](#persistent-configuration-myconfigjson)
- [Admin Commands](#admin-commands)
  - [Prompt Management](#prompt-management)
  - [Token Management](#token-management)
  - [Conversational Chat Management](#conversational-chat-management)
  - [Miscellaneous](#miscellaneous)
- [Fishing Game Admin Commands](#fishing-game-admin-commands)
- [How to Add a New Fish](#how-to-add-a-new-fish)
- [Example Usage](#example-usage)
- [Tips & Notes](#tips--notes)
- [License](#license)

---

## Features & Commands

> **Note:**  
> **The bot will only respond to users who have the `funbot` role (or the role set by the admin).**  
> Server owners/admins can set which role is required for bot access using the admin commands `!setrole` and `!showrole`.  
> _If a user does not have this role, the bot will ignore their commands and let them know they are not entitled to use it._

| Command                                   | Description                                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `!funbot`                                 | List all available commands and their descriptions.                                         |
| `!adminhelp`                              | [Show the list of admin commands.](#admin-commands)                                         |
| `!advice [topic]`                         | Receive wholesome advice, optionally on a topic. 📝                                         |
| `!bday <username>`                        | Send a festive, emoji-filled happy birthday message. 🎂🎉                                    |
| `!botinfo`                                | Show info about this bot and important policies.                                            |
| `!compliment [@user] [topic]`             | Give someone (or yourself) a wholesome compliment, optionally about a topic. 🌟             |
| `!feelgood [recipient]`                   | Get a 50-word, uplifting message for yourself or someone else! 😊                           |
| `!games`                                  | List all available games and how to use them. 🎮                                            |
| `!image <description>`                    | Generate an image with DALL·E from your description. 🖼️                                    |
| `!inspo [recipient]`                      | Receive a unique, inspirational quote, optionally addressed to someone. 💡                  |
| `!joke [topic]`                           | Hear a random, family-friendly joke, or specify a topic for a themed joke! 😂               |
| `!q <your question>` / `!quick <your question>` / `!qask <your question>` | Quick free-form question to ChatGPT (short reply, stays in channel). ⚡                      |
| `!showprompts`                            | Show all prompts currently set up in the configuration. 📋                                  |

---

## 🎮 Games Menu (`!games`)

| Command                                   | Description                                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `!8ball <your question>`                   | Ask the Magic 8 Ball a yes/no question. 🎱                                                  |
| `!flip`                                   | Flip a coin. 🪙                                                                             |
| `!roll <number_of_dice> <dice_type>`      | Roll dice! Example: `!roll 2 20` for 2d20.<br>Supported dice types: d4, d6, d8, d10, d12, d20, d100 (default is d6). 🎲 |

> For more details on each command, type `!command` (e.g., `!joke`) or use `!games` for game info.

---

## 🎣 Fishing Game Commands (`!fish`, `!fishlist`, `!fishinfo`)

| Command / Alias                          | Description                                                                                 |
|-------------------------------------------|---------------------------------------------------------------------------------------------|
| `!fish` / `!f` / `!cast`                 | Go fishing! Catch a random fish and earn points.                                            |
| `!fishstats` / `!fstats` / `!fstat`      | View your fishing stats, including biggest catch and total points.                          |
| `!fplayer <@user>` / `!fstats <@user>`   | View another user's fishing stats.                                                          |
| `!fishlist` / `!flist`                   | List all available fish, their stats, and images in a table.                                |
| `!fishinfo <fish name>`                  | Show detailed stats and image for a specific fish.                                          |
| `!fishhelp` / `!fhelp`                   | Show help for all fishing game commands.                                                    |

- Fish sizes and points are always within realistic limits for each species.
- The biggest catch image is shown in your stats!
- Use `!fishinfo <fish name>` to see detailed stats and the image for any fish.

---

## 💬 Conversational Chat Commands

| Command                                   | Description                                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `!chat <your message>` / `!ask <your message>` / `!query <your message>` | Start a new ChatGPT thread. The bot will remember your conversation in that thread for a configurable number of days (default: 7, set by admin). |
| `!endchat`                                | End your chat early and delete the thread and its memory (only the thread creator or an admin can use this). |
| `!mythreads`                              | List all your active chat threads.                                                          |
| `!allthreads`                             | (Admin) List all active chat threads.                                                       |
| `!threadages`                             | (Admin) List all active chat threads with their age and time until expiration.              |
| `!q <your question>` / `!quick <your question>` / `!qask <your question>` | Quick free-form question to ChatGPT (short reply, stays in channel). ⚡                      |

> _Note: Only the thread creator or a server admin can end a chat early. Otherwise, threads and their memory are deleted automatically after the configured retention period for privacy._

- **Retention Policy:** Chat threads and their memory are automatically deleted after a configurable number of days (default: 7). Admins can change this with `!setchatretention <days>`.
- **Admin Override:** Server admins can end any chat thread early by using `!endchat` inside the thread.

---

## 🎣 Fishing Game Commands

| Command / Alias                          | Description                                                                                 |
|-------------------------------------------|---------------------------------------------------------------------------------------------|
| `!fish` / `!f` / `!cast`                 | Go fishing! Catch a random fish and earn points.                                            |
| `!fishstats` / `!fstats` / `!fstat`      | View your fishing stats, including biggest catch and total points.                          |
| `!fplayer <@user>` / `!fstats <@user>`   | View another user's fishing stats.                                                          |
| `!fishlist` / `!flist`                   | List all available fish, their stats, and images.                                           |
| `!fishhelp` / `!fhelp`                   | Show help for all fishing game commands.                                                    |

- Fish sizes and points are always within realistic limits for each species.
- The biggest catch image is shown in your stats!

---

## 🏠 Server Information Commands

| Command         | Description                                                                                 |
|-----------------|---------------------------------------------------------------------------------------------|
| `!si-server`    | Show general server info (name, ID, owner, region, creation date, member count). 🏠         |
| `!si-members`   | Show member statistics (total, humans, bots, online/offline breakdown). 👥                  |
| `!si-emojis`    | List all custom emojis in this server. 😃                                                  |
| `!si-stickers`  | List all custom stickers in this server. 🗒️                                                |
| `!si-mods`      | List all server moderators and admins. 🛡️                                                  |

---

## 📌 How the Bot Handles Long Replies

If your reply to `!query`, `!ask`, or `!chat` is longer than Discord's 2000-character message limit, the bot will automatically create a new thread for you in the channel.  
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

The bot uses a `myconfig.json` file to store persistent settings, such as the maximum number of tokens (response length) for each command, debugging options, and chat thread retention.

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
    "The 'tokenuse' option enables token usage debugging. If set to true, the bot will report token usage after each ChatGPT-based command.",
    "The 'chat_thread_retention_days' option controls how many days chat threads and their memory are kept before automatic cleanup. Only the user with ADMIN_USER_ID can change this value."
  ],
  "max_tokens": {
    "feelgood": 80,
    "inspo": 60,
    "bday": 90,
    "joke": 60,
    "compliment": 60,
    "advice": 60,
    "query": 500
  },
  "tokenuse": false,
  "required_role": "funbot",
  "chat_thread_retention_days": 7,
  "prompts": {
    "feelgood": {
      "generic": "Craft a warm, uplifting, 50-word message that feels like a heartfelt hug from a close friend, addressed to {user}. Make it gentle, kind, and encouraging — the sort of note someone would want to reread on a tough day.",
      "targeted": "Craft a warm, uplifting, 50-word message that feels like a heartfelt hug from a close friend, addressed to {recipient}. Make it gentle, kind, and encouraging — the sort of note someone would want to reread on a tough day."
    },
    "inspo": {
      "generic": "Create a powerful, original inspirational quote, directly addressed to {user}, that feels like a mentor’s wisdom wrapped in poetic simplicity. Avoid clichés. Think soul-stirring and memorable — something they'd want to frame.",
      "targeted": "Write a powerful, original inspirational quote for {recipient}, something they’d want to remember forever. Avoid clichés. Make it feel like deep wisdom spoken by someone who knows their journey."
    },
    "bday": {
      "generic": "Write a chaotic-good, emoji-stuffed birthday message for {username}, full of memes, good vibes, and ridiculous levels of hype. Make it perfect for Discord culture, like it came from an over-caffeinated bestie."
    },
    "joke": {
      "generic": "Give me a wholesome, random joke that’s clever enough to make an adult chuckle, but clean enough to share with kids. Avoid groan-worthy dad jokes — make it feel clever and sweet.",
      "targeted": "Tell me a clever, family-friendly joke about {topic} that would make even grandma laugh and a kid repeat it at dinner."
    },
    "compliment": {
      "generic": "Write a heartfelt, Discord-friendly compliment from {sender} to {recipient}, focused on celebrating what makes them genuinely special. Keep it specific, kind, and warm — like a friend who really sees them.",
      "targeted": "Write a meaningful compliment from {sender} to {recipient} about {topic}, Discord-ready and full of charm. Avoid general flattery. Make it feel like a real friend appreciating the exact thing that matters."
    },
    "advice": {
      "generic": "Offer a short, sincere piece of advice someone would give to a close friend who needed a quiet moment of truth — kind, but unflinching.",
      "targeted": "You're a wise, empathetic guide with a knack for giving grounded, real-talk advice. Share a short but sincere insight about {topic}, like you'd offer to a close friend who's quietly struggling but not saying much."
    }
  }
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

### Conversational Chat Management

- `!setchatretention <days>`  
  Set how many days chat threads and their memory are kept (default: 7, min: 1, max: 30).

- `!endchat`  
  End and delete any chat thread early (when used by an admin inside the thread).

- `!mythreads`  
  List all your active chat threads.

- `!allthreads`  
  List all active chat threads (admin only).

- `!threadages`  
  List all active chat threads with their age and time until expiration (admin only).

### Miscellaneous

- `!showrole`  
  Show the current required role for using bot commands.

- `!setrole <role_name>`  
  Set the required role for using bot commands (set to blank or `@everyone` to allow all users).

- `!showconfig`  
  Show the current configuration options (excluding comments) from `myconfig.json` as a code block or in a thread if it's too long.

- `!reloadconfig`  
  Reload the configuration from `myconfig.json` (useful if you edited the file manually).

- `!adminhelp`  
  Show this list of admin commands.

**Warning:**  
Increasing max_tokens will result in longer responses and higher OpenAI API usage/costs. Use with care!

---

## 🛠️ Fishing Game Admin Commands

> **Only the user with the `ADMIN_USER_ID` can use these commands.**

| Command / Alias                          | Description                                                                                 |
|-------------------------------------------|---------------------------------------------------------------------------------------------|
| `!addfish <name> <min_size_cm> <max_size_cm> <min_weight_kg> <max_weight_kg>` | Add a new fish species to the game.                                                         |
| `!fishadmin` / `!fadmin`                 | Show all fishing admin commands and usage.                                                  |

---

## 🐟 How to Add a New Fish

1. **Create Your Fish Image**
   - Design a 1:1 aspect ratio image of your fish (square).
   - Recommended size: **200px x 200px** (keeps file size small and ensures consistent display in Discord).
   - Save the image as a `.png` file.

2. **Name the Image File**
   - Use the fish’s name, capitalize each word, and replace spaces with a dash (don't use underscores, discord doesn't like it).
   - Example: `Blue Tang` → `Blue-Tang.png`
   - Place the image in the `FishingGameAssets/` folder in your bot’s directory.

3. **Upload the Image**
   - Copy your `.png` file into the `FishingGameAssets/` folder alongside the other fish images.

4. **Add the Fish via Discord Command**
   - In your Discord server, use the following command (replace values as needed):
     ```
     !addfish <name> <min_size_cm> <max_size_cm> <min_weight_kg> <max_weight_kg>
     ```
     Example:
     ```
     !addfish Blue-Tang 10 40 0.2 0.6
     ```
   - The bot will add the fish to the game and use your uploaded image automatically.

**Tips:**
- Make sure the image filename matches the fish name formatting exactly.
- You can check your new fish with `!fishlist` after adding.

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

- `!setchatretention 3`  
  _Bot:_ "Chat thread retention period set to 3 days. This will apply to new and existing threads."

---

## Tips & Notes

- The bot uses OpenAI’s GPT-3.5 for text and DALL·E for images.
- Make sure your API keys are kept secret and never shared publicly.
- You can run the bot on any machine with Python 3.7+.
- For more info on Discord bots: [Discord Developer Portal Docs](https://discord.com/developers/docs/intro)
- For more info on OpenAI API: [OpenAI API Docs](https://platform.openai.com/docs/)

---

## License

```
Copyright (c) 2025 Ryan McKenzie (@M1XZG)
Repository: discord-bot-for-fun
https://github.com/M1XZG/discord-bot-for-fun
```

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🎉 Have fun and