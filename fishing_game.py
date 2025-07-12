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
from fishing_contest import is_contest_active, get_current_contest_id, get_contest_thread, is_contest_thread

# Constants
FISHING_ASSETS_DIR = "FishingGameAssets"
FISH_DB = "fishing_game.db"
DEFAULT_FISHING_CONFIG_FILE = "fishing_game_config.json"
FISHING_CONFIG_FILE = "my_fishing_game_config.json"

NO_CATCH_CHANCE = 0.15  # 15% chance to catch nothing

# Module-level variables
FISHING_DB = "fishing_game.db"
FISHING_CONFIG_FILE = "my_fishing_game_config.json"
cooldowns = {}

# Track recent catches per user to avoid duplicates
recent_catches = {}  # {user_id: [list of last N fish caught]}
RECENT_CATCH_MEMORY = 10  # Increased to 10 for more variety

# Rarity system
FISH_RARITY_WEIGHTS = {
    "legendary": 1,    # Extremely rare
    "epic": 5,         # Very rare
    "rare": 20,        # Rare
    "uncommon": 50,    # Uncommon
    "common": 100      # Common
}

def get_fish_rarity(fish_name):
    """Determine fish rarity based on name."""
    name_lower = fish_name.lower()
    
    # Junk items - very common
    if any(word in name_lower for word in ["old_boot", "old_boots"]):
        return "junk"
    # Legendary - Extremely rare catches
    if any(word in name_lower for word in ["blue_whale", "whale_shark"]):
        return "legendary"
    # Epic - Very rare catches
    elif any(word in name_lower for word in ["great_white_shark", "hammerhead_shark", "manta_ray", "giant_squid"]):
        return "epic"
    # Rare - Rare catches
    elif any(word in name_lower for word in ["marlin", "swordfish", "barracuda", "tarpon", "mahi_mahi", "wahoo"]):
        return "rare"
    # Uncommon - Less common catches
    elif any(word in name_lower for word in ["pike", "perch", "carp", "grouper", "snapper", "flounder"]):
        return "uncommon"
    # Common - Default for most fish
    else:
        return "common"

def get_time_bonus_fish():
    """Get fish that are more common at certain times."""
    current_hour = datetime.now().hour
    
    # Night fishing (8 PM - 4 AM) - nocturnal fish more active
    if current_hour >= 20 or current_hour <= 4:
        return ["catfish", "eel", "anglerfish", "squid", "octopus"]
    # Early morning (5 AM - 8 AM) - best fishing time
    elif 5 <= current_hour <= 8:
        return ["bass", "trout", "salmon", "pike", "perch"]
    # Morning to noon (9 AM - 12 PM)
    elif 9 <= current_hour <= 12:
        return ["tuna", "mackerel", "herring", "sardine"]
    # Afternoon (1 PM - 5 PM) - deep water fish
    elif 13 <= current_hour <= 17:
        return ["marlin", "swordfish", "mahi_mahi", "wahoo"]
    # Evening (6 PM - 7 PM) - feeding time
    else:
        return ["snapper", "grouper", "barracuda", "tarpon"]

# On first run, copy fishing_game_config.json to my_fishing_game_config.json if not present
if not os.path.exists(FISHING_CONFIG_FILE):
    if os.path.exists(DEFAULT_FISHING_CONFIG_FILE):
        shutil.copy(DEFAULT_FISHING_CONFIG_FILE, FISHING_CONFIG_FILE)

def init_fishing_db():
    """Initialize the fishing database."""
    conn = sqlite3.connect(FISH_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS catches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            catch_type TEXT, -- 'fish' or 'user'
            catch_name TEXT,
            weight REAL,
            points INTEGER,
            timestamp DATETIME,
            contest_id TEXT
        )
    """)
    conn.commit()
    conn.close()

def record_catch(user_id, user_name, catch_type, catch_name, weight, points, contest_id=None):
    """Record a catch in the database."""
    conn = sqlite3.connect(FISH_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO catches (user_id, user_name, catch_type, catch_name, weight, points, timestamp, contest_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (str(user_id), user_name, catch_type, catch_name, weight, points, datetime.utcnow(), contest_id)
    )
    conn.commit()
    conn.close()

def get_fish_list():
    """Get list of available fish images."""
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif')
    return [f for f in os.listdir(FISHING_ASSETS_DIR) if f.lower().endswith(valid_extensions)]

def format_time_display(seconds):
    """Format seconds into a readable time string."""
    if seconds >= 60:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds > 0 else f"{minutes}m"
    return f"{seconds}s"

def format_cooldown_remaining(remaining_seconds):
    """Format remaining cooldown time."""
    if remaining_seconds >= 60:
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}m {seconds}s" if seconds > 0 else f"{minutes}m"
    return f"{int(remaining_seconds)}s"

def setup_fishing(bot):
    """Set up all fishing-related commands."""
    
    @bot.command(name="fish", aliases=["f", "cast", "fishing"], help="Go fishing and catch something! Usage: !fish")
    async def fish(ctx):
        """Main fishing command."""
        # Check if we should use contest thread
        contest_thread = get_contest_thread()
        
        # If there's a contest thread but contest isn't active yet, prevent fishing
        if contest_thread and ctx.channel.id == contest_thread.id and not is_contest_active():
            await ctx.send("⚠️ The contest hasn't started yet! Wait for the START announcement!")
            return
        
        # If contest is active but not in the thread
        if is_contest_active() and contest_thread and ctx.channel.id != contest_thread.id:
            await ctx.send(f"🎣 A contest is active! Please fish in the contest thread: {contest_thread.mention}")
            return
        
        # Skip cooldown entirely during contests
        if not is_contest_active():
            # Only check cooldown if NOT in a contest
            user_id = str(ctx.author.id)
            current_time = datetime.utcnow()
            
            if user_id in cooldowns:
                time_since_last = (current_time - cooldowns[user_id]).total_seconds()
                if time_since_last < cooldown_seconds:
                    remaining = cooldown_seconds - time_since_last
                    await ctx.send(f"🎣 You need to wait {int(remaining)}s before fishing again!")
                    return
            
            # Update cooldown for next time (only if not in contest)
            cooldowns[user_id] = current_time
        
        # 1 in member_catch_ratio chance to "catch" a user
        if (random.randint(1, member_catch_ratio) == 1 and 
            ctx.guild is not None and 
            len(ctx.guild.members) > 1):
            
            # Exclude bots and the caster
            candidates = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
            if candidates:
                caught = random.choice(candidates)
                weight_kg = round(random.uniform(55, 140), 1)  # Standardized to kg
                points = 1000 + int(weight_kg * 2.2)  # Convert to points based on lbs equivalent
                
                # Apply contest bonus if active
                if is_contest_active():
                    points = int(points * 1.5)  # 50% bonus during contests
                
                embed = discord.Embed(
                    title="🎣 INCREDIBLE! You caught a server member!",
                    description=(
                        f"**{ctx.author.display_name}** reeled in **{caught.display_name}**!\n"
                        f"Weight: **{weight_kg} kg** ({weight_kg * 2.2:.1f} lbs)\n"
                        f"Points: **{points}**" + 
                        ("\n🏆 **Contest Bonus Applied!**" if is_contest_active() else "")
                    ),
                    color=discord.Color.gold()
                )
                embed.set_thumbnail(url=caught.display_avatar.url)
                
                # Record catch with contest ID if applicable
                contest_id = get_current_contest_id() if is_contest_active() else None
                record_catch(ctx.author.id, ctx.author.display_name, "user", caught.display_name, weight_kg, points, contest_id)
                
                # Send silently during contests
                if is_contest_active() and get_contest_thread() and ctx.channel.id == get_contest_thread().id:
                    await ctx.send(embed=embed, silent=True)
                else:
                    await ctx.send(embed=embed)
                return

        # Random chance to catch nothing
        if random.random() < NO_CATCH_CHANCE:
            # User caught nothing
            embed = discord.Embed(
                title="🎣 No luck this time...",
                description=f"**{ctx.author.display_name}** didn't catch anything!",
                color=discord.Color.greyple()
            )
            
            # Add random consolation messages
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
            
            # Try to attach the no-fish image
            no_fish_path = os.path.join(FISHING_ASSETS_DIR, "No-Fish.png")
            if os.path.exists(no_fish_path):
                file = discord.File(no_fish_path, filename="No-Fish.png")
                embed.set_image(url="attachment://No-Fish.png")
                
                # Send with or without file
                if is_contest_active() and get_contest_thread() and ctx.channel.id == get_contest_thread().id:
                    await ctx.send(embed=embed, file=file, silent=True)
                else:
                    await ctx.send(embed=embed, file=file)
            else:
                # No image found, just send embed
                if is_contest_active() and get_contest_thread() and ctx.channel.id == get_contest_thread().id:
                    await ctx.send(embed=embed, silent=True)
                else:
                    await ctx.send(embed=embed)
            
            # Don't record anything for no catch
            return

        # Otherwise, catch a fish
        fish_files = get_fish_list()
        if not fish_files:
            await ctx.send("No fish assets found! Please add images to the FishingGameAssets folder.")
            return
        
        # Get user's recent catches
        user_id = str(ctx.author.id)
        user_recent = recent_catches.get(user_id, [])
        
        # Get time-based bonus fish
        time_bonus_fish = get_time_bonus_fish()
        
        # Create weighted selection based on multiple factors
        fish_weights = {}
        
        for fish_file in fish_files:
            fish_base = os.path.splitext(fish_file)[0].lower()
            
            # Start with rarity weight
            rarity = get_fish_rarity(fish_base)
            weight = FISH_RARITY_WEIGHTS.get(rarity, 50)
            
            # Apply time bonus (3x weight if it's a good time for this fish)
            if any(bonus in fish_base for bonus in time_bonus_fish):
                weight *= 3
            
            # Reduce weight for recent catches
            if fish_file in user_recent:
                # The more recent, the less likely
                idx = user_recent.index(fish_file)
                reduction_factor = 10 - idx  # Most recent gets /10, second recent /9, etc.
                weight = max(1, weight // reduction_factor)
            
            fish_weights[fish_file] = weight
        
        # Select fish using weights
        fish_files_list = list(fish_weights.keys())
        weights_list = list(fish_weights.values())
        fish_file = random.choices(fish_files_list, weights=weights_list, k=1)[0]
        
        # Update recent catches
        if user_id not in recent_catches:
            recent_catches[user_id] = []
        recent_catches[user_id].insert(0, fish_file)  # Add to front
        recent_catches[user_id] = recent_catches[user_id][:RECENT_CATCH_MEMORY]  # Keep only last N
        
        fish_base_name = os.path.splitext(fish_file)[0]
        fish_name = fish_base_name.replace("_", " ")

        # Find fish config entry
        fish_entry = next((f for f in fish_list if f["name"].lower() == fish_base_name.lower()), None)
        
        if fish_entry:
            # Generate random size and weight within configured ranges
            size_cm = round(random.uniform(fish_entry["min_size_cm"], fish_entry["max_size_cm"]), 1)
            weight_kg = round(random.uniform(fish_entry["min_weight_kg"], fish_entry["max_weight_kg"]), 2)
            
            # Get description if available
            description = fish_entry.get("description", "A mysterious creature from the depths.")
            
            # Calculate points
            default_max_points = int(max(1, round(fish_entry["max_weight_kg"] * 10 + fish_entry["max_size_cm"])))
            points = int(max(1, round(weight_kg * 10 + size_cm)))
            points = min(points, default_max_points * 2)  # Cap at 2x max
            
            weight_str = f"{weight_kg} kg"
            size_str = f"{size_cm} cm"
        else:
            # Fallback if config missing
            size_str = "unknown"
            weight_str = "unknown"
            points = 1
            weight_kg = 0
            description = "A mysterious catch!"

        # Apply contest bonus to points
        if is_contest_active():
            points = int(points * 1.5)  # 50% bonus during contests

        # Get rarity for color coding
        rarity = get_fish_rarity(fish_base_name)
        
        # Set embed color based on rarity
        rarity_colors = {
            "legendary": discord.Color.gold(),
            "epic": discord.Color.purple(),
            "rare": discord.Color.blue(),
            "uncommon": discord.Color.green(),
            "common": discord.Color.darker_gray(),
            "junk": discord.Color.from_rgb(139, 69, 19)  # Brown color
        }
        
        # Create embed with rarity color and description
        embed = discord.Embed(
            title="🎣 You caught a fish!",
            description=(
                f"**{ctx.author.display_name}** caught a **{fish_name}**!\n"
                f"*{description}*\n\n"
                f"**Size:** {size_str}\n"
                f"**Weight:** {weight_str}\n"
                f"**Points:** {points}\n"
                f"**Rarity:** {rarity.capitalize()}" +
                ("\n🏆 **Contest Bonus Applied!**" if is_contest_active() else "")
            ),
            color=rarity_colors.get(rarity, discord.Color.blue())
        )
        
        # Add special reactions for rare catches
        if rarity in ["legendary", "epic"]:
            embed.set_footer(text="🌟 Amazing catch! 🌟")
        
        # Attach image
        file_path = os.path.join(FISHING_ASSETS_DIR, fish_file)
        file = discord.File(file_path, filename=fish_file)
        embed.set_image(url=f"attachment://{fish_file}")
        
        # Record catch with contest ID if applicable
        contest_id = get_current_contest_id() if is_contest_active() else None
        record_catch(ctx.author.id, ctx.author.display_name, "fish", fish_name, weight_kg, points, contest_id)
        
        # Send silently during contests - INCLUDE THE FILE!
        if is_contest_active() and get_contest_thread() and ctx.channel.id == get_contest_thread().id:
            await ctx.send(embed=embed, file=file, silent=True)
        else:
            await ctx.send(embed=embed, file=file)

    @bot.command(help="Show current fishing conditions and what's biting. Usage: !fishconditions", aliases=["conditions"])
    async def fishconditions(ctx):
        """Show current fishing conditions based on time."""
        current_hour = datetime.now().hour
        time_bonus_fish = get_time_bonus_fish()
        
        # Determine time period
        if current_hour >= 20 or current_hour <= 4:
            period = "Night (8 PM - 4 AM)"
            description = "🌙 Nocturnal fish are more active!"
        elif 5 <= current_hour <= 8:
            period = "Early Morning (5 AM - 8 AM)"
            description = "🌅 Prime fishing time! Fish are hungry!"
        elif 9 <= current_hour <= 12:
            period = "Morning (9 AM - 12 PM)"
            description = "☀️ Good conditions for smaller fish."
        elif 13 <= current_hour <= 17:
            period = "Afternoon (1 PM - 5 PM)"
            description = "🌊 Deep water predators are hunting."
        else:
            period = "Evening (6 PM - 7 PM)"
            description = "🌆 Fish are feeding before nightfall."
        
        embed = discord.Embed(
            title="🎣 Current Fishing Conditions",
            description=f"**{period}**\n{description}",
            color=discord.Color.blue()
        )
        
        # Format the bonus fish names nicely
        bonus_fish_display = [f.replace("_", " ").title() for f in time_bonus_fish]
        embed.add_field(
            name="🐟 Fish Biting Now (3x chance)",
            value=", ".join(bonus_fish_display),
            inline=False
        )
        
        embed.set_footer(text="Fish activity changes throughout the day!")
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
            
            # Get leaderboard
            c.execute("""
                SELECT user_name, SUM(points) as total_points, COUNT(*) as num_catches
                FROM catches
                WHERE catch_type = 'fish'
                GROUP BY user_id, user_name
                ORDER BY total_points DESC
                LIMIT 10
            """)
            leaderboard = c.fetchall()

            # Get user stats
            c.execute("""
                SELECT COUNT(*), SUM(points)
                FROM catches
                WHERE user_id = ? AND catch_type = 'fish'
            """, (str(target.id),))
            user_stats = c.fetchone() or (0, 0)

            # Get biggest catch
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
                lb_lines.append(f"{medal} **{name}** — {points:,} pts ({num} fish)")
            embed.add_field(name="Leaderboard", value="\n".join(lb_lines), inline=False)
        else:
            embed.add_field(name="Leaderboard", value="No catches yet!", inline=False)

        # Add user stats
        total_catches, total_points = user_stats
        stats_text = f"**Total Catches:** {total_catches}\n**Total Points:** {total_points or 0}\n"
        
        file = None
        if biggest:
            stats_text += f"**Biggest Fish:** {biggest[0]} ({float(biggest[1]):.2f} kg, {biggest[2]} pts)"
            
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

    @bot.command(help="(Admin only) Add a new fish to the config. Usage: !addfish <FishName> <MinSizeCM> <MaxSizeCM> <MinWeightKG> <MaxWeightKG> \"<Description>\"", hidden=True)
    async def addfish(ctx, fish_name: str = None, min_size_cm: float = None, max_size_cm: float = None, 
                      min_weight_kg: float = None, max_weight_kg: float = None, *, description: str = None):
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return

        # Validate parameters
        if None in (fish_name, min_size_cm, max_size_cm, min_weight_kg, max_weight_kg):
            await ctx.send("Usage: !addfish <FishName> <MinSizeCM> <MaxSizeCM> <MinWeightKG> <MaxWeightKG> \"<Description>\"")
            return

        # Validate ranges
        if min_size_cm >= max_size_cm or min_weight_kg >= max_weight_kg:
            await ctx.send("Error: Min values must be less than max values.")
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
            "description": description or "A mysterious creature from the depths."
        }
        config["fish"].append(new_fish)

        # Save config
        with open(FISHING_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Reload fish list
        global fish_list
        fish_list = config["fish"]

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
            rarity = get_fish_rarity(fish["name"])
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
        rarity = get_fish_rarity(fish["name"])
        rarity_colors = {
            "legendary": discord.Color.gold(),
            "epic": discord.Color.purple(),
            "rare": discord.Color.blue(),
            "uncommon": discord.Color.green(),
            "common": discord.Color.darker_gray(),
            "junk": discord.Color.from_rgb(139, 69, 19)  # Brown color
        }

        # Get description
        description = fish.get("description", "A mysterious creature from the depths.")

        # Build embed
        embed = discord.Embed(
            title=f"🐟 {fish['name']}",
            description=f"*{description}*",
            color=rarity_colors.get(rarity, discord.Color.teal())
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
            "• 🌊 **!fishconditions** — Show current fishing conditions and what's biting.\n"
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

# Load configuration
def load_fish_config():
    """Load fishing configuration from file."""
    with open(FISHING_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Initialize globals
FISH_CONFIG = load_fish_config()
member_catch_ratio = FISH_CONFIG.get("member_catch_ratio", 50)
fish_list = FISH_CONFIG["fish"]
cooldown_seconds = FISH_CONFIG.get("cooldown_seconds", 30)  # Default: 30 seconds
NO_CATCH_CHANCE = FISH_CONFIG.get("no_catch_chance", 0.15)  # Default 15%

# Track last fishing time per user
last_fish_time = defaultdict(lambda: datetime.min)

# Initialize DB on import
init_fishing_db()