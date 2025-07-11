# Administrator Guide

## Overview

This guide covers all administrative features and best practices for managing the Discord ChatGPT Fun Bot.

## Initial Setup

### 1. Bot Permissions

Ensure the bot has these Discord permissions:
- Send Messages
- Send Messages in Threads
- Create Public Threads
- Manage Threads
- Embed Links
- Attach Files
- Read Message History
- Use External Emojis
- Add Reactions

### 2. Role Configuration

Set up role restrictions:
```
!setrole Members      # Require "Members" role
!setrole @everyone    # Allow everyone (default)
!setrole null         # Remove restriction
```

### 3. Initial Configuration

Review and adjust default settings:
```
!showconfig           # View current config
!reloadconfig         # Reload from file
```

## ChatGPT Management

### Token Limits

Control API usage and response length:

```
!setmaxtokens feelgood 75     # Increase feelgood length
!setmaxtokens query 200       # Longer chat responses
!setmaxtokens joke 50         # Shorter jokes
!showtokens all              # View all limits
```

### Custom Prompts

Customize AI behavior for your community:

```
!setprompt joke generic "Tell a dad joke suitable for all ages"
!setprompt advice targeted "Give advice about {topic} in a friendly tone"
!showprompts joke            # View joke prompts
```

### Thread Management

Configure conversation threads:

```
!setchatretention 3d         # 3 days
!setchatretention 12h        # 12 hours
!setchatretention 1d12h      # 1.5 days
!threadages                  # View all threads
!allthreads                  # List all threads
```

### Token Usage Monitoring

Track OpenAI API usage:
```
!toggletokenusage            # Enable/disable display
```

## Fishing Game Administration

### Game Configuration

Manage the fishing mini-game:

```
!setfishcooldown 1m          # 1 minute cooldown
!setfishcooldown 30s         # 30 seconds
!setfishcooldown 0           # Disable cooldown
!fishcooldown                # Check current setting
```

### Adding Fish Species

Add new fish to the game:

1. Add image to `FishingGameAssets/` folder
2. Use the addfish command:
```
!addfish Goldfish 5 15 0.05 0.2
```
Parameters: Name MinSizeCM MaxSizeCM MinWeightKG MaxWeightKG

### Manual Configuration

Edit `my_fishing_game_config.json`:
```json
{
  "member_catch_ratio": 250,  // 1 in 250 chance
  "cooldown_seconds": 30,     // Cooldown in seconds
  "fish": [...]              // Fish species list
}
```

## Database Management & Statistics

### Admin Scripts

The bot includes several Python scripts for database management and statistics. Run these from the bot directory:

#### ChatGPT Statistics

Monitor ChatGPT usage without storing conversation content:

```bash
# View usage statistics
python3 admin-scripts/chatgpt-usage-stats.py              # Overall stats
python3 admin-scripts/chatgpt-usage-stats.py --leaderboard # Top users
python3 admin-scripts/chatgpt-usage-stats.py --timeline    # Usage patterns
python3 admin-scripts/chatgpt-usage-stats.py --threads     # Thread stats
python3 admin-scripts/chatgpt-usage-stats.py --days 7      # Last 7 days
python3 admin-scripts/chatgpt-usage-stats.py --user Bob    # Specific user

# Manage stats database
python3 admin-scripts/chatgpt-stats-db.py                  # Show info (default)
python3 admin-scripts/chatgpt-stats-db.py --init           # Initialize DB
python3 admin-scripts/chatgpt-stats-db.py --backup         # Create backup
```

**Note**: The stats database (`chatgpt_stats.db`) stores usage metadata only - no conversation content. This data is never automatically deleted and provides long-term usage tracking.

#### Conversation Analysis

Analyze and export conversation data:

```bash
# View conversation statistics
python3 admin-scripts/conversation-stats.py                # Overall stats
python3 admin-scripts/conversation-stats.py --threads      # List threads
python3 admin-scripts/conversation-stats.py --active       # Active only
python3 admin-scripts/conversation-stats.py --commands     # Command usage
python3 admin-scripts/conversation-stats.py --timeline     # Activity timeline

# Export conversations
python3 admin-scripts/dump-conversations.py                # Table format
python3 admin-scripts/dump-conversations.py --csv          # CSV export
python3 admin-scripts/dump-conversations.py --json         # JSON export
python3 admin-scripts/dump-conversations.py -o backup.csv --csv  # To file

# Export specific thread
python3 admin-scripts/conversation-stats.py --export thread_123
```

#### Fishing Game Statistics

View and analyze fishing game data:

```bash
# View fishing statistics
python3 admin-scripts/fishing-stats.py                     # Top 10 catches
python3 admin-scripts/fishing-stats.py --leaderboard       # Player rankings
python3 admin-scripts/fishing-stats.py --biggest           # Biggest catches
python3 admin-scripts/fishing-stats.py --summary           # Overall stats

# Filtering options
python3 admin-scripts/fishing-stats.py --user Alice        # Specific user
python3 admin-scripts/fishing-stats.py --fish Bass         # Specific fish
python3 admin-scripts/fishing-stats.py --sort weight       # Sort by weight
python3 admin-scripts/fishing-stats.py -n 50               # Show 50 records

# Database management
python3 admin-scripts/fishing-stats.py --db ../fishing_game.db  # Different DB path
```

### Database Locations

Default database files:
- `conversations.db` - Stores active conversation threads (auto-cleaned)
- `chatgpt_stats.db` - Permanent usage statistics (never auto-cleaned)
- `fishing_game.db` - Fishing game catches and records

### Backup Procedures

Regular backups are crucial:

```bash
# Quick backup
cp chatgpt_stats.db chatgpt_stats_$(date +%Y%m%d).db
cp fishing_game.db fishing_game_$(date +%Y%m%d).db

# Create stats backup with script
python3 admin-scripts/chatgpt-stats-db.py --backup

# Export conversations before cleanup
python3 admin-scripts/dump-conversations.py --csv -o conversations_$(date +%Y%m%d).csv
```

## Monitoring & Maintenance

### Daily Tasks

1. **Check bot status**: `!botinfo`
2. **Review active threads**: `!threadages`
3. **Monitor any errors** in console logs
4. **Check usage stats**: `python3 admin-scripts/chatgpt-usage-stats.py`

### Weekly Tasks

1. **Review configuration**: `!showconfig`
2. **Check thread cleanup** is working
3. **Update fish cooldowns** if needed
4. **Review token usage** if enabled
5. **Analyze usage patterns**: `python3 admin-scripts/chatgpt-usage-stats.py --timeline`
6. **Check top users**: `python3 admin-scripts/chatgpt-usage-stats.py --leaderboard`

### Monthly Tasks

1. **Backup databases**:
   ```bash
   python3 admin-scripts/chatgpt-stats-db.py --backup
   cp fishing_game.db backups/fishing_game_$(date +%Y%m).db
   ```
2. **Review usage trends**: `python3 admin-scripts/chatgpt-usage-stats.py --days 30`
3. **Export conversation summaries**: `python3 admin-scripts/dump-conversations.py --csv -o monthly_export.csv`
4. **Check database sizes**: 
   ```bash
   ls -lh *.db
   python3 admin-scripts/chatgpt-stats-db.py
   ```
5. **Update documentation** if needed
6. **Check for bot updates**

## Configuration Best Practices

### For Public Servers

```json
{
  "required_role": "Members",
  "token_usage_display": false,
  "chat_thread_retention_days": 3,
  "stats_tracking_enabled": true,
  "max_tokens": {
    "query": 100,
    "joke": 50
  }
}
```

### For Private Servers

```json
{
  "required_role": null,
  "token_usage_display": true,
  "chat_thread_retention_days": 14,
  "stats_tracking_enabled": true,
  "max_tokens": {
    "query": 300,
    "joke": 100
  }
}
```

## Command Reference

### Configuration Commands
- `!showconfig` - Display configuration
- `!reloadconfig` - Reload from file
- `!adminhelp` - Show admin commands

### Role Management
- `!showrole` - Show required role
- `!setrole <role>` - Set required role

### ChatGPT Settings
- `!setmaxtokens <cmd> <value>` - Set token limit
- `!setprompt <cmd> <variant> <text>` - Set prompt
- `!showtokens <cmd>` - Show token settings
- `!showprompts <cmd>` - Show prompts
- `!toggletokenusage` - Toggle usage display

### Thread Management
- `!setchatretention <time>` - Set retention
- `!allthreads` - List all threads
- `!threadages` - Show thread ages

### Fishing Administration
- `!fishadmin` - Show fishing admin help
- `!addfish` - Add new fish species
- `!setfishcooldown <time>` - Set cooldown
- `!fishcooldown` - Show cooldown
- `!fplayer` - Test member catch

## Security Considerations

1. **API Keys**: Never share or commit `.env` file
2. **Role Restrictions**: Use for public servers
3. **Token Limits**: Prevent API abuse
4. **Thread Retention**: Balance memory vs. cost
5. **Regular Backups**: Backup databases
6. **Stats Privacy**: Usage stats contain user IDs but no message content

## Troubleshooting

### Bot Not Responding
1. Check bot status: `!botinfo`
2. Verify permissions
3. Check role restrictions
4. Review error logs

### High API Usage
1. Reduce token limits
2. Shorten retention period
3. Enable usage display
4. Monitor with: `python3 admin-scripts/chatgpt-usage-stats.py --timeline`
5. Check heavy users: `python3 admin-scripts/chatgpt-usage-stats.py --leaderboard`

### Database Issues
1. Check file permissions
2. Backup and restart
3. Check disk space
4. Review error logs
5. Verify with: `python3 admin-scripts/chatgpt-stats-db.py`

## Cost Management

### OpenAI API Costs
- Monitor with token usage display
- Track with: `python3 admin-scripts/chatgpt-usage-stats.py`
- Set appropriate limits
- Use shorter retention periods
- Educate users about costs

### Optimization Tips
1. Lower token limits for high-use commands
2. Shorter thread retention
3. Encourage `!endchat` usage
4. Regular thread cleanup
5. Monitor usage patterns with admin scripts