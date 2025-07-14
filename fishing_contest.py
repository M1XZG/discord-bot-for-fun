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
import time  # Add this import
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
CONTEST_PREPARATION_TIME = 60  # Seconds to wait before contest starts

# Module-level variables
contest_state = {
    "active": False,
    "preparing": False,  # New state for preparation phase
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
            if loaded_state.get("prep_start_time"):
                loaded_state["prep_start_time"] = datetime.fromisoformat(loaded_state["prep_start_time"])
                
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

def is_contest_preparing():
    """Check if a contest is in preparation phase."""
    return contest_state.get("preparing", False)

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

def get_contest_start_time():
    """Get the start time of the current contest if preparing."""
    global contest_state
    if contest_state and contest_state.get("preparing", False):
        # During preparation, the contest starts after CONTEST_PREPARATION_TIME
        return datetime.utcnow() + timedelta(seconds=CONTEST_PREPARATION_TIME)
    return None

def setup_contest(bot):
    """Set up contest-related commands and tasks."""
    
    @bot.command(name="startcontest", help="(Admin only) Start a fishing contest. Usage: !startcontest [duration_minutes]", hidden=True)
    @commands.has_permissions(administrator=True)
    async def startcontest(ctx, duration: int = CONTEST_DURATION_MINUTES):
        """Start a new fishing contest."""
        if is_contest_active() or is_contest_preparing():
            await ctx.send("A contest is already active or preparing!")
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
        
        # Set up contest state - PREPARING phase
        contest_id = f"contest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        contest_state.update({
            "active": False,
            "preparing": True,
            "thread_id": thread.id,
            "contest_id": contest_id,
            "start_time": None,  # Will be set when contest actually starts
            "end_time": None,    # Will be set when contest actually starts
            "channel_id": ctx.channel.id,
            "prep_start_time": datetime.utcnow()  # Add this to track when prep started
        })
        save_contest_state()
        set_contest_thread(thread)
        
        # Calculate when contest will start (using time.time() for reliability)
        current_time = int(time.time())
        start_timestamp = current_time + CONTEST_PREPARATION_TIME  # 60 seconds from now
        end_timestamp = start_timestamp + (duration * 60)  # duration in minutes
        
        # Send preparation announcement
        prep_embed = discord.Embed(
            title="🎣 FISHING CONTEST PREPARING! 🎣",
            description=(
                f"**Duration:** {duration} minutes\n"
                f"**Thread:** {thread.mention}\n"
                f"**Starting:** <t:{start_timestamp}:t> (<t:{start_timestamp}:R>)\n"
                f"**Ending:** <t:{end_timestamp}:t> (<t:{end_timestamp}:R>)\n\n"
                "📢 **Get Ready!**\n"
                "• Head to the contest thread\n"
                "• Type `!joincontest` to learn how to participate\n"
                "• Contest will start automatically!\n"
                "• Fishing in the thread is LOCKED until the contest starts\n\n"
                "**Prizes:**\n"
                "🥇 First Place: Eternal glory!\n"
                "🥈 Second Place: Bragging rights!\n"
                "🥉 Third Place: A participation trophy!"
            ),
            color=discord.Color.orange()
        )
        
        await ctx.send(embed=prep_embed)
        await thread.send(
            "**🎣 CONTEST PREPARATION PHASE 🎣**\n\n"
            "The contest will begin in **60 seconds**!\n"
            "• ❌ Fishing is currently LOCKED\n"
            "• ✅ Use `!joincontest` to learn how to participate\n"
            "• ⏰ Get ready for the START announcement!\n\n"
            "*The thread will unlock for fishing when the contest begins.*"
        )
        
        # Schedule contest start
        asyncio.create_task(start_contest_after_delay(bot, thread, duration, contest_id))
    
    async def start_contest_after_delay(bot, thread, duration, contest_id):
        """Start the contest after preparation time."""
        await asyncio.sleep(CONTEST_PREPARATION_TIME)
        
        # Update state to active
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=duration)
        
        contest_state.update({
            "active": True,
            "preparing": False,
            "start_time": start_time,
            "end_time": end_time
        })
        save_contest_state()
        
        # Send start announcement
        current_time = int(time.time())
        end_timestamp = current_time + (duration * 60)  # duration minutes from now
        
        start_embed = discord.Embed(
            title="🎣 CONTEST STARTED! GO GO GO! 🎣",
            description=(
                "**The fishing contest has officially begun!**\n\n"
                f"**Ending:** <t:{end_timestamp}:t> (<t:{end_timestamp}:R>)\n\n"
                "🏆 **Rules:**\n"
                "• Fish ONLY in this thread to participate\n"
                "• NO cooldowns during the contest\n"
                "• 50% bonus points on ALL catches\n"
                "• Most points wins!\n"
                "• Ultra-legendary catches get special announcements!\n\n"
                "**START FISHING NOW WITH `!fish`**"
            ),
            color=discord.Color.green()
        )
        
        await thread.send(embed=start_embed)
        await thread.send("@everyone **CONTEST IS LIVE! START FISHING!** 🎣🎣🎣")
        
        # Schedule contest end
        asyncio.create_task(end_contest_after_delay(bot, duration * 60))
    
    @bot.command(name="endcontest", aliases=["cancelcontest", "stopcontest"], help="(Admin only) End the current fishing contest early.", hidden=True)
    @commands.has_permissions(administrator=True)
    async def endcontest(ctx):
        """End the current contest early."""
        if not (is_contest_active() or is_contest_preparing()):
            await ctx.send("No contest is currently active or preparing.")
            return
        
        if is_contest_preparing():
            # Cancel preparation
            contest_state.update({
                "active": False,
                "preparing": False,
                "thread_id": None,
                "contest_id": None,
                "start_time": None,
                "end_time": None,
                "channel_id": None
            })
            save_contest_state()
            await ctx.send("Contest preparation cancelled!")
            return
        
        await end_current_contest(bot)
        await ctx.send("Contest ended by admin!")
    
    @bot.command(name="conteststatus", help="Check if a fishing contest is active.")
    async def conteststatus(ctx):
        """Check current contest status."""
        if is_contest_preparing():
            thread_mention = f"<#{contest_state['thread_id']}>" if contest_state.get('thread_id') else 'Unknown'
            
            # Calculate when it will start
            if contest_state.get("prep_start_time"):
                prep_start = contest_state["prep_start_time"]
                if isinstance(prep_start, str):
                    prep_start = datetime.fromisoformat(prep_start)
                elapsed = (datetime.utcnow() - prep_start).total_seconds()
                time_until_start = max(0, CONTEST_PREPARATION_TIME - elapsed)
                
                if time_until_start > 0:
                    start_timestamp = int(time.time() + time_until_start)
                    start_info = f"<t:{start_timestamp}:R>"
                else:
                    start_info = "any moment now!"
            else:
                start_info = "~60 seconds"
            
            embed = discord.Embed(
                title="🎣 Contest Status: PREPARING",
                description=(
                    f"**Status:** Preparing to start\n"
                    f"**Thread:** {thread_mention}\n"
                    f"**Starting:** {start_info}\n\n"
                    "Head to the contest thread and wait for the START announcement!"
                ),
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=embed)
            return
            
        if not is_contest_active():
            await ctx.send("No contest is currently active. Ask an admin to start one with `!startcontest`!")
            return
        
        thread_mention = f"<#{contest_state['thread_id']}>" if contest_state.get('thread_id') else 'Unknown'
        
        # Calculate end timestamp
        if contest_state.get("end_time"):
            end_time = contest_state["end_time"]
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            remaining_seconds = (end_time - datetime.utcnow()).total_seconds()
            if remaining_seconds > 0:
                end_timestamp = int(time.time() + remaining_seconds)
                time_info = f"<t:{end_timestamp}:t> (<t:{end_timestamp}:R>)"
            else:
                time_info = "Contest ended!"
        else:
            time_info = "Unknown"
        
        embed = discord.Embed(
            title="🎣 Contest Status",
            description=(
                f"**Status:** Active\n"
                f"**Thread:** {thread_mention}\n"
                f"**Ending:** {time_info}\n\n"
                "Fish in the contest thread for no cooldowns and 50% bonus points!"
            ),
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="joincontest", help="Information about joining fishing contests.")
    async def joincontest(ctx):
        """Inform users how to join contests."""
        if is_contest_preparing():
            thread_id = contest_state.get('thread_id')
            thread_mention = f"<#{thread_id}>" if thread_id else 'the contest thread'
            
            embed = discord.Embed(
                title="🎣 Contest is Preparing!",
                description=(
                    f"**The contest hasn't started yet!**\n\n"
                    f"• Contest thread: {thread_mention}\n"
                    "• Starting in: ~60 seconds\n"
                    "• Fishing is LOCKED until it starts\n"
                    "• Wait for the START announcement!\n\n"
                    "**How to participate when it starts:**\n"
                    "• Just use `!fish` in the contest thread\n"
                    "• No sign-up needed!\n"
                    "• Your catches are automatically counted"
                ),
                color=discord.Color.orange()
            )
        elif is_contest_active():
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
    
    @bot.command(name="contesthelp", help="Show all contest-related commands and information.")
    async def contesthelp(ctx):
        """Show comprehensive contest help."""
        embed = discord.Embed(
            title="🎣 Fishing Contest Help 🎣",
            description="Everything you need to know about fishing contests!",
            color=discord.Color.blue()
        )
        
        # User commands
        embed.add_field(
            name="📢 User Commands",
            value=(
                "• `!conteststatus` - Check if a contest is active\n"
                "• `!joincontest` - Learn how to participate\n"
                "• `!contesthistory` - View past contest results\n"
                "• `!contestinfo <id>` - View detailed results\n"
                "• `!contesthelp` - Show this help message"
            ),
            inline=False
        )
        
        # Admin commands
        embed.add_field(
            name="🛠️ Admin Commands",
            value=(
                "• `!startcontest [minutes]` - Start a contest (1-60 min)\n"
                "• `!endcontest` - End contest early\n"
                "• `!schedulecontest <hours> [minutes]` - Schedule recurring contests"
            ),
            inline=False
        )
        
        # How contests work
        embed.add_field(
            name="🏆 How Contests Work",
            value=(
                "1. Admin starts contest with `!startcontest`\n"
                "2. A special thread is created (60s prep time)\n"
                "3. When contest starts, fish in the thread\n"
                "4. No cooldowns + 50% bonus points!\n"
                "5. Most points wins when time runs out"
            ),
            inline=False
        )
        
        # Contest benefits
        embed.add_field(
            name="✨ Contest Benefits",
            value=(
                "• **No cooldowns** - Fish as fast as you can!\n"
                "• **50% bonus points** - All catches worth more\n"
                "• **Special thread** - Dedicated contest space\n"
                "• **Auto tracking** - Scores tracked automatically\n"
                "• **Ultra-legendary announcements** - Special alerts!"
            ),
            inline=False
        )
        
        embed.set_footer(text="Good luck and happy fishing! 🎣")
        
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

async def start_contest(ctx, duration_str, delay_str):
    # ... existing code ...
    
    # After calculating start_time and end_time:
    start_time = datetime.utcnow() + delay
    end_time = start_time + duration
    
    # Convert to Unix timestamps for Discord
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())
    
    # Update the embed creation to use Discord timestamps:
    embed = discord.Embed(
        title="🎣 Fishing Contest Announced! 🏆",
        description=(
            f"A **{duration_minutes}-minute** fishing contest will begin in **{delay_minutes} minutes**!\n\n"
            f"**Start Time:** <t:{start_timestamp}:F>\n"  # Full date/time format
            f"**End Time:** <t:{end_timestamp}:F>\n\n"
            f"Use `!joincontest` to enter!\n"
            f"Contest fishing will take place in a dedicated thread."
        ),
        color=discord.Color.gold()
    )
    
    # ... rest of the function ...

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
        "preparing": False,
        "thread_id": None,
        "contest_id": None,
        "start_time": None,
        "end_time": None,
        "channel_id": None,
        "prep_start_time": None  # Clear this too
    })
    save_contest_state()
    set_contest_thread(None)

# Initialize database and load state on import
init_contest_db()
load_contest_state()