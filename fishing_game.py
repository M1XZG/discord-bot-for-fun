#!/usr/bin/env python3

# Copyright (c) 2025 Robert McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

import os
import re
import random
import sqlite3
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import json
import shutil
from collections import defaultdict
from fishing_contest import is_contest_active, get_current_contest_id, get_contest_thread, is_contest_thread, is_contest_preparing

# Constants
FISHING_ASSETS_DIR = "FishingGameAssets"
FISH_DB = "fishing_game.db"
DEFAULT_FISHING_CONFIG_FILE = "fishing_game_config.json"
FISHING_CONFIG_FILE = "my_fishing_game_config.json"

# Module-level variables
cooldowns = {}
recent_catches = {}  # {user_id: [list of last N fish caught]}
RECENT_CATCH_MEMORY = 10

# These will be populated after loading config
RARITY_TIERS = {}
FISH_RARITY_WEIGHTS = {}
RARITY_COLORS = {}
FISH_LOOKUP = {}
NO_CATCH_CHANCE = 0.15
member_catch_ratio = 50
fish_list = []
cooldown_seconds = 30

# Excluded files
EXCLUDED_FILES = ['no-fish.png', 'nofish.png', 'no_fish.png']

def init_fishing_db():
    """Initialize the fishing database."""
    with sqlite3.connect(FISH_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS catches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_name TEXT,
                catch_type TEXT,
                catch_name TEXT,
                weight REAL,
                points INTEGER,
                timestamp DATETIME,
                contest_id TEXT
            )
        """)
        conn.commit()

def record_catch(user_id, user_name, catch_type, catch_name, weight, points, contest_id=None):
    """Record a catch in the database."""
    with sqlite3.connect(FISH_DB) as conn:
        conn.execute(
            "INSERT INTO catches (user_id, user_name, catch_type, catch_name, weight, points, timestamp, contest_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(user_id), user_name, catch_type, catch_name, weight, points, datetime.utcnow(), contest_id)
        )
        conn.commit()

def get_fish_list():
    """Get list of available fish from the assets directory."""
    fish_files = []
    for file in os.listdir(FISHING_ASSETS_DIR):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            if file.lower() not in EXCLUDED_FILES:
                fish_files.append(file)
    return fish_files

def calculate_base_points(weight_kg, size_cm):
    """Calculate base points for any catch."""
    return int(max(1, round(weight_kg * 10 + size_cm)))

def format_time_display(seconds):
    """Format seconds into a readable time string."""
    if seconds >= 60:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds > 0 else f"{minutes}m"
    return f"{seconds}s"

def load_fish_config():
    """Load fishing configuration from file."""
    global RARITY_TIERS, FISH_RARITY_WEIGHTS, RARITY_COLORS, FISH_LOOKUP, NO_CATCH_CHANCE
    global member_catch_ratio, fish_list, cooldown_seconds
    
    with open(FISHING_CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Load basic config
    member_catch_ratio = config.get("member_catch_ratio", 50)
    cooldown_seconds = config.get("cooldown_seconds", 30)
    NO_CATCH_CHANCE = config.get("no_catch_chance", 0.15)
    fish_list = config["fish"]
    
    # Load rarity tiers
    RARITY_TIERS = config.get("rarity_tiers", {})
    
    # Build weight mapping
    FISH_RARITY_WEIGHTS = {tier: data.get("weight", 50) for tier, data in RARITY_TIERS.items()}
    
    # Build color mapping
    RARITY_COLORS = {}
    for tier, data in RARITY_TIERS.items():
        color_hex = data.get("color", "#7F8C8D")
        rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        RARITY_COLORS[tier] = discord.Color.from_rgb(*rgb)
    
    # Add fallback colors
    fallback_colors = {
        "ultra-legendary": discord.Color.from_rgb(255, 20, 147),
        "legendary": discord.Color.gold(),
        "epic": discord.Color.purple(),
        "rare": discord.Color.blue(),
        "uncommon": discord.Color.green(),
        "common": discord.Color.darker_gray(),
        "junk": discord.Color.from_rgb(139, 69, 19)
    }
    for tier, color in fallback_colors.items():
        if tier not in RARITY_COLORS:
            RARITY_COLORS[tier] = color
    
    # Build fish lookup dictionary
    FISH_LOOKUP = {fish["name"].lower(): fish for fish in fish_list}
    
    return config

# Copy default config if needed
if not os.path.exists(FISHING_CONFIG_FILE):
    if os.path.exists(DEFAULT_FISHING_CONFIG_FILE):
        shutil.copy(DEFAULT_FISHING_CONFIG_FILE, FISHING_CONFIG_FILE)

# Initialize everything
init_fishing_db()
FISH_CONFIG = load_fish_config()

def setup_fishing(bot):
    """Set up all fishing-related commands."""
    
    @bot.command(name="fish", aliases=["f", "cast", "fishing"], help="Go fishing and catch something! Usage: !fish")
    async def fish(ctx):
        """Main fishing command."""
        # Import at the top of the function to avoid circular imports
        from fishing_contest import get_contest_thread, is_contest_active, is_contest_preparing, contest_state
        
        # Check contest thread logic
        contest_thread = get_contest_thread()
        
        if contest_thread and ctx.channel.id == contest_thread.id and (not is_contest_active() or is_contest_preparing()):
            if is_contest_preparing():
                # Calculate actual time remaining
                if contest_state.get("prep_start_time"):
                    # Get when prep started
                    prep_start = contest_state["prep_start_time"]
                    
                    # If prep_start_time is a string, convert it
                    if isinstance(prep_start, str):
                        prep_start = datetime.fromisoformat(prep_start)
                    
                    # Calculate elapsed time
                    elapsed = (datetime.utcnow() - prep_start).total_seconds()
                    time_until_start = max(0, 60 - elapsed)  # 60 seconds prep time
                    
                    if time_until_start > 0:
                        minutes = int(time_until_start // 60)
                        seconds = int(time_until_start % 60)
                        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                        await ctx.send(f"⚠️ The contest is still preparing! Wait for the START announcement in **{time_str}**!")
                    else:
                        await ctx.send("⚠️ The contest is starting any moment now!")
                else:
                    # Fallback if no prep_start_time
                    await ctx.send("⚠️ The contest is still preparing! Wait for the START announcement!")
            else:
                await ctx.send("⚠️ The contest hasn't started yet! Wait for the START announcement!")
            return
        
        if is_contest_active() and contest_thread and ctx.channel.id != contest_thread.id:
            await ctx.send(f"🎣 A contest is active! Please fish in the contest thread: {contest_thread.mention}")
            return
        
        # Cooldown check (skip during contests)
        if not is_contest_active():
            user_id = str(ctx.author.id)
            current_time = datetime.utcnow()
            
            if user_id in cooldowns:
                time_since_last = (current_time - cooldowns[user_id]).total_seconds()
                if time_since_last < cooldown_seconds:
                    remaining = cooldown_seconds - time_since_last
                    await ctx.send(f"🎣 You need to wait {int(remaining)}s before fishing again!")
                    return
            
            cooldowns[user_id] = current_time
        
        # Member catch logic
        if random.randint(1, member_catch_ratio) == 1:
            await catch_member(ctx)
            return

        # Random chance to catch nothing
        if random.random() < NO_CATCH_CHANCE:
            await catch_nothing(ctx)
            return

        # Catch a fish
        await catch_fish(ctx)

    async def catch_member(ctx):
        """Handle catching a server member."""
        contest_thread = get_contest_thread()  # Fix: Add this line
        members = [m for m in ctx.guild.members if not m.bot and m != ctx.author]
        if not members:
            return
            
        member = random.choice(members)
        weight_kg = round(random.uniform(55, 140), 2)
        points = calculate_base_points(weight_kg, 190) * 2500  # Ultra-legendary multiplier
        
        if is_contest_active():
            points = int(points * 1.5)
        
        embed = discord.Embed(
            title="🎣 You caught a server member!",
            description=(
                f"**{ctx.author.display_name}** caught **{member.display_name}**!\n"
                f"*A fellow server member got tangled in your line!*\n\n"
                f"**Size:** 190 cm\n"
                f"**Weight:** {weight_kg} kg\n"
                f"**Points:** {points:,}\n"
                f"**Rarity:** Ultra-Legendary" +
                ("\n🏆 **Contest Bonus Applied!**" if is_contest_active() else "")
            ),
            color=RARITY_COLORS.get("ultra-legendary", discord.Color.from_rgb(255, 20, 147))
        )
        
        embed.set_footer(text="💎✨ ULTRA-LEGENDARY CATCH! ✨💎")
        embed.set_image(url=member.display_avatar.url)
        
        contest_id = get_current_contest_id() if is_contest_active() else None
        record_catch(ctx.author.id, ctx.author.display_name, "member", member.display_name, weight_kg, points, contest_id)
        
        if is_contest_active():
            announcement = await ctx.send(f"🎉 **INCREDIBLE!** {ctx.author.mention} just caught **{member.display_name}** - an **ULTRA-LEGENDARY** catch! 💎✨")
            await announcement.add_reaction("💎")
            await announcement.add_reaction("🎉")
            await announcement.add_reaction("🔥")
        
        try:
            if is_contest_active() and contest_thread and ctx.channel.id == contest_thread.id:
                await ctx.send(embed=embed, silent=True)
            else:
                await ctx.send(embed=embed)
        except discord.errors.HTTPException:
            # Thread might be archived/deleted
            await ctx.send(embed=embed)

    async def catch_nothing(ctx):
        """Handle no catch."""
        embed = discord.Embed(
            title="🎣 No luck this time...",
            description=f"**{ctx.author.display_name}** didn't catch anything!",
            color=discord.Color.greyple()
        )
        
        consolation_messages = [
            "Better luck next time!",
            "The fish must be sleeping...",
            "Maybe try different bait?",
            "Sometimes that's just how fishing goes!",
            "Even the best anglers have off days.",
            "The fish are laughing at you somewhere...",
            "Your line came back empty!",
            "Not even a nibble!",
            "The fish aren't biting right now.",
            "Try again! Persistence pays off."
        ]
        embed.set_footer(text=random.choice(consolation_messages))
        
        no_fish_path = os.path.join(FISHING_ASSETS_DIR, "No-Fish.png")
        if os.path.exists(no_fish_path):
            file = discord.File(no_fish_path, filename="No-Fish.png")
            embed.set_image(url="attachment://No-Fish.png")
            
            try:
                if is_contest_active() and get_contest_thread() and ctx.channel.id == get_contest_thread().id:
                    await ctx.send(embed=embed, file=file, silent=True)
                else:
                    await ctx.send(embed=embed, file=file)
            except discord.errors.HTTPException:
                await ctx.send(embed=embed, file=file)
        else:
            try:
                if is_contest_active() and get_contest_thread() and ctx.channel.id == get_contest_thread().id:
                    await ctx.send(embed=embed, silent=True)
                else:
                    await ctx.send(embed=embed)
            except discord.errors.HTTPException:
                await ctx.send(embed=embed)

    async def catch_fish(ctx):
        """Handle catching a fish."""
        contest_thread = get_contest_thread()
        fish_files = get_fish_list()
        if not fish_files:
            await ctx.send("No fish assets found! Please add images to the FishingGameAssets folder.")
            return
        
        # Get user's recent catches
        user_id = str(ctx.author.id)
        user_recent = recent_catches.get(user_id, [])
        
        # Create weighted selection
        fish_weights = {}
        for fish_file in fish_files:
            fish_base = os.path.splitext(fish_file)[0].lower()
            fish_data = FISH_LOOKUP.get(fish_base)
            
            if fish_data:
                rarity = fish_data.get("rarity", "common").lower()
                weight = FISH_RARITY_WEIGHTS.get(rarity, 50)
            else:
                weight = 50
            
            # Reduce weight for recent catches
            if fish_file in user_recent:
                idx = user_recent.index(fish_file)
                reduction_factor = max(1, 10 - idx)  # Fix: Ensure never 0
                weight = max(1, weight // reduction_factor)
            
            fish_weights[fish_file] = weight
        
        # Select fish
        fish_files_list = list(fish_weights.keys())
        weights_list = list(fish_weights.values())
        fish_file = random.choices(fish_files_list, weights=weights_list, k=1)[0]
        
        # Update recent catches
        if user_id not in recent_catches:
            recent_catches[user_id] = []
        recent_catches[user_id].insert(0, fish_file)
        recent_catches[user_id] = recent_catches[user_id][:RECENT_CATCH_MEMORY]
        
        fish_base_name = os.path.splitext(fish_file)[0]
        fish_name = fish_base_name.replace("_", " ")
        
        # Get fish data
        fish_entry = FISH_LOOKUP.get(fish_base_name.lower())
        
        if fish_entry:
            size_cm = round(random.uniform(fish_entry["min_size_cm"], fish_entry["max_size_cm"]), 1)
            weight_kg = round(random.uniform(fish_entry["min_weight_kg"], fish_entry["max_weight_kg"]), 2)
            description = fish_entry.get("description", "A mysterious creature from the depths.")
            rarity = fish_entry.get("rarity", "common").lower()
            
            # Calculate points
            points = calculate_base_points(weight_kg, size_cm)
            default_max_points = calculate_base_points(fish_entry["max_weight_kg"], fish_entry["max_size_cm"])
            points = min(points, default_max_points * 2)  # Cap at 2x max
            
            if rarity == "ultra-legendary":
                points = points * 5000
            
            weight_str = f"{weight_kg} kg"
            size_str = f"{size_cm} cm"
        else:
            size_str = "unknown"
            weight_str = "unknown"
            points = 1
            weight_kg = 0
            description = "A mysterious catch!"
            rarity = "common"

        if is_contest_active():
            points = int(points * 1.5)

        # Create embed
        embed = discord.Embed(
            title="🎣 You caught a fish!",
            description=(
                f"**{ctx.author.display_name}** caught a **{fish_name}**!\n"
                f"*{description}*\n\n"
                f"**Size:** {size_str}\n"
                f"**Weight:** {weight_str}\n"
                f"**Points:** {points:,}\n"
                f"**Rarity:** {rarity.capitalize()}" +
                ("\n🏆 **Contest Bonus Applied!**" if is_contest_active() else "")
            ),
            color=RARITY_COLORS.get(rarity, discord.Color.blue())
        )
        
        # Add special footers
        if rarity == "ultra-legendary":
            embed.set_footer(text="💎✨ ULTRA-LEGENDARY CATCH! ✨💎")
        elif rarity == "legendary":
            embed.set_footer(text="🌟 LEGENDARY CATCH! 🌟")
        elif rarity == "epic":
            embed.set_footer(text="✨ Epic catch! ✨")
        
        # Attach image
        file_path = os.path.join(FISHING_ASSETS_DIR, fish_file)
        file = discord.File(file_path, filename=fish_file)
        embed.set_image(url=f"attachment://{fish_file}")
        
        # Record catch
        contest_id = get_current_contest_id() if is_contest_active() else None
        record_catch(ctx.author.id, ctx.author.display_name, "fish", fish_name, weight_kg, points, contest_id)
        
        # Special announcement for ultra-legendary
        if is_contest_active() and rarity == "ultra-legendary":
            announcement = await ctx.send(f"🎉 **INCREDIBLE!** {ctx.author.mention} just caught an **ULTRA-LEGENDARY** {fish_name}! 💎✨")
            await announcement.add_reaction("💎")
            await announcement.add_reaction("🎉")
            await announcement.add_reaction("🔥")
        
        # Send message
        try:
            if is_contest_active() and contest_thread and ctx.channel.id == contest_thread.id:
                await ctx.send(embed=embed, file=file, silent=True)
            else:
                await ctx.send(embed=embed, file=file)
        except discord.errors.HTTPException:
            # Thread might be archived/deleted
            await ctx.send(embed=embed, file=file)

    @bot.command(help="Show all available fish organized by rarity. Usage: !fishconditions", aliases=["conditions"])
    async def fishconditions(ctx):
        """Show all fish organized by rarity."""
        # Organize fish by rarity
        fish_by_rarity = defaultdict(list)
        
        for fish in fish_list:
            rarity = fish.get("rarity", "common").lower()
            fish_by_rarity[rarity].append(fish["name"])
        
        # Create embed
        embed = discord.Embed(
            title="🎣 Available Fish by Rarity",
            description="All fish currently available to catch:",
            color=discord.Color.blue()
        )
        
        # Rarity order and colors
        rarity_order = ["ultra-legendary", "legendary", "epic", "rare", "uncommon", "common", "junk"]
        rarity_emojis = {
            "ultra-legendary": "💎",
            "legendary": "🌟",
            "epic": "✨",
            "rare": "💙",
            "uncommon": "💚",
            "common": "🐟",
            "junk": "🗑️"
        }
        
        # Add fields for each rarity
        for rarity in rarity_order:
            if rarity in fish_by_rarity:
                fish_names = fish_by_rarity[rarity]
                # Format fish names nicely
                formatted_names = [name.replace("_", " ").replace("-", " ") for name in fish_names]
                
                emoji = rarity_emojis.get(rarity, "🐟")
                embed.add_field(
                    name=f"{emoji} {rarity.capitalize()} ({len(fish_names)})",
                    value=", ".join(sorted(formatted_names)),
                    inline=False
                )
        
        # Add footer with catch chance info
        embed.set_footer(text="Rarer fish have lower catch rates!")
        await ctx.send(embed=embed)

    @bot.command(help="(Admin only) Test fishing for a server player. Usage: !fplayer", hidden=True)
    async def fplayer(ctx):
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
            
        if ctx.guild is None or len(ctx.guild.members) < 2:
            await ctx.send("Not enough members to catch!")
            return
            
        candidates = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
        if not candidates:
            await ctx.send("No valid members to catch.")
            return
            
        caught = random.choice(candidates)
        weight_kg = round(random.uniform(55, 140), 1)
        points = 1000 + int(weight_kg * 2.2)
        
        embed = discord.Embed(
            title="🎣 TEST: You caught a server member!",
            description=(
                f"**{ctx.author.display_name}** reeled in **{caught.display_name}**!\n"
                f"Weight: **{weight_kg} kg** ({weight_kg * 2.2:.1f} lbs)\n"
                f"Points: **{points}**"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=caught.display_avatar.url)
        await ctx.send(embed=embed)

    @bot.command(help="Show the fishing leaderboard and your stats. Usage: !fishstats [@user]")
    async def fishstats(ctx, user: discord.Member = None):
        target = user or ctx.author
        
        with sqlite3.connect(FISH_DB) as conn:
            c = conn.cursor()
            
            # Get leaderboard - include both 'fish' and 'member' catches
            c.execute("""
                SELECT user_name, SUM(points) as total_points, COUNT(*) as num_catches
                FROM catches
                WHERE catch_type IN ('fish', 'member')
                GROUP BY user_id, user_name
                ORDER BY total_points DESC
                LIMIT 10
            """)
            leaderboard = c.fetchall()

            # Get user stats - include both 'fish' and 'member' catches
            c.execute("""
                SELECT COUNT(*), SUM(points)
                FROM catches
                WHERE user_id = ? AND catch_type IN ('fish', 'member')
            """, (str(target.id),))
            user_stats = c.fetchone() or (0, 0)

            # Get biggest catch (still only fish, not members)
            c.execute("""
                SELECT catch_name, weight, points
                FROM catches
                WHERE user_id = ? AND catch_type = 'fish'
                ORDER BY weight DESC
                LIMIT 1
            """, (str(target.id),))
            biggest = c.fetchone()

        # Build embed
        embed = discord.Embed(
            title="🏆 Fishing Leaderboard — Top 10 Anglers",
            color=discord.Color.gold()
        )
        
        # Add leaderboard
        if leaderboard:
            medals = ["🥇", "🥈", "🥉"]
            lb_lines = []
            for i, (name, points, num) in enumerate(leaderboard, 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                lb_lines.append(f"{medal} **{name}** — {points:,} pts ({num} catches)")
            embed.add_field(name="Leaderboard", value="\n".join(lb_lines), inline=False)
        else:
            embed.add_field(name="Leaderboard", value="No catches yet!", inline=False)

        # Add user stats
        total_catches, total_points = user_stats
        stats_text = f"**Total Catches:** {total_catches}\n**Total Points:** {total_points:,}\n"
        
        file = None
        if biggest:
            stats_text += f"**Biggest Fish:** {biggest[0]} ({float(biggest[1]):.2f} kg, {biggest[2]:,} pts)"
            
            # Try to find and attach the image
            fish_base = biggest[0].replace(" ", "_")
            fish_files = {os.path.splitext(f)[0].lower(): f for f in get_fish_list()}
            image_file = fish_files.get(fish_base.lower())
            
            if image_file:
                file_path = os.path.join(FISHING_ASSETS_DIR, image_file)
                file = discord.File(file_path, filename=image_file)
                embed.set_image(url=f"attachment://{image_file}")
        else:
            stats_text += "**Biggest Fish:** None yet!"
            
        embed.add_field(name=f"{target.display_name}'s Stats", value=stats_text, inline=False)

        if file:
            await ctx.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed)

    @bot.command(help="(Admin only) Add a new fish to the config. Usage: !addfish <FishName> <MinSizeCM> <MaxSizeCM> <MinWeightKG> <MaxWeightKG> <Rarity> \"<Description>\"", hidden=True)
    async def addfish(ctx, fish_name: str = None, min_size_cm: float = None, max_size_cm: float = None, 
                      min_weight_kg: float = None, max_weight_kg: float = None, rarity: str = None, *, description: str = None):
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return

        # Validate parameters
        if None in (fish_name, min_size_cm, max_size_cm, min_weight_kg, max_weight_kg, rarity):
            await ctx.send("Usage: !addfish <FishName> <MinSizeCM> <MaxSizeCM> <MinWeightKG> <MaxWeightKG> <Rarity> \"<Description>\"")
            return

        # Validate rarity
        valid_rarities = list(RARITY_TIERS.keys()) if RARITY_TIERS else ["common", "uncommon", "rare", "epic", "legendary", "ultra-legendary", "junk"]
        if rarity.lower() not in valid_rarities:
            await ctx.send(f"Invalid rarity. Choose from: {', '.join(valid_rarities)}")
            return

        # Check if file exists
        files = os.listdir(FISHING_ASSETS_DIR)
        file_match = next((f for f in files if os.path.splitext(f)[0].lower() == fish_name.lower()), None)
        if not file_match:
            await ctx.send(f"No file found in {FISHING_ASSETS_DIR} matching '{fish_name}'. Please upload the image first.")
            return

        fish_name_on_disk = os.path.splitext(file_match)[0]

        # Load and update config
        with open(FISHING_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Check for duplicate
        if any(f["name"].lower() == fish_name_on_disk.lower() for f in config["fish"]):
            await ctx.send(f"A fish named '{fish_name_on_disk}' already exists in the config.")
            return

        # Add new fish
        new_fish = {
            "name": fish_name_on_disk,
            "min_size_cm": float(min_size_cm),
            "max_size_cm": float(max_size_cm),
            "min_weight_kg": float(min_weight_kg),
            "max_weight_kg": float(max_weight_kg),
            "rarity": rarity.lower(),
            "description": description or "A mysterious creature from the depths."
        }
        config["fish"].append(new_fish)

        # Save config
        with open(FISHING_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Reload fish list and lookup
        global fish_list, FISH_LOOKUP
        fish_list = config["fish"]
        FISH_LOOKUP = {fish["name"].lower(): fish for fish in fish_list}

        await ctx.send(f"✅ Fish '{fish_name_on_disk}' added to the config! (Image file: {file_match})")

    @bot.command(help="List all fish and their stats in a table. Usage: !fishlist")
    async def fishlist(ctx):
        if not fish_list:
            await ctx.send("No fish are currently configured.")
            return

        # Build table with rarity
        header = "| Fish Name           | Size (cm)      | Weight (kg)    | Rarity      |\n"
        header += "|---------------------|----------------|----------------|-------------|\n"
        rows = []
        
        for fish in sorted(fish_list, key=lambda f: f["name"].lower()):
            name = fish["name"][:20]  # Truncate long names
            size = f"{fish['min_size_cm']}–{fish['max_size_cm']}"
            weight = f"{fish['min_weight_kg']}–{fish['max_weight_kg']}"
            rarity = fish.get("rarity", "common").lower()
            rows.append(f"| {name:<20}| {size:<15}| {weight:<15}| {rarity:<12}|")
            
        table = header + "\n".join(rows)
        
        # Check if message would be too long
        message = f"**Available Fish ({len(fish_list)} total):**\n```markdown\n{table}\n```\n_Use `!fishinfo <FishName>` to see the card for any fish!_"
        
        if len(message) > 2000:
            # Split into multiple messages
            await ctx.send(f"**Available Fish ({len(fish_list)} total):**")
            await ctx.send(f"```markdown\n{table[:1900]}\n```")
            await ctx.send(f"```markdown\n{table[1900:]}\n```")
            await ctx.send("_Use `!fishinfo <FishName>` to see the card for any fish!_")
        else:
            await ctx.send(message)

    @bot.command(help="Show info and image for a specific fish. Usage: !fishinfo <FishName>")
    async def fishinfo(ctx, *, fish_name: str = None):
        if not fish_name:
            await ctx.send("Usage: !fishinfo <FishName>")
            return
            
        # Find fish in config
        fish = next((f for f in fish_list if f["name"].lower() == fish_name.lower()), None)
        if not fish:
            # Try partial match
            partial_matches = [f for f in fish_list if fish_name.lower() in f["name"].lower()]
            if partial_matches:
                names = ", ".join(f["name"] for f in partial_matches[:5])
                await ctx.send(f"No exact match for '{fish_name}'. Did you mean: {names}?")
            else:
                await ctx.send(f"No fish named '{fish_name}' found.")
            return

        # Get rarity
        rarity = fish.get("rarity", "common").lower()

        # Get description
        description = fish.get("description", "A mysterious creature from the depths.")

        # Build embed
        embed = discord.Embed(
            title=f"🐟 {fish['name']}",
            description=f"*{description}*",
            color=RARITY_COLORS.get(rarity, discord.Color.teal())
        )
        
        # Add fields
        embed.add_field(name="Size Range", value=f"{fish['min_size_cm']}–{fish['max_size_cm']} cm", inline=True)
        embed.add_field(name="Weight Range", value=f"{fish['min_weight_kg']}–{fish['max_weight_kg']} kg", inline=True)
        embed.add_field(name="Max Points", value=f"~{int(fish['max_weight_kg'] * 10 + fish['max_size_cm'])}", inline=True)
        embed.add_field(name="Rarity", value=rarity.capitalize(), inline=True)
        
        # Find and attach image
        fish_files = {os.path.splitext(f)[0].lower(): f for f in get_fish_list()}
        image_file = fish_files.get(fish["name"].lower())
        
        if image_file:
            file_path = os.path.join(FISHING_ASSETS_DIR, image_file)
            file = discord.File(file_path, filename=image_file)
            embed.set_image(url=f"attachment://{image_file}")
            await ctx.send(embed=embed, file=file)
        else:
            embed.set_footer(text="No image found in FishingGameAssets.")
            await ctx.send(embed=embed)

    @bot.command(help="(Admin only) Set fishing cooldown time. Usage: !setfishcooldown <time> (e.g., 30s, 5m, 1m30s)", hidden=True)
    async def setfishcooldown(ctx, *, time_str: str = None):
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        if not time_str:
            await ctx.send("Usage: !setfishcooldown <time> (e.g., 30s, 5m, 1m30s, 0 to disable)")
            return
        
        # Parse time string
        if time_str == "0":
            new_cooldown = 0
        else:
            pattern = r'(?:(\d+)m)?(?:(\d+)s)?'
            match = re.match(pattern, time_str.strip())
            
            if not match or (not match.group(1) and not match.group(2)):
                await ctx.send("Invalid time format. Use formats like: 30s, 5m, 1m30s, 0 (to disable)")
                return
            
            minutes = int(match.group(1)) if match.group(1) else 0
            seconds = int(match.group(2)) if match.group(2) else 0
            new_cooldown = (minutes * 60) + seconds
            
            if new_cooldown > 3600:  # Max 1 hour
                await ctx.send("Cooldown cannot exceed 1 hour (3600 seconds).")
                return
        
        # Update config
        global FISH_CONFIG, cooldown_seconds
        FISH_CONFIG["cooldown_seconds"] = new_cooldown
        cooldown_seconds = new_cooldown
        
        # Save to file
        with open(FISHING_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(FISH_CONFIG, f, indent=2)
        
        # Reload the full config to ensure consistency
        FISH_CONFIG = load_fish_config()
        
        # Send confirmation
        if new_cooldown == 0:
            await ctx.send("🎣 Fishing cooldown disabled!")
        else:
            time_display = format_time_display(new_cooldown)
            await ctx.send(f"🎣 Fishing cooldown set to **{time_display}**!")

    @bot.command(help="(Admin only) Show current fishing cooldown setting.", hidden=True)
    async def fishcooldown(ctx):
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        if cooldown_seconds == 0:
            await ctx.send("🎣 Fishing cooldown is currently **disabled**.")
        else:
            time_display = format_time_display(cooldown_seconds)
            await ctx.send(f"🎣 Current fishing cooldown: **{time_display}**")

    @bot.command(help="Show fishing game help and commands. Usage: !fishhelp", aliases=["fishinghelp"])
    async def fishhelp(ctx):
        help_text = (
            "🎣 **__Fishing Game Commands__** 🎣\n\n"
            "🐟 **Player Commands:**\n"
            "• 🎣 **!fish** / **!f** / **!cast** / **!fishing** — Go fishing and try to catch a fish!\n"
            "• 🏆 **!fishstats [@user]** — View the fishing leaderboard and your (or another user's) stats.\n"
            "• 📜 **!fishlist** — List all fish and their stats in a table.\n"
            "• ℹ️ **!fishinfo <FishName>** — Show info and image for a specific fish.\n"
            "• 🌊 **!fishconditions** — Show all available fish organized by rarity.\n"
            "• ❓ **!fishhelp** / **!fishinghelp** — Show this help message.\n"
            "\n"
            "🛠️ **Admin Commands:**\n"
            "• ⏱️ **!setfishcooldown <time>** — Set fishing cooldown (e.g., 30s, 5m, 0 to disable).\n"
            "• ⏱️ **!fishcooldown** — Show current cooldown setting.\n"
            "• ➕ **!addfish** — Add a new fish species to the game.\n"
            "• 👤 **!fplayer** — Test fishing for a random server member.\n"
            "\n"
            f"Current cooldown: **{format_time_display(cooldown_seconds) if cooldown_seconds > 0 else 'disabled'}**\n"
            f"Fish rarity affects catch rates! Look for 🌟 legendary and epic catches!"
        )
        await ctx.send(help_text)

    @bot.command(help="Show all fishing admin commands. Usage: !fishadmin", aliases=["fishingadmin"])
    async def fishadmin(ctx):
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return

        help_text = (
            "🛠️ **__Fishing Game Admin Commands__** 🛠️\n\n"
            "• ➕ **!addfish <FishName> <MinSizeCM> <MaxSizeCM> <MinWeightKG> <MaxWeightKG>**\n"
            "  Add a new fish to the config (image must be uploaded first).\n\n"
            "• ⏱️ **!setfishcooldown <time>**\n"
            "  Set fishing cooldown time (e.g., 30s, 5m, 1m30s, 0 to disable).\n\n"
            "• ⏱️ **!fishcooldown**\n"
            "  Show current fishing cooldown setting.\n\n"
            "• 👤 **!fplayer**\n"
            "  Test fishing for a random server member (admin only).\n\n"
            "All fish images must be placed in the `FishingGameAssets` folder before adding them with `!addfish`.\n"
            "Admins can customize fish stats, member catch ratio, and cooldown in `my_fishing_game_config.json`."
        )
        await ctx.send(help_text)

# Initialize DB on import
init_fishing_db()