# Mini-Games

## Overview

Simple, fun games for quick entertainment and server engagement.

## Available Games

### 🪙 Coin Flip

Flip a virtual coin and optionally make predictions.

**Command**: `!flip [heads/tails]`

**How it works**:
- Random 50/50 chance
- Optional prediction
- Animated flip message
- Shows result with emoji

**Examples**:
```
!flip           # Just flip
!flip heads     # Predict heads
!flip tails     # Predict tails
```

### 🎲 Dice Roll

Roll a standard 6-sided die with optional guessing.

**Command**: `!dice [1-6]`

**Features**:
- Numbers 1-6
- Optional prediction
- Animated roll effect
- Win/lose feedback

**Examples**:
```
!dice           # Just roll
!dice 6         # Guess 6
!dice 3         # Guess 3
```

### 🎱 Magic 8-Ball

Ask the magic 8-ball for mystical answers.

**Command**: `!8ball <question>`

**Responses include**:
- Positive (Yes, definitely!)
- Negative (Don't count on it)
- Neutral (Ask again later)
- Mysterious (The stars aren't aligned)

**Examples**:
```
!8ball Will I win the lottery?
!8ball Should I eat pizza tonight?
!8ball Is today my lucky day?
```

## Response Types

### Magic 8-Ball Responses

**Positive** 🟢
- It is certain
- Without a doubt
- Yes definitely
- You may rely on it
- Most likely
- Yes
- Signs point to yes

**Negative** 🔴
- Don't count on it
- My reply is no
- My sources say no
- Outlook not so good
- Very doubtful

**Neutral** 🟡
- Reply hazy, try again
- Ask again later
- Better not tell you now
- Cannot predict now
- Concentrate and ask again

## Game Statistics

Currently, mini-games don't track statistics, making them perfect for:
- Quick fun
- Breaking tension
- Decision making
- Server engagement

## Usage Tips

### For Players
1. **Coin flip** for quick decisions
2. **Dice roll** for random selection (1-6)
3. **8-ball** for fun predictions
4. **Combine** with other activities

### For Server Fun
- **Settling debates**: "!flip to decide"
- **Game choices**: "!dice for game mode"
- **Daily questions**: "!8ball question of the day"
- **Event decisions**: Use for randomization

## Command Cooldowns

Mini-games have no cooldowns, allowing:
- Rapid-fire usage
- Group participation
- Spam-free design
- Instant entertainment

## Integration Ideas

### With Other Features
1. **Fishing cooldown**: Play while waiting
2. **Chat threads**: Add randomness to conversations
3. **Decision making**: Server polls and choices

### Custom Uses
- **Giveaways**: !dice for winner selection
- **Role assignment**: !flip for team selection
- **Daily predictions**: !8ball for fun forecasts

## Future Enhancements

Potential additions:
- Win/loss tracking
- Streak counters
- Custom die sizes
- More 8-ball responses
- Betting system
- Tournament mode

## Technical Details

### Implementation
- Pure Python random module
- No external dependencies
- Lightweight execution
- Thread-safe design

### Response Time
- Instant results
- No API calls
- No database queries
- Minimal processing