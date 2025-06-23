import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import openai

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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

@bot.command(help="Give a user a personalized compliment! Usage: !compliment <username>")
async def compliment(ctx, username: str = None):
    sender = ctx.author.nick or ctx.author.name
    if username is None:
        username = sender
    prompt = f"Write a wholesome, personalized compliment for {username} from {sender}, suitable for Discord."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await ctx.send(msg)

@bot.command(help="Get a short piece of wholesome advice!")
async def advice(ctx):
    prompt = "Give me a short, wholesome piece of advice."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await ctx.send(msg)

@bot.command(name="help", help="List all commands and their descriptions.")
async def help_command(ctx):
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
    msg = await ask_chatgpt(prompt, max_tokens=200)
    await ctx.send(msg)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)