#!/usr/bin/env python3

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import openai
import requests
from datetime import datetime, timedelta

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ALL_ACCESS = os.getenv("OPENAI_ALL_ACCESS")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
openai.api_key = OPENAI_API_KEY

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

async def ask_chatgpt(prompt, max_tokens=80):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative, friendly assistant for a Discord server."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            n=1,
            temperature=0.8,
        )
        # Defensive: check for expected structure and content
        if (
            hasattr(response, "choices")
            and response.choices
            and hasattr(response.choices[0], "message")
            and hasattr(response.choices[0].message, "content")
            and response.choices[0].message.content
        ):
            return response.choices[0].message.content.strip()
        else:
            print(f"OpenAI API returned unexpected response: {response}")
            return "Sorry, I couldn't get a response from ChatGPT."
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Sorry, I couldn't get a response from ChatGPT."

async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.command(help="Get a short, 50-word feel good message!")
async def feelgood(ctx):
    user = ctx.author.nick or ctx.author.name
    prompt = f"Write a short, 50-word, positive, uplifting feel-good message addressed to {user}."
    msg = await ask_chatgpt(prompt, max_tokens=80)
    await ctx.send(msg)

@bot.command(help="Get an inspirational quote!")
async def inspo(ctx):
    user = ctx.author.nick or ctx.author.name
    prompt = f"Give me a unique, inspirational quote and address it to {user}."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await ctx.send(msg)

@bot.command(help="Wish a happy birthday to someone! Usage: !bday <username>")
async def bday(ctx, username: str):
    prompt = f"Write a festive, emoji-filled happy birthday message for {username} in a fun Discord style."
    msg = await ask_chatgpt(prompt, max_tokens=90)
    await ctx.send(msg)

@bot.command(help="Get a random, light-hearted joke! Optionally specify a topic: !joke [topic]")
async def joke(ctx, topic: str = None):
    if topic:
        prompt = f"Tell me a random, light-hearted, family-friendly joke about {topic}."
    else:
        prompt = "Tell me a random, light-hearted, family-friendly joke."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await ctx.send(msg)

@bot.command(help="Give a user a personalized compliment! Usage: !compliment [@user] [topic]")
async def compliment(ctx, user: discord.Member = None, *, topic: str = None):
    await ctx.message.delete()
    sender = ctx.author.nick or ctx.author.name
    if user:
        recipient = user.nick or user.name
        mention = user.mention
    else:
        recipient = sender
        mention = ctx.author.mention

    if topic:
        prompt = f"Write a wholesome, personalized compliment for {recipient} from {sender}, about: {topic}. Make it suitable for Discord."
    else:
        prompt = f"Write a wholesome, personalized compliment for {recipient} from {sender}, suitable for Discord."

    msg = await ask_chatgpt(prompt, max_tokens=60)
    await ctx.send(f"{mention} {msg}")

@bot.command(help="Get a short piece of wholesome advice! Optionally specify a topic: !advice [topic]")
async def advice(ctx, *, topic: str = None):
    if topic:
        prompt = f"Give me a short, wholesome piece of advice about {topic}."
    else:
        prompt = "Give me a short, wholesome piece of advice."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await ctx.send(msg)

@bot.command(name="funbot", help="List all commands and their descriptions.")
async def funbot_command(ctx):
    help_text = "**Available Commands:**\n"
    commands_sorted = sorted(
        (cmd for cmd in bot.commands if not cmd.hidden),
        key=lambda c: c.name
    )
    for command in commands_sorted:
        usage = f" {command.usage}" if command.usage else ""
        help_text += f"**!{command.name}**{usage} - {command.help}\n"
    await ctx.send(help_text)

@bot.command(help="Ask ChatGPT any question! Usage: !query <your prompt>")
async def query(ctx, *, prompt: str = None):
    if not prompt or not prompt.strip():
        await ctx.send("You need to provide a prompt to ask ChatGPT. Usage: `!query <your prompt>`")
        return
    msg = await ask_chatgpt(prompt, max_tokens=500)
    await ctx.send(msg)

@bot.command(help="Generate an image with DALL·E! Usage: !image <description>")
async def image(ctx, *, prompt: str = None):
    if not prompt or not prompt.strip():
        await ctx.send("You need to provide a prompt to generate an image. Usage: `!image <description>`")
        return
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        await ctx.send(image_url)
    except Exception as e:
        print(f"OpenAI Image Error: {e}")
        await ctx.send("Sorry, I couldn't generate an image for that prompt.")

@bot.command(help="(hidden)", hidden=True)
async def apistats(ctx):
    if ctx.author.id != ADMIN_USER_ID:
        return

    headers = {
        "Authorization": f"Bearer {OPENAI_ALL_ACCESS}",
        "OpenAI-Organization": "org-ovkptdCXPXKxJxOWehyR0NcO"
    }

    # Get usage for the current month
    now = datetime.utcnow()
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")  # Use today, not tomorrow

    try:
        # Usage
        usage_url = f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
        usage_resp = requests.get(usage_url, headers=headers)
        usage_data = usage_resp.json()
        print("USAGE DATA:", usage_data)
        if "error" in usage_data:
            await ctx.send(f"OpenAI Usage API error: {usage_data['error'].get('message', 'Unknown error')}")
            return
        total_usage = usage_data.get("total_usage", 0) / 100.0

        # Budget
        credit_url = "https://api.openai.com/v1/dashboard/billing/credit_grants"
        credit_resp = requests.get(credit_url, headers=headers)
        credit_data = credit_resp.json()
        print("CREDIT DATA:", credit_data)
        if "error" in credit_data:
            await ctx.send(f"OpenAI Credit API error: {credit_data['error'].get('message', 'Unknown error')}")
            return
        total_granted = credit_data.get("total_granted", 0)
        total_used = credit_data.get("total_used", 0)
        total_available = credit_data.get("total_available", 0)

        msg = (
            f"**OpenAI API Usage Stats (this month):**\n"
            f"Total used: ${total_usage:.2f}\n"
            f"Total granted: ${total_granted:.2f}\n"
            f"Total available: ${total_available:.2f}\n"
        )
        await ctx.send(msg)
    except Exception as e:
        print(f"API Stats Error: {e}")
        await ctx.send("Could not retrieve API stats at this time.")

@bot.command(help="(hidden)", hidden=True)
async def list_models(ctx):
    if ctx.author.id != ADMIN_USER_ID:
        return
    try:
        response = openai.Model.list(api_key=OPENAI_ALL_ACCESS, organization="org-ovkptdCXPXKxJxOWehyR0NcO")
        models = [model["id"] for model in response["data"]]
        models_text = "\n".join(models)
        # Discord messages have a 2000 character limit
        if len(models_text) > 1900:
            await ctx.send("Too many models to display. Here are the first 20:\n" + "\n".join(models[:20]))
        else:
            await ctx.send(f"**Available OpenAI Models:**\n{models_text}")
    except Exception as e:
        print(f"OpenAI List Models Error: {e}")
        await ctx.send("Could not retrieve model list at this time.")

@bot.check
async def global_funbot_role_check(ctx):
    if ctx.guild is None:
        return False  # Ignore DMs
    funbot_role = discord.utils.get(ctx.author.roles, name="funbot")
    if funbot_role is None:
        await ctx.send("You are not entitled to run this command. Access is at the owner's discretion.")
        return False
    return True

bot.run(token, log_handler=handler, log_level=logging.ERROR)
