#!/usr/bin/env python3

# Copyright (c) 2025 Your Name
# This software is released under the MIT License.
# See LICENSE file for details.

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import openai
import requests
from datetime import datetime, timedelta
import json
import io
import shutil
import re
import time
import random
from bot_games import flip_coin, roll_dice, magic_8_ball

# --- Persistent Config Helpers ---
CONFIG_FILE = "myconfig.json"
DEFAULT_CONFIG_FILE = "config.json"

# On startup, copy config.json to myconfig.json if myconfig.json does not exist
if not os.path.exists(CONFIG_FILE):
    if os.path.exists(DEFAULT_CONFIG_FILE):
        shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_FILE)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

config = load_config()

def get_max_tokens(command, default):
    return int(config.get("max_tokens", {}).get(command, default))

def set_max_tokens(command, value):
    if "max_tokens" not in config:
        config["max_tokens"] = {}
    config["max_tokens"][command] = value
    save_config(config)

def is_admin(ctx):
    return ctx.author.id == ADMIN_USER_ID

def get_tokenuse():
    return config.get("tokenuse", False)

def set_tokenuse(value: bool):
    config["tokenuse"] = value
    save_config(config)

def get_required_role():
    return config.get("required_role", "funbot")

def set_required_role(role_name):
    config["required_role"] = role_name
    save_config(config)
# --- End Persistent Config Helpers ---

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ALL_ACCESS = os.getenv("OPENAI_ALL_ACCESS")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
openai.api_key = OPENAI_API_KEY

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True  # <-- Add this line

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def should_send_as_file(text, limit=2000):
    return len(text) > limit

def summarize_text_for_thread(text, max_length=40):
    # Remove markdown/code blocks and newlines, keep it simple
    summary = text.strip().replace('\n', ' ').replace('`', '')
    # Truncate to the last full word within max_length
    if len(summary) > max_length:
        cut = summary[:max_length].rfind(' ')
        if cut == -1:
            cut = max_length
        summary = summary[:cut] + "..."
    return summary

async def send_long_response(ctx, text, filename="response.txt"):
    # If the message is short, just send it as usual
    if len(text) <= 2000:
        await ctx.send(text)
        return

    # Use the user's name, command (unless it's 'query'), and a summary of the reply for the thread name
    thread_name = "Long Response"
    if hasattr(ctx, "author") and hasattr(ctx, "command"):
        summary = summarize_text_for_thread(text)
        cmd_name = ctx.command.name
        if cmd_name == "query":
            thread_name = f"{ctx.author.display_name}: {summary}"
        else:
            thread_name = f"{ctx.author.display_name} - {cmd_name}: {summary}"
        # Discord thread name limit is 100 chars
        if len(thread_name) > 95:
            thread_name = thread_name[:95] + "..."

    thread = await ctx.channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.public_thread,
        message=ctx.message if hasattr(ctx, "message") else None
    )

    def smart_chunks(s, limit=2000):
        i = 0
        n = len(s)
        while i < n:
            # Try to find a paragraph boundary
            end = min(i + limit, n)
            chunk = s[i:end]
            para_idx = chunk.rfind('\n\n')
            if para_idx != -1 and i + para_idx + 2 - i > 100:
                split_at = i + para_idx + 2
            else:
                # Try to find a sentence boundary
                sent_match = list(re.finditer(r'([.!?])\s', chunk))
                if sent_match:
                    last_sent = sent_match[-1].end()
                    if last_sent > 100:
                        split_at = i + last_sent
                    else:
                        split_at = None
                else:
                    split_at = None
                # Try to find a space
                if split_at is None:
                    space_idx = chunk.rfind(' ')
                    if space_idx != -1 and space_idx > 100:
                        split_at = i + space_idx + 1
                # Fallback: hard split
                if split_at is None or split_at <= i:
                    split_at = end
            yield s[i:split_at]
            i = split_at

    for chunk in smart_chunks(text, 2000):
        await thread.send(chunk)
    await ctx.send(f"{ctx.author.mention} The response was too long, so I've posted it in a new thread: {thread.mention}")

# Add this admin command:
@bot.command(help="Enable or disable token usage debugging (ADMIN only). Usage: !settokenuse on|off", hidden=True)
async def settokenuse(ctx, value: str):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    if value.lower() in ("on", "true", "yes", "1"):
        set_tokenuse(True)
        await ctx.send("Token usage debugging is now ON.")
    elif value.lower() in ("off", "false", "no", "0"):
        set_tokenuse(False)
        await ctx.send("Token usage debugging is now OFF.")
    else:
        await ctx.send("Usage: !settokenuse on|off")

# --- ask_chatgpt returns both reply and token info if enabled ---
async def ask_chatgpt(prompt, max_tokens=80):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative, friendly assistant for a Discord server."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            n=1,
            temperature=0.8,
        )
        # Defensive: check for expected structure and content
        if (
            hasattr(response, "choices")
            and response.choices
            and hasattr(response.choices[0], "message")
            and hasattr(response.choices[0].message, "content")
            and response.choices[0].message.content
        ):
            reply = response.choices[0].message.content.strip()
            # Token usage reporting
            token_debug = ""
            if get_tokenuse() and hasattr(response, "usage"):
                usage = response.usage
                prompt_tokens = usage.get("prompt_tokens", "N/A")
                completion_tokens = usage.get("completion_tokens", "N/A")
                total_tokens = usage.get("total_tokens", "N/A")
                token_debug = (
                    f"\n\n**[Token Usage]**\n"
                    f"Prompt tokens: {prompt_tokens}\n"
                    f"Reply tokens: {completion_tokens}\n"
                    f"Total tokens: {total_tokens}"
                )
            return reply, token_debug
        else:
            print(f"OpenAI API returned unexpected response: {response}")
            return "Sorry, I couldn't get a response from ChatGPT.", ""
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Sorry, I couldn't get a response from ChatGPT.", ""

# --- In every command that calls ask_chatgpt, append token info if present ---
@bot.command(help="Get a short, 50-word feel good message! Optionally specify a recipient: !feelgood [recipient]")
async def feelgood(ctx, *, recipient: str = None):
    user = ctx.author.nick or ctx.author.name
    if recipient:
        prompt = get_prompt("feelgood", "targeted", recipient=recipient)
    else:
        prompt = get_prompt("feelgood", "generic", user=user)
    max_tokens = get_max_tokens("feelgood", 80)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    await ctx.send(msg + token_debug)

@bot.command(help="Get an inspirational quote! Optionally specify a recipient: !inspo [recipient]")
async def inspo(ctx, *, recipient: str = None):
    user = ctx.author.nick or ctx.author.name
    if recipient:
        prompt = get_prompt("inspo", "targeted", recipient=recipient)
    else:
        prompt = get_prompt("inspo", "generic", user=user)
    max_tokens = get_max_tokens("inspo", 60)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    await ctx.send(msg + token_debug)

@bot.command(help="Wish a happy birthday to someone! Usage: !bday <username>")
async def bday(ctx, username: str):
    prompt = get_prompt("bday", "generic", username=username)
    max_tokens = get_max_tokens("bday", 90)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    await ctx.send(msg + token_debug)

@bot.command(help="Get a random, light-hearted joke! Optionally specify a topic: !joke [topic]")
async def joke(ctx, topic: str = None):
    if topic:
        prompt = get_prompt("joke", "targeted", topic=topic)
    else:
        prompt = get_prompt("joke", "generic")
    max_tokens = get_max_tokens("joke", 60)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    await ctx.send(msg + token_debug)

@bot.command(help="Give a user a personalized compliment! Usage: !compliment [@user] [topic]")
async def compliment(ctx, user: discord.Member = None, *, topic: str = None):
    await ctx.message.delete()
    sender = ctx.author.nick or ctx.author.name
    if user:
        recipient = user.nick or user.name
        mention = user.mention
    else:
        recipient = sender
        mention = ctx.author.mention

    if topic:
        prompt = get_prompt("compliment", "targeted", recipient=recipient, sender=sender, topic=topic)
    else:
        prompt = get_prompt("compliment", "generic", recipient=recipient, sender=sender)
    max_tokens = get_max_tokens("compliment", 60)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    await ctx.send(f"{mention} {msg}{token_debug}")

@bot.command(help="Get a short piece of wholesome advice! Optionally specify a topic: !advice [topic]")
async def advice(ctx, *, topic: str = None):
    if topic:
        prompt = get_prompt("advice", "targeted", topic=topic)
    else:
        prompt = get_prompt("advice", "generic")
    max_tokens = get_max_tokens("advice", 60)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    await ctx.send(msg + token_debug)

@bot.command(help="List all available games and how to use them.")
async def games(ctx):
    msg = (
        "🎮 **Available Games:**\n"
        "• 🎱 **!8ball <your question>** — Ask the Magic 8 Ball a yes/no question.\n"
        "• 🪙 **!flip** — Flip a coin.\n"
        "• 🎲 **!roll <number_of_dice> <dice_type>** — Roll dice! Example: `!roll 2 20` for 2d20.\n"
        "   Supported dice types: d4, d6, d8, d10, d12, d20, d100 (default is d6).\n"
        "\nType the command for more details or to play!"
    )
    await ctx.send(msg)

@bot.command(name="si-mods", help="List all server moderators and admins (users with Manage Messages or Administrator permission).")
async def si_mods(ctx):
    guild = ctx.guild
    mods = []
    for member in guild.members:
        perms = member.guild_permissions
        if perms.administrator or perms.manage_messages:
            if not member.bot:
                mods.append(f"{member.mention} ({member.display_name})")
    if not mods:
        await ctx.send("No moderators or admins found in this server.")
        return
    msg = "**Server Moderators/Admins:**\n" + "\n".join(mods)
    # Discord message limit: send as file if too long
    if len(msg) > 1900:
        await send_long_response(ctx, msg, filename="moderators.txt")
    else:
        await ctx.send(msg)

# Update the funbot help command to mention !games and server info commands
@bot.command(name="funbot", help="List all commands and their descriptions.")
async def funbot_command(ctx):
    help_text = (
        "✨ **__FunBot Command List__** ✨\n"
        "Here are the commands you can use:\n\n"
    )
    emoji_map = {
        "feelgood": "😊",
        "inspo": "💡",
        "bday": "🎂",
        "joke": "😂",
        "compliment": "🌟",
        "advice": "📝",
        "image": "🖼️",
        "query": "❓",
        "ask": "❓",
        "showprompts": "📋",
        "botinfo": "ℹ️",
        "funbot": "🤖",
        "games": "🎮",
        # "flip": "🪙", "roll": "🎲", "8ball": "🎱",  # Do not show these in !funbot
    }
    # Exclude game commands from the main help
    game_commands = {"flip", "roll", "8ball"}
    filtered_commands = [cmd for cmd in bot.commands if not cmd.hidden and cmd.name not in game_commands]
    commands_sorted = sorted(filtered_commands, key=lambda c: c.name)

    # Main commands (excluding server info)
    for command in commands_sorted:
        if command.name.startswith("si-"):
            continue  # We'll add these in a separate section
        emoji = emoji_map.get(command.name, "•")
        usage = f" {command.usage}" if hasattr(command, "usage") and command.usage else ""
        # Special case: show both !query and !ask for the query command
        if command.name == "query" and "ask" in command.aliases:
            help_text += f"{emoji} **!query**/**!ask**{usage} — {command.help}\n"
        else:
            help_text += f"{emoji} **!{command.name}**{usage} — {command.help}\n"
    # Add botinfo and games command explicitly if not already present
    if "!botinfo" not in help_text:
        help_text += "ℹ️ **!botinfo** — Show info about this bot and important policies.\n"
    if "!games" not in help_text:
        help_text += "🎮 **!games** — List all available games and how to use them.\n"

    # --- Server Info Section ---
    help_text += (
        "\n__**Server Info Commands**__\n"
        "These commands show information about your Discord server:\n"
        "• 🏠 **!si-server** — Show general server info (name, ID, owner, region, creation date, member count).\n"
        "• 👥 **!si-members** — Show member statistics (total, humans, bots, online/offline breakdown).\n"
        "• 😃 **!si-emojis** — List all custom emojis in this server.\n"
        "• 🗒️ **!si-stickers** — List all custom stickers in this server.\n"
        "• 🛡️ **!si-mods** — List all server moderators and admins.\n"
    )

    help_text += (
        "\n__Tip__: Use `!command` for more info on each command. "
        "For games, use `!games`."
    )
    await ctx.send(help_text)

# Example usage in your commands:
@bot.command(help="Ask ChatGPT any question! Usage: !query <your prompt>", aliases=["ask"])
async def query(ctx, *, prompt: str = None):
    if not prompt or not prompt.strip():
        await ctx.send("You need to provide a prompt to ask ChatGPT. Usage: `!query <your prompt>`")
        return
    max_tokens = get_max_tokens("query", 500)
    msg, token_debug = await ask_chatgpt(prompt, max_tokens=max_tokens)
    full_msg = msg + token_debug
    await send_long_response(ctx, full_msg, filename="chatgpt_reply.txt")

@bot.command(help="Generate an image with DALL·E! Usage: !image <description>")
async def image(ctx, *, prompt: str = None):
    if not prompt or not prompt.strip():
        await ctx.send("You need to provide a prompt to generate an image. Usage: `!image <description>`")
        return
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        await ctx.send(image_url)
    except Exception as e:
        print(f"OpenAI Image Error: {e}")
        await ctx.send("Sorry, I couldn't generate an image for that prompt.")

# --- Admin-only commands for config management ---

@bot.command(help="Show the current config options (ADMIN only, omits comments)", hidden=True)
async def showconfig(ctx):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    try:
        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)
        # Remove any keys that are comments (e.g., "_info")
        config_no_comments = {k: v for k, v in config_data.items() if not k.startswith("_")}
        config_str = json.dumps(config_no_comments, indent=2)
        # Always send as a file attachment
        file = discord.File(io.BytesIO(config_str.encode("utf-8")), filename="config.json")
        await ctx.send("Here is the current config:", file=file)
    except Exception as e:
        await ctx.send(f"Could not read config file: {e}")

@bot.command(help="Set a prompt for a command (ADMIN only)", hidden=True)
async def setprompt(ctx, command: str, variant: str, *, template: str):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    if "prompts" not in config:
        config["prompts"] = {}
    if command not in config["prompts"]:
        config["prompts"][command] = {}
    config["prompts"][command][variant] = template
    save_config(config)
    await ctx.send(f"Prompt for `{command}` ({variant}) updated.")

@bot.command(help="Show the prompt for a command (ADMIN only)", hidden=True)
async def showprompt(ctx, command: str, variant: str = None):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    prompts = config.get("prompts", {})
    cmd_prompts = prompts.get(command, {})
    if not cmd_prompts:
        await ctx.send(f"No prompts found for `{command}`.")
        return

    # If variant is specified, show only that variant
    if variant:
        template = cmd_prompts.get(variant)
        if template:
            await ctx.send(f"Prompt for `{command}` ({variant}):\n```{template}```")
        else:
            await ctx.send(f"No prompt found for `{command}` ({variant}).")
        return

    # If no variant specified, show all variants for the command
    msg = f"Prompts for `{command}`:\n"
    found = False
    for v, template in cmd_prompts.items():
        msg += f"\n**{v}**:\n```{template}```\n"
        found = True
    if found:
        await ctx.send(msg)
    else:
        await ctx.send(f"No prompts found for `{command}`.")

@bot.command(help="Show admin commands (ADMIN only)", hidden=True)
async def adminhelp(ctx):
    if not is_admin(ctx):
        return

    help_text = "**Admin Commands:**\n"

    # Prompt Management
    help_text += "\n__Prompt Management__\n"
    help_text += (
        "`!setprompt <command> <variant> <template>` - Set a prompt for a command/variant\n"
        "`!showprompt <command> [variant]` - Show the prompt for a command/variant\n"
        "`!showprompts` - Show all prompts currently set up\n"
    )

    # Token Management
    help_text += "\n__Token Management__\n"
    help_text += (
        "`!setmaxtokens <command> <value>` - Set max tokens for a command\n"
        "`!showmaxtokens` - Show current max_tokens settings\n"
        "`!settokenuse on|off` - Enable or disable token usage debugging\n"
    )

    # Miscellaneous
    help_text += "\n__Miscellaneous__\n"
    misc_cmds = [
        ("!showconfig", "Show the entire config.json file"),
        ("!reloadconfig", "Reload the configuration from myconfig.json"),
        ("!showrole", "Show the current required role for using bot commands"),
        ("!setrole <role_name>", "Set the required role for using bot commands"),
        ("!adminhelp", "Show this list of admin commands"),
    ]
    # Sort alphabetically by command name
    misc_cmds_sorted = sorted(misc_cmds, key=lambda x: x[0])
    for cmd, desc in misc_cmds_sorted:
        help_text += f"`{cmd}` - {desc}\n"

    await ctx.send(help_text)

@bot.command(help="Set max tokens for a command (ADMIN only)", hidden=True)
async def setmaxtokens(ctx, command: str, value: int):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    set_max_tokens(command, value)
    await ctx.send(f"Set max tokens for `{command}` to {value}.")

@bot.command(help="Show current max_tokens settings (ADMIN only)", hidden=True)
async def showmaxtokens(ctx):
    if not is_admin(ctx):
        return
    mt = config.get("max_tokens", {})
    if not mt:
        await ctx.send("No max_tokens settings found.")
    else:
        await ctx.send(f"Current max_tokens: ```{json.dumps(mt, indent=2)}```")

@bot.command(help="Show all prompts currently set up")
async def showprompts(ctx):
    prompts = config.get("prompts", {})
    if not prompts:
        await ctx.send("No prompts are currently set up.")
        return
    msg = "**Current Prompts:**\n"
    for command, variants in prompts.items():
        msg += f"\n__{command}__:\n"
        for variant, template in variants.items():
            msg += f"  • **{variant}**: `{template}`\n"
    # Discord message limit: send as file if too long
    if len(msg) > 1900:
        await send_long_response(ctx, msg, filename="prompts.txt")
    else:
        await ctx.send(msg)

@bot.command(help="Reload the configuration from myconfig.json (ADMIN only)", hidden=True)
async def reloadconfig(ctx):
    global config
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    try:
        start = time.perf_counter()
        with open(CONFIG_FILE, "r") as f:
            lines = f.readlines()
        config = json.loads("".join(lines))
        elapsed = (time.perf_counter() - start) * 1000  # ms
        await ctx.send(f"Configuration reloaded from myconfig.json in {elapsed:.1f} ms ({len(lines)} lines read).")
    except Exception as e:
        await ctx.send(f"Failed to reload configuration: {e}")

# --- End Admin-only commands ---

@bot.command(help="(hidden)", hidden=True)
async def apistats(ctx):
    if ctx.author.id != ADMIN_USER_ID:
        return

    headers = {
        "Authorization": f"Bearer {OPENAI_ALL_ACCESS}",
        "OpenAI-Organization": "org-ovkptdCXPXKxJxOWehyR0NcO"
    }

    # Get usage for the current month
    now = datetime.utcnow()
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")  # Use today, not tomorrow

    try:
        # Usage
        usage_url = f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
        usage_resp = requests.get(usage_url, headers=headers)
        usage_data = usage_resp.json()
        print("USAGE DATA:", usage_data)
        if "error" in usage_data:
            await ctx.send(f"OpenAI Usage API error: {usage_data['error'].get('message', 'Unknown error')}")
            return
        total_usage = usage_data.get("total_usage", 0) / 100.0

        # Budget
        credit_url = "https://api.openai.com/v1/dashboard/billing/credit_grants"
        credit_resp = requests.get(credit_url, headers=headers)
        credit_data = credit_resp.json()
        print("CREDIT DATA:", credit_data)
        if "error" in credit_data:
            await ctx.send(f"OpenAI Credit API error: {credit_data['error'].get('message', 'Unknown error')}")
            return
        total_granted = credit_data.get("total_granted", 0)
        total_used = credit_data.get("total_used", 0)
        total_available = credit_data.get("total_available", 0)

        msg = (
            f"**OpenAI API Usage Stats (this month):**\n"
            f"Total used: ${total_usage:.2f}\n"
            f"Total granted: ${total_granted:.2f}\n"
            f"Total available: ${total_available:.2f}\n"
        )
        await ctx.send(msg)
    except Exception as e:
        print(f"API Stats Error: {e}")
        await ctx.send("Could not retrieve API stats at this time.")

@bot.command(help="(hidden)", hidden=True)
async def list_models(ctx):
    if ctx.author.id != ADMIN_USER_ID:
        return
    try:
        response = openai.Model.list(api_key=OPENAI_ALL_ACCESS, organization="org-ovkptdCXPXKxJxOWehyR0NcO")
        models = [model["id"] for model in response["data"]]
        models_text = "\n".join(models)
        # Discord messages have a 2000 character limit
        if len(models_text) > 1900:
            await ctx.send("Too many models to display. Here are the first 20:\n" + "\n".join(models[:20]))
        else:
            await ctx.send(f"**Available OpenAI Models:**\n{models_text}")
    except Exception as e:
        print(f"OpenAI List Models Error: {e}")
        await ctx.send("Could not retrieve model list at this time.")

@bot.check
async def global_funbot_role_check(ctx):
    if ctx.guild is None:
        return False  # Ignore DMs
    required_role = get_required_role()
    if not required_role:
        return True  # No restriction
    if discord.utils.get(ctx.author.roles, name=required_role):
        return True
    if ctx.author.id == ADMIN_USER_ID:
        return True
    await ctx.send(f"You need the `{required_role}` role to use this bot.")
    return False

def get_prompt(command, variant="generic", **kwargs):
    prompts = config.get("prompts", {})
    cmd_prompts = prompts.get(command, {})
    template = cmd_prompts.get(variant)
    if not template:
        return ""
    return template.format(**kwargs)

@bot.command(help="Show info about this bot and important policies.")
async def botinfo(ctx):
    info = (
        "**Discord ChatGPT Fun Bot 🤖✨**\n"
        "This bot brings positive vibes, inspiration, jokes, compliments, advice, and creative AI to your server! "
        "It uses OpenAI's GPT for text and DALL·E for images. "
        "Try commands like `!feelgood`, `!inspo`, `!joke`, `!compliment`, `!advice`, and more.\n\n"
        "By using this bot, you agree to the following policies:\n"
        "• <https://github.com/M1XZG/discord-bot-for-fun/blob/main/PRIVACY_POLICY.md>\n"
        "• <https://github.com/M1XZG/discord-bot-for-fun/blob/main/TERMS_OF_SERVICE.md>\n"
        "Please read these documents for details on data usage and your rights."
    )
    await ctx.send(info)

@bot.command(help="Flip a coin! Usage: !flip")
async def flip(ctx):
    result = flip_coin()
    await ctx.send(f"🪙 The coin landed on: **{result}**")

@bot.command(
    help="Roll dice! Usage: !roll <number_of_dice> <dice_type>. "
         "Example: !roll 2 20 for 2d20. "
         "Supported dice types: d4, d6, d8, d10, d12, d20, d100."
)
async def roll(ctx, num_dice: int = 1, dice_type: int = 6):
    rolls = roll_dice(num_dice, dice_type)
    if len(rolls) == 1:
        await ctx.send(f"🎲 You rolled a **{rolls[0]}** on a d{dice_type}")
    else:
        rolls_str = ', '.join(str(r) for r in rolls)
        await ctx.send(f"🎲 You rolled: {rolls_str} (Total: {sum(rolls)}) on {len(rolls)}d{dice_type}")

@bot.command(name="8ball", help="Ask the Magic 8 Ball a yes/no question! Usage: !8ball <your question>")
async def _8ball(ctx, *, question: str = None):
    if not question:
        await ctx.send("🎱 Please ask a yes/no question. Usage: `!8ball <your question>`")
        return
    answer = magic_8_ball()
    await ctx.send(f"🎱 Question: {question}\nMagic 8 Ball says: **{answer}**")

@bot.command(help="Show the current required role for using bot commands (ADMIN only)", hidden=True)
async def showrole(ctx):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    await ctx.send(f"Current required role: `{get_required_role()}`")

@bot.command(help="Set the required role for using bot commands (ADMIN only)", hidden=True)
async def setrole(ctx, *, role_name: str):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    set_required_role(role_name)
    await ctx.send(f"Required role for bot commands set to `{role_name}`.")

@bot.command(name="si-server", help="Show general server info.")
async def si_server(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"🏠 Server Info: {guild.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
    embed.add_field(name="👑 Owner", value=str(guild.owner), inline=True)
    embed.add_field(name="🌍 Region", value=str(getattr(guild, 'region', 'N/A')), inline=True)
    embed.add_field(name="📅 Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name="si-members", help="Show member statistics for this server.")
async def si_members(ctx):
    guild = ctx.guild
    total = guild.member_count
    online = sum(1 for m in guild.members if m.status == discord.Status.online)
    idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
    dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
    bots = sum(1 for m in guild.members if m.bot)
    humans = total - bots
    msg = (
        f"**👥 Member Stats for {guild.name}:**\n"
        f"👤 Total: {total}\n"
        f"🧑‍🤝‍🧑 Humans: {humans}\n"
        f"🤖 Bots: {bots}\n"
        f"🟢 Online: {online}\n"
        f"🌙 Idle: {idle}\n"
        f"⛔ Do Not Disturb: {dnd}\n"
        f"⚫ Offline: {offline}"
    )
    await ctx.send(msg)

@bot.command(name="si-emojis", help="List all custom emojis in this server.")
async def si_emojis(ctx):
    guild = ctx.guild
    if not guild.emojis:
        await ctx.send("This server has no custom emojis.")
        return
    emoji_list = [str(e) for e in guild.emojis]
    # Discord message limit: chunk if needed
    chunk_size = 50
    for i in range(0, len(emoji_list), chunk_size):
        chunk = emoji_list[i:i+chunk_size]
        await ctx.send(" ".join(chunk))

@bot.command(name="si-stickers", help="List all custom stickers in this server.")
async def si_stickers(ctx):
    guild = ctx.guild
    stickers = await guild.fetch_stickers()
    if not stickers:
        await ctx.send("This server has no custom stickers.")
        return
    msg = "**Custom Stickers:**\n"
    for sticker in stickers:
        msg += f"- {sticker.name} ([preview]({sticker.url}))\n"
    # Discord message limit: send as file if too long
    if len(msg) > 1900:
        await send_long_response(ctx, msg, filename="stickers.txt")
    else:
        await ctx.send(msg)

bot.run(token, log_handler=handler, log_level=logging.ERROR)
