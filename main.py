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

@bot.command(name="funbot", help="List all commands and their descriptions.")
async def funbot_command(ctx):
    help_text = (
        "✨ **__FunBot Command List__** ✨\n"
        "Here are the commands you can use:\n\n"
    )
    commands_sorted = sorted(
        (cmd for cmd in bot.commands if not cmd.hidden),
        key=lambda c: c.name
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
    }
    for command in commands_sorted:
        emoji = emoji_map.get(command.name, "•")
        usage = f" {command.usage}" if hasattr(command, "usage") and command.usage else ""
        # Special case: show both !query and !ask for the query command
        if command.name == "query" and "ask" in command.aliases:
            help_text += f"{emoji} **!query**/**!ask**{usage} — {command.help}\n"
        else:
            help_text += f"{emoji} **!{command.name}**{usage} — {command.help}\n"
    # Add botinfo command explicitly if not already present
    if "!botinfo" not in help_text:
        help_text += "ℹ️ **!botinfo** — Show info about this bot and important policies.\n"

    help_text += (
        "\n__Tip__: Use `!command` for more info on each command. "
        "For privacy and terms, see `!botinfo`."
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
        # Discord code block, limit to 1990 chars for safety
        if len(config_str) > 1990:
            await send_long_response(ctx, f"```json\n{config_str}\n```", filename="config.json")
        else:
            await ctx.send(f"```json\n{config_str}\n```")
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
    help_text += (
        "`!showconfig` - Show the entire config.json file\n"
        "`!reloadconfig` - Reload the configuration from myconfig.json\n"
        "`!adminhelp` - Show this list of admin commands\n"
    )

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
    funbot_role = discord.utils.get(ctx.author.roles, name="funbot")
    if funbot_role is None:
        await ctx.send("You are not entitled to run this command. Access is at the owner's discretion.")
        return False
    return True

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
        "• [Privacy Policy](https://github.com/M1XZG/discord-bot-for-fun/blob/main/PRIVACY_POLICY.md)\n"
        "• [Terms of Service](https://github.com/M1XZG/discord-bot-for-fun/blob/main/TERMS_OF_SERVICE.md)\n"
        "Please read these documents for details on data usage and your rights."
    )
    await ctx.send(info)

bot.run(token, log_handler=handler, log_level=logging.ERROR)
