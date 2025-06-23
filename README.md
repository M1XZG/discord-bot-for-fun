# Discord ChatGPT Fun Bot 🤖✨

A Discord bot for fun, feel-good, and inspirational commands powered by OpenAI's GPT!  
Bring positive vibes, jokes, and creative AI to your server. 🌈

---

## Features & Commands

> **Note:**  
> **The bot will only respond to users who have the `funbot` role.**  
> Server owners/admins must create a role called `funbot` and assign it to any members who should be able to use the bot’s commands.  
> _If a user does not have this role, the bot will ignore their commands and let them know they are not entitled to use it._

| Command                        | Description                                                                                 |
|--------------------------------|---------------------------------------------------------------------------------------------|
| `!advice [topic]`              | Receive wholesome advice, optionally on a topic. 🧠                                         |
| `!bday <username>`             | Send a festive, emoji-filled happy birthday message. 🎂🎉                                    |
| `!compliment [@user] [topic]`  | Give someone (or yourself) a wholesome compliment, optionally about a topic. 🥰             |
| `!feelgood`                    | Get a 50-word, uplifting message just for you! 🌞                                           |
| `!image <description>`         | Generate an image with DALL·E from your description. 🎨                                    |
| `!inspo`                       | Receive a unique, inspirational quote. 💡                                                   |
| `!joke [topic]`                | Hear a random, family-friendly joke, or specify a topic for a themed joke! 😂               |
| `!query <your prompt>`         | Ask ChatGPT anything you want!                                                             |

> _Note: Some admin-only or hidden commands may exist for bot management._

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

## Example Usage

- `!feelgood`  
  _Bot:_ “Hey [your name], you’re doing amazing! Keep shining bright like the star you are! 🌟”

- `!joke cats`  
  _Bot:_ “Why was the cat sitting on the computer? To keep an eye on the mouse! 🐱🖱️”

- `!compliment @micki your hair looks great`  
  _Bot:_ “@micki, your hair looks absolutely fantastic today! 💇‍♀️✨”

- `!image a robot surfing a rainbow wave`  
  _Bot:_ _[Bot posts a DALL·E generated image]_ 🌊🤖🌈

---

## Tips & Notes

- The bot uses OpenAI’s GPT-3.5 for text and DALL·E for images.
- Make sure your API keys are kept secret and never shared publicly.
- You can run the bot on any machine with Python 3.7+.
- For more info on Discord bots: [Discord Developer Portal Docs](https://discord.com/developers/docs/intro)
- For more info on OpenAI API: [OpenAI API Docs](https://platform.openai.com/docs/)

---

## 🎉 Have fun and spread good vibes! 🎉