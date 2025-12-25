#!/usr/bin/env python3

"""
🎰 Casino statistics CLI

Reports chip balances, profit leaderboards, ledger activity, and per-game
RTP for Slots and Roulette. Defaults to a summary plus top balances.

Database schema (from casino.py):
- casino_chips(guild_id, user_id, balance, last_updated, last_faucet)
- casino_ledger(id, guild_id, user_id, game, delta, balance_after, ts, meta)
- slots_rounds(id, guild_id, user_id, bet, payout, symbols, ts)
- roulette_rounds(id, guild_id, user_id, bet, payout, selection, result_number, result_color, ts)
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
import asyncio
from dotenv import load_dotenv
import discord


def fmt_date(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


def connect_or_die(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        print(f"❌ Database not found: {path}", file=sys.stderr)
        print("💡 Run the bot first or specify --db path", file=sys.stderr)
        sys.exit(1)
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        sys.exit(1)


def add_common_args(p: argparse.ArgumentParser):
    p.add_argument(
        "--db",
        type=str,
        default="games_stats.db",
        help="Path to database file (default: games_stats.db)",
    )
    p.add_argument("-n", "--number", type=int, default=10, help="Number of rows to display")
    p.add_argument("--all", action="store_true", help="Show all rows (ignore -n)")
    p.add_argument("--guild", type=str, help="Filter by guild id")
    p.add_argument("--user", type=str, help="Filter by user id")


def build_parser() -> argparse.ArgumentParser:
    epilog = """
Examples:
  %(prog)s                        # Summary + top balances
  %(prog)s --summary              # Summary only
  %(prog)s --balances -n 20       # Top 20 balances
  %(prog)s --profits              # Top net profit (ledger deltas)
  %(prog)s --ledger --user 123    # Ledger for a user
  %(prog)s --slots --top          # Top slots payouts
  %(prog)s --roulette --rtp       # Roulette RTP and hit distribution
"""
    parser = argparse.ArgumentParser(
        description="🎰 Display casino statistics from the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    add_common_args(parser)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--summary", action="store_true", help="Show overall casino summary")
    group.add_argument("--balances", action="store_true", help="Show chip balance leaderboard")
    group.add_argument("--profits", action="store_true", help="Show net profit leaderboard from ledger")
    group.add_argument("--ledger", action="store_true", help="Show ledger entries")
    group.add_argument("--slots", action="store_true", help="Show slots stats")
    group.add_argument("--roulette", action="store_true", help="Show roulette stats")

    # Ledger filters
    parser.add_argument("--game", type=str, help="Filter ledger/rounds by game name")
    parser.add_argument("--since", type=str, help="Filter ts >= ISO-8601 timestamp")
    parser.add_argument("--until", type=str, help="Filter ts <= ISO-8601 timestamp")

    # Slots details
    parser.add_argument("--top", action="store_true", help="Show top payouts (slots/roulette)")
    parser.add_argument("--dist", action="store_true", help="Show distribution details (symbols/colors/parity)")
    parser.add_argument("--rtp", action="store_true", help="Show RTP (total payout / total bet)")
    parser.add_argument("--welcome", action="store_true", help="Include welcome grants in summary")
    parser.add_argument("--faucet", action="store_true", help="Include faucet stats in summary")
    # Name resolution flags
    parser.add_argument("--names", dest="names", action="store_true", default=True,
                        help="Resolve guild and user IDs to Discord names (default)")
    parser.add_argument("--no-names", dest="names", action="store_false",
                        help="Do not resolve names; show numeric IDs only")
    parser.add_argument("--show-ids", action="store_true",
                        help="Append numeric IDs after names in parentheses")

    # Balance adjustment (admin) — mutually exclusive operations
    adjust = parser.add_mutually_exclusive_group()
    adjust.add_argument("--set", type=int, help="Set user balance to this exact amount")
    adjust.add_argument("--add", type=int, help="Add this amount to user balance (can be negative)")
    adjust.add_argument("--sub", type=int, help="Subtract this amount from user balance")
    parser.add_argument("--reason", type=str, default="admin-script",
                        help="Reason/meta to store in ledger (default: admin-script)")
    parser.add_argument("--confirm", action="store_true",
                        help="Execute the update. Without this, performs a dry-run preview only.")

    return parser


def print_summary(conn: sqlite3.Connection, include_welcome: bool, include_faucet: bool):
    c = conn.cursor()

    c.execute("SELECT COUNT(*) AS players, COALESCE(SUM(balance),0) AS chips FROM casino_chips")
    row = c.fetchone()
    players = row["players"] or 0
    chips = row["chips"] or 0

    c.execute("SELECT COUNT(*) AS entries, COALESCE(SUM(delta),0) AS net FROM casino_ledger")
    led = c.fetchone()
    entries = led["entries"] or 0
    net = led["net"] or 0

    print("🎰 Casino Summary")
    print("─" * 40)
    print(f"Players:            {players}")
    print(f"Total chips:        {chips}")
    print(f"Ledger entries:     {entries}")
    print(f"Net delta (ledger): {net}")

    # Per-game RTP from audit tables
    # Slots
    c.execute("SELECT COALESCE(SUM(bet),0) AS bet, COALESCE(SUM(payout),0) AS pay, COUNT(*) AS rounds FROM slots_rounds")
    s = c.fetchone()
    s_bet, s_pay, s_rounds = s["bet"], s["pay"], s["rounds"]
    s_rtp = (s_pay / s_bet) if s_bet else 0.0
    print(f"Slots:   rounds={s_rounds}  total_bet={s_bet}  total_payout={s_pay}  RTP={s_rtp:.3f}")

    # Roulette
    c.execute("SELECT COALESCE(SUM(bet),0) AS bet, COALESCE(SUM(payout),0) AS pay, COUNT(*) AS spins FROM roulette_rounds")
    r = c.fetchone()
    r_bet, r_pay, r_spins = r["bet"], r["pay"], r["spins"]
    r_rtp = (r_pay / r_bet) if r_bet else 0.0
    print(f"Roulette: spins={r_spins}  total_bet={r_bet}  total_payout={r_pay}  RTP={r_rtp:.3f}")

    if include_welcome:
        c.execute("SELECT COUNT(*) AS grants, COALESCE(SUM(delta),0) AS chips FROM casino_ledger WHERE game='welcome'")
        w = c.fetchone()
        print(f"Welcome grants:     count={w['grants']}  chips={w['chips']}")

    if include_faucet:
        c.execute("SELECT COUNT(*) AS claims, COALESCE(SUM(delta),0) AS chips FROM casino_ledger WHERE game='faucet'")
        f = c.fetchone()
        print(f"Faucet claims:      count={f['claims']}  chips={f['chips']}")


def _now_iso() -> str:
    from datetime import timezone
    return datetime.now(timezone.utc).isoformat()


def adjust_balance(conn: sqlite3.Connection, guild_id: str, user_id: str, *, set_to: int | None = None, add: int | None = None, sub: int | None = None, reason: str = "admin-script") -> dict:
    """Transactional balance adjustment with ledger entry.
    Returns a dict with keys: ok, before, after, delta, message.
    """
    if set_to is None and add is None and sub is None:
        return {"ok": False, "message": "No operation specified"}
    delta = 0
    if set_to is not None:
        # compute delta relative to current
        pass
    elif add is not None:
        delta = int(add)
    elif sub is not None:
        delta = -int(sub)

    ts = _now_iso()
    c = conn.cursor()
    try:
        c.execute("BEGIN IMMEDIATE")
        c.execute(
            "SELECT balance FROM casino_chips WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        row = c.fetchone()
        before = int(row[0]) if row else 0
        if set_to is not None:
            delta = int(set_to) - before
        after = before + int(delta)
        if after < 0:
            conn.rollback()
            return {"ok": False, "before": before, "after": before, "delta": 0, "message": "Cannot set negative balance"}
        # upsert chips
        if row:
            c.execute(
                "UPDATE casino_chips SET balance = ?, last_updated = ? WHERE guild_id = ? AND user_id = ?",
                (after, ts, str(guild_id), str(user_id)),
            )
        else:
            c.execute(
                "INSERT INTO casino_chips (guild_id, user_id, balance, last_updated) VALUES (?, ?, ?, ?)",
                (str(guild_id), str(user_id), after, ts),
            )
        # ledger entry: game=admin
        c.execute(
            "INSERT INTO casino_ledger (guild_id, user_id, game, delta, balance_after, ts, meta) VALUES (?, ?, 'admin', ?, ?, ?, ?)",
            (str(guild_id), str(user_id), int(delta), after, ts, reason),
        )
        conn.commit()
        return {"ok": True, "before": before, "after": after, "delta": int(delta), "message": "updated"}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"ok": False, "message": f"DB error: {e}"}


def print_balances(conn: sqlite3.Connection, limit: int, guild: str | None, user: str | None):
    c = conn.cursor()
    sql = "SELECT guild_id, user_id, balance, last_updated, last_faucet FROM casino_chips WHERE 1=1"
    params = []
    if guild:
        sql += " AND guild_id = ?"
        params.append(guild)
    if user:
        sql += " AND user_id = ?"
        params.append(user)
    sql += " ORDER BY balance DESC"
    if limit:
        sql += f" LIMIT {limit}"

    c.execute(sql, params)
    rows = c.fetchall()
    print("🏆 Chip Balances")
    print("─" * 100)
    print(f"{'Rank':<6} {'Guild':<24} {'User':<24} {'Balance':<10} {'Updated':<16} {'Last Faucet':<16}")
    print("─" * 100)
    rank = 1
    for r in rows:
        g = format_guild(r['guild_id'])
        u = format_user(r['guild_id'], r['user_id'])
        print(f"{rank:<6} {g:<24} {u:<24} {int(r['balance']):<10} {fmt_date(r['last_updated']):<16} {fmt_date(r['last_faucet']) if r['last_faucet'] else '-':<16}")
        rank += 1


def print_profits(conn: sqlite3.Connection, limit: int, guild: str | None, user: str | None):
    c = conn.cursor()
    sql = (
        "SELECT guild_id, user_id, COALESCE(SUM(delta),0) AS net, COUNT(*) AS actions "
        "FROM casino_ledger WHERE 1=1"
    )
    params = []
    if guild:
        sql += " AND guild_id = ?"
        params.append(guild)
    if user:
        sql += " AND user_id = ?"
        params.append(user)
    sql += " GROUP BY guild_id, user_id ORDER BY net DESC"
    if limit:
        sql += f" LIMIT {limit}"

    c.execute(sql, params)
    rows = c.fetchall()
    print("💹 Net Profit Leaderboard (ledger deltas)")
    print("─" * 90)
    print(f"{'Rank':<6} {'Guild':<24} {'User':<24} {'Net Chips':<12} {'Entries':<8}")
    print("─" * 90)
    rank = 1
    for r in rows:
        g = format_guild(r['guild_id'])
        u = format_user(r['guild_id'], r['user_id'])
        print(f"{rank:<6} {g:<24} {u:<24} {int(r['net']):<12} {int(r['actions']):<8}")
        rank += 1


def print_ledger(conn: sqlite3.Connection, limit: int, guild: str | None, user: str | None, game: str | None, since: str | None, until: str | None):
    c = conn.cursor()
    sql = "SELECT ts, guild_id, user_id, game, delta, balance_after, meta FROM casino_ledger WHERE 1=1"
    params = []
    if guild:
        sql += " AND guild_id = ?"
        params.append(guild)
    if user:
        sql += " AND user_id = ?"
        params.append(user)
    if game:
        sql += " AND game = ?"
        params.append(game)
    if since:
        sql += " AND ts >= ?"
        params.append(since)
    if until:
        sql += " AND ts <= ?"
        params.append(until)
    sql += " ORDER BY ts DESC"
    if limit:
        sql += f" LIMIT {limit}"

    c.execute(sql, params)
    rows = c.fetchall()
    print("📒 Casino Ledger")
    print("─" * 130)
    print(f"{'Date':<16} {'Guild':<24} {'User':<24} {'Game':<10} {'Delta':<8} {'Balance':<10} {'Meta':<30}")
    print("─" * 130)
    for r in rows:
        meta = r['meta'] if r['meta'] else ''
        g = format_guild(r['guild_id'])
        u = format_user(r['guild_id'], r['user_id'])
        print(f"{fmt_date(r['ts']):<16} {g:<24} {u:<24} {r['game']:<10} {int(r['delta']):<8} {int(r['balance_after']):<10} {meta:<30}")


def print_slots(conn: sqlite3.Connection, limit: int, show_top: bool, show_dist: bool, show_rtp: bool, guild: str | None, user: str | None):
    c = conn.cursor()
    # Base stats
    c.execute("SELECT COALESCE(SUM(bet),0) AS bet, COALESCE(SUM(payout),0) AS pay, COUNT(*) AS rounds FROM slots_rounds")
    s = c.fetchone()
    s_bet, s_pay, s_rounds = s['bet'], s['pay'], s['rounds']
    s_rtp = (s_pay / s_bet) if s_bet else 0.0
    print("🎰 Slots Stats")
    print("─" * 60)
    print(f"Rounds: {s_rounds}  Total bet: {s_bet}  Total payout: {s_pay}  RTP: {s_rtp:.3f}")

    where = "WHERE 1=1"
    params = []
    if guild:
        where += " AND guild_id = ?"
        params.append(guild)
    if user:
        where += " AND user_id = ?"
        params.append(user)

    if show_top:
        sql = f"SELECT ts, guild_id, user_id, bet, payout, symbols FROM slots_rounds {where} ORDER BY payout DESC"
        if limit:
            sql += f" LIMIT {limit}"
        c.execute(sql, params)
        rows = c.fetchall()
        print("🏅 Top Slots Payouts")
        print("─" * 100)
        print(f"{'Date':<16} {'Guild':<24} {'User':<24} {'Bet':<8} {'Payout':<8} {'Symbols':<20}")
        print("─" * 100)
        for r in rows:
            g = format_guild(r['guild_id'])
            u = format_user(r['guild_id'], r['user_id'])
            print(f"{fmt_date(r['ts']):<16} {g:<24} {u:<24} {int(r['bet']):<8} {int(r['payout']):<8} {r['symbols']:<20}")

    if show_dist:
        sql = f"SELECT symbols, COUNT(*) AS cnt FROM slots_rounds {where} GROUP BY symbols ORDER BY cnt DESC"
        if limit:
            sql += f" LIMIT {limit}"
        c.execute(sql, params)
        print("🎲 Symbol Combination Frequency")
        for r in c.fetchall():
            print(f"   {r['symbols']}: {r['cnt']}")

    if show_rtp:
        # already printed overall RTP; also show pair vs triple implied from payout values if desired
        pass


def print_roulette(conn: sqlite3.Connection, limit: int, show_top: bool, show_dist: bool, show_rtp: bool, guild: str | None, user: str | None):
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(bet),0) AS bet, COALESCE(SUM(payout),0) AS pay, COUNT(*) AS spins FROM roulette_rounds")
    r = c.fetchone()
    r_bet, r_pay, r_spins = r['bet'], r['pay'], r['spins']
    r_rtp = (r_pay / r_bet) if r_bet else 0.0
    print("🎯 Roulette Stats")
    print("─" * 60)
    print(f"Spins: {r_spins}  Total bet: {r_bet}  Total payout: {r_pay}  RTP: {r_rtp:.3f}")

    where = "WHERE 1=1"
    params = []
    if guild:
        where += " AND guild_id = ?"
        params.append(guild)
    if user:
        where += " AND user_id = ?"
        params.append(user)

    if show_top:
        sql = f"SELECT ts, guild_id, user_id, bet, payout, selection, result_number, result_color FROM roulette_rounds {where} ORDER BY payout DESC"
        if limit:
            sql += f" LIMIT {limit}"
        c.execute(sql, params)
        rows = c.fetchall()
        print("🏅 Top Roulette Payouts")
        print("─" * 120)
        print(f"{'Date':<16} {'Guild':<24} {'User':<24} {'Bet':<8} {'Payout':<8} {'Selection':<16} {'Result':<12} {'Color':<8}")
        print("─" * 120)
        for r in rows:
            g = format_guild(r['guild_id'])
            u = format_user(r['guild_id'], r['user_id'])
            print(f"{fmt_date(r['ts']):<16} {g:<24} {u:<24} {int(r['bet']):<8} {int(r['payout']):<8} {r['selection']:<16} {int(r['result_number']):<12} {r['result_color']:<8}")

# ─── Discord Name Resolution (optional) ───────────────────────────────────────
_resolver = None
_resolver_loop = None

class NameResolver:
    def __init__(self, loop: asyncio.AbstractEventLoop, show_ids: bool = False):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        self.client = discord.Client(intents=intents)
        self.loop = loop
        self.ready = asyncio.Event()
        self.guild_names: dict[str, str] = {}
        self.user_names: dict[tuple[str, str], str] = {}
        self.show_ids = show_ids

        @self.client.event
        async def on_ready():
            self.ready.set()

    async def start(self, token: str):
        asyncio.create_task(self.client.start(token))
        await self.ready.wait()

    async def shutdown(self):
        try:
            await self.client.close()
        except Exception:
            pass

    async def guild_name_async(self, gid: str) -> str:
        if gid in self.guild_names:
            return self.guild_names[gid]
        if gid == "dm":
            name = "DM"
        else:
            g = self.client.get_guild(int(gid))
            name = g.name if g else str(gid)
        self.guild_names[gid] = name
        return name

    async def user_name_async(self, gid: str, uid: str) -> str:
        key = (gid, uid)
        if key in self.user_names:
            return self.user_names[key]
        name = str(uid)
        try:
            if gid == "dm":
                u = await self.client.fetch_user(int(uid))
                if u:
                    name = getattr(u, "global_name", None) or getattr(u, "name", str(uid))
            else:
                g = self.client.get_guild(int(gid))
                member = g.get_member(int(uid)) if g else None
                if not member and g:
                    try:
                        member = await g.fetch_member(int(uid))
                    except Exception:
                        member = None
                if member:
                    name = member.display_name
        except Exception:
            pass
        self.user_names[key] = name
        return name

def format_guild(gid: str) -> str:
    if not _resolver:
        return str(gid)
    name = _resolver_loop.run_until_complete(_resolver.guild_name_async(str(gid)))
    return f"{name} ({gid})" if _resolver.show_ids and gid != "dm" else name

def format_user(gid: str, uid: str) -> str:
    if not _resolver:
        return str(uid)
    name = _resolver_loop.run_until_complete(_resolver.user_name_async(str(gid), str(uid)))
    return f"{name} ({uid})" if _resolver.show_ids else name

    if show_dist:
        # Color distribution
        sql = f"SELECT result_color, COUNT(*) AS cnt FROM roulette_rounds {where} GROUP BY result_color ORDER BY cnt DESC"
        c.execute(sql, params)
        print("🎨 Color Distribution")
        for r in c.fetchall():
            print(f"   {r['result_color']}: {r['cnt']}")

        # Parity distribution (excluding zeros)
        sql = f"SELECT (result_number % 2) AS odd, COUNT(*) AS cnt FROM roulette_rounds {where} WHERE result_number <> 0 GROUP BY (result_number % 2) ORDER BY cnt DESC"
        c.execute(sql, params)
        print("➗ Parity Distribution (no 0)")
        for r in c.fetchall():
            label = "odd" if int(r['odd']) == 1 else "even"
            print(f"   {label}: {r['cnt']}")

        # Dozens
        sql = f"SELECT CASE WHEN 1<=result_number AND result_number<=12 THEN 1 WHEN 13<=result_number AND result_number<=24 THEN 2 WHEN 25<=result_number AND result_number<=36 THEN 3 ELSE 0 END AS dozen, COUNT(*) AS cnt FROM roulette_rounds {where} GROUP BY dozen ORDER BY dozen"
        c.execute(sql, params)
        print("🔢 Dozens Distribution")
        for r in c.fetchall():
            label = {0: 'zero', 1: '1st12', 2: '2nd12', 3: '3rd12'}.get(int(r['dozen']), str(r['dozen']))
            print(f"   {label}: {r['cnt']}")

    if show_rtp:
        # already printed overall RTP
        pass


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Determine limit
    limit = None if args.all else (args.number or 10)

    conn = connect_or_die(args.db)

    # Initialize optional Discord name resolver
    global _resolver, _resolver_loop
    if args.names:
        load_dotenv()
        token = os.getenv("DISCORD_TOKEN")
        if token:
            _resolver_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_resolver_loop)
            _resolver = NameResolver(_resolver_loop, show_ids=args.show_ids)
            try:
                _resolver_loop.run_until_complete(_resolver.start(token))
            except Exception as e:
                print(f"⚠️ Name resolution disabled (Discord login failed): {e}", file=sys.stderr)
                _resolver = None
                try:
                    _resolver_loop.close()
                except Exception:
                    pass
                _resolver_loop = None
        else:
            print("⚠️ Name resolution disabled: DISCORD_TOKEN not set (.env).", file=sys.stderr)

    # If an adjustment operation is requested, handle it first
    if any([args.set is not None, args.add is not None, args.sub is not None]):
        if not args.guild or not args.user:
            print("❌ Provide --guild and --user to target a balance.", file=sys.stderr)
            conn.close()
            return
        # Preview names (if resolver on) for clarity
        target_guild = format_guild(args.guild) if _resolver else str(args.guild)
        target_user = format_user(args.guild, args.user) if _resolver else str(args.user)
        op_text = (
            f"set to {args.set}" if args.set is not None else
            (f"add {args.add}" if args.add is not None else f"subtract {args.sub}")
        )
        print("🔧 Balance Adjustment (preview)")
        print("─" * 60)
        print(f"Guild: {target_guild}")
        print(f"User:  {target_user}")
        print(f"Op:    {op_text}")
        print(f"Reason: {args.reason}")
        if not args.confirm:
            print("⚠️ Dry-run only. Add --confirm to execute.")
            conn.close()
            if _resolver and _resolver_loop:
                _resolver_loop.run_until_complete(_resolver.shutdown())
                _resolver_loop.close()
            return
        # Execute
        result = adjust_balance(
            conn,
            guild_id=str(args.guild),
            user_id=str(args.user),
            set_to=args.set,
            add=args.add,
            sub=args.sub,
            reason=args.reason,
        )
        if result.get("ok"):
            print("✅ Updated")
            print(f"Before: {result['before']}  Delta: {result['delta']}  After: {result['after']}")
        else:
            print(f"❌ {result.get('message','failed')}")
        conn.close()
        if _resolver and _resolver_loop:
            _resolver_loop.run_until_complete(_resolver.shutdown())
            _resolver_loop.close()
        return

    # Default view: summary + top balances
    if not any([args.summary, args.balances, args.profits, args.ledger, args.slots, args.roulette]):
        print_summary(conn, include_welcome=False, include_faucet=False)
        print()
        print_balances(conn, limit=10, guild=args.guild, user=args.user)
        conn.close()
        # Clean up resolver if running
        if _resolver and _resolver_loop:
            _resolver_loop.run_until_complete(_resolver.shutdown())
            _resolver_loop.close()
        return

    if args.summary:
        print_summary(conn, include_welcome=args.welcome, include_faucet=args.faucet)
    elif args.balances:
        print_balances(conn, limit=limit, guild=args.guild, user=args.user)
    elif args.profits:
        print_profits(conn, limit=limit, guild=args.guild, user=args.user)
    elif args.ledger:
        print_ledger(conn, limit=limit, guild=args.guild, user=args.user, game=args.game, since=args.since, until=args.until)
    elif args.slots:
        print_slots(conn, limit=limit, show_top=args.top, show_dist=args.dist, show_rtp=args.rtp, guild=args.guild, user=args.user)
    elif args.roulette:
        print_roulette(conn, limit=limit, show_top=args.top, show_dist=args.dist, show_rtp=args.rtp, guild=args.guild, user=args.user)

    conn.close()
    if _resolver and _resolver_loop:
        _resolver_loop.run_until_complete(_resolver.shutdown())
        _resolver_loop.close()


if __name__ == "__main__":
    main()
