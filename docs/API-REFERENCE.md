# API Reference

## Module Structure

### Main Modules

#### main.py
Entry point and core bot functionality.

**Key Functions**:
- `load_config()` - Load configuration from JSON
- `save_config()` - Save configuration to JSON
- `is_admin()` - Check admin permissions
- `has_required_role()` - Check role requirements

**Global Variables**:
- `bot` - Discord bot instance
- `config` - Configuration dictionary
- `prompts` - Prompt templates
- `max_tokens` - Token limits

#### chatgpt.py
ChatGPT integration and conversation management.

**Key Functions**:
- `set_globals()` - Initialize module globals
- `get_chatgpt_response()` - Get AI response
- `init_conversation_db()` - Initialize database
- `save_conversation()` - Save chat history
- `load_conversation()` - Load chat history
- `delete_thread_data()` - Clean up thread
- `format_time_duration()` - Format time display
- `setup_cleanup_task()` - Start cleanup task

**Classes**:
- Uses OpenAI client: `OpenAI(api_key=key)`

#### fishing_game.py
Complete fishing game implementation.

**Key Functions**:
- `init_fishing_db()` - Initialize database
- `record_catch()` - Save catch record
- `get_fish_list()` - Get available fish
- `format_time_display()` - Format cooldown
- `check_cooldown()` - Check user cooldown
- `fish_command()` - Main fishing logic
- `setup_fishing()` - Register commands

**Global Variables**:
- `FISH_CONFIG` - Fish configuration
- `member_catch_ratio` - Member catch chance
- `cooldown_seconds` - Fishing cooldown
- `last_fish_time` - Cooldown tracking

#### bot_games.py
Simple mini-games implementation.

**Functions**:
- `flip_coin()` - Coin flip game
- `roll_dice()` - Dice roll game
- `magic_8_ball()` - 8-ball responses

## Database Schemas

### conversations.db

**conversations table**:
```sql
CREATE TABLE conversations (
    thread_id TEXT PRIMARY KEY,
    messages TEXT NOT NULL,
    last_updated DATETIME NOT NULL
);
```

**thread_meta table**:
```sql
CREATE TABLE thread_meta (
    thread_id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    created_at DATETIME NOT NULL
);
```

### fishing_game.db

**catches table**:
```sql
CREATE TABLE catches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    user_name TEXT,
    catch_type TEXT, -- 'fish' or 'user'
    catch_name TEXT,
    weight REAL,
    points INTEGER,
    timestamp DATETIME
);
```

## Configuration Schemas

### myconfig.json
```typescript
{
  required_role: string | null,
  token_usage_display: boolean,
  chat_thread_retention_days: number,
  max_tokens: {
    [command: string]: number
  },
  prompts: {
    [command: string]: {
      [variant: string]: string
    }
  }
}
```

### my_fishing_game_config.json
```typescript
{
  member_catch_ratio: number,
  cooldown_seconds: number,
  fish: Array<{
    name: string,
    min_size_cm: number,
    max_size_cm: number,
    min_weight_kg: number,
    max_weight_kg: number
  }>
}
```

## OpenAI Integration

### Chat Completion
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=150,
    temperature=0.8
)
```

### Image Generation
```python
response = client.images.generate(
    prompt="A sunset over mountains",
    n=1,
    size="1024x1024"
)
```

## Discord.py Events

### Used Events
- `on_ready` - Bot startup
- `on_message` - Message handling
- `on_command_error` - Error handling

### Custom Events
- Thread cleanup task (async loop)
- Conversation monitoring

## Error Handling

### Standard Pattern
```python
try:
    # Operation
except SpecificException as e:
    print(f"Specific error: {e}")
    # Handle gracefully
except Exception as e:
    print(f"Unexpected error: {e}")
    # Fallback behavior
```

### Database Connections
```python
with get_db_connection() as conn:
    c = conn.cursor()
    # Database operations
    conn.commit()
```

## Async Patterns

### Command Structure
```python
@bot.command(help="Description", aliases=["alt"])
async def command_name(ctx, *, parameter: str = None):
    async with ctx.typing():
        # Long operation
    await ctx.send(response)
```

### Thread Safety
- Use `asyncio.sleep()` for delays
- Avoid blocking operations
- Use `async with` for resources

## Extension Points

### Adding Commands
1. Add to appropriate module
2. Use `@bot.command()` decorator
3. Include help text
4. Handle errors gracefully

### Adding Fish Species
1. Add image to assets folder
2. Update configuration
3. No code changes needed

### Custom Prompts
1. Modify prompts in config
2. Use placeholders: `{topic}`
3. Test thoroughly

## Performance Considerations

### Database
- Use indexes on frequent queries
- Connection pooling via context managers
- Parameterized queries for safety

### Discord API
- Respect rate limits
- Use embeds for rich content
- Chunk long messages

### OpenAI API
- Cache responses where appropriate
- Monitor token usage
- Set reasonable limits