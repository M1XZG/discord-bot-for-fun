# Troubleshooting Guide

## Common Issues

### Bot Won't Start

#### Symptoms
- No response to commands
- "Bot is not ready" errors
- Python crashes on startup

#### Solutions

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Verify dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Check environment variables**:
   ```bash
   cat .env  # Should contain DISCORD_TOKEN and OPENAI_API_KEY
   ```

4. **Validate bot token**:
   - Go to Discord Developer Portal
   - Regenerate token if needed
   - Update .env file

### OpenAI Errors

#### "Invalid API Key"
```
Solution:
1. Check .env file has correct key
2. Verify key at platform.openai.com
3. Check for extra spaces/quotes
4. Regenerate key if needed
```

#### "Rate limit exceeded"
```
Solution:
1. Reduce max_tokens settings
2. Add cooldowns to commands
3. Check OpenAI usage dashboard
4. Upgrade OpenAI plan if needed
```

#### "Cannot import OpenAI"
```
Solution:
pip install --upgrade openai
# If using old version:
pip install openai==0.28.0
```

### Discord Errors

#### "Missing Permissions"
```
Solution:
1. Re-invite bot with correct permissions
2. Check role hierarchy
3. Verify channel permissions
4. Use !botinfo to check status
```

#### "Cannot create thread"
```
Solution:
1. Check bot has thread permissions
2. Verify not at thread limit
3. Check channel type supports threads
4. Try in different channel
```

#### "Buttons don't show or don't work"
```
Solution:
1. Ensure the bot has permission to send messages and use external emojis in the channel
2. Check that interactions aren't blocked by channel permissions
3. Verify there are no errors about timeouts in logs (RPS and Hi‑Lo use view timeouts)
4. For Hi‑Lo, the Cash Out button is enabled only after completing round 1
```

### Database Issues

#### "Database is locked"
```
Solution:
1. Restart the bot
2. Check file permissions:
   chmod 644 *.db
3. Remove .db-journal files
4. Backup and recreate database
```

#### "No such table"
```
Solution:
1. Delete the .db file
2. Restart bot (recreates tables)
3. Check init_db functions
```

#### "Casino chips not granting on first play"
```
Solution:
1. Ensure Casino feature is enabled (!enable casino)
2. The welcome bonus grants only once per user per guild; check `games_stats.db` → `casino_ledger` for `game='welcome'`
3. Try a different casino command (slots/hilo/roulette) to trigger first play
4. Verify the bot has write permissions on games_stats.db
```

#### "Faucet says already claimed"
```
Solution:
1. Faucet is once every 24 hours (rolling window)
2. Check `last_faucet` column in `casino_chips` for the user
3. Wait until 24h has passed or test with a different account
```

#### "RPS stats not updating"
```
Solution:
1. Confirm games feature is enabled (!features)
2. Check that games_stats.db exists and is writable
3. Look for "Error recording RPS result" in logs
4. Use !rpsstats to verify values per server
```

### Configuration Problems

#### "Config not updating"
```
Solution:
1. Use !reloadconfig command
2. Check JSON syntax:
   python -m json.tool myconfig.json
3. Verify file permissions
4. Check for typos in keys
```

#### "Command not found"
```
Solution:
1. Check required_role setting
2. Verify user has permission
3. Use !help to see available commands
4. Check if module loaded correctly
5. Remember: new or changed commands require a bot restart to register with Discord
```

### Assets

#### "Roulette help image doesn't show"
```
Solution:
1. Confirm file exists at image-assets/roulette-table.png
2. Bot needs permission to attach files in the channel
3. If missing, the command falls back to text-only help
```

## Error Messages

### ChatGPT Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| "Sorry, I couldn't generate a response" | API call failed | Check API key and credits |
| "Token limit exceeded" | Response too long | Reduce max_tokens |
| "Invalid prompt" | Prompt formatting error | Check prompt templates |

### Fishing Game Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| "No fish assets found" | Missing images | Add images to FishingGameAssets/ |
| "You need to wait X seconds" | Cooldown active | Wait or adjust cooldown |
| "Could not add fish" | Config error | Check fish name matches image |

### Thread Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| "Failed to create thread" | Discord API error | Check permissions and limits |
| "Thread not found" | Thread deleted | Create new thread |
| "Not a chat thread" | Wrong thread type | Use in bot-created threads |

## Debugging Steps

### 1. Enable Logging

Add to main.py:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 2. Check Console Output

Look for:
- Startup messages
- Error tracebacks
- API responses
- Database queries

### 3. Test Individual Components

```python
# Test OpenAI
python -c "from openai import OpenAI; print('OK')"

# Test Discord.py
python -c "import discord; print(discord.__version__)"

# Test database
python -c "import sqlite3; print('OK')"
```

### 4. Verify File Structure

```
discord-bot-for-fun/
├── main.py
├── chatgpt.py
├── games.py
├── fishing_game.py
├── .env
├── myconfig.json
├── my_fishing_game_config.json
├── FishingGameAssets/
│   └── (fish images)
├── conversations.db
├── chatgpt_stats.db
├── fishing_game.db
└── games_stats.db
```

## Performance Issues

### Bot is Slow

1. **Check token limits** - Reduce for faster responses
2. **Monitor API calls** - Enable token usage display
3. **Database optimization** - Vacuum databases periodically
4. **Reduce thread retention** - Lower retention period

### High Memory Usage

1. **Clear old threads** - Use cleanup task
2. **Limit conversation history** - Already capped at 20
3. **Restart periodically** - Schedule restarts
4. **Monitor with**: `!botinfo`

## Getting Help

### Information to Provide

When asking for help, include:

1. **Error message** (full traceback)
2. **Bot version** (!botinfo output)
3. **Python version**
4. **Recent changes**
5. **Config settings** (without tokens!)

### Where to Get Help

1. **GitHub Issues**: Bug reports
2. **GitHub Discussions**: Questions
3. **Discord Support**: If available
4. **Documentation**: Check all guides

### Emergency Recovery

If nothing works:

1. **Backup data**:
   ```bash
   cp *.db backup/
   cp my*.json backup/
   ```

2. **Fresh install**:
   ```bash
   git pull
   pip install -r requirements.txt --upgrade
   ```

3. **Reset configs**:
   ```bash
   cp config.json myconfig.json
   cp fishing_game_config.json my_fishing_game_config.json
   ```

4. **Restart bot**:
   ```bash
   python main.py
   ```

## Preventive Measures

### Regular Maintenance

1. **Weekly backups** of databases
2. **Monitor API usage** and costs
3. **Update dependencies** monthly
4. **Review error logs** regularly
5. **Test commands** after changes

### Best Practices

1. **Use version control** for configs
2. **Document custom changes**
3. **Test in dev server first**
4. **Keep dependencies updated**
5. **Monitor Discord/OpenAI status**