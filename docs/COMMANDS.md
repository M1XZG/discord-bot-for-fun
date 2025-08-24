# Command Reference

## User Commands

### 🤖 ChatGPT Commands

| Command | Description | Usage | Aliases |
|---------|-------------|-------|---------|
| `!feelgood` | Get an uplifting message | `!feelgood [recipient]` | - |
| `!joke` | Get a family-friendly joke | `!joke [topic]` | - |
| `!compliment` | Give a wholesome compliment | `!compliment [@user] [topic]` | - |
| `!advice` | Get wholesome advice | `!advice [topic]` | - |
| `!inspo` | Get an inspirational quote | `!inspo [recipient]` | - |
| `!q` | Quick ChatGPT question | `!q <your question>` | `!quick`, `!qask` |
| `!image` | Generate an AI image | `!image <description>` | - |
| `!chat` | Start a conversation thread | `!chat <message>` | `!ask`, `!query` |
| `!endchat` | End your chat thread | `!endchat` | - |
| `!mythreads` | List your active threads | `!mythreads` | - |

### 🎣 Fishing Game Commands

| Command | Description | Usage | Aliases |
|---------|-------------|-------|---------|
| `!fish` | Go fishing! | `!fish` | `!f`, `!cast`, `!fishing` |
| `!fishstats` | View leaderboard and stats | `!fishstats [@user]` | - |
| `!fishlist` | List all fish species | `!fishlist` | - |
| `!fishinfo` | Get info about a fish | `!fishinfo <FishName>` | - |
| `!fishhelp` | Show fishing help | `!fishhelp` | `!fishinghelp` |

### 🏆 Fishing Contest Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `!joincontest` | Join upcoming fishing contest | `!joincontest` |
| `!contestinfo` | Show current/next contest info | `!contestinfo` |
| `!contestlb` | Show live contest leaderboard | `!contestlb` |
| `!pastcontests` | List past fishing contests | `!pastcontests` |
| `!contestresults` | Show specific contest results | `!contestresults <id>` |
| `!contesthelp` | Show contest help | `!contesthelp` |

### 🎮 Mini-Games

| Command | Description | Usage |
|---------|-------------|-------|
| `!flip` | Flip a coin | `!flip` |
| `!roll` | Roll dice | `!roll [NdX]` or `!roll [count] [sides]` |
| `!8ball` | Ask the magic 8-ball | `!8ball <question>` |
| `!rps` | Rock-Paper-Scissors vs bot or challenge a user | `!rps` or `!rps <rock|paper|scissors>` or `!rps @user` |
| `!rpsstats` | View RPS stats (per server) | `!rpsstats [@user]` |
| `!choose` | Randomly pick from options | `!choose a | b | c` |

### ℹ️ Information Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `!help` | Show all commands | `!help [command]` |
| `!botinfo` | Show bot information | `!botinfo` |
| `!serverinfo` | Show server information | `!serverinfo` |
| `!userinfo` | Show user information | `!userinfo [@user]` |

## Admin Commands

### 🔧 Configuration Management

| Command | Description | Usage |
|---------|-------------|-------|
| `!showconfig` | Display configuration | `!showconfig` |
| `!reloadconfig` | Reload configuration | `!reloadconfig` |
| `!showrole` | Show required role | `!showrole` |
| `!setrole` | Set required role | `!setrole <role_name>` |

### 💬 ChatGPT Configuration

| Command | Description | Usage |
|---------|-------------|-------|
| `!setmaxtokens` | Set token limit | `!setmaxtokens <command> <value>` |
| `!setprompt` | Set custom prompt | `!setprompt <command> <variant> <prompt>` |
| `!showtokens` | Show token settings | `!showtokens <command>` |
| `!showprompts` | Show prompts | `!showprompts <command>` |
| `!toggletokenusage` | Toggle token display | `!toggletokenusage` |

### 🧵 Thread Management

| Command | Description | Usage |
|---------|-------------|-------|
| `!setchatretention` | Set thread retention | `!setchatretention <time>` |
| `!allthreads` | List all threads | `!allthreads` |
| `!threadages` | Show thread ages | `!threadages` or `!threadage` |

### 🎣 Fishing Administration

| Command | Description | Usage |
|---------|-------------|-------|
| `!fishadmin` | Show admin commands | `!fishadmin` |
| `!addfish` | Add new fish species | `!addfish <name> <minSize> <maxSize> <minWeight> <maxWeight>` |
| `!setfishcooldown` | Set fishing cooldown | `!setfishcooldown <time>` |
| `!fishcooldown` | Show cooldown setting | `!fishcooldown` |
| `!fplayer` | Test member catching | `!fplayer` |

### 🏆 Contest Administration

| Command | Description | Usage |
|---------|-------------|-------|
| `!startcontest` | Schedule a fishing contest | `!startcontest <duration> <delay>` |
| `!cancelcontest` | Cancel current contest | `!cancelcontest` |

### 🛠️ System Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `!adminhelp` | Show admin commands | `!adminhelp` |

## Command Examples

### ChatGPT Examples
```
!feelgood @username
!joke programming
!compliment @friend about their helpfulness
!q What's the weather like on Mars?
!image a sunset over mountains with a lake
!chat Tell me about space exploration
```

### Fishing Examples
```
!fish
!fishstats @friend
!fishinfo Bass
!setfishcooldown 45s
!addfish Trout 15 50 0.3 2.5
```

### Contest Examples
```
!startcontest 10m 5m     # 10-min contest in 5 minutes
!startcontest 30m 1h     # 30-min contest in 1 hour
!joincontest             # Join the upcoming contest
!contestlb               # Check live standings
!contestresults 3        # View contest #3 results
!cancelcontest           # Admin: cancel contest
```

### Configuration Examples
```
!setrole Members
!setmaxtokens joke 100
!setchatretention 3d12h
!setprompt joke generic Tell me a dad joke.
```

### Contest Commands
- `!startcontest [minutes]` - (Admin) Start a fishing contest
- `!endcontest` / `!cancelcontest` / `!stopcontest` - (Admin) End contest early
- `!conteststatus` - Check if a contest is active
- `!joincontest` - Learn how to participate in contests
- `!contesthistory` - View past contest results
- `!contestinfo <id>` - View detailed results of a specific