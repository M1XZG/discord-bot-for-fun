# 🎣 Fishing Game Documentation

The fishing game is a fun, interactive game where players can catch various sea creatures and compete for high scores.

## Table of Contents
- [Basic Commands](#basic-commands)
- [Game Features](#game-features)
- [Fishing Mechanics](#fishing-mechanics)
- [Contests](#contests)
- [Configuration](#configuration)
- [Admin Commands](#admin-commands)

## Basic Commands

### Player Commands
- **`!fish`** (aliases: `!f`, `!cast`, `!fishing`) - Cast your line and try to catch something!
- **`!fishstats [@user]`** - View the fishing leaderboard and your or another player's statistics
- **`!fishlist`** - Display all available fish with their stats and rarity
- **`!fishinfo <fish_name>`** - Show detailed information and image for a specific fish
- **`!fishconditions`** (alias: `!conditions`) - Check all available fish organized by rarity
- **`!fishhelp`** (alias: `!fishinghelp`) - Show all fishing commands

### Contest Commands
- **`!contesthistory`** - View past fishing contest results
- **`!contestinfo <contest_id>`** - View detailed results from a specific contest

## Game Features

### 🌟 Rarity System
Fish are categorized into seven rarity tiers that affect catch rates:
- **Ultra-Legendary** (Deep Pink) - Rarest of all (0.5% weight) - Diamond Ring
- **Legendary** (Gold) - Extremely rare (1% weight) - Blue Whale
- **Epic** (Purple) - Very rare (5% weight) - Great White Shark, Hammerhead Shark, Narwhal
- **Rare** (Blue) - Rare catches (15% weight) - Marlin, Sailfish, Barracuda, Tarpon
- **Uncommon** (Green) - Less common (30% weight) - Sea-Bass, Smallmouth-Bass, Bonefish
- **Common** (Gray) - Most fish (50% weight) - Most standard fish
- **Junk** (Brown) - Trash items (60% weight) - Stinky-Boot, Worn-Trainers

### 📋 Fish Descriptions
Each fish includes a unique description that adds flavor to your catch, like:
- *"The apex predator of the ocean, both feared and respected worldwide."* (Great White Shark)
- *"A tiny marine marvel where males carry and birth the young."* (Seahorse)
- *"A priceless engagement ring lost at sea. Someone's heartbreak is your treasure!"* (Diamond Ring)
- *"A single rotting boot filled with mysterious sludge. Even the fish avoid this putrid footwear."* (Stinky-Boot)

### 💎 Ultra-Legendary Catches
The rarest tier includes special treasures:
- **Diamond Ring**: Despite being tiny (2-5cm), can mysteriously weigh up to 50kg!
  - Minimum points: ~2 (light ring)
  - Maximum points: ~505 (heavy treasure)
  - With contest bonus: up to 757 points!

### 🎲 Catch Variety System
The game uses smart randomization to ensure variety:
- Tracks your last 10 catches to avoid repetition
- Uses weighted selection based on rarity
- 15% chance to catch nothing (shows consolation message with No-Fish.png)
- 1 in 50 chance to "catch" a server member instead of a fish!

### 🗑️ Junk Catches
Sometimes you'll pull up trash instead of fish:
- **Stinky-Boot**: Weight ranges from 0.3-15kg for variable points
- **Worn-Trainers**: Old sneakers with weights from 0.4-20kg
- These items have humorous descriptions and count towards your stats!

## Fishing Mechanics

### Points Calculation
Points are calculated based on both size and weight:
```
Base Points = (weight_kg × 10) + size_cm
```
Maximum points are capped at 2× the fish's theoretical maximum to prevent outliers.

### Cooldowns
- Default: 30 seconds between casts
- Cooldowns are **disabled** during contests
- Admins can adjust or disable cooldowns
- Shows exact time remaining if you try to fish too soon

### Special Catches
- **Server Members**: Occasionally you might "catch" another server member!
  - Worth 1000+ points
  - Shows their avatar
  - Weight: 55-140 kg
  - Still possible during contests!
- **No Catch**: Sometimes the fish just aren't biting
  - 15% chance
  - Shows random consolation message
  - Displays No-Fish.png if available
  - No points or database entry

## Contests

### Contest Features
- **Dedicated Thread**: Each contest gets its own thread in the channel
- **No Cooldowns**: Fish as fast as you want during contests
- **50% Point Bonus**: All catches worth 1.5x points
- **Auto-Duration**: Contests run for a set time (default 5 minutes)
- **Live Updates**: See catches in real-time in the thread
- **Final Results**: Automatic leaderboard when contest ends
- **Thread Management**: Threads are locked and archived after contests

### Starting a Contest
Admins can start a contest with:
```
!startfishingcontest [duration_minutes] [thread_name]
```

Example: `!startfishingcontest 10 "Weekend Fishing Tournament"`

### Contest Flow
1. Admin starts contest → Thread created with "[ACTIVE]" tag
2. "GET READY!" countdown (10 seconds)
3. "🎣 START FISHING!" → Contest begins
4. Players fish in the thread with no cooldowns
5. Contest ends → Final results posted automatically
6. Thread locked and archived for history

## Configuration

The game uses `my_fishing_game_config.json` for customization:

```json
{
  "member_catch_ratio": 50,      // 1 in X chance to catch a member
  "cooldown_seconds": 30,         // Seconds between casts
  "no_catch_chance": 0.15,        // Chance to catch nothing
  "rarity_tiers": {               // Rarity configuration
    "ultra-legendary": {
      "weight": 0.5,              // Extremely rare
      "color": "#FF1493"          // Deep Pink
    },
    "legendary": {
      "weight": 1,                // Relative catch weight
      "color": "#FFD700"          // Gold color for embeds
    },
    "epic": {
      "weight": 5,
      "color": "#9B59B6"          // Purple
    },
    "rare": {
      "weight": 15,
      "color": "#3498DB"          // Blue
    },
    "uncommon": {
      "weight": 30,
      "color": "#2ECC40"          // Green
    },
    "common": {
      "weight": 50,
      "color": "#7F8C8D"          // Gray
    },
    "junk": {
      "weight": 60,
      "color": "#8B4513"          // Brown
    }
  },
  "fish": [...]                   // Fish data array
}
```

### Fish Data Structure
```json
{
  "name": "Great-White-Shark",
  "min_size_cm": 300,
  "max_size_cm": 600,
  "min_weight_kg": 680,
  "max_weight_kg": 2300,
  "rarity": "epic",
  "description": "The apex predator of the ocean, both feared and respected worldwide."
}
```

## Admin Commands

### Configuration Commands
- **`!setfishcooldown <time>`** - Set cooldown (e.g., "30s", "5m", "0" to disable)
- **`!fishcooldown`** - Display current cooldown setting
- **`!addfish <name> <min_size> <max_size> <min_weight> <max_weight> <rarity> "description"`** - Add new fish species

### Contest Management
- **`!startfishingcontest [duration] [name]`** - Start a fishing contest
- **`!stopfishingcontest`** - Force end an active contest

### Testing Commands
- **`!fplayer`** - Test catching a server member

### Examples
```
!addfish Goldfish 10 25 0.1 0.5 common "A classic pet fish that somehow ended up in open water."
!setfishcooldown 45s
!startfishingcontest 15 "Friday Night Fish Frenzy"
```

## Tips for Players

1. **Check conditions**: Use `!fishconditions` to see all available fish by rarity
2. **Join contests**: No cooldowns and 50% bonus points!
3. **Check the leaderboard**: Use `!fishstats` to see where you rank
4. **Learn about fish**: Use `!fishinfo` to study your catches
5. **Variety is key**: The game prevents repeat catches for better variety
6. **Don't give up**: Even junk catches earn points!

## Database Storage

All catches are stored in `fishing_game.db` with:
- User information
- Catch details (type, name, weight, size, points)
- Timestamps
- Contest associations
- Rarity tracking

This allows for persistent leaderboards, statistics tracking, and contest history.

## Asset Requirements

### Fish Images
- **Location**: `FishingGameAssets/` folder
- **Formats**: PNG, JPG, JPEG, GIF
- **Naming**: Must match fish name exactly (case-insensitive)
  - Example: `Great-White-Shark.png` for "Great-White-Shark"
- **Special Images**:
  - `No-Fish.png` - Shown when nothing is caught
  - Member avatars - Automatically fetched when catching members

## Complete Fish List

The game includes 30+ catchable items across all rarity tiers:

### Ultra-Legendary (0.5% chance)
- Diamond-Ring (lost treasure worth a fortune!)

### Legendary (1% chance)
- Blue-Whale (up to 150,000kg!)

### Epic (5% chance)
- Great-White-Shark
- Hammerhead-Shark
- Narwhal

### Rare (15% chance)
- Barracuda
- Mahi-Mahi
- Marlin
- Sailfish
- Tarpon
- Wahoo

### Uncommon (30% chance)
- Blue-Shark
- Bonefish
- Sea-Bass
- Smallmouth-Bass
- Tuna

### Common (50% chance)
- Blue-Tang
- Butterfly-fish
- Clown-Fish
- Crab
- Lobster
- Parrot-Fish
- Pearch
- Sea-Cucumber
- Seahorse
- Shrimp
- Starfish
- Sea-Urchin

### Junk (60% chance)
- Stinky-Boot
- Worn-Trainers

Use `!fishlist` to see detailed stats for all fish!

---

*Happy Fishing! 🎣*