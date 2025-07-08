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

## Monitoring & Maintenance

### Daily Tasks

1. **Check bot status**: `!botinfo`
2. **Review active threads**: `!threadages`
3. **Monitor any errors** in console logs

### Weekly Tasks

1. **Review configuration**: `!showconfig`
2. **Check thread cleanup** is working
3. **Update fish cooldowns** if needed
4. **Review token usage** if enabled

### Monthly Tasks

1. **Backup databases**:
   - `conversations.db`
   - `fishing_game.db`
2. **Review and cleanup** old threads
3. **Update documentation** if needed
4. **Check for bot updates**

## Configuration Best Practices

### For Public Servers

```json
{
  "required_role": "Members",
  "token_usage_display": false,
  "chat_thread_retention_days": 3,
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
4. Monitor with `!threadages`

### Database Issues
1. Check file permissions
2. Backup and restart
3. Check disk space
4. Review error logs

## Cost Management

### OpenAI API Costs
- Monitor with token usage display
- Set appropriate limits
- Use shorter retention periods
- Educate users about costs

### Optimization Tips
1. Lower token limits for high-use commands
2. Shorter thread retention
3. Encourage `!endchat` usage
4. Regular thread cleanup