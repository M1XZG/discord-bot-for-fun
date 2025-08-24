# Copyright (c) 2025 Robert McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

import asyncio
import io
import json
import sqlite3
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv  # Add this
from openai import OpenAI  # Use new OpenAI client

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global variables (will be set by main.py)
prompts = {}
max_tokens = {}
config = {}
token_usage_enabled = False
CONVO_DB = "conversations.db"
STATS_DB = "chatgpt_stats.db"
stats_tracking_enabled = True

def set_globals(prompts_dict, max_tokens_dict, config_dict, token_usage_flag, convo_db_path, api_key=None):
    """Set global variables from main.py"""
    global prompts, max_tokens, config, token_usage_enabled, CONVO_DB, client, STATS_DB, stats_tracking_enabled
    prompts = prompts_dict
    max_tokens = max_tokens_dict
    config = config_dict
    token_usage_enabled = token_usage_flag
    CONVO_DB = convo_db_path
    # Add stats DB path from config if available
    STATS_DB = config_dict.get("stats_db_path", "chatgpt_stats.db")
    stats_tracking_enabled = config_dict.get("stats_tracking_enabled", True)
    if api_key:
        client.api_key = api_key

def get_prompt(command, variant="generic", **kwargs):
    """
    Retrieves a prompt template for a given command and variant,
    then formats it with the provided keyword arguments.
    """
    cmd_prompts = prompts.get(command, {})
    template = cmd_prompts.get(variant, "")
    if not template:
        return ""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        print(f"Error formatting prompt for {command}/{variant}: {e}")
        return template

async def send_long_response(ctx_or_channel, text, max_length=1900, filename="response.txt"):
    """Send a response, splitting it if it's too long for Discord."""
    if not hasattr(ctx_or_channel, 'send'):
        raise ValueError("Invalid context or channel object")
    
    channel = ctx_or_channel
    is_context = hasattr(ctx_or_channel, 'message')
    
    if len(text) <= max_length:
        await channel.send(text)
        return
    
    # Send as file if too long
    if len(text) > max_length * 3:  # If it would take more than 3 messages
        file = discord.File(io.StringIO(text), filename=filename)
        await channel.send("Response too long, sending as file:", file=file)
        return
    
    # Otherwise split into chunks
    chunks = []
    while text:
        # Find a good break point (newline, space, or max_length)
        chunk = text[:max_length]
        break_point = max_length
        
        if len(text) > max_length:
            # Try to break at newline
            newline_pos = chunk.rfind('\n')
            if newline_pos > max_length * 0.8:  # Only if it's not too far back
                break_point = newline_pos + 1
            else:
                # Try to break at space
                space_pos = chunk.rfind(' ')
                if space_pos > max_length * 0.8:
                    break_point = space_pos + 1
        
        chunks.append(text[:break_point].rstrip())
        text = text[break_point:].lstrip()
    
    for i, chunk in enumerate(chunks):
        if i == 0:
            await channel.send(chunk)
        else:
            await channel.send(f"...{chunk}")

async def get_chatgpt_response(prompt, command="query", conversation_history=None):
    """
    Get a response from ChatGPT API using the new client format.
    Returns the response text and token usage info.
    """
    max_t = max_tokens.get(command, 150)
    
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_t,
            temperature=0.8
        )
        
        reply = response.choices[0].message.content.strip()
        usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        return reply, usage
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None, {}

def get_db_connection():
    """Get a database connection with proper settings."""
    conn = sqlite3.connect(CONVO_DB)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_conversation_db():
    """Initialize the conversation database with proper error handling."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if tables exist and create/migrate as needed
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
            if c.fetchone():
                # Table exists, check if it has the right columns
                c.execute("PRAGMA table_info(conversations)")
                columns = [col[1] for col in c.fetchall()]
                
                if 'messages' not in columns:
                    # Old table structure, migrate it
                    print("Migrating conversations table to new structure...")
                    c.execute("DROP TABLE conversations")
                    c.execute("DROP TABLE IF EXISTS thread_meta")
            
            # Create tables with correct structure
            c.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    thread_id TEXT PRIMARY KEY,
                    messages TEXT NOT NULL,
                    last_updated DATETIME NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS thread_meta (
                    thread_id TEXT PRIMARY KEY,
                    creator_id TEXT NOT NULL,
                    created_at DATETIME NOT NULL
                )
            """)
            
            # Create indexes for better performance
            c.execute("CREATE INDEX IF NOT EXISTS idx_thread_meta_creator ON thread_meta(creator_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_thread_meta_created ON thread_meta(created_at)")
            
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def init_stats_db():
    """Initialize the statistics database."""
    if not stats_tracking_enabled:
        return
        
    try:
        conn = sqlite3.connect(STATS_DB)
        c = conn.cursor()
        
        # Create main stats table
        c.execute("""
            CREATE TABLE IF NOT EXISTS command_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                command TEXT NOT NULL,
                input_chars INTEGER NOT NULL,
                output_chars INTEGER NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                thread_id TEXT,
                is_thread_message BOOLEAN DEFAULT 0
            )
        """)
        
        # Create thread summary table
        c.execute("""
            CREATE TABLE IF NOT EXISTS thread_stats (
                thread_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                closed_at DATETIME,
                total_messages INTEGER DEFAULT 0,
                total_input_chars INTEGER DEFAULT 0,
                total_output_chars INTEGER DEFAULT 0,
                total_prompt_tokens INTEGER DEFAULT 0,
                total_completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                close_reason TEXT
            )
        """)
        
        # Create indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_command_stats_user ON command_stats(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_command_stats_timestamp ON command_stats(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_command_stats_command ON command_stats(command)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_thread_stats_user ON thread_stats(user_id)")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing stats database: {e}")

def log_command_usage(user, command, input_text, output_text, usage_info, thread_id=None, is_thread_message=False):
    """Log command usage statistics."""
    if not stats_tracking_enabled:
        return
        
    try:
        conn = sqlite3.connect(STATS_DB)
        c = conn.cursor()
        
        # Get user display name
        user_name = getattr(user, 'display_name', str(user))
        
        c.execute("""
            INSERT INTO command_stats (
                timestamp, user_id, user_name, command, 
                input_chars, output_chars,
                prompt_tokens, completion_tokens, total_tokens,
                thread_id, is_thread_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            str(user.id),
            user_name,
            command,
            len(input_text),
            len(output_text),
            usage_info.get('prompt_tokens', 0),
            usage_info.get('completion_tokens', 0),
            usage_info.get('total_tokens', 0),
            thread_id,
            is_thread_message
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging command usage: {e}")

def create_thread_stats(thread_id, user):
    """Create initial thread statistics entry."""
    if not stats_tracking_enabled:
        return
        
    try:
        conn = sqlite3.connect(STATS_DB)
        c = conn.cursor()
        
        user_name = getattr(user, 'display_name', str(user))
        
        c.execute("""
            INSERT INTO thread_stats (
                thread_id, user_id, user_name, created_at,
                total_messages, total_input_chars, total_output_chars,
                total_prompt_tokens, total_completion_tokens, total_tokens
            ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, 0)
        """, (
            str(thread_id),
            str(user.id),
            user_name,
            datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating thread stats: {e}")

def update_thread_stats(thread_id):
    """Update thread statistics from command_stats."""
    if not stats_tracking_enabled:
        return
        
    try:
        conn = sqlite3.connect(STATS_DB)
        c = conn.cursor()
        
        # Calculate totals from command_stats
        c.execute("""
            UPDATE thread_stats
            SET 
                total_messages = (
                    SELECT COUNT(*) FROM command_stats 
                    WHERE thread_id = ? AND is_thread_message = 1
                ),
                total_input_chars = (
                    SELECT COALESCE(SUM(input_chars), 0) FROM command_stats 
                    WHERE thread_id = ? AND is_thread_message = 1
                ),
                total_output_chars = (
                    SELECT COALESCE(SUM(output_chars), 0) FROM command_stats 
                    WHERE thread_id = ? AND is_thread_message = 1
                ),
                total_prompt_tokens = (
                    SELECT COALESCE(SUM(prompt_tokens), 0) FROM command_stats 
                    WHERE thread_id = ? AND is_thread_message = 1
                ),
                total_completion_tokens = (
                    SELECT COALESCE(SUM(completion_tokens), 0) FROM command_stats 
                    WHERE thread_id = ? AND is_thread_message = 1
                ),
                total_tokens = (
                    SELECT COALESCE(SUM(total_tokens), 0) FROM command_stats 
                    WHERE thread_id = ? AND is_thread_message = 1
                )
            WHERE thread_id = ?
        """, (thread_id, thread_id, thread_id, thread_id, thread_id, thread_id, thread_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating thread stats: {e}")

def close_thread_stats(thread_id, reason="manual"):
    """Mark thread as closed in statistics."""
    if not stats_tracking_enabled:
        return
        
    try:
        conn = sqlite3.connect(STATS_DB)
        c = conn.cursor()
        
        c.execute("""
            UPDATE thread_stats
            SET closed_at = ?, close_reason = ?
            WHERE thread_id = ?
        """, (
            datetime.now(timezone.utc).isoformat(),
            reason,
            str(thread_id)
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error closing thread stats: {e}")

def save_conversation(thread_id, messages):
    """Save conversation history to database."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO conversations (thread_id, messages, last_updated) VALUES (?, ?, ?)",
                (str(thread_id), json.dumps(messages), datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
    except Exception as e:
        print(f"Error saving conversation: {e}")

def load_conversation(thread_id):
    """Load conversation history from database."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT messages FROM conversations WHERE thread_id = ?", (str(thread_id),))
            row = c.fetchone()
            if row:
                return json.loads(row['messages'])
    except Exception as e:
        print(f"Error loading conversation: {e}")
    return []

def delete_thread_data(thread_id):
    """Delete all data for a thread."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM conversations WHERE thread_id = ?", (str(thread_id),))
            c.execute("DELETE FROM thread_meta WHERE thread_id = ?", (str(thread_id),))
            conn.commit()
    except Exception as e:
        print(f"Error deleting thread data: {e}")

def get_chat_thread_retention_days():
    """Get the chat thread retention period in days from config."""
    return config.get("chat_thread_retention_days", 7)

def format_time_duration(td):
    """Format a timedelta into a readable string."""
    days = td.days
    hours = td.seconds // 3600
    mins = (td.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if mins > 0 or not parts:  # Show minutes if nothing else or if there are minutes
        parts.append(f"{mins}m")
    
    return " ".join(parts[:2])  # Show at most 2 parts

def setup_chatgpt(bot):
    """Setup all ChatGPT-related commands."""
    
    # Import io for file handling
    import io
    
    # Helper function for token usage display
    async def send_token_usage(ctx, usage):
        """Send token usage info if enabled."""
        if token_usage_enabled and usage:
            await ctx.send(
                f"_Token usage - Prompt: {usage.get('prompt_tokens', 0)}, "
                f"Reply: {usage.get('completion_tokens', 0)}, "
                f"Total: {usage.get('total_tokens', 0)}_"
            )
    
    @bot.command(help="Get a 50-word, uplifting message for yourself or someone else! Usage: !feelgood [recipient]")
    async def feelgood(ctx, *, recipient: str = None):
        """Generate a feel-good message."""
        if recipient and recipient.strip():
            # For targeted messages, pass both user and recipient
            prompt = get_prompt("feelgood", "targeted", 
                              user=ctx.author.display_name,
                              sender=ctx.author.display_name, 
                              recipient=recipient.strip())
        else:
            # For generic messages, pass user
            prompt = get_prompt("feelgood", "generic", 
                              user=ctx.author.display_name,
                              sender=ctx.author.display_name, 
                              recipient=ctx.author.display_name)
        
        async with ctx.typing():
            reply, usage = await get_chatgpt_response(prompt, command="feelgood")
        
        if reply:
            await ctx.send(reply)
            await send_token_usage(ctx, usage)
            # Add logging
            log_command_usage(ctx.author, "feelgood", prompt, reply, usage)
        else:
            await ctx.send("Sorry, I couldn't generate a feel-good message right now. Please try again later!")

    @bot.command(help="Hear a random, family-friendly joke, or specify a topic for a themed joke! Usage: !joke [topic]")
    async def joke(ctx, *, topic: str = None):
        """Tell a joke."""
        if topic and topic.strip():
            prompt = get_prompt("joke", "targeted", topic=topic.strip())
        else:
            prompt = get_prompt("joke", "generic")
        
        async with ctx.typing():
            reply, usage = await get_chatgpt_response(prompt, command="joke")
        
        if reply:
            await ctx.send(reply)
            await send_token_usage(ctx, usage)
            # Add logging
            log_command_usage(ctx.author, "joke", prompt, reply, usage)
        else:
            await ctx.send("Sorry, I couldn't think of a joke right now. Please try again later!")

    @bot.command(help="Give someone (or yourself) a wholesome compliment, optionally about a topic. Usage: !compliment [@user] [topic]")
    async def compliment(ctx, member: discord.Member = None, *, topic: str = None):
        """Give a compliment."""
        target = member or ctx.author
        if topic and topic.strip():
            prompt = get_prompt("compliment", "targeted", 
                              sender=ctx.author.display_name, 
                              recipient=target.display_name, 
                              topic=topic.strip())
        else:
            prompt = get_prompt("compliment", "generic", 
                              sender=ctx.author.display_name, 
                              recipient=target.display_name)
        
        async with ctx.typing():
            reply, usage = await get_chatgpt_response(prompt, command="compliment")
        
        if reply:
            await ctx.send(reply)
            await send_token_usage(ctx, usage)
            # Add logging
            log_command_usage(ctx.author, "compliment", prompt, reply, usage)
        else:
            await ctx.send("Sorry, I couldn't generate a compliment right now. Please try again later!")

    @bot.command(help="Receive wholesome advice, optionally on a topic. Usage: !advice [topic]")
    async def advice(ctx, *, topic: str = None):
        """Give advice."""
        if topic and topic.strip():
            prompt = get_prompt("advice", "targeted", topic=topic.strip())
        else:
            prompt = get_prompt("advice", "generic")
        
        async with ctx.typing():
            reply, usage = await get_chatgpt_response(prompt, command="advice")
        
        if reply:
            await ctx.send(reply)
            await send_token_usage(ctx, usage)
            # Add logging
            log_command_usage(ctx.author, "advice", prompt, reply, usage)
        else:
            await ctx.send("Sorry, I couldn't generate advice right now. Please try again later!")

    @bot.command(help="Receive a unique, inspirational quote, optionally addressed to someone. Usage: !inspo [recipient]")
    async def inspo(ctx, *, recipient: str = None):
        """Generate an inspirational quote."""
        if recipient and recipient.strip():
            prompt = get_prompt("inspo", "targeted", sender=ctx.author.display_name, recipient=recipient.strip())
        else:
            prompt = get_prompt("inspo", "generic", sender=ctx.author.display_name, recipient=ctx.author.display_name)
        
        async with ctx.typing():
            reply, usage = await get_chatgpt_response(prompt, command="inspo")
        
        if reply:
            await ctx.send(reply)
            await send_token_usage(ctx, usage)
            # Add logging
            log_command_usage(ctx.author, "inspo", prompt, reply, usage)
        else:
            await ctx.send("Sorry, I couldn't generate an inspirational quote right now. Please try again later!")

    @bot.command(help="Quick free-form question to ChatGPT (short reply, stays in channel). Usage: !q <your question>",
                 aliases=["quick", "qask"])
    async def q(ctx, *, question: str = None):
        """Quick question to ChatGPT."""
        if not question or not question.strip():
            await ctx.send("Please provide a question. Usage: `!q <your question>`")
            return
        
        async with ctx.typing():
            reply, usage = await get_chatgpt_response(question.strip(), command="query")
        
        if reply:
            await send_long_response(ctx, reply)
            await send_token_usage(ctx, usage)
            # Add logging
            log_command_usage(ctx.author, "q", question.strip(), reply, usage)
        else:
            await ctx.send("Sorry, I couldn't get a response from ChatGPT. Please try again later!")

    @bot.command(help="Generate an image with DALL·E from your description. Usage: !image <description>")
    async def image(ctx, *, description: str = None):
        """Generate an image using OpenAI's DALL·E."""
        if not description or not description.strip():
            await ctx.send("Please provide a description for the image. Usage: `!image <description>`")
            return
        
        await ctx.send(f"🖼️ Generating image for: \"{description.strip()}\" ...")
        
        try:
            response = client.images.generate(
                prompt=description.strip(),
                n=1,
                size="1024x1024"
            )
            
            if response.data:
                image_url = response.data[0].url
                await ctx.send(image_url)
                
                # Calculate approximate image data size
                # DALL-E images are typically JPEG format
                # 1024x1024 JPEG is approximately 200-400KB depending on complexity
                # We'll use an average estimate
                image_size_estimate = 300 * 1024  # 300KB in bytes
                
                # For image generation, we track:
                # - input_chars: the prompt length
                # - output_chars: the image URL length + estimated image data size
                # - tokens: estimated based on prompt (roughly 1 token per 4 chars)
                prompt_tokens_estimate = len(description.strip()) // 4
                
                usage_info = {
                    'prompt_tokens': prompt_tokens_estimate,
                    'completion_tokens': 0,  # No text completion tokens
                    'total_tokens': prompt_tokens_estimate,
                    'image_size': image_size_estimate  # Store for reference
                }
                
                # Log the image generation
                # For output, we'll use the URL length + a note about image size
                output_text = f"{image_url} [Image: 1024x1024, ~{image_size_estimate//1024}KB]"
                log_command_usage(ctx.author, "image", description.strip(), output_text, usage_info)
                
            else:
                await ctx.send("Sorry, I couldn't generate an image for that prompt.")
        except Exception as e:
            print(f"OpenAI Image API error: {e}")
            await ctx.send("Sorry, there was an error generating the image. Please try again later.")

    @bot.command(help="Start a new ChatGPT conversation thread. Usage: !chat <your message>",
                 aliases=["ask", "query"])
    async def chat(ctx, *, message: str = None):
        """Start a conversational chat thread."""
        if not message or not message.strip():
            await ctx.send("Please provide a message. Usage: `!chat <your message>`")
            return
        
        # Create a new thread
        thread_name = f"Chat with {ctx.author.display_name}"[:100]  # Discord limit
        try:
            thread = await ctx.message.create_thread(
                name=thread_name,
                auto_archive_duration=10080  # 7 days
            )
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create thread: {e}")
            return
        
        # Save thread metadata
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO thread_meta (thread_id, creator_id, created_at) VALUES (?, ?, ?)",
                    (str(thread.id), str(ctx.author.id), datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
            # Add thread stats creation
            create_thread_stats(thread.id, ctx.author)
        except Exception as e:
            print(f"Error saving thread metadata: {e}")
            await thread.send("Error saving thread data. Chat may not work properly.")
            return
        
        # Get initial response
        async with thread.typing():
            reply, usage = await get_chatgpt_response(message.strip(), command="query")
        
        if reply:
            # Save conversation
            messages = [
                {"role": "user", "content": message.strip()},
                {"role": "assistant", "content": reply}
            ]
            save_conversation(thread.id, messages)
            
            # Log the initial chat message
            log_command_usage(ctx.author, "chat", message.strip(), reply, usage, 
                             thread_id=str(thread.id), is_thread_message=False)
            
            retention_days = get_chat_thread_retention_days()
            
            # Format retention period for display
            if retention_days >= 1:
                retention_display = f"{int(retention_days)} day{'s' if int(retention_days) != 1 else ''}"
            else:
                hours = int(retention_days * 24)
                retention_display = f"{hours} hour{'s' if hours != 1 else ''}"
            
            # Send welcome message
            embed = discord.Embed(
                title="💬 Chat Thread Started!",
                description=f"I'll remember our conversation in this thread for **{retention_display}**.",
                color=discord.Color.green()
            )
            embed.add_field(name="End Chat", value="Use `!endchat` to end this chat early", inline=False)
            embed.set_footer(text=f"Thread ID: {thread.id}")
            await thread.send(embed=embed)
            
            # Send the actual response
            await send_long_response(thread, reply)
            await send_token_usage(thread, usage)
        else:
            await thread.send("Sorry, I couldn't start the chat. Please try again later!")
            await thread.delete()

    @bot.command(help="End your chat thread early and delete it (only works inside a chat thread).")
    async def endchat(ctx):
        """End a chat thread."""
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send("This command only works inside a chat thread.")
            return
        
        # Check permissions
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT creator_id FROM thread_meta WHERE thread_id = ?", (str(ctx.channel.id),))
                row = c.fetchone()
                
                if not row:
                    await ctx.send("This doesn't appear to be a chat thread.")
                    return
                
                creator_id = row['creator_id']
        except Exception as e:
            print(f"Error checking thread ownership: {e}")
            await ctx.send("Error checking thread ownership.")
            return
        
        is_admin = ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild
        
        if str(ctx.author.id) != creator_id and not is_admin:
            await ctx.send("Only the thread creator or an admin can end this chat.")
            return
        
        # Delete DB data and the thread
        delete_thread_data(ctx.channel.id)
        # Close thread stats
        close_thread_stats(ctx.channel.id, reason="manual")
        
        embed = discord.Embed(
            title="🛑 Ending Chat",
            description="This thread and its memory will be deleted in 10 seconds...",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        await asyncio.sleep(10)
        try:
            await ctx.channel.delete(reason="Chat ended by user or admin with !endchat")
        except Exception as e:
            print(f"Could not delete thread {ctx.channel.id}: {e}")

    # Setup conversation listener
    @bot.event
    async def on_message(message):
        # Don't respond to ourselves or other bots
        if message.author.bot:
            return
        
        # Check if this is in a chat thread
        if isinstance(message.channel, discord.Thread):
            # Don't process commands as conversation
            if message.content.startswith(bot.command_prefix):
                await bot.process_commands(message)
                return
            
            # Check if this is a chat thread
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT creator_id FROM thread_meta WHERE thread_id = ?", (str(message.channel.id),))
                    row = c.fetchone()
                    
                    if not row:
                        await bot.process_commands(message)
                        return
            except Exception as e:
                print(f"Error checking thread: {e}")
                await bot.process_commands(message)
                return
            
            # Load conversation history
            messages = load_conversation(message.channel.id)
            
            # Limit conversation history to prevent token overflow
            if len(messages) > 20:  # Keep last 20 messages
                messages = messages[-20:]
            
            # Add new message
            messages.append({"role": "user", "content": message.content})
            
            # Get response
            async with message.channel.typing():
                reply, usage = await get_chatgpt_response(
                    message.content, 
                    command="query", 
                    conversation_history=messages
                )
            
            if reply:
                # Add assistant response
                messages.append({"role": "assistant", "content": reply})
                
                # Save updated conversation
                save_conversation(message.channel.id, messages)
                
                # Log the thread message
                log_command_usage(message.author, "thread_message", message.content, reply, usage, 
                                 thread_id=str(message.channel.id), is_thread_message=True)
                
                # Update thread stats
                update_thread_stats(str(message.channel.id))
                
                await send_long_response(message.channel, reply)
                await send_token_usage(message.channel, usage)
            else:
                await message.channel.send("Sorry, I couldn't generate a response. Please try again.")
        
        # Process commands regardless
        await bot.process_commands(message)

    @bot.command(help="List all your active chat threads.")
    async def mythreads(ctx):
        """List all active chat threads for the user."""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT thread_id, created_at FROM thread_meta WHERE creator_id = ? ORDER BY created_at DESC",
                    (str(ctx.author.id),)
                )
                rows = c.fetchall()
        except Exception as e:
            print(f"Error fetching threads: {e}")
            await ctx.send("Error fetching your threads.")
            return
        
        if not rows:
            await ctx.send("You have no active chat threads.")
            return
        
        embed = discord.Embed(
            title="Your Active Chat Threads",
            color=discord.Color.blue()
        )
        
        for thread_id, created_at in rows[:10]:  # Limit to 10 most recent
            try:
                thread = await bot.fetch_channel(int(thread_id))
                created_dt = datetime.fromisoformat(created_at)
                age = datetime.now(timezone.utc) - created_dt
                embed.add_field(
                    name=thread.name,
                    value=f"[Go to thread](https://discord.com/channels/{ctx.guild.id}/{thread.id})\nAge: {format_time_duration(age)}",
                    inline=False
                )
            except Exception:
                pass
        
        if len(rows) > 10:
            embed.set_footer(text=f"Showing 10 of {len(rows)} threads")
        
        await ctx.send(embed=embed)

    @bot.command(help="(Admin) List all active chat threads.", hidden=True)
    async def allthreads(ctx):
        """List all active chat threads (admin only)."""
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT thread_id, creator_id, created_at FROM thread_meta ORDER BY created_at DESC")
                rows = c.fetchall()
        except Exception as e:
            print(f"Error fetching threads: {e}")
            await ctx.send("Error fetching threads.")
            return
        
        if not rows:
            await ctx.send("There are no active chat threads.")
            return
        
        msg = "**All Active Chat Threads:**\n"
        for thread_id, creator_id, created_at in rows:
            try:
                thread = await bot.fetch_channel(int(thread_id))
                user = await bot.fetch_user(int(creator_id))
                msg += f"- [{thread.name}](https://discord.com/channels/{ctx.guild.id}/{thread.id}) by {user.mention}\n  (created {created_at})\n"
            except Exception:
                msg += f"- (Thread ID {thread_id}) by <@{creator_id}>\n  (created {created_at}) [not found]\n"
        
        await send_long_response(ctx, msg, filename="all_threads.txt")

    @bot.command(help="(Admin) List all active chat threads with their age and time until expiration.", 
                 hidden=True, aliases=["threadage"])
    async def threadages(ctx):
        """List thread ages and expiration times (admin only)."""
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        retention_days = get_chat_thread_retention_days()
        now = datetime.now(timezone.utc)
        
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT thread_id, creator_id, created_at FROM thread_meta ORDER BY created_at")
                rows = c.fetchall()
        except Exception as e:
            print(f"Error fetching threads: {e}")
            await ctx.send("Error fetching threads.")
            return
        
        if not rows:
            await ctx.send("There are no active chat threads.")
            return
        
        embed = discord.Embed(
            title="Active Chat Threads (Age & Expiry)",
            description=f"Retention period: {retention_days} days",
            color=discord.Color.orange()
        )
        
        threads_info = []
        for thread_id, creator_id, created_at in rows:
            try:
                thread = await bot.fetch_channel(int(thread_id))
                user = await bot.fetch_user(int(creator_id))
                
                # Parse created_at as UTC
                created_dt = datetime.fromisoformat(created_at)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                
                age = now - created_dt
                expires_in = timedelta(days=retention_days) - age
                
                if expires_in.total_seconds() < 0:
                    status = "⚠️ **EXPIRED**"
                elif expires_in.total_seconds() < 3600:  # Less than 1 hour
                    status = "🔴 Expires soon"
                elif expires_in.days < 1:
                    status = "🟡 Expires today"
                else:
                    status = "🟢 Active"
                
                threads_info.append({
                    'thread': thread,
                    'user': user,
                    'age': age,
                    'expires_in': expires_in,
                    'status': status
                })
            except Exception:
                pass
        
        # Sort by expiration time (soonest first)
        threads_info.sort(key=lambda x: x['expires_in'])
        
        for info in threads_info[:25]:  # Discord embed field limit
            embed.add_field(
                name=f"{info['status']} {info['thread'].name}",
                value=(
                    f"By: {info['user'].mention}\n"
                    f"Age: {format_time_duration(info['age'])}\n"
                    f"Expires: {format_time_duration(info['expires_in']) if info['expires_in'].total_seconds() > 0 else 'Expired'}"
                ),
                inline=True
            )
        
        if len(threads_info) > 25:
            embed.set_footer(text=f"Showing 25 of {len(threads_info)} threads")
        
        await ctx.send(embed=embed)

async def cleanup_old_threads(bot):
    """Clean up old conversation threads based on retention policy."""
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            retention_days = get_chat_thread_retention_days()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT thread_id, created_at FROM thread_meta")
                rows = c.fetchall()
            
            threads_to_delete = []
            for thread_id, created_at in rows:
                try:
                    created_dt = datetime.fromisoformat(created_at)
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                    
                    if created_dt < cutoff_date:
                        threads_to_delete.append(thread_id)
                except Exception as e:
                    print(f"Error parsing date for thread {thread_id}: {e}")
            
            # Delete expired threads
            for thread_id in threads_to_delete:
                try:
                    thread = await bot.fetch_channel(int(thread_id))
                    await thread.delete(reason=f"Conversation thread expired (older than {retention_days} days)")
                    print(f"Deleted expired thread {thread_id}")
                except discord.NotFound:
                    print(f"Thread {thread_id} already deleted")
                except Exception as e:
                    print(f"Could not delete thread {thread_id}: {e}")
                
                # Always clean up database
                delete_thread_data(thread_id)
                # Close thread stats
                close_thread_stats(thread_id, reason="expired")
            
            if threads_to_delete:
                print(f"Cleaned up {len(threads_to_delete)} expired threads")
        
        except Exception as e:
            print(f"Error in cleanup task: {e}")
        
        # Wait before next cleanup
        await asyncio.sleep(3600)  # Run every hour

def setup_cleanup_task(bot):
    """Register a listener to start the cleanup task once the bot is ready."""
    started = {"done": False}

    async def _on_ready():
        # Ensure we only start one background task
        if started["done"]:
            return
        started["done"] = True
        # We're in an async context; the loop is running, safe to create a task
        asyncio.create_task(cleanup_old_threads(bot))

    # Add as a listener instead of using @bot.event to avoid overriding existing handlers
    bot.add_listener(_on_ready, "on_ready")

# Initialize the database when module is loaded
try:
    init_conversation_db()
except Exception as e:
    print(f"Failed to initialize conversation database: {e}")

# Initialize stats database at module load
try:
    init_stats_db()
except Exception as e:
    print(f"Failed to initialize stats database: {e}")