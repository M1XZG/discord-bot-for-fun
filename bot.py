import os
import discord
from discord import app_commands
from discord.ext import commands
import openai
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

async def ask_chatgpt(prompt, max_tokens=80):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a creative, friendly assistant for a Discord server."},
                      {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            n=1,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Sorry, I couldn't get a response from ChatGPT."

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="feelgood", description="Get a short, 50-word feel good message!")
async def feelgood_command(interaction: discord.Interaction):
    prompt = "Write a short, 50-word, positive, uplifting feel-good message."
    msg = await ask_chatgpt(prompt, max_tokens=80)
    await interaction.response.send_message(msg)

@bot.tree.command(name="inspo", description="Get an inspirational quote!")
async def inspo_command(interaction: discord.Interaction):
    prompt = "Give me a unique, inspirational quote."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await interaction.response.send_message(msg)

@bot.tree.command(name="bday", description="Wish a happy birthday to someone!")
@app_commands.describe(username="Who is the birthday person?")
async def bday_command(interaction: discord.Interaction, username: str):
    prompt = f"Write a festive, emoji-filled happy birthday message for {username} in a fun Discord style."
    msg = await ask_chatgpt(prompt, max_tokens=90)
    await interaction.response.send_message(msg)

@bot.tree.command(name="joke", description="Get a random, light-hearted joke!")
async def joke_command(interaction: discord.Interaction):
    prompt = "Tell me a random, light-hearted, family-friendly joke."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await interaction.response.send_message(msg)

@bot.tree.command(name="compliment", description="Give a user a personalized compliment!")
@app_commands.describe(username="Who do you want to compliment?")
async def compliment_command(interaction: discord.Interaction, username: str):
    prompt = f"Write a wholesome, personalized compliment for {username} suitable for Discord."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await interaction.response.send_message(msg)

@bot.tree.command(name="advice", description="Get a short piece of wholesome advice!")
async def advice_command(interaction: discord.Interaction):
    prompt = "Give me a short, wholesome piece of advice."
    msg = await ask_chatgpt(prompt, max_tokens=60)
    await interaction.response.send_message(msg)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)