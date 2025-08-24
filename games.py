#!/usr/bin/env python3

# Copyright (c) 2025 Robert McKenzie (@M1XZG)
# Repository: discord-bot-for-fun
# https://github.com/M1XZG/discord-bot-for-fun
# 
# This software is released under the MIT License.
# See LICENSE.md for details.

"""
Games module: core game logic and command registration.

Usage from main:
    from games import setup_games
    setup_games(bot, is_feature_enabled)
"""

import random
import re
import sqlite3
from datetime import datetime, timezone
import discord

# --- Core Game Logic ---

DND_DICE_TYPES = [4, 6, 8, 10, 12, 20, 100]

def flip_coin():
    """Flip a coin and return 'Heads' or 'Tails'."""
    return random.choice(["Heads", "Tails"])

def roll_dice(num_dice=1, dice_type=6):
    """Roll a specified number and type of dice. Returns a list of ints."""
    try:
        dice_type = int(dice_type)
    except Exception:
        dice_type = 6
    if dice_type not in DND_DICE_TYPES:
        dice_type = 6
    try:
        num_dice = int(num_dice)
    except Exception:
        num_dice = 1
    num_dice = max(1, min(num_dice, 20))  # cap to 20 dice
    return [random.randint(1, dice_type) for _ in range(num_dice)]

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
    """Return a random Magic 8 Ball response."""
    return random.choice(MAGIC_8_BALL_RESPONSES)


# --- Games Stats (SQLite) ---

GAMES_DB = "games_stats.db"

def _games_db_connect():
    conn = sqlite3.connect(GAMES_DB)
    return conn

def init_games_db():
    try:
        conn = _games_db_connect()
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS rps_stats (
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                draws INTEGER NOT NULL DEFAULT 0,
                last_played DATETIME NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_rps_stats_guild ON rps_stats(guild_id)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing games DB: {e}")

def _record_rps_result(guild_id: int | str | None, user: discord.abc.User | discord.Member, result: str):
    """Record an RPS result for a user within a guild. result in {'win','loss','draw'}."""
    try:
        gid = str(guild_id) if guild_id is not None else "dm"
        uid = str(user.id)
        wins = 1 if result == "win" else 0
        losses = 1 if result == "loss" else 0
        draws = 1 if result == "draw" else 0
        now_iso = datetime.now(timezone.utc).isoformat()

        conn = _games_db_connect()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO rps_stats (guild_id, user_id, wins, losses, draws, last_played)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                draws = draws + excluded.draws,
                last_played = excluded.last_played
            """,
            (gid, uid, wins, losses, draws, now_iso),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording RPS result: {e}")

def _get_rps_stats(guild_id: int | str | None, user_id: int | str):
    try:
        gid = str(guild_id) if guild_id is not None else "dm"
        uid = str(user_id)
        conn = _games_db_connect()
        c = conn.cursor()
        c.execute(
            "SELECT wins, losses, draws, last_played FROM rps_stats WHERE guild_id = ? AND user_id = ?",
            (gid, uid),
        )
        row = c.fetchone()
        conn.close()
        if row:
            wins, losses, draws, last_played = row
            total = wins + losses + draws
            return {
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "total": total,
                "last_played": last_played,
            }
        return {"wins": 0, "losses": 0, "draws": 0, "total": 0, "last_played": None}
    except Exception as e:
        print(f"Error loading RPS stats: {e}")
        return {"wins": 0, "losses": 0, "draws": 0, "total": 0, "last_played": None}

# Initialize DB at module import
try:
    init_games_db()
except Exception as _e:
    print(f"Failed to initialize games database: {_e}")


# --- Command Registration ---

def setup_games(bot, is_feature_enabled):
    """Register game commands on the provided bot.

    The commands honor the server feature toggle via is_feature_enabled("games").
    """

    @bot.command(help="Flip a coin and see if it's Heads or Tails.")
    async def flip(ctx):
        if not is_feature_enabled("games"):
            await ctx.send("Games are not enabled on this server.")
            return
        result = flip_coin()
        await ctx.send(f"🪙 {result}!")

    @bot.command(help="Roll dice. Usage: !roll [NdX] or !roll [count] [sides]. Example: !roll 2d20 or !roll 3 6")
    async def roll(ctx, *, args: str | None = None):
        if not is_feature_enabled("games"):
            await ctx.send("Games are not enabled on this server.")
            return
        count = 1
        sides = 6
        if args:
            s = args.strip().lower()
            m = re.match(r"^(\d*)d(\d+)$", s)
            if m:
                count = int(m.group(1)) if m.group(1) else 1
                sides = int(m.group(2))
            else:
                parts = s.split()
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    count = int(parts[0])
                    sides = int(parts[1])
        rolls = roll_dice(count, sides)
        total = sum(rolls)
        dice_label = f"{len(rolls)}d{sides}"
        rolls_preview = ", ".join(map(str, rolls[:20]))
        msg = f"🎲 Rolled {dice_label}: [{rolls_preview}]  → Total: {total}"
        await ctx.send(msg)

    @bot.command(name="8ball", aliases=["eightball"], help="Ask the Magic 8 Ball a question. Usage: !8ball <question>")
    async def eightball_cmd(ctx, *, question: str | None = None):
        if not is_feature_enabled("games"):
            await ctx.send("Games are not enabled on this server.")
            return
        if not question or not question.strip():
            await ctx.send("Ask me a yes/no question. Usage: `!8ball <question>`")
            return
        answer = magic_8_ball()
        await ctx.send(f"🎱 {answer}")

    @bot.command(help="Play Rock, Paper, Scissors. Click a button or use: !rps <rock|paper|scissors>")
    async def rps(ctx, choice: str | None = None):
        if not is_feature_enabled("games"):
            await ctx.send("Games are not enabled on this server.")
            return
        options = ["rock", "paper", "scissors"]

        # PvP Mode: if the message mentions a user, challenge them to RPS
        if ctx.message.mentions:
            challenged = ctx.message.mentions[0]
            if not ctx.guild:
                await ctx.send("Challenges are only available in servers.")
                return
            if challenged.id == ctx.author.id:
                await ctx.send("You can't challenge yourself. Use !rps to play me or challenge someone else.")
                return
            if challenged.bot:
                await ctx.send("You can't challenge a bot. Use !rps to play me instead.")
                return

            class RPSPvPView(discord.ui.View):
                def __init__(self, p1: discord.Member, p2: discord.Member, timeout: float = 60.0):
                    super().__init__(timeout=timeout)
                    self.p1 = p1
                    self.p2 = p2
                    self.choices: dict[int, str] = {}
                    self.message: discord.Message | None = None
                    self.completed = False

                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    if interaction.user.id not in (self.p1.id, self.p2.id):
                        await interaction.response.send_message(
                            "This match isn't for you. Start your own with !rps @user",
                            ephemeral=True,
                        )
                        return False
                    # Prevent double-picking
                    if interaction.user.id in self.choices:
                        await interaction.response.send_message("You've already locked in your move.", ephemeral=True)
                        return False
                    return True

                async def on_timeout(self) -> None:
                    if self.completed:
                        return
                    # Disable buttons
                    for child in self.children:
                        if isinstance(child, discord.ui.Button):
                            child.disabled = True
                    try:
                        if self.message:
                            p1_chosen = self.p1.id in self.choices
                            p2_chosen = self.p2.id in self.choices
                            if p1_chosen and not p2_chosen:
                                # p2 forfeits
                                _record_rps_result(getattr(self.message.guild, 'id', None), self.p1, "win")
                                _record_rps_result(getattr(self.message.guild, 'id', None), self.p2, "loss")
                                content = f"⏳ Time's up! {self.p2.mention} forfeits. {self.p1.mention} wins by default!"
                            elif p2_chosen and not p1_chosen:
                                _record_rps_result(getattr(self.message.guild, 'id', None), self.p1, "loss")
                                _record_rps_result(getattr(self.message.guild, 'id', None), self.p2, "win")
                                content = f"⏳ Time's up! {self.p1.mention} forfeits. {self.p2.mention} wins by default!"
                            else:
                                content = "⏳ Time's up! No moves were made. Match canceled."
                            await self.message.edit(content=content, view=self)
                    except Exception:
                        pass
                    self.stop()

                async def _resolve(self):
                    # Both moves present, determine result and update
                    if self.completed or len(self.choices) < 2:
                        return
                    self.completed = True
                    p1_choice = self.choices[self.p1.id]
                    p2_choice = self.choices[self.p2.id]
                    outcome_text = {
                        ("rock", "scissors"): f"{self.p1.mention} wins!",
                        ("paper", "rock"): f"{self.p1.mention} wins!",
                        ("scissors", "paper"): f"{self.p1.mention} wins!",
                        ("scissors", "rock"): f"{self.p2.mention} wins!",
                        ("rock", "paper"): f"{self.p2.mention} wins!",
                        ("paper", "scissors"): f"{self.p2.mention} wins!",
                    }.get((p1_choice, p2_choice), ("It's a draw!" if p1_choice == p2_choice else f"{self.p2.mention} wins!"))

                    # Record stats
                    if "draw" in outcome_text.lower():
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.p1, "draw")
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.p2, "draw")
                    elif self.p1.mention in outcome_text:
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.p1, "win")
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.p2, "loss")
                    else:
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.p1, "loss")
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.p2, "win")

                    # Disable buttons and update message
                    for child in self.children:
                        if isinstance(child, discord.ui.Button):
                            child.disabled = True
                    content = f"🪨📄✂️ {self.p1.mention}: {p1_choice} | {self.p2.mention}: {p2_choice} → {outcome_text}"
                    try:
                        if self.message:
                            await self.message.edit(content=content, view=self)
                    except Exception:
                        pass
                    self.stop()

                async def _choose(self, interaction: discord.Interaction, move: str):
                    self.choices[interaction.user.id] = move
                    # Acknowledge without revealing choice
                    waiting_for = self.p2 if interaction.user.id == self.p1.id else self.p1
                    try:
                        await interaction.response.edit_message(
                            content=f"{interaction.user.mention} has locked in! Waiting for {waiting_for.mention}…",
                            view=self,
                        )
                    except Exception:
                        pass
                    if len(self.choices) == 2:
                        await self._resolve()

                @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary, emoji="🪨")
                async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._choose(interaction, "rock")

                @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary, emoji="📄")
                async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._choose(interaction, "paper")

                @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary, emoji="✂️")
                async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._choose(interaction, "scissors")

            view = RPSPvPView(ctx.author, challenged, timeout=60.0)
            msg = await ctx.send(f"{ctx.author.mention} has challenged {challenged.mention} to Rock, Paper, Scissors!\nBoth players: pick your move within 60 seconds.", view=view)
            view.message = msg
            return

        if choice and choice.lower() in options:
            user = choice.lower()
            bot_choice = random.choice(options)
            outcome = {
                ("rock", "scissors"): "You win!",
                ("paper", "rock"): "You win!",
                ("scissors", "paper"): "You win!",
            }.get((user, bot_choice), ("It's a draw!" if user == bot_choice else "I win!"))
            # Record stats per guild
            if outcome == "You win!":
                _record_rps_result(getattr(ctx.guild, 'id', None), ctx.author, "win")
            elif outcome == "I win!":
                _record_rps_result(getattr(ctx.guild, 'id', None), ctx.author, "loss")
            else:
                _record_rps_result(getattr(ctx.guild, 'id', None), ctx.author, "draw")
            await ctx.send(f"🪨📄✂️ You: {user} | Me: {bot_choice} → {outcome}")
            return

        class RPSView(discord.ui.View):
            def __init__(self, author: discord.Member, timeout: float = 15.0):
                super().__init__(timeout=timeout)
                self.author = author
                self.message: discord.Message | None = None
                self.completed: bool = False  # set True once a move is made

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message(
                        "This RPS game isn't for you. Run !rps to start your own!",
                        ephemeral=True,
                    )
                    return False
                return True

            async def on_timeout(self) -> None:
                # If the game already completed, don't overwrite the result
                if self.completed:
                    return
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                try:
                    if self.message:
                        taunts = [
                            "fell asleep at the buttons… I win by default! 🏆",
                            "couldn't decide in time. Default loss!",
                            "timed out — I'll take that W! 😎",
                            "missed your move. GG, I win by default!",
                            "blinked and the timer ran out. Victory is mine!"
                        ]
                        display = getattr(self.author, "display_name", "You")
                        await self.message.edit(
                            content=f"⏳ Time's up, {display}! You {random.choice(taunts)}",
                            view=self,
                        )
                        # Record default loss on timeout
                        _record_rps_result(getattr(self.message.guild, 'id', None), self.author, "loss")
                except Exception:
                    pass
                # Stop the view after timing out
                self.stop()

            async def _play(self, interaction: discord.Interaction, user_choice: str):
                bot_choice = random.choice(options)
                outcome = {
                    ("rock", "scissors"): "You win!",
                    ("paper", "rock"): "You win!",
                    ("scissors", "paper"): "You win!",
                }.get((user_choice, bot_choice), ("It's a draw!" if user_choice == bot_choice else "I win!"))
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                content = f"🪨📄✂️ You: {user_choice} | Me: {bot_choice} → {outcome}"
                self.completed = True
                # Update the message with the final result and stop the view so it won't timeout
                await interaction.response.edit_message(content=content, view=self)
                # Record stats based on outcome
                if outcome == "You win!":
                    _record_rps_result(getattr(interaction.guild, 'id', None), interaction.user, "win")
                elif outcome == "I win!":
                    _record_rps_result(getattr(interaction.guild, 'id', None), interaction.user, "loss")
                else:
                    _record_rps_result(getattr(interaction.guild, 'id', None), interaction.user, "draw")
                self.stop()

            @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary, emoji="🪨")
            async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self._play(interaction, "rock")

            @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary, emoji="📄")
            async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self._play(interaction, "paper")

            @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary, emoji="✂️")
            async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self._play(interaction, "scissors")

        view = RPSView(ctx.author)
        msg = await ctx.send("Choose your move:", view=view)
        view.message = msg

    @bot.command(help="Choose randomly from options. Usage: !choose option1 | option2 | option3")
    async def choose(ctx, *, options: str | None = None):
        if not is_feature_enabled("games"):
            await ctx.send("Games are not enabled on this server.")
            return
        if not options:
            await ctx.send("Provide options separated by `|`. Example: !choose tea | coffee | juice")
            return
        parts = [p.strip() for p in re.split(r"\||,", options) if p.strip()]
        if len(parts) < 2:
            await ctx.send("Need at least two options. Example: !choose red | blue")
            return
        pick = random.choice(parts)
        await ctx.send(f"🎯 I choose: {pick}")

    @bot.command(help="View your Rock-Paper-Scissors stats for this server.")
    async def rpsstats(ctx, member: discord.Member | None = None):
        if not is_feature_enabled("games"):
            await ctx.send("Games are not enabled on this server.")
            return
        target = member or ctx.author
        stats = _get_rps_stats(getattr(ctx.guild, 'id', None), target.id)
        wins = stats["wins"]
        losses = stats["losses"]
        draws = stats["draws"]
        total = max(stats["total"], 1)
        winrate = (wins / total) * 100.0
        last = stats["last_played"]
        name = getattr(target, 'display_name', str(target))
        embed = discord.Embed(
            title=f"RPS Stats — {name}",
            description=f"Server: {ctx.guild.name if ctx.guild else 'DM'}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Wins", value=str(wins))
        embed.add_field(name="Losses", value=str(losses))
        embed.add_field(name="Draws", value=str(draws))
        embed.add_field(name="Win rate", value=f"{winrate:.1f}%")
        if last:
            embed.set_footer(text=f"Last played: {last}")
        await ctx.send(embed=embed)
