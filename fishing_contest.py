#!/usr/bin/env python3

# Copyright (c) 2025 Robert McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

import os
import sqlite3
import json
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks
import asyncio
from collections import defaultdict

# Constants
CONTEST_DB = "contest_data.db"
CONTEST_STATE_FILE = "contest_state.json"
FISH_DB = "fishing_game.db"
CONTEST_DURATION_MINUTES = 10  # Default duration
CONTEST_FREQUENCY_HOURS = 24  # Default frequency

# Module-level variables
contest_state = {
    "active": False,
    "thread_id": None,
    "contest_id": None,
    "start_time": None,
    "end_time": None,
    "channel_id": None
}
scheduled_contests = []  # List of scheduled contest times

def init_contest_db():
    """Initialize contest database tables."""
    with sqlite3.connect(CONTEST_DB) as conn:
        # Contest metadata table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contests (
                contest_id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                channel_id TEXT,
                thread_id TEXT,
                winner_user_id TEXT,
                winner_user_name TEXT,
                winner_points INTEGER,
                total_participants INTEGER
            )
        """)
        
        # Contest results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contest_results (
                contest_id TEXT,
                user_id TEXT,
                user_name TEXT,
                total_catches INTEGER,
                total_points INTEGER,
                biggest_catch TEXT,
                biggest_weight REAL,
                PRIMARY KEY (contest_id, user_id)
            )
        """)
        conn.commit()

def save_contest_state():
    """Save current contest state to file."""
    with open(CONTEST_STATE_FILE, "w") as f:
        json.dump(contest_state, f, indent=2, default=str)

def load_contest_state():
    """Load contest state from file."""
    global contest_state
    if os.path.exists(CONTEST_STATE_FILE):
        try:
            with open(CONTEST_STATE_FILE, "r") as f:
                loaded_state = json.load(f)
                
            # Convert string times back to datetime objects
            if loaded_state.get("start_time"):
                loaded_state["start_time"] = datetime.fromisoformat(loaded_state["start_time"])
            if loaded_state.get("end_time"):
                loaded_state["end_time"] = datetime.fromisoformat(loaded_state["end_time"])
                
            contest_state.update(loaded_state)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading contest state: {e}")

def is_contest_active():
    """Check if a contest is currently active."""
    if not contest_state["active"]:
        return False
    
    # Check if contest has expired
    if contest_state.get("end_time") and datetime.utcnow() > contest_state["end_time"]:
        contest_state["active"] = False
        save_contest_state()
        return False
        
    return True

def get_current_contest_id():
    """Get the current contest ID."""
    return contest_state.get("contest_id") if is_contest_active() else None

def get_contest_thread():
    """Get the contest thread object if it exists."""
    if not contest_state.get("thread_id"):
        return None
    
    # This will be set by the bot when needed
    return getattr(get_contest_thread, '_thread', None)

def set_contest_thread(thread):
    """Set the contest thread object (called by bot)."""
    get_contest_thread._thread = thread

def is_contest_thread(channel):
    """Check if a channel is the active contest thread."""
    return (contest_state.get("thread_id") and 
            channel.id == contest_state["thread_id"])

def format_time_remaining(end_time):
    """Format time remaining in a readable way."""
    if not end_time:
        return "Unknown"
    
    remaining = end_time - datetime.utcnow()
    if remaining.total_seconds() <= 0:
        return "Contest ended!"
    
    minutes = int(remaining.total_seconds() // 60)
    seconds = int(remaining.total_seconds() % 60)
    
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def setup_contest(bot):
    """Set up contest-related commands and tasks."""
    
    @bot.command(name="startcontest", help="(Admin only) Start a fishing contest. Usage: !startcontest [duration_minutes]", hidden=True)
    @commands.has_permissions(administrator=True)
    async def startcontest(ctx, duration: int = CONTEST_DURATION_MINUTES):
        """Start a new fishing contest."""
        if is_contest_active():
            await ctx.send("A contest is already active!")
            return
        
        if duration < 1 or duration > 60:
            await ctx.send("Contest duration must be between 1 and 60 minutes.")
            return
        
        # Create contest thread
        thread_name = f"🎣 Fishing Contest - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
        thread = await ctx.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread,
            auto_archive_duration=60
        )
        
        # Set up contest state
        contest_id = f"contest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=duration)
        
        contest_state.update({
            "active": True,
            "thread_id": thread.id,
            "contest_id": contest_id,
            "start_time": start_time,
            "end_time": end_time,
            "channel_id": ctx.channel.id
        })
        save_contest_state()
        set_contest_thread(thread)
        
        # Send contest announcement
        embed = discord.Embed(
            title="🎣 FISHING CONTEST STARTING! 🎣",
            description=(
                f"**Duration:** {duration} minutes\n"
                f"**Thread:** {thread.mention}\n\n"
                "🏆 **Rules:**\n"
                "• Fish in the contest thread to participate\n"
                "• No cooldowns during contest!\n"
                "• 50% bonus points on all catches\n"
                "• Most points wins!\n\n"
                "**GO GO GO!** 🎣"
            ),
            color=discord.Color.gold(),
            timestamp=end_time
        )
        embed.set_footer(text="Contest ends")
        
        await ctx.send(embed=embed)
        await thread.send("🎣 **CONTEST STARTED!** Start fishing with `!fish` - no cooldowns, 50% bonus points!")
        
        # Schedule contest end
        asyncio.create_task(end_contest_after_delay(bot, duration * 60))
    
    @bot.command(name="endcontest", aliases=["cancelcontest", "stopcontest"], help="(Admin only) End the current fishing contest early.", hidden=True)
    @commands.has_permissions(administrator=True)
    async def endcontest(ctx):
        """End the current contest early."""
        if not is_contest_active():
            await ctx.send("No contest is currently active.")
            return
        
        await end_current_contest(bot)
        await ctx.send("Contest ended by admin!")
    
    @bot.command(name="conteststatus", help="Check if a fishing contest is active.")
    async def conteststatus(ctx):
        """Check current contest status."""
        if not is_contest_active():
            await ctx.send("No contest is currently active. Ask an admin to start one!")
            return
        
        thread = get_contest_thread()
        time_remaining = format_time_remaining(contest_state.get("end_time"))
        
        thread_mention = f"<#{contest_state['thread_id']}>" if contest_state.get('thread_id') else 'Unknown'
        
        embed = discord.Embed(
            title="🎣 Contest Status",
            description=(
                f"**Status:** Active\n"
                f"**Thread:** {thread_mention}\n"
                f"**Time Remaining:** {time_remaining}\n\n"
                "Fish in the contest thread for no cooldowns and 50% bonus points!"
            ),
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="contesthistory", help="View past fishing contest results.")
    async def contesthistory(ctx):
        """Show history of past contests."""
        with sqlite3.connect(CONTEST_DB) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT contest_id, start_time, winner_user_name, winner_points, total_participants
                FROM contests
                ORDER BY start_time DESC
                LIMIT 10
            """)
            contests = c.fetchall()
        
        if not contests:
            await ctx.send("No contest history found.")
            return
        
        embed = discord.Embed(
            title="🏆 Fishing Contest History",
            description="Last 10 contests:",
            color=discord.Color.gold()
        )
        
        for contest in contests:
            contest_id, start_time, winner, points, participants = contest
            date = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(
                name=f"📅 {date}",
                value=(
                    f"**Winner:** {winner or 'No winner'}\n"
                    f"**Points:** {points or 0:,}\n"
                    f"**Participants:** {participants or 0}\n"
                    f"**ID:** `{contest_id}`"
                ),
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="contestinfo", help="View detailed results from a specific contest. Usage: !contestinfo <contest_id>")
    async def contestinfo(ctx, contest_id: str = None):
        """Show detailed results for a specific contest."""
        if not contest_id:
            await ctx.send("Usage: !contestinfo <contest_id>")
            return
        
        with sqlite3.connect(CONTEST_DB) as conn:
            c = conn.cursor()
            
            # Get contest info
            c.execute("""
                SELECT start_time, end_time, winner_user_name, winner_points, total_participants
                FROM contests
                WHERE contest_id = ?
            """, (contest_id,))
            contest_info = c.fetchone()
            
            if not contest_info:
                await ctx.send(f"No contest found with ID: `{contest_id}`")
                return
            
            # Get top 10 results
            c.execute("""
                SELECT user_name, total_catches, total_points, biggest_catch, biggest_weight
                FROM contest_results
                WHERE contest_id = ?
                ORDER BY total_points DESC
                LIMIT 10
            """, (contest_id,))
            results = c.fetchall()
        
        start_time, end_time, winner, winner_points, participants = contest_info
        
        embed = discord.Embed(
            title=f"🎣 Contest Results: {contest_id}",
            description=(
                f"**Date:** {datetime.fromisoformat(start_time).strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"**Duration:** {int((datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds() / 60)} minutes\n"
                f"**Participants:** {participants}\n"
            ),
            color=discord.Color.gold()
        )
        
        # Add leaderboard
        if results:
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, (name, catches, points, biggest, weight) in enumerate(results, 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                leaderboard_text += (
                    f"{medal} **{name}** - {points:,} pts ({catches} catches)\n"
                    f"   Biggest: {biggest} ({weight:.2f}kg)\n"
                )
            
            embed.add_field(
                name="🏆 Top Anglers",
                value=leaderboard_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="schedulecontest", help="(Admin only) Schedule automatic contests. Usage: !schedulecontest <hours> [duration_minutes]", hidden=True)
    @commands.has_permissions(administrator=True)
    async def schedulecontest(ctx, hours: int, duration: int = CONTEST_DURATION_MINUTES):
        """Schedule recurring contests."""
        if hours < 1 or hours > 168:  # Max 1 week
            await ctx.send("Contest frequency must be between 1 and 168 hours.")
            return
        
        if duration < 1 or duration > 60:
            await ctx.send("Contest duration must be between 1 and 60 minutes.")
            return
        
        # Store schedule settings (you'd want to persist this)
        scheduled_contests.append({
            "frequency_hours": hours,
            "duration_minutes": duration,
            "channel_id": ctx.channel.id,
            "next_run": datetime.utcnow() + timedelta(hours=hours)
        })
        
        await ctx.send(f"✅ Contests scheduled every {hours} hours for {duration} minutes!")
    
    # Background task to check scheduled contests
    @tasks.loop(minutes=1)
    async def check_scheduled_contests():
        """Check if any scheduled contests should start."""
        current_time = datetime.utcnow()
        
        for schedule in scheduled_contests[:]:  # Copy list to allow modification
            if current_time >= schedule["next_run"] and not is_contest_active():
                # Start scheduled contest
                channel = bot.get_channel(schedule["channel_id"])
                if channel:
                    # Create fake context for the command
                    fake_ctx = type('obj', (object,), {
                        'channel': channel,
                        'send': channel.send
                    })
                    
                    # Start contest
                    await startcontest(fake_ctx, schedule["duration_minutes"])
                    
                    # Update next run time
                    schedule["next_run"] = current_time + timedelta(hours=schedule["frequency_hours"])
    
    # Start background task when bot is ready
    @bot.event
    async def on_ready_contest():
        if not check_scheduled_contests.is_running():
            check_scheduled_contests.start()

    @bot.command(name="joincontest", help="Information about joining fishing contests.")
    async def joincontest(ctx):
        """Inform users how to join contests."""
        if is_contest_active():
            thread_id = contest_state.get('thread_id')
            thread_mention = f"<#{thread_id}>" if thread_id else 'the contest thread'
            
            embed = discord.Embed(
                title="🎣 How to Join the Contest",
                description=(
                    f"**No need to join!** Just start fishing in {thread_mention}!\n\n"
                    "• Go to the contest thread\n"
                    "• Use `!fish` to catch fish\n"
                    "• No cooldowns during contests\n"
                    "• 50% bonus points on all catches\n"
                    "• Your catches are automatically counted!\n\n"
                    f"**Current Contest Thread:** {thread_mention}"
                ),
                color=discord.Color.blue()
            )
            
            time_remaining = format_time_remaining(contest_state.get("end_time"))
            embed.add_field(name="Time Remaining", value=time_remaining, inline=False)
        else:
            embed = discord.Embed(
                title="🎣 No Active Contest",
                description=(
                    "There's no contest running right now!\n\n"
                    "When a contest starts:\n"
                    "• A special thread will be created\n"
                    "• Just fish in that thread to participate\n"
                    "• No sign-up needed!\n\n"
                    "Ask an admin to start a contest with `!startcontest`"
                ),
                color=discord.Color.greyple()
            )
        
        await ctx.send(embed=embed)

async def end_contest_after_delay(bot, delay_seconds):
    """End contest after specified delay."""
    await asyncio.sleep(delay_seconds)
    if is_contest_active():
        await end_current_contest(bot)

async def end_current_contest(bot):
    """End the current contest and announce results."""
    if not is_contest_active():
        return
    
    contest_id = contest_state["contest_id"]
    thread_id = contest_state["thread_id"]
    
    # Get contest results from fishing database
    with sqlite3.connect(FISH_DB) as conn:
        c = conn.cursor()
        
        # Get all catches during this contest
        c.execute("""
            SELECT user_id, user_name, COUNT(*) as total_catches, 
                   SUM(points) as total_points,
                   MAX(weight) as biggest_weight
            FROM catches
            WHERE contest_id = ?
            GROUP BY user_id, user_name
            ORDER BY total_points DESC
        """, (contest_id,))
        results = c.fetchall()
        
        # Get biggest catch details for each user
        biggest_catches = {}
        for user_id, _, _, _, max_weight in results:
            c.execute("""
                SELECT catch_name
                FROM catches
                WHERE contest_id = ? AND user_id = ? AND weight = ?
                LIMIT 1
            """, (contest_id, user_id, max_weight))
            catch = c.fetchone()
            if catch:
                biggest_catches[user_id] = catch[0]
    
    # Store results in contest database
    with sqlite3.connect(CONTEST_DB) as conn:
        c = conn.cursor()
        
        # Store contest metadata
        winner = results[0] if results else (None, "No participants", 0, 0, 0)
        c.execute("""
            INSERT INTO contests 
            (contest_id, start_time, end_time, channel_id, thread_id, 
             winner_user_id, winner_user_name, winner_points, total_participants)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contest_id,
            contest_state["start_time"],
            contest_state["end_time"],
            contest_state["channel_id"],
            thread_id,
            winner[0],
            winner[1],
            winner[3],
            len(results)
        ))
        
        # Store individual results
        for user_id, user_name, catches, points, max_weight in results:
            biggest_catch = biggest_catches.get(user_id, "Unknown")
            c.execute("""
                INSERT INTO contest_results
                (contest_id, user_id, user_name, total_catches, total_points, 
                 biggest_catch, biggest_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (contest_id, user_id, user_name, catches, points, biggest_catch, max_weight))
        
        conn.commit()
    
    # Create results embed
    embed = discord.Embed(
        title="🏁 CONTEST ENDED! 🏁",
        description="Final Results:",
        color=discord.Color.gold()
    )
    
    if results:
        # Add top 3
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, user_name, catches, points, max_weight) in enumerate(results[:3]):
            biggest = biggest_catches.get(user_id, "Unknown")
            embed.add_field(
                name=f"{medals[i]} {user_name}",
                value=f"**{points:,} points** ({catches} catches)\nBiggest: {biggest} ({max_weight:.2f}kg)",
                inline=False
            )
    else:
        embed.add_field(name="No participants", value="Better luck next time!", inline=False)
    
    embed.set_footer(text=f"Contest ID: {contest_id}")
    
    # Send results
    thread = get_contest_thread()
    if thread:
        try:
            await thread.send(embed=embed)
            await thread.send("Thanks for participating! This thread will be archived.")
            # Archive thread
            await thread.edit(archived=True)
        except discord.errors.HTTPException:
            pass
    
    # Also send to main channel
    channel = bot.get_channel(contest_state["channel_id"])
    if channel:
        await channel.send(embed=embed)
    
    # Clear contest state
    contest_state.update({
        "active": False,
        "thread_id": None,
        "contest_id": None,
        "start_time": None,
        "end_time": None,
        "channel_id": None
    })
    save_contest_state()
    set_contest_thread(None)

# Initialize database and load state on import
init_contest_db()
load_contest_state()