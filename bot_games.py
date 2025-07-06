# Copyright (c) 2025 Ryan McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

# Code Citations
#
# Some Magic 8 Ball responses adapted from:
# License: GPL_3_0
# https://github.com/Zackattak01/CheeseBot/tree/ea103a10850b379b0dbafbfdbb8739f7500993f3/CheeseBot/Commands/Modules/FunModule.cs

"""
Game logic for Discord bot.
Imported and used by [main.py](main.py).

References:
- [`flip_coin`](bot-games.py): Flip a coin, returns "Heads" or "Tails".
- [`roll_dice`](bot-games.py): Roll 1-6 dice, returns a list of results.
- [`magic_8_ball`](bot-games.py): Get a random Magic 8 Ball response.
"""

import random

DND_DICE_TYPES = [4, 6, 8, 10, 12, 20, 100]

def flip_coin():
    """
    Flip a coin and return 'Heads' or 'Tails'.

    Used in: [main.py](main.py) as [`flip_coin`](bot-games.py)
    """
    return random.choice(["Heads", "Tails"])

def roll_dice(num_dice=1, dice_type=6):
    """
    Roll a specified number and type of dice (supports D&D dice: d4, d6, d8, d10, d12, d20, d100).
    Returns a list of integers.

    Used in: [main.py](main.py) as [`roll_dice`](bot-games.py)
    """
    try:
        dice_type = int(dice_type)
    except Exception:
        dice_type = 6
    if dice_type not in DND_DICE_TYPES:
        dice_type = 6  # default to d6 if invalid
    try:
        num_dice = int(num_dice)
    except Exception:
        num_dice = 1
    num_dice = max(1, min(num_dice, 20))  # limit to 20 dice for sanity
    rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
    return rolls

MAGIC_8_BALL_RESPONSES = [
    # Affirmative (10)
    "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes – definitely.",
    "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
    "Yes.", "Signs point to yes.",
    # Negative (5)
    "Don't count on it.", "My reply is no.", "My sources say no.",
    "Outlook not so good.", "Very doubtful.",
    # Non-committal (5)
    "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
    "Cannot predict now.", "Concentrate and ask again."
]

def magic_8_ball():
    """
    Return a random Magic 8 Ball response.

    Used in: [main.py](main.py) as [`magic_8_ball`](bot-games.py)
    """
    return random.choice(MAGIC_8_BALL_RESPONSES)