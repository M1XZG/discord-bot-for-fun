# Configuration Guide

## Configuration Files

The bot uses several configuration files:

### myconfig.json

Main configuration file with the following structure:

```json
{
  "required_role": null,
  "token_usage_display": false,
  "chat_thread_retention_days": 7,
  "max_tokens": {
    "feelgood": 50,
    "joke": 75,
    "compliment": 50,
    "advice": 100,
    "inspo": 50,
    "query": 150,
    "image": 50
  },
  "prompts": {
    "feelgood": {
      "generic": "Write a 50-word uplifting message...",
      "targeted": "..."
    }
  }
}
```

### my_fishing_game_config.json

Fishing game configuration:

```json
{
  "member_catch_ratio": 250,
  "cooldown_seconds": 30,
  "fish": [
    {
      "name": "Bass",
      "min_size_cm": 20,
      "max_size_cm": 60,
      "min_weight_kg": 0.5,
      "max_weight_kg": 5
    }
  ]
}
```

## Configuration Options

### General Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `required_role` | string/null | null | Role required to use bot commands |
| `token_usage_display` | boolean | false | Show OpenAI token usage |
| `chat_thread_retention_days` | number | 7 | Days to keep chat threads |

### Token Limits

Configure max tokens for each command type:

| Command | Default | Description |
|---------|---------|-------------|
| `feelgood` | 50 | Feel-good messages |
| `joke` | 75 | Jokes |
| `compliment` | 50 | Compliments |
| `advice` | 100 | Advice |
| `inspo` | 50 | Inspirational quotes |
| `query` | 150 | General queries |
| `image` | 50 | Image descriptions |

### Custom Prompts

You can customize prompts for each command:

```json
"prompts": {
  "joke": {
    "generic": "Tell a family-friendly joke.",
    "targeted": "Tell a family-friendly joke about {topic}."
  }
}
```

## Runtime Configuration

### Admin Commands

- `!reloadconfig` - Reload configuration from file
- `!showconfig` - Display current configuration
- `!setmaxtokens <command> <value>` - Adjust token limits
- `!setprompt <command> <variant> <prompt>` - Set custom prompts
- `!toggletokenusage` - Toggle token usage display
- `!setchatretention <time>` - Set thread retention (e.g., 1d, 12h)

### Fishing Game Settings

- `!setfishcooldown <time>` - Set fishing cooldown
- `!addfish <name> <min_size> <max_size> <min_weight> <max_weight>` - Add fish species

## Environment Variables

Required in `.env` file:

```env
DISCORD_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
```

## Best Practices

1. **Backup configs** before making changes
2. **Test changes** in a development server first
3. **Monitor token usage** to control costs
4. **Set appropriate retention** for chat threads
5. **Configure role restrictions** for public servers