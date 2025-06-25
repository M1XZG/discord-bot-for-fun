# HOW-TO-RUN.md

## 🛠️ Step-by-Step Guide: Running the Discord ChatGPT Fun Bot

> **Note:**  
> This guide assumes you have already completed the OpenAI API onboarding process ([OpenAI API Login](https://platform.openai.com/login)), set up your Discord developer account, and created your bot in the [Discord Developer Portal](https://discord.com/developers/applications).  
> You will need your OpenAI API key and your Discord bot token to proceed.

Follow these steps to set up and run your own instance of the Discord ChatGPT Fun Bot.

---

### 1. Clone the Repository

Open a terminal and run:

```sh
git clone https://github.com/M1XZG/discord-bot-for-fun.git
cd discord-bot-for-fun
```

---

### 2. Set Up a Python Virtual Environment

It’s best to use a virtual environment to keep dependencies isolated:

```sh
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Python Dependencies

```sh
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Copy the example environment file and edit it:

```sh
cp .env.example .env
nano .env
```

Fill in your Discord bot token, OpenAI API key, and your Discord user ID.

---

### 5. (Optional) Edit Configuration

You can edit `config.json` to adjust default settings, or let the bot create `myconfig.json` on first run.

---

### 6. Run the Bot

To run the bot in the foreground:

```sh
python3 main.py
```

Or, if you made it executable:

```sh
./main.py
```

---

### 7. (Recommended) Run the Bot in the Background with `screen`

Install `screen` if you don’t have it:

```sh
sudo apt-get install screen
```

Start a new screen session:

```sh
screen -S funbot
```

Then run the bot as above. To detach from the screen session (leaving the bot running):

- Press `Ctrl+A` then `D`

To reattach later:

```sh
screen -r funbot
```

---

### 8. (Alternative) Use `tmux` Instead of `screen`

If you prefer `tmux`:

```sh
sudo apt-get install tmux
tmux new -s funbot
```

Run the bot, then detach with `Ctrl+B` then `D`. Reattach with:

```sh
tmux attach -t funbot
```

---

Your bot should now be running!  
For more details, see the [README.md](README.md)