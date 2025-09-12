---
title: Mini Games
permalink: /features/mini-games
---
{% comment %}Inlined from docs/FEATURES/mini-games.md{% endcomment %}
# Mini-Games

## Overview

Quick, zero-setup games for fun and engagement. Includes buttons-based Rock-Paper-Scissors, dice rolling with NdX syntax, and more.

## Available Games

### 🪙 Coin Flip — `!flip`

Flip a virtual coin.

- Output: Heads or Tails
- No cooldown

Examples:
```
!flip
```

### 🎲 Dice Roll — `!roll`

Roll one or more dice using familiar formats.

- Syntax: `!roll NdX` or `!roll <count> <sides>`
- Supported dice: d4, d6, d8, d10, d12, d20, d100 (others default to d6)
- Caps at 20 dice per roll

Examples:
```
!roll           # defaults to 1d6
!roll 2d20
!roll 3 6
```

### ✂️ Rock, Paper, Scissors — `!rps`

Two ways to play:

1) Solo vs Bot (buttons UI)
- Command: `!rps`
- Buttons to choose Rock/Paper/Scissors
- 15s timeout; if you don’t pick, you lose by default and get playfully mocked

2) Challenge Another User (PvP)
- Command: `!rps @user`
- Mentions the challenged user so they get notified
- 60s timeout so both players can respond
- Forfeit rules: if only one player picks before time runs out, the other loses by default

Direct text play:
```
!rps rock
!rps paper
!rps scissors
```

### 📊 RPS Stats — `!rpsstats`

View Rock-Paper-Scissors stats per server (no cross-server bleed):

- Command: `!rpsstats` or `!rpsstats @user`
- Tracks wins, losses, draws, win rate, and last played time
- Stored in `games_stats.db` keyed by (guild_id, user_id)

### 🎱 Magic 8-Ball — `!8ball`

Ask the magic 8-ball a question and get a classic response.

Examples:
```
!8ball Will I win the lottery?
!8ball Should I eat pizza tonight?
```

### 🎯 Random Choice — `!choose`

Pick randomly from options separated by `|` or commas.

Examples:
```
!choose tea | coffee | juice
!choose red, blue, green
```

## Game Statistics

- RPS maintains per-user, per-server stats (wins/losses/draws, last played)
- Other games are stateless

## Command Cooldowns

- No cooldowns on mini-games
- RPS uses view timeouts (15s solo, 60s PvP) rather than command cooldowns

## Technical Details

- Implemented with Python’s `random`
- Discord UI buttons for RPS
- SQLite `games_stats.db` for RPS statistics