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
import platform
import re
from games import setup_games
from fishing_game import setup_fishing
from fishing_contest import setup_contest
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

# Optional single admin override (from env or config). If unset, defaults to 0 (disabled)
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID") or config.get("admin_user_id", 0) or 0)

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

def get_chatgpt_required_role():
    # Backward compatible: prefer a dedicated key, fallback to legacy 'required_role'
    return config.get("chatgpt_required_role", config.get("required_role"))

def set_chatgpt_required_role(role_name):
    config["chatgpt_required_role"] = role_name
    save_config(config)

def get_features():
    # Default: all features enabled
    return config.setdefault("features", {
        "chatgpt": True,
        "fishing": True,
        "games": True,
    })

def is_feature_enabled(name: str) -> bool:
    feats = get_features()
    return bool(feats.get(name, True))

def set_feature(name: str, enabled: bool):
    feats = get_features()
    if name not in ("chatgpt", "fishing", "games"):
        raise ValueError("Invalid feature name")
    feats[name] = bool(enabled)
    config["features"] = feats
    save_config(config)

# Add this helper (used by global check and admin-only commands)
def is_admin_like(ctx) -> bool:
    perms = getattr(ctx.author, "guild_permissions", None)
    return (
        (perms and (perms.administrator or perms.manage_guild))
        or (ctx.author.id == ADMIN_USER_ID)
    )

# Feature categories used for gating and in help
FISHING_COMMANDS = {
    # Fishing core
    "fish", "fishhelp", "fishinghelp", "fishinfo", "fishlist", "fishstats",
    # Fishing admin
    "addfish", "setfishcooldown", "fishcooldown", "fishadmin", "fishingadmin", "fplayer",
    # Contest
    "startcontest", "endcontest", "cancelcontest", "stopcontest", "conteststatus",
    "joincontest", "contesthelp", "contesthistory", "contestinfo", "schedulecontest",
}

GAME_COMMANDS = {"flip", "roll", "8ball", "botinfo", "rps", "rpsstats", "choose"}

CHATGPT_COMMANDS = {
    # Conversational
    "chat", "ask", "query", "q", "endchat", "mythreads", "allthreads", "threadages",
    # Content
    "feelgood", "inspo", "bday", "joke", "compliment", "advice", "image",
    # Admin/config for ChatGPT
    "setmaxtokens", "setprompt", "showmaxtokens", "showprompts", "toggletokenusage",
    "setchatretention",
}

# Admin-only subsets per feature
CHATGPT_ADMIN_COMMANDS = {
    "setmaxtokens", "showmaxtokens", "setprompt", "showprompts",
    "toggletokenusage", "setchatretention", "setchatgptrole", "showchatgptrole",
    "setrole", "showrole",
    # admin thread utilities
    "allthreads", "threadages",
}

FISHING_ADMIN_COMMANDS = {
    # fishing admin
    "fishadmin", "addfish", "setfishcooldown", "fishcooldown",
    # contest admin
    "contestadmin", "startcontest", "endcontest", "cancelcontest", "schedulecontest",
}

ADMIN_CORE_COMMANDS = {
    # feature toggles and global admin
    "features", "enable", "disable", "setfeature", "showfeatures",
}

ADMIN_COMMANDS_GLOBAL = ADMIN_CORE_COMMANDS | CHATGPT_ADMIN_COMMANDS | FISHING_ADMIN_COMMANDS

# Track start time for uptime reporting
BOT_START_TIME: datetime | None = None

# Accept friendly names and common typos for features
FEATURE_ALIASES = {
    "chatgpt": {"chatgpt", "chat", "gpt", "ai", "chatgtp"},  # includes common typo
    "fishing": {"fishing", "fish"},
    "games": {"games", "game"},
}

def normalize_feature_name(name):
    if not name:
        return None
    n = name.lower().strip()
    for key, aliases in FEATURE_ALIASES.items():
        if n in aliases:
            return key
    return None

# --- Bot Code ---

# Suppress deprecation warnings from Discord.py
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Intents are required for receiving events about guilds, members, and messages
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Required for accessing message content in events

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)
bot.remove_command("help")  # Use our custom help

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

# Initialize ChatGPT commands and globals
set_chatgpt_globals(prompts, max_tokens, config, token_usage_enabled, "conversations.db", api_key=os.getenv("OPENAI_API_KEY"))
setup_chatgpt(bot)
setup_cleanup_task(bot)
setup_games(bot, is_feature_enabled)
# Wire real fishing/contest modules (registers commands like !fish/!f and contest admin)
setup_fishing(bot)
setup_contest(bot)

# --- Admin Commands ---

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def setfeature(ctx, name: str, *, value: str):
    """Set a feature flag for the server."""
    enabled = value.lower() in ("true", "1", "yes")
    try:
        set_feature(name, enabled)
        await ctx.send(f"Feature `{name}` has been {'enabled' if enabled else 'disabled'}.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command(help="Show feature toggle status (ADMIN only).", aliases=["showfeatures"])
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def features(ctx):
    feats = get_features()
    def onoff(b): return "ON ✅" if b else "OFF ❌"
    embed = discord.Embed(
        title="⚙️ Feature Toggles",
        color=discord.Color.teal(),
        description="Enable/disable major modules at runtime."
    )
    embed.add_field(name="ChatGPT", value=onoff(feats.get("chatgpt", True)))
    embed.add_field(name="Fishing", value=onoff(feats.get("fishing", True)))
    embed.add_field(name="Games", value=onoff(feats.get("games", True)))
    embed.set_footer(text="Use !enable <chatgpt|fishing|games> or !disable <chatgpt|fishing|games>")
    await ctx.send(embed=embed)

@bot.command(help="Enable a feature (ADMIN only). Usage: !enable <chatgpt|fishing|games>", aliases=["enablefeature"])
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def enable(ctx, feature: str = None):
    key = normalize_feature_name(feature)
    if not key:
        await ctx.send("Usage: !enable <chatgpt|fishing|games>")
        return
    set_feature(key, True)
    await ctx.send(f"✅ Enabled: {key}")

@bot.command(help="Disable a feature (ADMIN only). Usage: !disable <chatgpt|fishing|games>", aliases=["disablefeature"])
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def disable(ctx, feature: str = None):
    key = normalize_feature_name(feature)
    if not key:
        await ctx.send("Usage: !disable <chatgpt|fishing|games>")
        return
    set_feature(key, False)
    await ctx.send(f"❌ Disabled: {key}")

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def setmaxtokens(ctx, command: str, value: int):
    """Set the max tokens for a command."""
    try:
        set_max_tokens(command, value)
        await ctx.send(f"Max tokens for `{command}` set to {value}.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def showmaxtokens(ctx):
    """Show the current max tokens settings."""
    max_tokens = config.get("max_tokens", {})
    if not max_tokens:
        await ctx.send("No max tokens set for any commands.")
    else:
        token_lines = [f"{cmd}: {tokens}" for cmd, tokens in max_tokens.items()]
        await ctx.send("\n".join(token_lines))

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def setprompt(ctx, *, prompt: str):
    """Set the prompt for the ChatGPT commands."""
    config["prompts"]["chat"] = prompt
    save_config(config)
    await ctx.send("Prompt updated.")

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def showprompts(ctx):
    """Show the current prompts."""
    prompts = config.get("prompts", {})
    if not prompts:
        await ctx.send("No prompts set for any commands.")
    else:
        prompt_lines = [f"{cmd}: {prompt}" for cmd, prompt in prompts.items()]
        await ctx.send("\n".join(prompt_lines))

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def toggletokenusage(ctx):
    """Toggle the global token usage tracking."""
    current = get_tokenuse()
    set_tokenuse(not current)
    await ctx.send(f"Token usage tracking has been {'enabled' if not current else 'disabled'}.")

@bot.command()
@commands.check(lambda ctx: is_admin_like(ctx) and ctx.guild is not None)
async def setchatretention(ctx, days: int):
    """Set the number of days to retain chat threads."""
    if days < 0:
        await ctx.send("Retention days cannot be negative.")
        return
    config["chat_thread_retention_days"] = days
    save_config(config)
    await ctx.send(f"Chat thread retention period set to {days} days.")

@bot.command(
    name="showchatgptrole",
    aliases=["showrole"],  # legacy alias
    help="Show the required role for ChatGPT (ADMIN only).",
    hidden=True,
)
async def showchatgptrole(ctx):
    if not is_admin_like(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    role = get_chatgpt_required_role()
    await ctx.send(f"ChatGPT required role: `{role or 'none'}`")

@bot.command(
    name="setchatgptrole",
    aliases=["setrole"],  # legacy alias
    help="Set the required role for ChatGPT (ADMIN only). Usage: !setchatgptrole <role|none>",
    hidden=True,
)
async def setchatgptrole(ctx, *, role_name: str):
    if not is_admin_like(ctx):
        await ctx.send("You are not authorized to use this command.")
        return
    if role_name.lower() in ("none", "null", "off"):
        set_chatgpt_required_role(None)
        await ctx.send("ChatGPT role requirement has been cleared.")
    else:
        set_chatgpt_required_role(role_name)
        await ctx.send(f"ChatGPT required role set to `{role_name}`.")

# --- Fishing and contest commands are provided by fishing_game.py and fishing_contest.py ---

# --- ChatGPT Commands ---
# Handled by chatgpt.setup_chatgpt(bot), which registers all ChatGPT-related commands.


@bot.command(help="Show bot info and uptime.")
async def botinfo(ctx):
    """Display basic bot information, uptime, and feature toggles."""
    # Uptime
    now = datetime.now(timezone.utc)
    if BOT_START_TIME:
        delta = now - BOT_START_TIME
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    else:
        uptime_str = "unknown"

    feats = get_features()
    def onoff(b): return "ON ✅" if b else "OFF ❌"

    embed = discord.Embed(
        title="🤖 Bot Info",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Version", value=config.get("version", "dev"))
    embed.add_field(name="Python", value=platform.python_version())
    embed.add_field(name="discord.py", value=discord.__version__)
    embed.add_field(name="Guilds", value=str(len(bot.guilds)))
    embed.add_field(name="Users (cached)", value=str(len(bot.users)))
    embed.add_field(name="Uptime", value=uptime_str)
    embed.add_field(name="Features",
                    value=(
                        f"ChatGPT: {onoff(feats.get('chatgpt', True))}\n"
                        f"Fishing: {onoff(feats.get('fishing', True))}\n"
                        f"Games: {onoff(feats.get('games', True))}"
                    ),
                    inline=False)
    await ctx.send(embed=embed)

# --- Error Handling ---

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown command. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please check your input.")
    elif isinstance(error, commands.CheckFailure):
        # Triggered when admin-only checks fail
        await ctx.send("You don't have permission to use that command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")
        logger.error(f"Error in command {ctx.command}: {str(error)}", exc_info=True)

# --- Startup ---

@bot.event
async def on_ready():
    """Bot startup sequence."""
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info("------")
    # Load initial config
    global config
    global BOT_START_TIME
    config = load_config()
    BOT_START_TIME = datetime.now(timezone.utc)
    # Sync commands with Discord
    await bot.tree.sync()
    logger.info("Commands synced with Discord.")

def _collect_commands_by_names(names: set[str]):
    """Return sorted list of Command objects whose name is in names."""
    name_map = {cmd.name: cmd for cmd in bot.commands}
    cmds = [name_map[n] for n in names if n in name_map]
    return sorted(cmds, key=lambda c: c.name)

def _format_cmd_lines(cmds: list[commands.Command], max_lines: int | None = None):
    """Format commands as list lines with their help."""
    lines = []
    for cmd in cmds:
        desc = cmd.help or (cmd.brief if hasattr(cmd, "brief") else None) or "No description."
        lines.append(f"• !{cmd.name} — {desc}")
    if max_lines and len(lines) > max_lines:
        # keep it tidy and indicate there are more
        more = len(lines) - max_lines
        lines = lines[:max_lines] + [f"...and {more} more."]
    return "\n".join(lines) if lines else "_None_"

def _safe_field_value(text: str, limit: int = 1024) -> str:
    """Ensure embed field value does not exceed Discord's 1024-char limit."""
    if text is None:
        return "_None_"
    return text if len(text) <= limit else (text[: limit - 1] + "…")

def _section_enabled_label(enabled: bool):
    return "Enabled ✅" if enabled else "Disabled ❌"

def _resolve_section_name(arg: str | None):
    if not arg:
        return None
    a = arg.lower().strip()
    if a in {"chatgpt", "chat", "gpt", "ai"}:
        return "chatgpt"
    if a in {"games", "game"}:
        return "games"
    if a in {"fishing", "fish"}:
        return "fishing"
    if a in {"admin", "admins", "adminfunctions", "admin-funcs"}:
        return "admin"
    return None

@bot.command(name="help", help="Show help for all categories, or use !help <chatgpt|games|fishing|admin>.")
async def help_command(ctx, section: str = None):
    """Custom, sectioned help."""
    sec = _resolve_section_name(section)

    # Build command lists per category (user and admin splits)
    chatgpt_cmds_all = _collect_commands_by_names(CHATGPT_COMMANDS)
    chatgpt_cmds_admin = _collect_commands_by_names(CHATGPT_ADMIN_COMMANDS)
    chatgpt_cmds_user = [c for c in chatgpt_cmds_all if c.name not in CHATGPT_ADMIN_COMMANDS]

    games_cmds = _collect_commands_by_names(GAME_COMMANDS)

    fishing_cmds_all = _collect_commands_by_names(FISHING_COMMANDS)
    fishing_cmds_admin = _collect_commands_by_names(FISHING_ADMIN_COMMANDS)
    fishing_cmds_user = [c for c in fishing_cmds_all if c.name not in FISHING_ADMIN_COMMANDS]

    admin_cmds_global = _collect_commands_by_names(ADMIN_COMMANDS_GLOBAL)

    # Feature toggle labels
    chatgpt_enabled = is_feature_enabled("chatgpt")
    games_enabled = is_feature_enabled("games")
    fishing_enabled = is_feature_enabled("fishing")

    # Determine if viewer is admin-like
    admin_like = is_admin_like(ctx)

    # If a specific section was requested, show only that
    if sec:
        embed = discord.Embed(
            title=f"Help — {sec.capitalize()}",
            color=discord.Color.purple()
        )
        if sec == "chatgpt":
            embed.description = f"{_section_enabled_label(chatgpt_enabled)}"
            embed.add_field(
                name="ChatGPT — User Commands",
                value=_safe_field_value(_format_cmd_lines(chatgpt_cmds_user, max_lines=20)),
                inline=False
            )
            if admin_like:
                embed.add_field(
                    name="ChatGPT — Admin Commands",
                    value=_safe_field_value(_format_cmd_lines(chatgpt_cmds_admin, max_lines=20)),
                    inline=False
                )
        elif sec == "games":
            embed.description = f"{_section_enabled_label(games_enabled)}"
            embed.add_field(
                name="Games",
                value=_safe_field_value(_format_cmd_lines(games_cmds, max_lines=20)),
                inline=False
            )
        elif sec == "fishing":
            embed.description = f"{_section_enabled_label(fishing_enabled)}"
            embed.add_field(
                name="Fishing — User Commands",
                value=_safe_field_value(_format_cmd_lines(fishing_cmds_user, max_lines=20)),
                inline=False
            )
            if admin_like:
                embed.add_field(
                    name="Fishing — Admin Commands",
                    value=_safe_field_value(_format_cmd_lines(fishing_cmds_admin, max_lines=20)),
                    inline=False
                )
        elif sec == "admin":
            if admin_like:
                embed.description = "Admin-only commands."
                embed.add_field(
                    name="Administration",
                    value=_safe_field_value(_format_cmd_lines(admin_cmds_global, max_lines=25)),
                    inline=False
                )
            else:
                embed.description = "Admin-only commands. You don't have permission to use these."
        else:
            await ctx.send("Unknown help section. Try: chatgpt, games, fishing, admin.")
            return

        await ctx.send(embed=embed)
        return

    # Otherwise, show all sections in one embed
    embed = discord.Embed(
        title="Help — Overview",
        description="Tip: you can view a specific section with `!help chatgpt`, `!help fishing`, `!help games`, or `!help admin`.",
        color=discord.Color.purple()
    )

    embed.add_field(
        name=f"💬 ChatGPT — {_section_enabled_label(chatgpt_enabled)}",
        value=_safe_field_value(
            "User: " + _format_cmd_lines(chatgpt_cmds_user, max_lines=6)
            + ("\nAdmin: " + _format_cmd_lines(chatgpt_cmds_admin, max_lines=4) if admin_like else "")
        ),
        inline=False
    )
    embed.add_field(
        name=f"🎮 Games — {_section_enabled_label(games_enabled)}",
        value=_format_cmd_lines(games_cmds, max_lines=8),
        inline=False
    )
    embed.add_field(
        name=f"🎣 Fishing — {_section_enabled_label(fishing_enabled)}",
        value=_safe_field_value(
            "User: " + _format_cmd_lines(fishing_cmds_user, max_lines=6)
            + ("\nAdmin: " + _format_cmd_lines(fishing_cmds_admin, max_lines=4) if admin_like else "")
        ),
        inline=False
    )

    if admin_like:
        embed.add_field(
            name="🛠️ Admin Functions",
            value=_safe_field_value(_format_cmd_lines(admin_cmds_global, max_lines=10)),
            inline=False
        )
    else:
        embed.add_field(
            name="🛠️ Admin Functions",
            value="_Admin-only commands. Ask a server admin for access._",
            inline=False
        )

    await ctx.send(embed=embed)

# --- Run the Bot ---

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("Error: DISCORD_TOKEN not found in environment variables.")
    sys.exit(1)

# Start the bot
bot.run(TOKEN)