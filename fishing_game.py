import os
import random
import sqlite3
from datetime import datetime
import discord
from discord.ext import commands
import json

FISHING_ASSETS_DIR = "FishingGameAssets"
FISH_DB = "fishing_game.db"
FISHING_CONFIG_FILE = "fishing_game_config.json"

def init_fishing_db():
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
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

def record_catch(user_id, user_name, catch_type, catch_name, weight, points):
    conn = sqlite3.connect(FISH_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO catches (user_id, user_name, catch_type, catch_name, weight, points, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(user_id), user_name, catch_type, catch_name, weight, points, datetime.utcnow())
    )
    conn.commit()
    conn.close()

def get_fish_list():
    return [f for f in os.listdir(FISHING_ASSETS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

def random_weight():
    # Fish weights between 0.5 and 50 lbs, with some bias toward smaller fish
    return round(random.triangular(0.5, 50, 2.5), 2)

def points_for_weight(weight):
    # Simple: 1 point per 0.5 lbs, rounded up
    return int(max(1, round(weight * 2)))

async def fish_command(ctx):
    # 1 in 250 chance to "catch" a user
    if random.randint(1, 250) == 1 and ctx.guild is not None and len(ctx.guild.members) > 1:
        # Exclude bots and the caster
        candidates = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
        if candidates:
            caught = random.choice(candidates)
            weight = round(random.uniform(120, 300), 1)  # "weight" in lbs
            points = 1000 + int(weight)  # High value
            embed = discord.Embed(
                title="🎣 INCREDIBLE! You caught a server member!",
                description=f"**{ctx.author.display_name}** reeled in **{caught.display_name}**!\n"
                            f"Weight: **{weight} lbs**\n"
                            f"Points: **{points}**",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=caught.display_avatar.url)
            record_catch(ctx.author.id, ctx.author.display_name, "user", caught.display_name, weight, points)
            await ctx.send(embed=embed)
            return

    # Otherwise, catch a fish
    fish_files = get_fish_list()
    if not fish_files:
        await ctx.send("No fish assets found! Please add images to the FishingGameAssets folder.")
        return
    fish_file = random.choice(fish_files)
    fish_base_name = os.path.splitext(fish_file)[0]
    fish_name = fish_base_name.replace("_", " ")

    # Find fish config entry
    fish_entry = next((f for f in FISH_CONFIG if f["name"].lower() == fish_base_name.lower()), None)
    if fish_entry:
        size_cm = round(random.uniform(fish_entry["min_size_cm"], fish_entry["max_size_cm"]), 1)
        weight_kg = round(random.uniform(fish_entry["min_weight_kg"], fish_entry["max_weight_kg"]), 2)
        weight_str = f"{weight_kg} kg"
        size_str = f"{size_cm} cm"
        points = int(max(1, round(weight_kg * 10 + size_cm)))  # Example: 10 pts per kg + 1 per cm
    else:
        # fallback if config missing
        size_str = "unknown"
        weight_str = "unknown"
        points = 1

    embed = discord.Embed(
        title="🎣 You caught a fish!",
        description=f"**{ctx.author.display_name}** caught a **{fish_name}**!\n"
                    f"Size: **{size_str}**\n"
                    f"Weight: **{weight_str}**\n"
                    f"Points: **{points}**",
        color=discord.Color.blue()
    )
    file_path = os.path.join(FISHING_ASSETS_DIR, fish_file)
    file = discord.File(file_path, filename=fish_file)
    embed.set_image(url=f"attachment://{fish_file}")
    record_catch(ctx.author.id, ctx.author.display_name, "fish", fish_name, weight_kg, points)
    await ctx.send(embed=embed, file=file)

def setup_fishing(bot):
    @bot.command(help="Go fishing! Try your luck and catch a fish. Usage: !fish")
    async def fish(ctx):
        await fish_command(ctx)

    @bot.command(help="(Admin only) Test fishing for a server player. Usage: !fplayer", hidden=True)
    async def fplayer(ctx):
        # Only allow admins (manage_guild or administrator)
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
        weight = round(random.uniform(120, 300), 1)  # "weight" in lbs
        points = 1000 + int(weight)  # High value
        embed = discord.Embed(
            title="🎣 TEST: You caught a server member!",
            description=f"**{ctx.author.display_name}** reeled in **{caught.display_name}**!\n"
                        f"Weight: **{weight} lbs**\n"
                        f"Points: **{points}**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=caught.display_avatar.url)
        record_catch(ctx.author.id, ctx.author.display_name, "user", caught.display_name, weight, points)
        await ctx.send(embed=embed)

    @bot.command(help="Show the fishing leaderboard and your stats. Usage: !fishstats")
    async def fishstats(ctx):
        conn = sqlite3.connect(FISH_DB)
        c = conn.cursor()
        # Leaderboard: top 10 by total points
        c.execute("""
            SELECT user_name, SUM(points) as total_points, COUNT(*) as num_catches
            FROM catches
            WHERE catch_type = 'fish'
            GROUP BY user_id, user_name
            ORDER BY total_points DESC
            LIMIT 10
        """)
        leaderboard = c.fetchall()

        # User stats
        c.execute("""
            SELECT COUNT(*), SUM(points)
            FROM catches
            WHERE user_id = ? AND catch_type = 'fish'
        """, (str(ctx.author.id),))
        user_stats = c.fetchone() or (0, 0)

        c.execute("""
            SELECT catch_name, weight, points
            FROM catches
            WHERE user_id = ? AND catch_type = 'fish'
            ORDER BY weight DESC
            LIMIT 1
        """, (str(ctx.author.id),))
        biggest = c.fetchone()
        conn.close()

        embed = discord.Embed(
            title="🎣 Fishing Leaderboard",
            color=discord.Color.green()
        )
        if leaderboard:
            lb_text = ""
            for i, (name, points, num) in enumerate(leaderboard, 1):
                lb_text += f"**{i}. {name}** — {points} pts ({num} fish)\n"
            embed.add_field(name="Top 10 Fishers", value=lb_text, inline=False)
        else:
            embed.add_field(name="Top 10 Fishers", value="No catches yet!", inline=False)

        # User stats
        total_catches, total_points = user_stats
        stats_text = f"**Total Catches:** {total_catches}\n**Total Points:** {total_points or 0}\n"
        if biggest:
            stats_text += f"**Biggest Fish:** {biggest[0]} ({float(biggest[1]):.2f} kg, {biggest[2]} pts)"
        else:
            stats_text += "**Biggest Fish:** None yet!"
        embed.add_field(name=f"{ctx.author.display_name}'s Stats", value=stats_text, inline=False)

        await ctx.send(embed=embed)

def load_fish_config():
    with open(FISHING_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

FISH_CONFIG = load_fish_config()
member_catch_ratio = FISH_CONFIG.get("member_catch_ratio", 250)
fish_list = FISH_CONFIG["fish"]

# Initialize DB on import
init_fishing_db()