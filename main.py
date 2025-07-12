#!/usr/bin/env python3

# Copyright (c) 2025 Robert McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json
import shutil
import time
import sys
from datetime import datetime, timezone
from bot_games import flip_coin, roll_dice, magic_8_ball
from fishing_game import setup_fishing
from fishing_contest import setup_fishing_contest
from chatgpt import setup_chatgpt, set_globals as set_chatgpt_globals, setup_cleanup_task

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

# Extract prompts and max_tokens from config
prompts = config.get("prompts", {})
max_tokens = config.get("max_tokens", {})
token_usage_enabled = config.get("tokenuse", False)

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

def get_chat_thread_retention_days():
    return config.get("chat_thread_retention_days", 7)

# --- End Persistent Config Helpers ---

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Add this
OPENAI_ALL_ACCESS = os.getenv("OPENAI_ALL_ACCESS")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None, case_insensitive=True)

CONVO_DB = "conversations.db"

# Set up ChatGPT module - pass the API key
set_chatgpt_globals(prompts, max_tokens, config, token_usage_enabled, CONVO_DB, OPENAI_API_KEY)
setup_chatgpt(bot)

# Utility functions
def chunk_and_send(ctx, text, chunk_size=1900):
    """Yield chunks of text for Discord message limits."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]

# --- Bot Commands ---

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

@bot.command(name="funbot", help="List all commands and their descriptions.")
async def funbot_command(ctx):
    retention_days = get_chat_thread_retention_days()
    
    embed = discord.Embed(
        title="✨ FunBot Command List ✨",
        description="Here are the commands you can use:",
        color=discord.Color.purple()
    )

    # Main commands (exclude fishing and game commands)
    fishing_commands = {"fish", "f", "cast", "fishing", "fishadmin", "fishingadmin", 
                       "fishhelp", "fishinghelp", "fishinfo", "fishlist", "fishstats",
                       "joincontest", "contestinfo", "contestlb", "pastcontests", 
                       "contestresults", "contesthelp", "startcontest", "cancelcontest"}
    game_commands = {"flip", "roll", "8ball"}
    
    filtered_commands = [
        cmd for cmd in bot.commands 
        if not cmd.hidden 
        and cmd.name not in fishing_commands 
        and cmd.name not in game_commands
        and cmd.name not in {"chat", "endchat", "mythreads", "allthreads", "threadages"}
        and not cmd.name.startswith("si-")
    ]
    commands_sorted = sorted(filtered_commands, key=lambda c: c.name)
    
    emoji_map = {
        "feelgood": "😊",
        "inspo": "💡",
        "bday": "🎂",
        "joke": "😂",
        "compliment": "🌟",
        "advice": "📝",
        "image": "🖼️",
        "q": "⚡",
        "showprompts": "📋",
        "botinfo": "ℹ️",
        "funbot": "🤖",
        "games": "🎮",
    }
    
    # Split general commands into chunks if needed
    main_cmds = []
    for command in commands_sorted:
        emoji = emoji_map.get(command.name, "•")
        usage = f" {command.usage}" if hasattr(command, "usage") and command.usage else ""
        if command.aliases:
            main_cmds.append(f"{emoji} **!{command.name}**/**!{'/!'.join(command.aliases)}**{usage} — {command.help}")
        else:
            main_cmds.append(f"{emoji} **!{command.name}**{usage} — {command.help}")
    
    if "!botinfo" not in str(main_cmds):
        main_cmds.append("ℹ️ **!botinfo** — Show info about this bot and important policies.")
    if "!games" not in str(main_cmds):
        main_cmds.append("🎮 **!games** — List all available games and how to use them.")
    
    # Join commands and check length
    main_cmds_text = "\n".join(main_cmds)
    if len(main_cmds_text) > 1024:
        # Split into two fields
        mid_point = len(main_cmds) // 2
        first_half = "\n".join(main_cmds[:mid_point])
        second_half = "\n".join(main_cmds[mid_point:])
        embed.add_field(name="General Commands (1/2)", value=first_half, inline=False)
        embed.add_field(name="General Commands (2/2)", value=second_half, inline=False)
    else:
        embed.add_field(name="General Commands", value=main_cmds_text, inline=False)

    # Games
    games_text = (
        "🎱 **!8ball <your question>** — Ask the Magic 8 Ball a yes/no question.\n"
        "🪙 **!flip** — Flip a coin.\n"
        "🎲 **!roll <number_of_dice> <dice_type>** — Roll dice! Example: `!roll 2 20` for 2d20.\n"
        "Supported dice types: d4, d6, d8, d10, d12, d20, d100 (default is d6)."
    )
    embed.add_field(name="🎮 Games", value=games_text, inline=False)

    # Fishing Game
    fishing_text = (
        "🎣 **!fish**/**!f**/**!cast**/**!fishing** — Go fishing! Try your luck and catch a fish.\n"
        "🎣 **!fishhelp**/**!fishinghelp** — Show fishing game help and commands.\n"
        "📋 **!fishinfo <FishName>** — Show info and image for a specific fish.\n"
        "📜 **!fishlist** — List all fish and their stats in a table.\n"
        "🏆 **!fishstats [@user]** — Show the fishing leaderboard and your stats.\n"
        "🛠️ **!fishadmin**/**!fishingadmin** — Show all fishing admin commands (admin only)."
    )
    embed.add_field(name="🎣 Fishing Game", value=fishing_text, inline=False)

    # Conversational Chat Commands
    chat_text = (
        f"💬 **!chat**/**!ask**/**!query** <your message> — Start a new ChatGPT thread. The bot will remember your conversation in that thread.\n"
        "🛑 **!endchat** — End your chat early and delete the thread and its memory (only the thread creator can use this).\n"
        "📋 **!mythreads** — List all your active chat threads.\n"
        "📋 **!allthreads** — (Admin) List all active chat threads.\n"
        f"*Note: Only you (the thread creator) can end your chat early. Otherwise, threads and their memory are deleted automatically after {retention_days} days.*"
    )
    embed.add_field(name="💬 Conversational Chat Commands", value=chat_text, inline=False)

    # Server Info
    server_info = (
        "🏠 **!si-server** — Show general server info (name, ID, owner, region, creation date, member count).\n"
        "👥 **!si-members** — Show member statistics (total, humans, bots, online/offline breakdown).\n"
        "😃 **!si-emojis** — List all custom emojis in this server.\n"
        "🗒️ **!si-stickers** — List all custom stickers in this server.\n"
        "🛡️ **!si-mods** — List all server moderators and admins."
    )
    embed.add_field(name="🏠 Server Info Commands", value=server_info, inline=False)

    embed.set_footer(text="Tip: Use !command for more info on each command. For games, use !games.")

    await ctx.send(embed=embed)

# --- Admin-only commands for config management ---

@bot.command(help="Show admin commands (ADMIN only)", hidden=True)
async def adminhelp(ctx):
    if not is_admin(ctx):
        return

    embed = discord.Embed(
        title="🛠️ Admin Commands",
        description="**Only the user with the `ADMIN_USER_ID` can use these commands.**",
        color=discord.Color.from_rgb(255, 115, 250)
    )

    embed.add_field(
        name="__Prompt Management__",
        value=(
            "`!setprompt <command> <variant> <template>` - Set a prompt for a command/variant\n"
            "`!showprompt <command> [variant]` - Show the prompt for a command/variant\n"
            "`!showprompts` - Show all prompts currently set up"
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="────────────", inline=False)

    embed.add_field(
        name="__Token Management__",
        value=(
            "`!setmaxtokens <command> <value>` - Set max tokens for a command\n"
            "`!showmaxtokens` - Show current max_tokens settings\n"
            "`!settokenuse on|off` - Enable or disable token usage debugging"
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="────────────", inline=False)

    embed.add_field(
        name="__Conversational Chat Management__",
        value=(
            "`!chat <your message>` - Start a new ChatGPT thread (user command)\n"
            "`!endchat` - End and delete your chat thread early (user command, or admin override)\n"
            "`!setchatretention <time>` - Set how many days/hours chat threads and their memory are kept (e.g., 1d, 12h, 1d12h, 6d)\n"
            "`!threadages` - List all active chat threads with their age and time until expiration (admin only)\n"
            "Admins can set how many days chat threads and their memory are kept using the `chat_thread_retention_days` config option (default: 7 days).\n"
            "Admins can now also end any chat thread early with `!endchat` inside the thread."
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="────────────", inline=False)

    misc_cmds = [
        ("!showconfig", "Show the entire config.json file"),
        ("!reloadconfig", "Reload the configuration from myconfig.json"),
        ("!showrole", "Show the current required role for using bot commands"),
        ("!setrole <role_name>", "Set the required role for using bot commands"),
        ("!adminhelp", "Show this list of admin commands"),
    ]
    misc_cmds_sorted = sorted(misc_cmds, key=lambda x: x[0])
    misc_text = "\n".join(f"`{cmd}` - {desc}" for cmd, desc in misc_cmds_sorted)
    embed.add_field(
        name="__Miscellaneous__",
        value=misc_text,
        inline=False
    )

    await ctx.send(embed=embed)

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
        from chatgpt import send_long_response
        await send_long_response(ctx, msg, filename="prompts.txt")
    else:
        await ctx.send(msg)

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

@bot.command(help="Set how many days/hours chat threads and their memory are kept (ADMIN only). Usage: !setchatretention <time> (e.g., 1d, 12h, 1d12h, 6d)", hidden=True)
async def setchatretention(ctx, *, time_str: str):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    
    # Parse time string (e.g., "1d", "12h", "1d12h", "6d")
    import re
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?'
    match = re.match(pattern, time_str.strip())
    
    if not match or (not match.group(1) and not match.group(2)):
        await ctx.send("Invalid time format. Please use formats like: 1d, 12h, 1d12h, 6d")
        return
    
    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    
    total_hours = (days * 24) + hours
    total_days = total_hours / 24
    
    # Validate range (minimum 1 hour, maximum 30 days)
    if total_hours < 1:
        await ctx.send("Please provide a retention period of at least 1 hour.")
        return
    if total_days > 30:
        await ctx.send("Please provide a retention period of 30 days or less.")
        return
    
    # Store as decimal days for compatibility
    config["chat_thread_retention_days"] = total_days
    save_config(config)
    
    # Format response message
    if days and hours:
        time_display = f"{days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''}"
    elif days:
        time_display = f"{days} day{'s' if days != 1 else ''}"
    else:
        time_display = f"{hours} hour{'s' if hours != 1 else ''}"
    
    await ctx.send(f"Chat thread retention period set to {time_display} ({total_days:.2f} days). This will apply to new and existing threads.")

@bot.command(help="Reload the configuration from myconfig.json (ADMIN only)", hidden=True)
async def reloadconfig(ctx):
    global config, prompts, max_tokens, token_usage_enabled
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    try:
        start = time.perf_counter()
        with open(CONFIG_FILE, "r") as f:
            lines = f.readlines()
        config = json.loads("".join(lines))
        # Update globals
        prompts = config.get("prompts", {})
        max_tokens = config.get("max_tokens", {})
        token_usage_enabled = config.get("tokenuse", False)
        # Update ChatGPT module globals
        set_chatgpt_globals(prompts, max_tokens, config, token_usage_enabled, CONVO_DB, OPENAI_API_KEY)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        await ctx.send(f"Configuration reloaded from myconfig.json in {elapsed:.1f} ms ({len(lines)} lines read).")
    except Exception as e:
        await ctx.send(f"Failed to reload configuration: {e}")

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

@bot.command(help="Show the entire config from myconfig.json (ADMIN only)", hidden=True)
async def showconfig(ctx):
    if not is_admin(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    # Pretty print config
    config_str = json.dumps(config, indent=2)
    if len(config_str) > 1900:
        from chatgpt import send_long_response
        await send_long_response(ctx, f"```json\n{config_str}\n```", filename="config.json")
    else:
        await ctx.send(f"```json\n{config_str}\n```")

# --- Bot Info and Server Info Commands ---

@bot.command(help="Show info about this bot and important policies.")
async def botinfo(ctx):
    # Try to get the current git branch
    branch = "unknown"
    commit_hash = "unknown"
    commit_date = "unknown"
    last_merge = "unknown"
    commits_ahead = 0
    commits_behind = 0
    
    try:
        import subprocess
        
        # Get current branch
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        
        # Get current commit hash (short)
        commit_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
        
        # Get commit date
        commit_date = subprocess.check_output(["git", "log", "-1", "--format=%cd", "--date=short"]).decode("utf-8").strip()
        
        # Get last merge commit date
        try:
            last_merge = subprocess.check_output(
                ["git", "log", "--merges", "-1", "--format=%cd", "--date=short"]
            ).decode("utf-8").strip()
        except:
            last_merge = "No merges found"
        
        # Get commits ahead/behind main
        if branch != "main":
            try:
                # Fetch latest (optional, might fail without internet)
                subprocess.run(["git", "fetch"], capture_output=True)
                
                # Get ahead/behind counts
                ahead_behind = subprocess.check_output(
                    ["git", "rev-list", "--left-right", "--count", f"origin/main...{branch}"]
                ).decode("utf-8").strip()
                behind, ahead = ahead_behind.split()
                commits_behind = int(behind)
                commits_ahead = int(ahead)
            except:
                pass
                
    except Exception:
        pass

    # Git info formatting
    git_info = f"**Branch:** `{branch}`"
    if branch == "main":
        git_info += " (main branch)"
    else:
        git_info += f" ({commits_ahead} ahead, {commits_behind} behind main)" if commits_ahead or commits_behind else ""
    
    git_info += f"\n**Commit:** `{commit_hash}` ({commit_date})"
    if last_merge and last_merge != "No merges found":
        git_info += f"\n**Last Merge:** {last_merge}"

    # Count lines of code
    code_files = ["main.py", "bot_games.py", "chatgpt.py", "fishing_game.py"]
    total_lines = 0
    file_stats = []
    for file in code_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
                total_lines += lines
                file_stats.append(f"{file}: {lines}")
        except Exception:
            pass

    code_info = f"**Python Code:** {total_lines} lines total"
    
    # Get bot uptime
    uptime_str = "Unknown"
    if hasattr(bot, 'start_time'):
        uptime = datetime.now(timezone.utc) - bot.start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        else:
            uptime_str = f"{minutes}m"
    
    # Server count
    server_count = len(bot.guilds)
    total_users = sum(guild.member_count for guild in bot.guilds)
    
    # Create embed for better formatting
    embed = discord.Embed(
        title="Discord ChatGPT Fun Bot 🤖✨",
        description="Bringing positive vibes, inspiration, and AI creativity to your server!",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="📊 Bot Statistics",
        value=f"Servers: **{server_count}**\nUsers: **{total_users:,}**\nUptime: **{uptime_str}**",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Version Info",
        value=f"Branch: **{branch}**\nCommit: **{commit_hash}**\nPython: **{sys.version.split()[0]}**",
        inline=True
    )
    
    embed.add_field(
        name="📝 Code Stats",
        value=f"Total Lines: **{total_lines}**\nFiles: **{len(code_files)}**",
        inline=True
    )
    
    if branch != "main" and (commits_ahead or commits_behind):
        embed.add_field(
            name="🔀 Branch Status",
            value=f"**{commits_ahead}** ahead, **{commits_behind}** behind main",
            inline=False
        )
    
    embed.add_field(
        name="📜 Legal",
        value="[Privacy Policy](https://github.com/M1XZG/discord-bot-for-fun/blob/main/PRIVACY_POLICY.md) • [Terms of Service](https://github.com/M1XZG/discord-bot-for-fun/blob/main/TERMS_OF_SERVICE.md)",
        inline=False
    )
    
    embed.set_footer(text=f"Last commit: {commit_date} • Last merge: {last_merge}")
    
    await ctx.send(embed=embed)

# Track bot start time
@bot.event
async def on_ready():
    if not hasattr(bot, 'start_time'):
        bot.start_time = datetime.now(timezone.utc)
    print(f'{bot.user} has connected to Discord!')

# Game commands
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

# Server info commands
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
        from chatgpt import send_long_response
        await send_long_response(ctx, msg, filename="stickers.txt")
    else:
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
        from chatgpt import send_long_response
        await send_long_response(ctx, msg, filename="moderators.txt")
    else:
        await ctx.send(msg)

# Role checking
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

# Setup other modules
setup_fishing(bot)
setup_fishing_contest(bot)

@bot.event
async def setup_hook():
    """Initialize bot tasks."""
    # Import here to avoid circular imports
    from chatgpt import cleanup_old_threads
    bot.loop.create_task(cleanup_old_threads(bot))

# Run the bot
bot.run(token, log_handler=handler, log_level=logging.ERROR)
