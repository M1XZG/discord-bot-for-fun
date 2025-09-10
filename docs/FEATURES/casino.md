# 🎰 Casino

The Casino adds a fun, server-local chip economy with multiple games and a clean audit trail.

## Highlights

- One-time Welcome Bonus: +2000 chips the first time a player uses any casino game
- Daily Faucet: +500 chips once every 24 hours via `!faucet`
- Clear Balance: `!chips` shows your or another member’s balance
- Admin Tools: `!givechips @user <amount>` to grant or remove chips
- Games included:
  - Slots — pairs refund the bet; triples pay multipliers
  - Hi‑Lo — keep guessing higher/lower; ends on first loss; Cash Out after round 1
  - Roulette — European (single zero); supports color, parity, high/low, dozens, columns, and straight numbers

## Commands

User
- `!chips [@user]` — Show chip balance
- `!faucet` — Claim daily +500 chips
- `!slots <bet>` — Spin once
- `!slotshelp` — Paytable and multipliers
- `!hilo <bet>` — Multi‑round until first loss; Cash Out available after round 1
- `!hilohelp` — Rules and payout
- `!roulette <bet> <selection>` — Play roulette
- `!roulettehelp` — Bet types and payouts (includes a visual table image)
- `!roulettetable` — ASCII layout and legend

Admin
- `!givechips @user <amount>` — Grant/remove chips (negative to remove)

## Gameplay Details

### Welcome Bonus & Faucet
- New players receive a one-time welcome grant of +2000 chips automatically on their first casino play (slots/hilo/roulette).
- Players can claim +500 chips once every 24h with `!faucet`.

### Slots
- Symbols: 7️⃣ ⭐ 🔔 🍇 🍋 🍒
- Pairs: refund your bet (x1)
- Triples: multipliers (example paytable)
  - 7️⃣7️⃣7️⃣ — x30
  - ⭐⭐⭐ — x20
  - 🔔🔔🔔 — x12
  - 🍇🍇🍇 — x8
  - 🍋🍋🍋 — x6
  - 🍒🍒🍒 — x5

Play with: `!slots 50`

### Hi‑Lo
- Draw a starting card, then guess if the next card is higher or lower
- Each guess deducts your bet
- Correct guess pays even money (net +bet)
- Equal value is a push (bet returned)
- First loss ends the game
- After the first round, a Cash Out button lets you stop anytime

Play with: `!hilo 25`

### Roulette (European)
- Single zero (0)
- Supported bets:
  - Even-money: `red`, `black`, `even`, `odd`, `low` (1–18), `high` (19–36)
  - 2:1: dozens (`1st12`, `2nd12`, `3rd12`), columns (`1st`, `2nd`, `3rd`)
  - 35:1: straight numbers `0..36`
- Visuals: `!roulettehelp` shows a table image; `!roulettetable` shows an ASCII layout

Examples:
```
!roulette 50 red
!roulette 25 17
!roulette 100 3rd12
!roulette 20 2nd
```

## Data & Audit

All chip movements are recorded in a ledger for clarity and anti-cheat auditing.

Tables in `games_stats.db`:
- `casino_chips(guild_id, user_id, balance, last_updated, last_faucet)`
- `casino_ledger(id, guild_id, user_id, game, delta, balance_after, ts, meta)`
- `slots_rounds(id, guild_id, user_id, bet, payout, symbols, ts)`
- `roulette_rounds(id, guild_id, user_id, bet, payout, selection, result_number, result_color, ts)`

Notes
- The welcome grant is recorded with `game='welcome'`
- Bets and payouts are logged per round for roulette and slots

## Configuration

The Casino feature is controlled by feature flags (see Configuration guide). The faucet and welcome amounts are fixed by default: 500 daily faucet, 2000 welcome. Server‑configurable amounts may be introduced in a future release.
