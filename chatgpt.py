# Copyright (c) 2025 Ryan McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

import asyncio
import json
import openai
import sqlite3
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands
import os  # Add this import

# Global variables (will be set by main.py)
prompts = {}
max_tokens = {}
config = {}
token_usage_enabled = False
CONVO_DB = "conversations.db"

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def set_globals(prompts_dict, max_tokens_dict, config_dict, token_usage_flag, convo_db_path, api_key):
    """Set global variables from main.py"""
    global prompts, max_tokens, config, token_usage_enabled, CONVO_DB
    prompts = prompts_dict
    max_tokens = max_tokens_dict
    config = config_dict
    token_usage_enabled = token_usage_flag
    CONVO_DB = convo_db_path
    openai.api_key = api_key  # Set the API key here

def get_prompt(command, variant="generic", **kwargs):
    """
    Retrieves a prompt template for a given command and variant,
    then formats it with the provided keyword arguments.
    """
    if command not in prompts:
        return ""
    cmd_prompts = prompts.get(command, {})
    template = cmd_prompts.get(variant)
    if not template:
        return ""
    return template.format(**kwargs)

async def send_long_response(ctx_or_channel, text, max_length=1900, filename="response.txt"):
    """Send a response, splitting it if it's too long for Discord."""
    # Determine if we have a context or a channel
    if hasattr(ctx_or_channel, 'send'):
        channel = ctx_or_channel
        is_context = hasattr(ctx_or_channel, 'message')
    else:
        raise ValueError("Invalid context or channel object")
    
    if len(text) <= max_length:
        await channel.send(text)
    else:
        # Send the first chunk
        await channel.send(text[:max_length] + "...")
        
        # If it's a context object and not already in a thread, create one
        if is_context and not isinstance(channel, discord.Thread):
            thread = await ctx_or_channel.message.create_thread(
                name=f"Full Response - {ctx_or_channel.author.name}",
                auto_archive_duration=1440  # 24 hours
            )
            # Send remaining text in chunks within the thread
            remaining = text[max_length:]
            while remaining:
                chunk = remaining[:max_length]
                remaining = remaining[max_length:]
                await thread.send(chunk)
        else:
            # Already in a thread or channel, just send remaining chunks
            remaining = text[max_length:]
            while remaining:
                chunk = remaining[:max_length]
                remaining = remaining[max_length:]
                await channel.send(chunk)

async def get_chatgpt_response(prompt, command="query", conversation_history=None):
    """
    Get a response from ChatGPT API.
    Returns the response text and token usage info.
    """
    max_t = max_tokens.get(command, 150)
    
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_t,
            temperature=0.8
        )
        
        reply = response.choices[0].message['content'].strip()
        usage = response.get('usage', {})
        
        return reply, usage
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None, None

def init_conversation_db():
    """Initialize the conversation database."""
    conn = sqlite3.connect(CONVO_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            thread_id TEXT PRIMARY KEY,
            messages TEXT,
            last_updated DATETIME
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS thread_meta (
            thread_id TEXT PRIMARY KEY,
            creator_id TEXT,
            created_at DATETIME
        )
    """)
    conn.commit()
    conn.close()

def save_conversation(thread_id, messages):
    """Save conversation history to database."""
    conn = sqlite3.connect(CONVO_DB)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO conversations (thread_id, messages, last_updated) VALUES (?, ?, ?)",
        (str(thread_id), json.dumps(messages), datetime.now(timezone.utc))
    )
    conn.commit()
    conn.close()

def load_conversation(thread_id):
    """Load conversation history from database."""
    conn = sqlite3.connect(CONVO_DB)
    c = conn.cursor()
    c.execute("SELECT messages FROM conversations WHERE thread_id = ?", (str(thread_id),))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return []

def delete_thread_data(thread_id):
    """Delete all data for a thread."""
    conn = sqlite3.connect(CONVO_DB)
    c = conn.cursor()
    c.execute("DELETE FROM conversations WHERE thread_id = ?", (str(thread_id),))
    c.execute("DELETE FROM thread_meta WHERE thread_id = ?", (str(thread_id),))
    conn.commit()
    conn.close()

def get_chat_thread_retention_days():
    """Get the chat thread retention period in days from config."""
    return config.get("chat_thread_retention_days", 7)

def setup_chatgpt(bot):
    """Setup all ChatGPT-related commands."""
    
    @bot.command(help="Get a 50-word, uplifting message for yourself or someone else! Usage: !feelgood [recipient]")
    async def feelgood(ctx, *, recipient: str = None):
        """Generate a feel-good message."""
        if recipient and recipient.strip():
            prompt = get_prompt("feelgood", "targeted", sender=ctx.author.display_name, recipient=recipient.strip())
        else:
            prompt = get_prompt("feelgood", "generic", sender=ctx.author.display_name, recipient=ctx.author.display_name)
        
        reply, usage = await get_chatgpt_response(prompt, command="feelgood")
        
        if reply:
            await ctx.send(reply)
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await ctx.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
        else:
            await ctx.send("Sorry, I couldn't generate a feel-good message right now. Please try again later!")

    @bot.command(help="Hear a random, family-friendly joke, or specify a topic for a themed joke! Usage: !joke [topic]")
    async def joke(ctx, *, topic: str = None):
        """Tell a joke."""
        if topic and topic.strip():
            prompt = get_prompt("joke", "targeted", topic=topic.strip())
        else:
            prompt = get_prompt("joke", "generic")
        
        reply, usage = await get_chatgpt_response(prompt, command="joke")
        
        if reply:
            await ctx.send(reply)
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await ctx.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
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
        
        reply, usage = await get_chatgpt_response(prompt, command="compliment")
        
        if reply:
            await ctx.send(reply)
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await ctx.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
        else:
            await ctx.send("Sorry, I couldn't generate a compliment right now. Please try again later!")

    @bot.command(help="Receive wholesome advice, optionally on a topic. Usage: !advice [topic]")
    async def advice(ctx, *, topic: str = None):
        """Give advice."""
        if topic and topic.strip():
            prompt = get_prompt("advice", "targeted", topic=topic.strip())
        else:
            prompt = get_prompt("advice", "generic")
        
        reply, usage = await get_chatgpt_response(prompt, command="advice")
        
        if reply:
            await ctx.send(reply)
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await ctx.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
        else:
            await ctx.send("Sorry, I couldn't generate advice right now. Please try again later!")

    @bot.command(help="Receive a unique, inspirational quote, optionally addressed to someone. Usage: !inspo [recipient]")
    async def inspo(ctx, *, recipient: str = None):
        """Generate an inspirational quote."""
        if recipient and recipient.strip():
            prompt = get_prompt("inspo", "targeted", sender=ctx.author.display_name, recipient=recipient.strip())
        else:
            prompt = get_prompt("inspo", "generic", sender=ctx.author.display_name, recipient=ctx.author.display_name)
        
        reply, usage = await get_chatgpt_response(prompt, command="inspo")
        
        if reply:
            await ctx.send(reply)
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await ctx.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
        else:
            await ctx.send("Sorry, I couldn't generate an inspirational quote right now. Please try again later!")

    @bot.command(help="Quick free-form question to ChatGPT (short reply, stays in channel). Usage: !q <your question>",
                 aliases=["quick", "qask"])
    async def q(ctx, *, question: str = None):
        """Quick question to ChatGPT."""
        if not question or not question.strip():
            await ctx.send("Please provide a question. Usage: `!q <your question>`")
            return
        
        reply, usage = await get_chatgpt_response(question.strip(), command="query")
        
        if reply:
            await send_long_response(ctx, reply)
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await ctx.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
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
            response = openai.Image.create(
                prompt=description.strip(),
                n=1,
                size="1024x1024"
            )
            
            if "data" in response and response["data"]:
                image_url = response["data"][0]["url"]
                await ctx.send(image_url)
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
        thread_name = f"Chat with {ctx.author.display_name}"
        thread = await ctx.message.create_thread(
            name=thread_name,
            auto_archive_duration=10080  # 7 days
        )
        
        # Save thread metadata
        conn = sqlite3.connect(CONVO_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO thread_meta (thread_id, creator_id, created_at) VALUES (?, ?, ?)",
            (str(thread.id), str(ctx.author.id), datetime.now(timezone.utc))
        )
        conn.commit()
        conn.close()
        
        # Get initial response
        reply, usage = await get_chatgpt_response(message.strip(), command="query")
        
        if reply:
            # Save conversation
            messages = [
                {"role": "user", "content": message.strip()},
                {"role": "assistant", "content": reply}
            ]
            save_conversation(thread.id, messages)
            
            retention_days = get_chat_thread_retention_days()
            
            # Format retention period for display
            if retention_days >= 1:
                retention_display = f"{int(retention_days)} day{'s' if int(retention_days) != 1 else ''}"
            else:
                hours = int(retention_days * 24)
                retention_display = f"{hours} hour{'s' if hours != 1 else ''}"
            
            # Send welcome message separately
            welcome_msg = (
                f"💬 **Chat thread started!** I'll remember our conversation in this thread for {retention_display}.\n"
                f"You can end this chat early with `!endchat`."
            )
            await thread.send(welcome_msg)
            
            # Send the actual response using send_long_response to handle long messages
            await send_long_response(thread, reply)
            
            if token_usage_enabled:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                await thread.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
        else:
            await thread.send("Sorry, I couldn't start the chat. Please try again later!")
            await thread.delete()

    @bot.command(help="End your chat thread early and delete it (only works inside a chat thread).")
    async def endchat(ctx):
        """End a chat thread."""
        # Check if in a thread
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send("This command only works inside a chat thread.")
            return
        
        # Check if user is thread creator or admin
        conn = sqlite3.connect(CONVO_DB)
        c = conn.cursor()
        c.execute("SELECT creator_id FROM thread_meta WHERE thread_id = ?", (str(ctx.channel.id),))
        row = c.fetchone()
        conn.close()
        
        if not row:
            await ctx.send("This doesn't appear to be a chat thread.")
            return
        
        creator_id = row[0]
        is_admin = ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild
        
        if str(ctx.author.id) != creator_id and not is_admin:
            await ctx.send("Only the thread creator or an admin can end this chat.")
            return
        
        # Delete DB data and the thread
        delete_thread_data(ctx.channel.id)
        try:
            await ctx.send("Ending chat and deleting this thread and its memory in 30 seconds...")
            await asyncio.sleep(30)
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
            conn = sqlite3.connect(CONVO_DB)
            c = conn.cursor()
            c.execute("SELECT creator_id FROM thread_meta WHERE thread_id = ?", (str(message.channel.id),))
            row = c.fetchone()
            conn.close()
            
            if row and not message.content.startswith(bot.command_prefix):
                # Load conversation history
                messages = load_conversation(message.channel.id)
                
                # Add new message
                messages.append({"role": "user", "content": message.content})
                
                # Get response
                reply, usage = await get_chatgpt_response(message.content, command="query", conversation_history=messages)
                
                if reply:
                    # Add assistant response
                    messages.append({"role": "assistant", "content": reply})
                    
                    # Save updated conversation
                    save_conversation(message.channel.id, messages)
                    
                    await message.channel.send(reply)
                    
                    if token_usage_enabled:
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        await message.channel.send(f"_Token usage - Prompt: {prompt_tokens}, Reply: {completion_tokens}_")
        
        # IMPORTANT: Always process commands, regardless of whether we're in a thread or not
        await bot.process_commands(message)

    @bot.command(help="List all your active chat threads.")
    async def mythreads(ctx):
        """List all active chat threads you have started."""
        conn = sqlite3.connect(CONVO_DB)
        c = conn.cursor()
        c.execute("SELECT thread_id, created_at FROM thread_meta WHERE creator_id = ?", (str(ctx.author.id),))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            await ctx.send("You have no active chat threads.")
            return
        
        msg = "**Your Active Chat Threads:**\n"
        for thread_id, created_at in rows:
            try:
                thread = await bot.fetch_channel(int(thread_id))
                msg += f"- [{thread.name}](https://discord.com/channels/{ctx.guild.id}/{thread.id})\n  (created {created_at})\n"
            except Exception:
                msg += f"- (Thread ID {thread_id})\n  (created {created_at}) [not found]\n"
        
        await ctx.send(msg)

    @bot.command(help="(Admin) List all active chat threads.", hidden=True)
    async def allthreads(ctx):
        """List all active chat threads (admin only)."""
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        conn = sqlite3.connect(CONVO_DB)
        c = conn.cursor()
        c.execute("SELECT thread_id, creator_id, created_at FROM thread_meta")
        rows = c.fetchall()
        conn.close()
        
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
        
        await send_long_response(ctx, msg)

    @bot.command(help="(Admin) List all active chat threads with their age and time until expiration.", hidden=True)
    async def threadages(ctx):
        """List thread ages and expiration times (admin only)."""
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            await ctx.send("You must be a server admin to use this command.")
            return
        
        retention_days = get_chat_thread_retention_days()
        now = datetime.now(timezone.utc)
        
        conn = sqlite3.connect(CONVO_DB)
        c = conn.cursor()
        c.execute("SELECT thread_id, creator_id, created_at FROM thread_meta")
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            await ctx.send("There are no active chat threads.")
            return
        
        msg = "**All Active Chat Threads (with age and expiry):**\n"
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
                
                # Format age and expires_in
                def fmt(td):
                    days = td.days
                    hours = td.seconds // 3600
                    mins = (td.seconds % 3600) // 60
                    if days > 0:
                        return f"{days}d {hours}h"
                    elif hours > 0:
                        return f"{hours}h {mins}m"
                    else:
                        return f"{mins}m"
                
                msg += (
                    f"- [{thread.name}](https://discord.com/channels/{ctx.guild.id}/{thread.id}) "
                    f"by {user.mention}\n"
                    f"  Age: {fmt(age)}, Expires in: {fmt(expires_in)} (created {created_at})\n"
                )
            except Exception:
                msg += f"- (Thread ID {thread_id}) by <@{creator_id}> (created {created_at}) [not found]\n"
        
        await send_long_response(ctx, msg, filename="threadages.txt")

async def cleanup_old_threads(bot):
    """Clean up old conversation threads based on retention policy."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        retention_days = get_chat_thread_retention_days()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        conn = sqlite3.connect(CONVO_DB)
        c = conn.cursor()
        c.execute("SELECT thread_id, created_at FROM thread_meta")
        rows = c.fetchall()
        conn.close()
        
        old_threads = []
        for thread_id, created_at in rows:
            try:
                # Parse the created_at datetime properly
                created_dt = datetime.fromisoformat(created_at)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                
                # Only add to old_threads if it's actually expired
                if created_dt < cutoff_date:
                    old_threads.append(thread_id)
            except Exception as e:
                print(f"Error parsing date for thread {thread_id}: {e}")
        
        for thread_id in old_threads:
            try:
                thread = await bot.fetch_channel(int(thread_id))
                await thread.delete(reason=f"Conversation thread expired (older than {retention_days} days)")
            except Exception as e:
                print(f"Could not delete thread {thread_id}: {e}")
            delete_thread_data(thread_id)
        
        await asyncio.sleep(3600)  # Run every hour

def setup_cleanup_task(bot):
    """Setup the cleanup task for old threads."""
    bot.loop.create_task(cleanup_old_threads(bot))

# Initialize the database when module is loaded
init_conversation_db()