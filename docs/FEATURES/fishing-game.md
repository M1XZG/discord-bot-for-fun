# Fishing Game

## Overview

A complete fishing mini-game with 30+ fish species, leaderboards, collectibles, and competitive fishing contests!

## How to Play

### Basic Fishing

1. **Cast your line**: `!fish` (or `!f`)
2. **Wait for result**: You'll catch either:
   - A fish (common)
   - A server member (rare - 1/250 chance)
3. **Earn points**: Based on size and weight
4. **Check stats**: `!fishstats`

### Commands

| Command | Description |
|---------|-------------|
| `!fish` | Go fishing |
| `!fishstats [@user]` | View stats and leaderboard |
| `!fishlist` | See all available fish |
| `!fishinfo <fish>` | Details about specific fish |
| `!fishhelp` | Game help |

## 🏆 Fishing Contests

### Overview
Compete against other anglers in time-limited fishing contests with special rules and prizes!

### Contest Features
- **No cooldowns** during contests - fish as fast as you can!
- **50% bonus points** on all catches during contests
- **Dedicated contest threads** for organized competition
- **Live leaderboards** to track standings
- **Automatic results** and winner announcement

### Player Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!joincontest` | Join the upcoming contest | `!joincontest` |
| `!contestinfo` | Show current/next contest info | `!contestinfo` |
| `!contestlb` | Display live contest leaderboard | `!contestlb` |
| `!pastcontests` | List previous contests | `!pastcontests` |
| `!contestresults <id>` | Show specific contest results | `!contestresults 5` |
| `!contesthelp` | Show contest help | `!contesthelp` |

### How Contests Work

1. **Announcement Phase**
   - Admin schedules a contest with start time and duration
   - Players can join using `!joincontest`
   - Contest details shown with countdown

2. **Thread Creation** (1 minute before start)
   - Dedicated thread created automatically
   - Thread shows "[WAITING]" status
   - Rules and countdown displayed
   - **Important**: Don't fish until the START announcement!

3. **Contest Start**
   - Thread status changes to "[ACTIVE]"
   - Big "FISH NOW!" announcement with participant pings
   - All cooldowns removed
   - 50% bonus points active

4. **During Contest**
   - Fish only in the contest thread
   - Use `!fish` as fast as you can (no cooldowns!)
   - Check live standings with `!contestlb`
   - All catches earn 50% bonus points

5. **Contest End**
   - Results announced automatically
   - Winner crowned with total points and catches
   - Thread locked and archived
   - Stats saved for history

### Contest Rules
- Fish caught before the official start don't count
- Must fish in the contest thread during active contests
- All fish species available during contests
- Member catches still possible (and worth more!)
- Join before the contest starts to participate

## Game Mechanics

### Fish Properties
- **Size**: Measured in centimeters
- **Weight**: Measured in kilograms
- **Points**: Calculated from size and weight
- **Rarity**: All fish have equal catch chance

### Point Calculation
```
Base Points = (Weight × 10) + Size
Contest Points = Base Points × 1.5 (50% bonus)
```

Maximum points capped at 2× the fish's theoretical maximum.

### Member Catches
- **Chance**: 1 in 250 (configurable)
- **Weight**: 55-140 kg
- **Points**: 1000 + (weight × 2.2)
- **Special**: Shows member's avatar
- **Contest bonus**: Also gets 50% bonus during contests

### Cooldown System
- Default: 30 seconds between casts
- Applies to all users
- Configurable by admins
- Shows remaining time if triggered
- **Disabled during contests!**

## Fish Species

The game includes 30+ fish species:

### Common Fish
- Bass, Trout, Salmon, Tuna
- Catfish, Perch, Pike, Carp

### Exotic Fish
- Marlin, Swordfish, Barracuda
- Mahi-Mahi, Wahoo, Tarpon

### Rare/Large Fish
- Blue Whale, Great White Shark
- Whale Shark, Manta Ray

View all with `!fishlist`

## Leaderboard System

### Statistics Tracked
- Total catches
- Total points
- Biggest catch (by weight)
- Individual fish records
- Contest wins and participation

### Leaderboard Features
- Top 10 anglers displayed
- Medal emojis for top 3
- Personal stats section
- Biggest catch preview
- Contest history

## Admin Configuration

### Contest Management
```
!startcontest <duration> <delay>    # Schedule a contest
!cancelcontest                      # Cancel current contest
```

Examples:
```
!startcontest 10m 5m    # 10-minute contest starting in 5 minutes
!startcontest 30m 1h    # 30-minute contest starting in 1 hour
!startcontest 1h 30m    # 1-hour contest starting in 30 minutes
```

### Add New Fish
```
!addfish <name> <minSize> <maxSize> <minWeight> <maxWeight>
```

Example:
```
!addfish Goldfish 5 15 0.05 0.2
```

### Cooldown Management
```
!setfishcooldown 45s    # 45 seconds
!setfishcooldown 2m     # 2 minutes
!setfishcooldown 1m30s  # 1 minute 30 seconds
!setfishcooldown 0      # Disable cooldown
```

### Configuration File

`my_fishing_game_config.json`:
```json
{
  "member_catch_ratio": 250,
  "cooldown_seconds": 30,
  "fish": [...]
}
```

## Asset Management

### Fish Images
- Location: `FishingGameAssets/` folder
- Format: PNG, JPG, JPEG, GIF
- Naming: Match fish name (spaces → underscores)

### Adding Fish Assets
1. Add image to `FishingGameAssets/`
2. Name it matching the fish (e.g., `Great_White_Shark.png`)
3. Use `!addfish` to configure stats

## Tips & Strategies

### For Players
1. **Fish regularly** to climb leaderboard
2. **Join contests** for bonus points and glory
3. **Check fishinfo** to learn about catches
4. **Compete** for biggest catches
5. **Collect** all species (use `!fishlist`)
6. **Watch for contests** and join early!

### For Contest Success
1. **Join early** with `!joincontest`
2. **Be ready** when the contest starts
3. **Fish fast** - no cooldowns during contests
4. **Stay in thread** - only contest thread catches count
5. **Check standings** with `!contestlb`

### For Admins
1. **Balance stats** for fair gameplay
2. **Add variety** with new species
3. **Schedule contests** during peak hours
4. **Vary contest lengths** for different challenges
5. **Create events** with themed contests
6. **Announce ahead** to build excitement

## Database

The game uses SQLite to store:
- User catches
- Fish records
- Statistics
- Timestamps
- Contest history
- Contest participants
- Contest results

Databases:
- `fishing_game.db` - Main game database
- Contest data stored in same database

## Contest Technical Details

### Contest States
1. **NONE** - No contest active
2. **SCHEDULED** - Contest announced, accepting joins
3. **STARTING** - Thread created, waiting to start
4. **ACTIVE** - Contest running, fishing enabled
5. **ENDED** - Contest finished, results posted

### Contest Database Tables
- `contests` - Contest metadata and results
- `contest_participants` - Who joined each contest
- `catches` - Includes contest_id for contest catches

## Troubleshooting

### No fish appearing
- Check `FishingGameAssets/` folder exists
- Verify fish images are present
- Check file permissions

### Can't add fish
- Ensure image exists first
- Check admin permissions
- Verify name matches file

### Contest Issues
- **Can't join**: Check if contest is scheduled
- **Can't fish in thread**: Wait for START announcement
- **Not in leaderboard**: Make sure fishing in contest thread
- **Thread not created**: Check bot permissions

### Stats not updating
- Database may be locked
- Check write permissions
- Restart bot if needed