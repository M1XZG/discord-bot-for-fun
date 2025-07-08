# Fishing Game

## Overview

A complete fishing mini-game with 30+ fish species, leaderboards, and collectibles.

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

## Game Mechanics

### Fish Properties
- **Size**: Measured in centimeters
- **Weight**: Measured in kilograms
- **Points**: Calculated from size and weight
- **Rarity**: All fish have equal catch chance

### Point Calculation
```
Points = (Weight × 10) + Size
```

Maximum points capped at 2× the fish's theoretical maximum.

### Member Catches
- **Chance**: 1 in 250 (configurable)
- **Weight**: 55-140 kg
- **Points**: 1000 + (weight × 2.2)
- **Special**: Shows member's avatar

### Cooldown System
- Default: 30 seconds between casts
- Applies to all users
- Configurable by admins
- Shows remaining time if triggered

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

### Leaderboard Features
- Top 10 anglers displayed
- Medal emojis for top 3
- Personal stats section
- Biggest catch preview

## Admin Configuration

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
2. **Check fishinfo** to learn about catches
3. **Compete** for biggest catches
4. **Collect** all species (use `!fishlist`)

### For Admins
1. **Balance stats** for fair gameplay
2. **Add variety** with new species
3. **Adjust cooldown** based on activity
4. **Create events** (modify catch ratios)

## Database

The game uses SQLite to store:
- User catches
- Fish records
- Statistics
- Timestamps

Database: `fishing_game.db`

## Troubleshooting

### No fish appearing
- Check `FishingGameAssets/` folder exists
- Verify fish images are present
- Check file permissions

### Can't add fish
- Ensure image exists first
- Check admin permissions
- Verify name matches file

### Stats not updating
- Database may be locked
- Check write permissions
- Restart bot if needed