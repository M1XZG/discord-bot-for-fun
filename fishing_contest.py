# Copyright (c) 2025 Robert McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

import os
import sqlite3
import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
import asyncio
from typing import Optional, List, Dict
import re
import datetime as dt

# Constants
CONTEST_DB = "fishing_game.db"  # Use same DB as main fishing
FISHING_CONFIG_FILE = "my_fishing_game_config.json"

# Contest states
CONTEST_NONE = "none"
CONTEST_SCHEDULED = "scheduled"
CONTEST_STARTING = "starting"
CONTEST_ACTIVE = "active"
CONTEST_ENDED = "ended"

class FishingContest:
    def __init__(self):
        self.current_contest_id = None
        self.contest_state = CONTEST_NONE
        self.contest_start_time = None
        self.contest_end_time = None
        self.contest_channel_id = None
        self.contest_thread = None
        self.participants = set()  # User IDs who joined
        self.contest_duration = 600  # Default 10 minutes

def is_contest_thread(channel_id):
    """Check if a channel is the current contest thread."""
    return (contest.contest_thread and 
            contest.contest_thread.id == channel_id and
            contest.contest_state in [CONTEST_STARTING, CONTEST_ACTIVE])

def init_contest_db():
    """Initialize contest-related database tables."""
    conn = sqlite3.connect(CONTEST_DB)
    c = conn.cursor()
    
    # Create contests table
    c.execute("""
        CREATE TABLE IF NOT EXISTS contests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            start_time DATETIME,
            end_time DATETIME,
            channel_id TEXT,
            thread_id TEXT,
            created_by TEXT,
            winner_id TEXT,
            winner_name TEXT,
            total_participants INTEGER,
            total_catches INTEGER
        )
    """)
    
    # Create contest_participants table
    c.execute("""
        CREATE TABLE IF NOT EXISTS contest_participants (
            contest_id INTEGER,
            user_id TEXT,
            user_name TEXT,
            joined_at DATETIME,
            FOREIGN KEY (contest_id) REFERENCES contests(id),
            PRIMARY KEY (contest_id, user_id)
        )
    """)
    
    # Add contest_id to catches table if not exists
    c.execute("PRAGMA table_info(catches)")
    columns = [column[1] for column in c.fetchall()]
    if 'contest_id' not in columns:
        c.execute("ALTER TABLE catches ADD COLUMN contest_id INTEGER REFERENCES contests(id)")
    
    conn.commit()
    conn.close()

# Global contest instance
contest = FishingContest()

async def create_contest_thread(channel: discord.TextChannel, contest_name: str, participants: set) -> discord.Thread:
    """Create a thread for the fishing contest."""
    # Create thread with [WAITING] status
    thread = await channel.create_thread(
        name=f"🎣 {contest_name} [WAITING]",
        type=discord.ChannelType.public_thread,
        auto_archive_duration=1440,  # 24 hours
        invitable=False  # Prevent random people from being added
    )
    
    # Send warning message
    warning_embed = discord.Embed(
        title="⚠️ Contest Not Started Yet!",
        description=(
            "This thread is for the upcoming fishing contest.\n"
            "**DO NOT FISH YET!**\n\n"
            f"Contest starts: <t:{int(contest.contest_start_time.timestamp())}:R>\n\n"
            "Any fish caught before the official start will NOT count!"
        ),
        color=discord.Color.red()
    )
    await thread.send(embed=warning_embed)
    
    return thread

async def post_contest_rules(thread: discord.Thread, duration_minutes: int):
    """Post contest rules to the thread."""
    embed = discord.Embed(
        title="🎣 Fishing Contest Rules",
        description=(
            f"**Duration:** {duration_minutes} minutes\n"
            f"**Start Time:** <t:{int(contest.contest_start_time.timestamp())}:R>\n\n"
            "**⚠️ DO NOT FISH YET! Wait for the START announcement!**\n"
            "**⚠️ Fishing before the start will NOT count!**\n\n"
            "**Rules:**\n"
            "• All fish caught during the contest earn **50% bonus points**\n"
            "• The angler with the most total points wins\n"
            "• **NO COOLDOWNS** - fish as fast as you can!\n"
            "• Use `!fish` in this thread to participate\n"
            "• Use `!contestlb` to see live standings\n\n"
            "**Good luck, anglers!** 🐟"
        ),
        color=discord.Color.red()  # Red to indicate not started
    )
    await thread.send(embed=embed)

async def update_contest_in_db(contest_id: int, **kwargs):
    """Update contest information in database."""
    conn = sqlite3.connect(CONTEST_DB)
    c = conn.cursor()
    
    set_clauses = []
    values = []
    for key, value in kwargs.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)
    
    values.append(contest_id)
    query = f"UPDATE contests SET {', '.join(set_clauses)} WHERE id = ?"
    c.execute(query, values)
    conn.commit()
    conn.close()

def setup_fishing_contest(bot):
    """Set up all fishing contest commands and tasks."""
    
    @tasks.loop(seconds=5)  # Check more frequently for better timing
    async def contest_checker():
        """Check contest status and handle state transitions."""
        if contest.contest_state == CONTEST_SCHEDULED:
            now = dt.datetime.now(dt.timezone.utc)
            
            # Check if it's time to create the thread (1 minute before start)
            time_until_start = (contest.contest_start_time - now).total_seconds()
            
            if time_until_start <= 60 and not contest.contest_thread:
                contest.contest_state = CONTEST_STARTING
                channel = bot.get_channel(contest.contest_channel_id)
                if channel:
                    # Create thread with WAITING status
                    contest_name = f"Fishing Contest - {now.strftime('%Y-%m-%d %H:%M')} UTC"
                    thread = await create_contest_thread(channel, contest_name, contest.participants)
                    contest.contest_thread = thread
                    
                    # Update DB with thread ID
                    await update_contest_in_db(contest.current_contest_id, thread_id=str(thread.id))
                    
                    # Post rules
                    await post_contest_rules(thread, contest.contest_duration // 60)
                    
                    # Ping participants
                    if contest.participants:
                        mentions = " ".join([f"<@{uid}>" for uid in contest.participants])
                        await thread.send(
                            f"🎣 **Contest starting in 1 minute!**\n"
                            f"{mentions}\n"
                            f"Get ready to fish! The contest will begin at <t:{int(contest.contest_start_time.timestamp())}:R>"
                        )
        
        elif contest.contest_state == CONTEST_STARTING:
            now = dt.datetime.now(dt.timezone.utc)
            
            # Check if it's time to start
            if now >= contest.contest_start_time:
                contest.contest_state = CONTEST_ACTIVE
                if contest.contest_thread:
                    # Update thread name to show it's active
                    try:
                        thread_name = contest.contest_thread.name.replace("[WAITING]", "[ACTIVE]")
                        await contest.contest_thread.edit(name=thread_name)
                    except discord.HTTPException:
                        pass  # Ignore if we can't edit
                    
                    # Send start message with big announcement
                    embed = discord.Embed(
                        title="🎣 CONTEST HAS STARTED! 🎣",
                        description=(
                            "# 🐟 FISH NOW! 🐟\n\n"
                            "The contest is officially underway!\n"
                            "**Start fishing with `!fish`**\n"
                            "**Check standings with `!contestlb`**\n\n"
                            f"Contest ends <t:{int(contest.contest_end_time.timestamp())}:R>"
                        ),
                        color=discord.Color.green()
                    )
                    embed.set_footer(text="May the best angler win! 🏆")
                    
                    # Ping participants if any
                    if contest.participants:
                        mentions = " ".join([f"<@{uid}>" for uid in contest.participants])
                        await contest.contest_thread.send(f"{mentions}\n**GO GO GO!** 🎣")
                    
                    await contest.contest_thread.send(embed=embed)
        
        elif contest.contest_state == CONTEST_ACTIVE:
            now = dt.datetime.now(dt.timezone.utc)
            
            # Check if contest has ended
            if now >= contest.contest_end_time:
                contest.contest_state = CONTEST_ENDED
                await end_contest(bot)

    async def end_contest(bot):
        """End the current contest and announce results."""
        if not contest.current_contest_id:
            return
        
        conn = sqlite3.connect(CONTEST_DB)
        c = conn.cursor()
        
        # Get contest results
        c.execute("""
            SELECT user_id, user_name, SUM(points) as total_points, COUNT(*) as catches
            FROM catches
            WHERE contest_id = ?
            GROUP BY user_id, user_name
            ORDER BY total_points DESC
            LIMIT 10
        """, (contest.current_contest_id,))
        results = c.fetchall()
        
        # Get total stats
        c.execute("""
            SELECT COUNT(DISTINCT user_id), COUNT(*)
            FROM catches
            WHERE contest_id = ?
        """, (contest.current_contest_id,))
        total_participants, total_catches = c.fetchone()
        
        conn.close()
        
        # Announce results
        if contest.contest_thread:
            embed = discord.Embed(
                title="🏆 Contest Results",
                color=discord.Color.gold()
            )
            
            winner_name = None
            if results:
                # Winner
                winner_id, winner_name, winner_points, winner_catches = results[0]
                embed.add_field(
                    name="🥇 WINNER",
                    value=f"**{winner_name}** with {winner_points:,} points ({winner_catches} catches)!",
                    inline=False
                )
                
                # Update contest in DB
                await update_contest_in_db(
                    contest.current_contest_id,
                    winner_id=winner_id,
                    winner_name=winner_name,
                    total_participants=total_participants,
                    total_catches=total_catches
                )
                
                # Top 3
                if len(results) > 1:
                    medals = ["🥇", "🥈", "🥉"]
                    top_3 = []
                    for i, (uid, name, points, catches) in enumerate(results[:3]):
                        top_3.append(f"{medals[i]} **{name}** - {points:,} pts ({catches} fish)")
                    embed.add_field(name="Top Anglers", value="\n".join(top_3), inline=False)
            else:
                embed.add_field(name="Results", value="No fish were caught during this contest!", inline=False)
            
            embed.add_field(
                name="Contest Stats",
                value=f"**Participants:** {total_participants}\n**Total Catches:** {total_catches}",
                inline=False
            )
            
            await contest.contest_thread.send(embed=embed)
            
            # Update thread title and lock
            winner_name_safe = winner_name if results else 'None'
            new_title = f"🎣 Contest - {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')} - Winner: {winner_name_safe}"
            try:
                await contest.contest_thread.edit(
                    name=new_title[:100], 
                    locked=True,
                    archived=True,
                    reason="Contest ended"
                )
            except discord.HTTPException as e:
                print(f"Failed to update thread: {e}")
        
        # Reset contest state
        contest.current_contest_id = None
        contest.contest_state = CONTEST_NONE
        contest.contest_thread = None
        contest.participants.clear()
    
    @bot.command(help="(Admin) Start a fishing contest. Usage: !startcontest <duration> <delay>")
    async def startcontest(ctx, duration: str = "10m", delay: str = "5m"):
        """Schedule a fishing contest."""
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        # Check if contest already active
        if contest.contest_state != CONTEST_NONE:
            await ctx.send("A contest is already scheduled or active!")
            return
        
        # Parse duration and delay
        def parse_time(time_str):
            match = re.match(r'(\d+)([mh])', time_str.lower())
            if not match:
                return None
            value, unit = match.groups()
            multiplier = 60 if unit == 'm' else 3600
            return int(value) * multiplier
        
        duration_seconds = parse_time(duration)
        delay_seconds = parse_time(delay)
        
        if not duration_seconds or not delay_seconds:
            await ctx.send("Invalid time format. Use formats like: 10m, 1h")
            return
        
        # Create contest
        now = dt.datetime.now(dt.timezone.utc)
        start_time = now + timedelta(seconds=delay_seconds)
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        conn = sqlite3.connect(CONTEST_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO contests (name, start_time, end_time, channel_id, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"Fishing Contest - {now.strftime('%Y-%m-%d %H:%M')} UTC",
            start_time,
            end_time,
            str(ctx.channel.id),
            str(ctx.author.id)
        ))
        contest_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Update contest state
        contest.current_contest_id = contest_id
        contest.contest_state = CONTEST_SCHEDULED
        contest.contest_start_time = start_time
        contest.contest_end_time = end_time
        contest.contest_channel_id = ctx.channel.id
        contest.contest_duration = duration_seconds
        
        # Send announcement
        embed = discord.Embed(
            title="🎣 Fishing Contest Scheduled!",
            description=(
                f"**Start Time:** <t:{int(start_time.timestamp())}:F> (<t:{int(start_time.timestamp())}:R>)\n"
                f"**Duration:** {duration}\n"
                f"**Channel:** {ctx.channel.mention}\n\n"
                "Use `!joincontest` to participate!\n"
                "A thread will be created 1 minute before the contest starts."
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @bot.command(help="Join the upcoming fishing contest. Usage: !joincontest")
    async def joincontest(ctx):
        """Join the scheduled fishing contest."""
        if contest.contest_state != CONTEST_SCHEDULED:
            await ctx.send("No contest is currently scheduled. Ask an admin to start one!")
            return
        
        if ctx.author.id in contest.participants:
            await ctx.send("You're already registered for the contest!")
            return
        
        # Add participant
        contest.participants.add(ctx.author.id)
        
        # Add to DB
        conn = sqlite3.connect(CONTEST_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO contest_participants (contest_id, user_id, user_name, joined_at)
            VALUES (?, ?, ?, ?)
        """, (contest.current_contest_id, str(ctx.author.id), ctx.author.display_name, dt.datetime.now(dt.timezone.utc)))
        conn.commit()
        conn.close()
        
        await ctx.send(
            f"✅ {ctx.author.mention} joined the fishing contest! "
            f"({len(contest.participants)} participants so far)\n"
            f"Contest starts <t:{int(contest.contest_start_time.timestamp())}:R>"
        )
    
    @bot.command(help="Show current/next contest info. Usage: !contestinfo")
    async def contestinfo(ctx):
        """Display information about current or upcoming contest."""
        if contest.contest_state == CONTEST_NONE:
            await ctx.send("No contest is currently scheduled or active.")
            return
        
        embed = discord.Embed(title="🎣 Contest Information", color=discord.Color.blue())
        
        if contest.contest_state == CONTEST_SCHEDULED:
            embed.add_field(
                name="Status",
                value=f"Scheduled - Starts <t:{int(contest.contest_start_time.timestamp())}:R>",
                inline=False
            )
            embed.add_field(name="Participants", value=f"{len(contest.participants)}", inline=True)
            embed.add_field(name="Duration", value=f"{contest.contest_duration // 60} minutes", inline=True)
        elif contest.contest_state in [CONTEST_STARTING, CONTEST_ACTIVE]:
            status = "Waiting to Start" if contest.contest_state == CONTEST_STARTING else "Active"
            time_text = f"Starts <t:{int(contest.contest_start_time.timestamp())}:R>" if contest.contest_state == CONTEST_STARTING else f"Ends <t:{int(contest.contest_end_time.timestamp())}:R>"
            embed.add_field(
                name="Status",
                value=f"{status} - {time_text}",
                inline=False
            )
            if contest.contest_thread:
                embed.add_field(name="Thread", value=contest.contest_thread.mention, inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(help="Show live contest leaderboard. Usage: !contestlb")
    async def contestlb(ctx):
        """Display current contest leaderboard."""
        if contest.contest_state != CONTEST_ACTIVE or not contest.current_contest_id:
            await ctx.send("No contest is currently active!")
            return
        
        conn = sqlite3.connect(CONTEST_DB)
        c = conn.cursor()
        c.execute("""
            SELECT user_name, SUM(points) as total_points, COUNT(*) as catches
            FROM catches
            WHERE contest_id = ?
            GROUP BY user_id, user_name
            ORDER BY total_points DESC
            LIMIT 10
        """, (contest.current_contest_id,))
        results = c.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="🏆 Contest Leaderboard",
            description=f"Ends <t:{int(contest.contest_end_time.timestamp())}:R>",
            color=discord.Color.gold()
        )
        
        if results:
            medals = ["🥇", "🥈", "🥉"]
            leaderboard = []
            for i, (name, points, catches) in enumerate(results):
                medal = medals[i] if i < 3 else f"{i+1}."
                leaderboard.append(f"{medal} **{name}** - {points:,} pts ({catches} fish)")
            embed.add_field(name="Top Anglers", value="\n".join(leaderboard), inline=False)
        else:
            embed.add_field(name="Leaderboard", value="No catches yet!", inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(help="List past fishing contests. Usage: !pastcontests")
    async def pastcontests(ctx):
        """Show list of past contests."""
        conn = sqlite3.connect(CONTEST_DB)
        c = conn.cursor()
        c.execute("""
            SELECT id, start_time, winner_name, total_participants, total_catches
            FROM contests
            WHERE winner_id IS NOT NULL
            ORDER BY start_time DESC
            LIMIT 10
        """)
        contests = c.fetchall()
        conn.close()
        
        if not contests:
            await ctx.send("No past contests found.")
            return
        
        embed = discord.Embed(title="🎣 Past Fishing Contests", color=discord.Color.blue())
        
        contest_list = []
        for contest_id, start_time, winner, participants, catches in contests:
            date = dt.datetime.fromisoformat(start_time).strftime("%Y-%m-%d")
            contest_list.append(f"**#{contest_id}** ({date}) - Winner: {winner} ({participants} anglers, {catches} catches)")
        
        embed.description = "\n".join(contest_list)
        embed.set_footer(text="Use !contestresults <id> to see detailed results")
        await ctx.send(embed=embed)
    
    @bot.command(help="Show specific contest results. Usage: !contestresults <id>")
    async def contestresults(ctx, contest_id: int):
        """Display detailed results for a specific contest."""
        conn = sqlite3.connect(CONTEST_DB)
        c = conn.cursor()
        
        # Get contest info
        c.execute("""
            SELECT start_time, end_time, winner_name, total_participants, total_catches
            FROM contests
            WHERE id = ?
        """, (contest_id,))
        contest_info = c.fetchone()
        
        if not contest_info:
            await ctx.send(f"Contest #{contest_id} not found.")
            conn.close()
            return
        
        start_time, end_time, winner, participants, total_catches = contest_info
        
        # Get top 10 results
        c.execute("""
            SELECT user_name, SUM(points) as total_points, COUNT(*) as catches
            FROM catches
            WHERE contest_id = ?
            GROUP BY user_id, user_name
            ORDER BY total_points DESC
            LIMIT 10
        """, (contest_id,))
        results = c.fetchall()
        conn.close()
        
        # Build embed
        start_dt = dt.datetime.fromisoformat(start_time)
        embed = discord.Embed(
            title=f"🏆 Contest #{contest_id} Results",
            description=f"**Date:** {start_dt.strftime('%Y-%m-%d %H:%M')} UTC",
            color=discord.Color.gold()
        )
        
        if results:
            medals = ["🥇", "🥈", "🥉"]
            leaderboard = []
            for i, (name, points, catches) in enumerate(results):
                medal = medals[i] if i < 3 else f"{i+1}."
                leaderboard.append(f"{medal} **{name}** - {points:,} pts ({catches} fish)")
            embed.add_field(name="Top Anglers", value="\n".join(leaderboard), inline=False)
        
        embed.add_field(
            name="Contest Stats",
            value=f"**Total Participants:** {participants}\n**Total Catches:** {total_catches}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(help="Show fishing contest help and commands. Usage: !contesthelp")
    async def contesthelp(ctx):
        """Display help for fishing contest commands."""
        help_text = (
            "🎣 **__Fishing Contest Commands__** 🎣\n\n"
            "**Player Commands:**\n"
            "• 📋 **!joincontest** — Join the upcoming fishing contest\n"
            "• ℹ️ **!contestinfo** — Show current/next contest information\n"
            "• 🏆 **!contestlb** — Show live contest leaderboard\n"
            "• 📜 **!pastcontests** — List past fishing contests\n"
            "• 📊 **!contestresults <id>** — Show detailed results for a specific contest\n"
            "• ❓ **!contesthelp** — Show this help message\n\n"
            
            "**Admin Commands:**\n"
            "• 🎮 **!startcontest <duration> <delay>** — Schedule a fishing contest\n"
            "  Example: `!startcontest 10m 5m` (10 min contest starting in 5 min)\n"
            "• ❌ **!cancelcontest** — Cancel the current fishing contest\n\n"
            
            "**Contest Rules:**\n"
            "• All fish caught during contests earn **50% bonus points**\n"
            "• **NO COOLDOWNS** during contests - fish as fast as you can!\n"
            "• Contests run in dedicated threads\n"
            "• Join before the contest starts to participate!"
        )
        await ctx.send(help_text)
    
    @bot.command(help="(Admin) Cancel the current fishing contest. Usage: !cancelcontest")
    async def cancelcontest(ctx):
        """Cancel the current fishing contest."""
        # Admin check
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        if contest.contest_state == CONTEST_NONE:
            await ctx.send("No contest is currently active or scheduled.")
            return
        
        # Reset contest state
        contest.current_contest_id = None
        contest.contest_state = CONTEST_NONE
        contest.contest_thread = None
        contest.participants.clear()
        
        await ctx.send("❌ Contest has been cancelled.")
    
    # Start the contest checker when bot is ready
    @bot.event
    async def on_ready():
        if not contest_checker.is_running():
            contest_checker.start()
    
    # Initialize database
    init_contest_db()

# Function to check if we're in a contest (called from main fishing game)
def is_contest_active():
    """Check if a fishing contest is currently active."""
    return contest.contest_state == CONTEST_ACTIVE

def get_current_contest_id():
    """Get the current contest ID if active."""
    if is_contest_active():
        return contest.current_contest_id
    return None

def get_contest_thread():
    """Get the current contest thread if it exists."""
    # Return thread if in STARTING or ACTIVE state
    if contest.contest_state in [CONTEST_STARTING, CONTEST_ACTIVE] and contest.contest_thread:
        return contest.contest_thread
    return None

def is_contest_starting():
    """Check if a fishing contest is starting (thread created but not active yet)."""
    return contest.contest_state == CONTEST_STARTING