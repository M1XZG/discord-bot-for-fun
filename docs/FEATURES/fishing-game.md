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

### Hidden / Admin-Oriented (Not shown in standard help)
- **`!fishreload`** – Reload fishing configuration from disk (admin)
- **`!fishdebug`** – Show loaded rarities, counts and config diagnostics (admin)

### Contest Commands
- **`!contesthistory`** - View past fishing contest results
- **`!contestinfo <contest_id>`** - View detailed results from a specific contest

## Game Features

### 🌟 Rarity System
Fish are categorized into eight rarity tiers that affect catch rates (weights shown are relative selection weights, lower = rarer):

| Rarity | Weight | Color | Examples |
|--------|--------|-------|----------|
| **Mythic** | 0.75 | Dark Orange | Helios-Sunfish |
| **Ultra-Legendary** | 0.5 | Deep Pink | Diamond-Ring |
| **Legendary** | 1 | Gold | Blue-Whale, Clockwork-Carp |
| **Epic** | 5 | Purple | Great-White-Shark, Hammerhead-Shark, Narwhal, Lavender-Braid-Eel, DevOps-Ducky |
| **Rare** | 15 | Blue | Marlin, Sailfish, Barracuda, Tarpon, Mahi-Mahi, Starfall-Salmon, Wahoo |
| **Uncommon** | 30 | Green | Sea-Bass, Smallmouth-Bass, Bonefish, Comfy-Catfish, Tuna |
| **Common** | 50 | Gray | Blue-Tang, Butterfly-fish, Clown-Fish, Crab, Lobster, Parrot-Fish, Perch, Sea-Cucumber, Seahorse, Shrimp, Starfish, Sea-Urchin, Button-Shield-Minnow, Tangled-Headset |
| **Junk** | 60 | Brown | Stinky-Boot, Worn-Trainers |

> The game internally normalizes weights; lower weight = rarer. Mythic sits between ultra‑legendary and legendary in rarity (rarer than legendary but slightly more common than ultra-legendary). Mythic fish currently award special point multipliers in catches.

### 📋 Fish Descriptions
Each fish includes a unique description that adds flavor to your catch, like:
- *"The apex predator of the ocean, both feared and respected worldwide."* (Great White Shark)
- *"A tiny marine marvel where males carry and birth the young."* (Seahorse)
- *"A priceless engagement ring lost at sea. Someone's heartbreak is your treasure!"* (Diamond Ring)
- *"A single rotting boot filled with mysterious sludge. Even the fish avoid this putrid footwear."* (Stinky-Boot)

### 💎 Mythic & Ultra-Legendary Catches
These tiers produce the most dramatic announcements:

**Mythic** – Currently includes the radiant Helios-Sunfish.

**Ultra-Legendary** – Includes special treasures like:
- **Diamond-Ring**: Despite being tiny can mysteriously weigh far more than expected.

> Both Mythic and Ultra-Legendary receive very large point multipliers. Contest multipliers stack.

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
  "rarity_tiers": {               // Rarity configuration (example weights)
    "mythic": { "weight": 0.75, "color": "#FF8C00" },
    "ultra-legendary": { "weight": 0.5, "color": "#FF1493" },
    "legendary": { "weight": 1, "color": "#FFD700" },
    "epic": { "weight": 5, "color": "#9B59B6" },
    "rare": { "weight": 15, "color": "#3498DB" },
    "uncommon": { "weight": 30, "color": "#2ECC40" },
    "common": { "weight": 50, "color": "#7F8C8D" },
    "junk": { "weight": 60, "color": "#8B4513" }
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

## Complete Fish List (Current Build)

The live configuration includes both classic species and new additions. For a visual catalog with images, see the separate [Fish Catalog](fishing-fish-catalog.md).

### Mythic
- Helios-Sunfish

### Ultra-Legendary
- Diamond-Ring

### Legendary
- Blue-Whale
- Clockwork-Carp

### Epic
- Great-White-Shark
- Hammerhead-Shark
- Narwhal
- Lavender-Braid-Eel
- DevOps-Ducky

### Rare
- Barracuda
- Mahi-Mahi
- Marlin
- Sailfish
- Tarpon
- Wahoo
- Starfall-Salmon

### Uncommon
- Sea-Bass
- Smallmouth-Bass
- Bonefish
- Comfy-Catfish
- Tuna

### Common
- Blue-Tang
- Butterfly-fish
- Clown-Fish
- Crab
- Lobster
- Parrot-Fish
- Perch
- Sea-Cucumber
- Seahorse
- Shrimp
- Starfish
- Sea-Urchin
- Button-Shield-Minnow
- Tangled-Headset

### Junk
- Stinky-Boot
- Worn-Trainers

Use `!fishlist` for detailed size/weight ranges.

---

*Happy Fishing! 🎣*