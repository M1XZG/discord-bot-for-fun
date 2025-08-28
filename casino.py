#!/usr/bin/env python3

# Casino module: chips ledger and casino games (v1)

import sqlite3
from datetime import datetime, timezone, timedelta
import secrets
import discord

CASINO_DB = "games_stats.db"  # reuse existing DB file


def _db_connect():
    return sqlite3.connect(CASINO_DB)


def init_casino_db():
    try:
        conn = _db_connect()
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS casino_chips (
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0,
                last_updated DATETIME NOT NULL,
                last_faucet DATETIME,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS casino_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                game TEXT NOT NULL,
                delta INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                ts DATETIME NOT NULL,
                meta TEXT
            )
            """
        )
        # Optional slots audit
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS slots_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                bet INTEGER NOT NULL,
                payout INTEGER NOT NULL,
                symbols TEXT NOT NULL,
                ts DATETIME NOT NULL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS roulette_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                bet INTEGER NOT NULL,
                payout INTEGER NOT NULL,
                selection TEXT NOT NULL,
                result_number INTEGER NOT NULL,
                result_color TEXT NOT NULL,
                ts DATETIME NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing casino DB: {e}")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _get_balance(guild_id: int | str | None, user_id: int | str) -> int:
    gid = str(guild_id) if guild_id is not None else "dm"
    uid = str(user_id)
    try:
        conn = _db_connect()
        c = conn.cursor()
        c.execute(
            "SELECT balance FROM casino_chips WHERE guild_id = ? AND user_id = ?",
            (gid, uid),
        )
        row = c.fetchone()
        conn.close()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def _set_balance(guild_id: int | str | None, user_id: int | str, new_balance: int):
    gid = str(guild_id) if guild_id is not None else "dm"
    uid = str(user_id)
    ts = _now_iso()
    conn = _db_connect()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO casino_chips (guild_id, user_id, balance, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            balance = excluded.balance,
            last_updated = excluded.last_updated
        """,
        (gid, uid, int(new_balance), ts),
    )
    conn.commit()
    conn.close()


def _adjust_balance(guild_id: int | str | None, user_id: int | str, delta: int, game: str, meta: str | None = None) -> int:
    gid = str(guild_id) if guild_id is not None else "dm"
    uid = str(user_id)
    ts = _now_iso()
    conn = _db_connect()
    c = conn.cursor()
    try:
        c.execute("BEGIN IMMEDIATE")
        c.execute(
            "SELECT balance FROM casino_chips WHERE guild_id = ? AND user_id = ?",
            (gid, uid),
        )
        row = c.fetchone()
        cur = int(row[0]) if row else 0
        new_balance = cur + int(delta)
        if new_balance < 0:
            conn.rollback()
            return cur
        if row:
            c.execute(
                "UPDATE casino_chips SET balance = ?, last_updated = ? WHERE guild_id = ? AND user_id = ?",
                (new_balance, ts, gid, uid),
            )
        else:
            c.execute(
                "INSERT INTO casino_chips (guild_id, user_id, balance, last_updated) VALUES (?, ?, ?, ?)",
                (gid, uid, new_balance, ts),
            )
        c.execute(
            "INSERT INTO casino_ledger (guild_id, user_id, game, delta, balance_after, ts, meta) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (gid, uid, game, int(delta), new_balance, ts, meta),
        )
        conn.commit()
        return new_balance
    except Exception:
        conn.rollback()
        return _get_balance(gid, uid)
    finally:
        conn.close()


def _get_last_faucet(guild_id: int | str | None, user_id: int | str):
    gid = str(guild_id) if guild_id is not None else "dm"
    uid = str(user_id)
    try:
        conn = _db_connect()
        c = conn.cursor()
        c.execute(
            "SELECT last_faucet FROM casino_chips WHERE guild_id = ? AND user_id = ?",
            (gid, uid),
        )
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _set_last_faucet(guild_id: int | str | None, user_id: int | str):
    gid = str(guild_id) if guild_id is not None else "dm"
    uid = str(user_id)
    ts = _now_iso()
    conn = _db_connect()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO casino_chips (guild_id, user_id, balance, last_updated, last_faucet)
        VALUES (?, ?, COALESCE((SELECT balance FROM casino_chips WHERE guild_id = ? AND user_id = ?), 0), ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            last_faucet = excluded.last_faucet,
            last_updated = excluded.last_updated
        """,
        (gid, uid, gid, uid, ts, ts),
    )
    conn.commit()
    conn.close()


def setup_casino(bot, is_feature_enabled):
    # Ensure DB exists
    try:
        init_casino_db()
    except Exception as _e:
        print(f"Casino DB init failed: {_e}")

    def _not_enabled(ctx):
        return not is_feature_enabled("casino")

    # --- Chips commands ---
    @bot.command(help="Show your chip balance or another member's.")
    async def chips(ctx, member: discord.Member | None = None):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        target = member or ctx.author
        bal = _get_balance(getattr(ctx.guild, 'id', None), target.id)
        name = getattr(target, 'display_name', str(target))
        await ctx.send(f"{name} balance: {bal} chips")

    @bot.command(help="Claim a small daily faucet to get started.")
    async def faucet(ctx, amount: int | None = None):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        # fixed faucet amount (optional override ignored for now for safety)
        faucet_amt = 500
        gid = getattr(ctx.guild, 'id', None)
        uid = ctx.author.id
        last = _get_last_faucet(gid, uid)
        allowed = True
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                now_utc = datetime.now(timezone.utc)
                # Compare UTC date (YYYY-MM-DD)
                allowed = (now_utc.date() != last_dt.date())
            except Exception:
                allowed = True
        if not allowed:
            await ctx.send("You have already claimed your daily faucet for today (UTC). Try again after 00:00 UTC.")
            return
        new_bal = _adjust_balance(gid, uid, faucet_amt, game="faucet", meta="daily faucet")
        _set_last_faucet(gid, uid)
        await ctx.send(f"Daily faucet claimed: +{faucet_amt} chips. New balance: {new_bal}")

    def _is_admin_like(ctx) -> bool:
        perms = getattr(ctx.author, "guild_permissions", None)
        return bool(perms and (perms.administrator or perms.manage_guild))

    @bot.command(help="Admin: give chips to a user. Usage: givechips @user amount")
    async def givechips(ctx, member: discord.Member, amount: int):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        if not _is_admin_like(ctx):
            await ctx.send("You do not have permission to use this command.")
            return
        if amount == 0:
            await ctx.send("Amount must be non-zero.")
            return
        gid = getattr(ctx.guild, 'id', None)
        new_bal = _adjust_balance(gid, member.id, int(amount), game="admin", meta=f"from:{ctx.author.id}")
        await ctx.send(f"Gave {amount} chips to {member.mention}. New balance: {new_bal}")

    # --- Slots game ---
    SYMBOLS = ["🍒", "🍋", "🍇", "🔔", "⭐", "7️⃣"]
    TRIPLE_PAYOUT = {"🍒": 5, "🍋": 6, "🍇": 8, "🔔": 12, "⭐": 20, "7️⃣": 30}
    PAIR_PAYOUT = 1  # returns bet for any pair

    def _spin_reels():
        return [secrets.choice(SYMBOLS), secrets.choice(SYMBOLS), secrets.choice(SYMBOLS)]

    def _payout_for(symbols: list[str], bet: int) -> int:
        a, b, c = symbols
        if a == b == c:
            mult = TRIPLE_PAYOUT.get(a, 0)
            return bet * mult
        if a == b or b == c or a == c:
            return bet * PAIR_PAYOUT
        return 0

    @bot.command(name="slotshelp", help="Show slots paytable and multipliers.", aliases=["slotspay", "slotstable"])
    async def slotshelp(ctx):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        # Build a paytable embed
        order = ["7️⃣", "⭐", "🔔", "🍇", "🍋", "🍒"]
        lines = []
        for sym in order:
            mult = TRIPLE_PAYOUT.get(sym, 0)
            lines.append(f"{sym} {sym} {sym} — x{mult}")
        triples_text = "\n".join(lines)

        embed = discord.Embed(
            title="Slots Paytable",
            description=(
                "Three reels. Match any pair to get your bet back.\n"
                "Three of a kind pays per the table below."
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(name="Symbols", value=" ".join(order), inline=False)
        embed.add_field(name="Three of a kind", value=triples_text, inline=False)
        embed.add_field(name="Pairs", value=f"Any two matching symbols — x{PAIR_PAYOUT}", inline=False)
        embed.set_footer(text="Play with: !slots <bet>")
        await ctx.send(embed=embed)

    # --- Welcome grant (first play only) ---
    FIRST_PLAY_GAMES = {"slots", "roulette", "hilo"}

    def _grant_first_play_if_needed(guild_id: int | str | None, user_id: int | str, amount: int = 2000) -> int:
        """Grant chips once on a player's first casino game (slots/hilo/roulette).
        Returns the amount granted (0 if not granted). Uses a transaction to avoid races.
        """
        gid = str(guild_id) if guild_id is not None else "dm"
        uid = str(user_id)
        ts = _now_iso()
        conn = _db_connect()
        c = conn.cursor()
        try:
            c.execute("BEGIN IMMEDIATE")
            # If they've ever played a casino game or already got welcome, do nothing
            placeholders = ",".join(["?"] * len(FIRST_PLAY_GAMES))
            params = [gid, uid, *list(FIRST_PLAY_GAMES)]
            c.execute(
                f"SELECT 1 FROM casino_ledger WHERE guild_id = ? AND user_id = ? AND (game IN ({placeholders}) OR game = 'welcome') LIMIT 1",
                params,
            )
            if c.fetchone():
                conn.rollback()
                return 0
            # Otherwise, credit the welcome amount and ledger it
            c.execute(
                "SELECT balance FROM casino_chips WHERE guild_id = ? AND user_id = ?",
                (gid, uid),
            )
            row = c.fetchone()
            cur = int(row[0]) if row else 0
            new_balance = cur + int(amount)
            if row:
                c.execute(
                    "UPDATE casino_chips SET balance = ?, last_updated = ? WHERE guild_id = ? AND user_id = ?",
                    (new_balance, ts, gid, uid),
                )
            else:
                c.execute(
                    "INSERT INTO casino_chips (guild_id, user_id, balance, last_updated) VALUES (?, ?, ?, ?)",
                    (gid, uid, new_balance, ts),
                )
            c.execute(
                "INSERT INTO casino_ledger (guild_id, user_id, game, delta, balance_after, ts, meta) VALUES (?, ?, 'welcome', ?, ?, ?, 'first_play_grant')",
                (gid, uid, int(amount), new_balance, ts),
            )
            conn.commit()
            return int(amount)
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return 0
        finally:
            conn.close()

    # --- Hi-Lo Card Game ---
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    RANK_VALUES = {r: i+2 for i, r in enumerate(RANKS)}  # 2..14
    SUITS = ["♠", "♥", "♦", "♣"]

    def _draw_card():
        r = secrets.choice(RANKS)
        s = secrets.choice(SUITS)
        v = RANK_VALUES[r]
        return {"rank": r, "suit": s, "value": v, "text": f"{r}{s}"}

    class HiloView(discord.ui.View):
        def __init__(self, ctx, bet: int, gid, uid):
            super().__init__(timeout=30)
            self.ctx = ctx
            self.bet = int(bet)
            self.gid = gid
            self.uid = uid
            self.cur = _draw_card()
            self.resolved = False
            self.message = None
            self.rounds = 0
            self.can_cash_out = False

        async def interaction_guard(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.uid:
                await interaction.response.send_message("This is not your Hi-Lo game.", ephemeral=True)
                return False
            return True

        async def _finish(self, interaction: discord.Interaction, guess: str):
            # Per-round bet: deduct upfront
            cur_bal = _get_balance(self.gid, self.uid)
            if cur_bal < self.bet:
                # End game due to insufficient funds
                self.resolved = True
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                embed = discord.Embed(
                    title="Hi-Lo",
                    description=f"Insufficient balance to continue. You have {cur_bal} chips.",
                    color=discord.Color.red(),
                )
                try:
                    if interaction.response.is_done():
                        await interaction.edit_original_response(embed=embed, view=self)
                    else:
                        await interaction.response.edit_message(embed=embed, view=self)
                except Exception:
                    pass
                return

            _adjust_balance(self.gid, self.uid, -self.bet, game="hilo", meta="bet")
            nxt = _draw_card()
            result = None  # "win", "lose", "push"

            if nxt["value"] == self.cur["value"]:
                result = "push"
                # refund bet only
                _adjust_balance(self.gid, self.uid, self.bet, game="hilo", meta="push")
            else:
                is_higher = nxt["value"] > self.cur["value"]
                correct = (guess == "higher" and is_higher) or (guess == "lower" and not is_higher)
                if correct:
                    result = "win"
                    # even money: net +bet (we already deducted -bet), so pay +2*bet
                    _adjust_balance(self.gid, self.uid, self.bet * 2, game="hilo", meta="payout")
                else:
                    result = "lose"

            final_bal = _get_balance(self.gid, self.uid)

            display = getattr(self.ctx.author, 'display_name', str(self.ctx.author))
            prefix = f"{self.ctx.author.mention} ({display}) "
            line = f"{self.cur['text']} → {nxt['text']}"

            if result == "win":
                # Continue to next round: set new current card, keep buttons enabled
                self.cur = nxt
                self.rounds += 1
                self.can_cash_out = True
                # enable Cash Out button
                for child in self.children:
                    if isinstance(child, discord.ui.Button) and child.label == "Cash Out":
                        child.disabled = False
                content = (
                    f"{prefix}{line} — Correct. You win +{self.bet}. Balance: {final_bal}\n"
                    f"Current card: {self.cur['text']} — Guess again or use Cash Out."
                )
                color = discord.Color.green()
                embed = discord.Embed(title="Hi-Lo", description=content, color=color)
                # Keep view active (do not disable buttons)
            elif result == "push":
                # Continue, set new current to next as well
                self.cur = nxt
                self.rounds += 1
                self.can_cash_out = True
                for child in self.children:
                    if isinstance(child, discord.ui.Button) and child.label == "Cash Out":
                        child.disabled = False
                content = (
                    f"{prefix}{line} — Push. Bet returned. Balance: {final_bal}\n"
                    f"Current card: {self.cur['text']} — Guess again or use Cash Out."
                )
                color = discord.Color.greyple()
                embed = discord.Embed(title="Hi-Lo", description=content, color=color)
            else:
                # Lose: end game
                self.resolved = True
                self.rounds += 1
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                content = f"{prefix}{line} — Wrong. You lose {self.bet}. Balance: {final_bal}"
                color = discord.Color.red()
                embed = discord.Embed(title="Hi-Lo", description=content, color=color)

            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Higher", style=discord.ButtonStyle.success)
        async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not await self.interaction_guard(interaction):
                return
            if self.resolved:
                await interaction.response.send_message("This game has already finished.", ephemeral=True)
                return
            await self._finish(interaction, "higher")

        @discord.ui.button(label="Lower", style=discord.ButtonStyle.danger)
        async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not await self.interaction_guard(interaction):
                return
            if self.resolved:
                await interaction.response.send_message("This game has already finished.", ephemeral=True)
                return
            await self._finish(interaction, "lower")

        @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.secondary, disabled=True)
        async def cashout(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not await self.interaction_guard(interaction):
                return
            if self.resolved:
                await interaction.response.send_message("This game has already finished.", ephemeral=True)
                return
            if not self.can_cash_out:
                await interaction.response.send_message("You can cash out after the first round.", ephemeral=True)
                return
            self.resolved = True
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            final_bal = _get_balance(self.gid, self.uid)
            display = getattr(self.ctx.author, 'display_name', str(self.ctx.author))
            prefix = f"{self.ctx.author.mention} ({display}) "
            embed = discord.Embed(
                title="Hi-Lo",
                description=f"{prefix}Cashed out after {self.rounds} round(s). Balance: {final_bal}",
                color=discord.Color.blurple(),
            )
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)

        async def on_timeout(self):
            if self.message and not self.resolved:
                self.resolved = True
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                embed = discord.Embed(
                    title="Hi-Lo",
                    description="Timed out. Game ended.",
                    color=discord.Color.dark_grey(),
                )
                try:
                    await self.message.edit(embed=embed, view=self)
                except Exception:
                    pass

    @bot.command(help="Play Hi-Lo; continues until you lose. Usage: hilo <bet>")
    async def hilo(ctx, bet: int | None = None):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        if bet is None or bet <= 0:
            await ctx.send("Provide a positive bet amount. Example: hilo 50")
            return
        gid = getattr(ctx.guild, 'id', None)
        uid = ctx.author.id
        # First-play welcome grant
        granted = _grant_first_play_if_needed(gid, uid)
        if granted:
            await ctx.send(f"{ctx.author.mention} Welcome bonus: +{granted} chips to get you started.")
        bal = _get_balance(gid, uid)
        if bal < bet:
            await ctx.send(f"Insufficient balance. You have {bal} chips.")
            return
        view = HiloView(ctx, int(bet), gid, uid)
        display = getattr(ctx.author, 'display_name', str(ctx.author))
        prefix = f"{ctx.author.mention} ({display}) "
        embed = discord.Embed(
            title="Hi-Lo",
            description=(
                f"{prefix}Current card: {view.cur['text']}\n"
                "Guess if the next card will be higher or lower.\n"
                "Equal value is a push and returns your bet.\n"
                "You can keep guessing. The game ends on your first loss."
            ),
            color=discord.Color.blurple(),
        )
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @bot.command(name="hilohelp", help="Show Hi-Lo rules and payout.")
    async def hilohelp(ctx):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        embed = discord.Embed(
            title="Hi-Lo Rules",
            description=(
                "Draw a card and guess if the next card is higher or lower.\n"
                "• Each round deducts your bet when you guess.\n"
                "• Correct guess: even money payout (net +bet).\n"
                "• Equal value: push (bet returned).\n"
                "• Wrong guess: round ends the game.\n"
                "Game continues on wins/pushes and ends on first loss.\n"
                "After your first round, a Cash Out button lets you end the game anytime."
            ),
            color=discord.Color.teal(),
        )
        embed.add_field(name="Ranks", value=" ".join(RANKS), inline=False)
        embed.set_footer(text="Play with: !hilo <bet>")
        await ctx.send(embed=embed)

    # --- Roulette ---
    EUROPEAN_NUMBERS = list(range(37))  # 0..36
    RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    BLACK_NUMBERS = set(n for n in range(1,37) if n not in RED_NUMBERS)

    def _roulette_color(n: int) -> str:
        if n == 0:
            return "green"
        return "red" if n in RED_NUMBERS else "black"

    def _roulette_dozen(n: int) -> int | None:
        if 1 <= n <= 12:
            return 1
        if 13 <= n <= 24:
            return 2
        if 25 <= n <= 36:
            return 3
        return None

    def _roulette_column(n: int) -> int | None:
        if n == 0:
            return None
        # columns: 1st = numbers congruent 1 mod 3; 2nd = 2 mod 3; 3rd = 0 mod 3
        r = n % 3
        return 3 if r == 0 else r

    def _fmt_roulette_number(n: int) -> str:
        icon = "🟢" if n == 0 else ("🔴" if n in RED_NUMBERS else "⚫")
        return f"{n:>2}{icon}"

    def _build_roulette_table_text() -> str:
        # Build a 3-column, 12-row layout with zero shown above.
        rows = [ _fmt_roulette_number(0) ]
        for r in range(12):
            a = 1 + 3*r
            b = 2 + 3*r
            c = 3 + 3*r
            rows.append(f"{_fmt_roulette_number(a)} | {_fmt_roulette_number(b)} | {_fmt_roulette_number(c)}")
        return "\n".join(rows)

    def _parse_roulette_selection(sel: str):
        s = sel.strip().lower()
        # straight number
        if s.isdigit():
            num = int(s)
            if 0 <= num <= 36:
                return ("straight", num)
        # color
        if s in {"red", "r"}:
            return ("color", "red")
        if s in {"black", "b"}:
            return ("color", "black")
        # parity
        if s in {"even", "ev"}:
            return ("parity", "even")
        if s in {"odd", "od"}:
            return ("parity", "odd")
        # high/low
        if s in {"low", "low18", "1-18", "1to18", "1to18"}:
            return ("range", "low")
        if s in {"high", "hi", "19-36", "19to36"}:
            return ("range", "high")
        # dozens
        if s in {"1st12", "first12", "dozen1", "1st dozen", "first dozen"}:
            return ("dozen", 1)
        if s in {"2nd12", "second12", "dozen2", "2nd dozen", "second dozen"}:
            return ("dozen", 2)
        if s in {"3rd12", "third12", "dozen3", "3rd dozen", "third dozen"}:
            return ("dozen", 3)
        # columns
        if s in {"1st", "first", "col1", "column1"}:
            return ("column", 1)
        if s in {"2nd", "second", "col2", "column2"}:
            return ("column", 2)
        if s in {"3rd", "third", "col3", "column3"}:
            return ("column", 3)
        return None

    def _roulette_payout_units(selection, hit_number: int) -> int:
        # returns units to pay relative to bet amount, e.g., 2 means pay 2*bet
        typ, val = selection
        if typ == "straight":
            return 36 if hit_number == val else 0  # 35:1 profit -> pay 36 units
        if typ == "color":
            return 2 if _roulette_color(hit_number) == val else 0  # 1:1 profit
        if typ == "parity":
            if hit_number == 0:
                return 0
            is_even = (hit_number % 2 == 0)
            return 2 if ((val == "even" and is_even) or (val == "odd" and not is_even)) else 0
        if typ == "range":
            if hit_number == 0:
                return 0
            return 2 if ((val == "low" and 1 <= hit_number <= 18) or (val == "high" and 19 <= hit_number <= 36)) else 0
        if typ == "dozen":
            return 3 if _roulette_dozen(hit_number) == val else 0  # 2:1 profit
        if typ == "column":
            return 3 if _roulette_column(hit_number) == val else 0  # 2:1 profit
        return 0

    @bot.command(name="roulette", help="Roulette. Usage: roulette <bet> <selection>. Examples: roulette 50 red | roulette 25 17 | roulette 100 3rd12 | roulette 20 column2")
    async def roulette(ctx, bet: int | None = None, *, selection: str | None = None):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        if bet is None or bet <= 0 or not selection:
            await ctx.send("Usage: roulette <bet> <selection> — try: red | black | even | odd | low | high | 1st12 | 2nd12 | 3rd12 | 1st | 2nd | 3rd | 0..36")
            return
        parsed = _parse_roulette_selection(selection)
        if not parsed:
            await ctx.send("Unknown selection. Try: red, black, even, odd, low, high, 1st12, 2nd12, 3rd12, 1st, 2nd, 3rd, or a number 0..36")
            return
        gid = getattr(ctx.guild, 'id', None)
        uid = ctx.author.id
        # First-play welcome grant
        granted = _grant_first_play_if_needed(gid, uid)
        if granted:
            await ctx.send(f"{ctx.author.mention} Welcome bonus: +{granted} chips to get you started.")
        bal = _get_balance(gid, uid)
        if bal < bet:
            await ctx.send(f"Insufficient balance. You have {bal} chips.")
            return
        # Deduct bet
        _adjust_balance(gid, uid, -int(bet), game="roulette", meta="bet")
        # Spin
        number = secrets.randbelow(37)
        color = _roulette_color(number)
        units = _roulette_payout_units(parsed, number)
        payout_amt = units * int(bet)
        if payout_amt > 0:
            final_bal = _adjust_balance(gid, uid, payout_amt, game="roulette", meta="payout")
        else:
            final_bal = _get_balance(gid, uid)
        # Audit
        try:
            conn = _db_connect()
            c = conn.cursor()
            c.execute(
                "INSERT INTO roulette_rounds (guild_id, user_id, bet, payout, selection, result_number, result_color, ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(gid) if gid is not None else "dm", str(uid), int(bet), int(payout_amt), selection.strip(), int(number), color, _now_iso()),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        # Present
        display = getattr(ctx.author, 'display_name', str(ctx.author))
        prefix = f"{ctx.author.mention} ({display}) "
        sel_text = selection.strip()
        icon = "🟢" if color == 'green' else ("🔴" if color == 'red' else "⚫")
        wheel = f"🎯 {number} {icon}"
        if payout_amt > 0:
            await ctx.send(f"{prefix}{wheel} — {sel_text} wins {payout_amt} chips. Balance: {final_bal}")
        else:
            await ctx.send(f"{prefix}{wheel} — {sel_text} loses. Balance: {final_bal}")

    @bot.command(name="roulettehelp", help="Show roulette bet types and payouts.")
    async def roulettehelp(ctx):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        embed = discord.Embed(
            title="Roulette — Bet Types and Payouts",
            description=(
                "European roulette (single zero). Place one bet per spin.\n"
                "Examples: !roulette 50 red | !roulette 25 17 | !roulette 100 3rd12 | !roulette 20 column2"
            ),
            color=discord.Color.dark_green(),
        )
        embed.add_field(name="Even-Money (x1 profit)", value="red, black, even, odd, low (1-18), high (19-36)", inline=False)
        embed.add_field(name="2:1 Profit", value="dozens (1st12, 2nd12, 3rd12), columns (1st, 2nd, 3rd)", inline=False)
        embed.add_field(name="35:1 Profit", value="straight number 0..36", inline=False)
        embed.add_field(name="Colors", value="Red numbers: " + ", ".join(str(n) for n in sorted(RED_NUMBERS)), inline=False)
        embed.set_footer(text="Win amount shown includes returning your stake. See !roulettetable for a layout diagram.")
        # Attempt to attach the table image for a visual reference
        try:
            file = discord.File("image-assets/roulette-table.png", filename="roulette-table.png")
            embed.set_image(url="attachment://roulette-table.png")
            await ctx.send(embed=embed, file=file)
        except Exception:
            # Fallback without image if file not found or cannot be read
            await ctx.send(embed=embed)

    @bot.command(name="roulettetable", help="Show the roulette table layout (European).")
    async def roulettetable(ctx):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        table_text = _build_roulette_table_text()
        embed = discord.Embed(
            title="Roulette Table (European)",
            description="0 is shown separately. Columns run down; dozens run across rows of 12.",
            color=discord.Color.dark_teal(),
        )
        # Use a code block to monospaced align columns
        embed.add_field(name="Layout", value=f"```\n{table_text}\n```", inline=False)
        embed.add_field(
            name="Legend",
            value="🟢 = 0, 🔴 = Red, ⚫ = Black\nColumns: 1st (1,4,...,34), 2nd (2,5,...,35), 3rd (3,6,...,36)",
            inline=False,
        )
        embed.set_footer(text="See !roulettehelp for bet types and payouts.")
        await ctx.send(embed=embed)

    @bot.command(help="Play slots once. Usage: slots <bet>")
    async def slots(ctx, bet: int | None = None):
        if _not_enabled(ctx):
            await ctx.send("Casino is not enabled on this server.")
            return
        if bet is None or bet <= 0:
            await ctx.send("Provide a positive bet amount. Example: slots 50")
            return
        gid = getattr(ctx.guild, 'id', None)
        uid = ctx.author.id
        # First-play welcome grant
        granted = _grant_first_play_if_needed(gid, uid)
        if granted:
            await ctx.send(f"{ctx.author.mention} Welcome bonus: +{granted} chips to get you started.")
        bal = _get_balance(gid, uid)
        if bal < bet:
            await ctx.send(f"Insufficient balance. You have {bal} chips.")
            return
        # Deduct bet
        after_bet = _adjust_balance(gid, uid, -bet, game="slots", meta="bet")
        # Spin
        reels = _spin_reels()
        payout = _payout_for(reels, bet)
        # Pay winnings
        if payout > 0:
            final_bal = _adjust_balance(gid, uid, payout, game="slots", meta="payout")
        else:
            final_bal = after_bet
        # Audit
        try:
            conn = _db_connect()
            c = conn.cursor()
            c.execute(
                "INSERT INTO slots_rounds (guild_id, user_id, bet, payout, symbols, ts) VALUES (?, ?, ?, ?, ?, ?)",
                (str(gid) if gid is not None else "dm", str(uid), int(bet), int(payout), "".join(reels), _now_iso()),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        # Present result
        line = " | ".join(reels)
        display = getattr(ctx.author, 'display_name', str(ctx.author))
        prefix = f"{ctx.author.mention} ({display}) "
        if payout > 0:
            msg = f"{prefix}{line} → You won {payout} chips. Balance: {final_bal}"
        else:
            msg = f"{prefix}{line} → No win. Balance: {final_bal}"
        await ctx.send(msg)
