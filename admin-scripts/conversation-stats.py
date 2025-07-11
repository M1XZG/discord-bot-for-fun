import os
import sys
import sqlite3
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ─── Parse Command Line Arguments ──────────────────────────────────────────────

parser = argparse.ArgumentParser(
    description='💬 Analyze ChatGPT conversation statistics from the database',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  %(prog)s                    # Show overall statistics
  %(prog)s --threads         # List all threads
  %(prog)s --active          # Show only active threads
  %(prog)s --user @username  # Show threads by specific user
  %(prog)s --days 7          # Show threads from last 7 days
  %(prog)s --commands        # Show command usage statistics
  %(prog)s --timeline        # Show usage timeline
  %(prog)s --verbose         # Show detailed thread info
  
Database tables analyzed: conversations, thread_meta
    """
)

parser.add_argument(
    '-t', '--threads',
    action='store_true',
    help='List all conversation threads'
)

parser.add_argument(
    '-a', '--active',
    action='store_true',
    help='Show only active threads'
)

parser.add_argument(
    '-u', '--user',
    type=str,
    help='Filter by username or user ID'
)

parser.add_argument(
    '-d', '--days',
    type=int,
    help='Show threads from last N days'
)

parser.add_argument(
    '-c', '--commands',
    action='store_true',
    help='Show ChatGPT command usage statistics'
)

parser.add_argument(
    '--timeline',
    action='store_true',
    help='Show conversation timeline by day/hour'
)

parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='Show detailed information'
)

parser.add_argument(
    '--db',
    type=str,
    default='conversations.db',
    help='Path to database file (default: conversations.db)'
)

parser.add_argument(
    '--export',
    type=str,
    help='Export thread messages to file (specify thread ID)'
)

args = parser.parse_args()

# ─── Check Database ────────────────────────────────────────────────────────────

if not os.path.exists(args.db):
    print(f"❌ Database not found: {args.db}", file=sys.stderr)
    print("💡 Make sure you're in the bot directory or specify --db path", file=sys.stderr)
    sys.exit(1)

# ─── Connect to Database ───────────────────────────────────────────────────────

try:
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
except sqlite3.Error as e:
    print(f"❌ Database error: {e}", file=sys.stderr)
    sys.exit(1)

# ─── Helper Functions ──────────────────────────────────────────────────────────

def format_date(timestamp):
    """Format timestamp to readable date"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return str(timestamp)

def get_thread_age(timestamp):
    """Calculate age of thread"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.fromtimestamp(timestamp)
        age = datetime.now() - dt.replace(tzinfo=None)
        
        if age.days > 0:
            return f"{age.days}d {age.seconds//3600}h"
        elif age.seconds >= 3600:
            return f"{age.seconds//3600}h {(age.seconds%3600)//60}m"
        else:
            return f"{age.seconds//60}m"
    except:
        return "Unknown"

def parse_messages(messages_json):
    """Parse JSON messages and extract information"""
    try:
        messages = json.loads(messages_json)
        user_messages = [m for m in messages if m.get('role') == 'user']
        assistant_messages = [m for m in messages if m.get('role') == 'assistant']
        
        total_length = sum(len(m.get('content', '')) for m in messages)
        commands = []
        
        # Extract commands from user messages
        for msg in user_messages:
            content = msg.get('content', '')
            if content.startswith('!'):
                cmd = content.split()[0]
                commands.append(cmd)
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_length': total_length,
            'commands': commands
        }
    except:
        return {
            'total_messages': 0,
            'user_messages': 0,
            'assistant_messages': 0,
            'total_length': 0,
            'commands': []
        }

# ─── Export Thread ─────────────────────────────────────────────────────────────

if args.export:
    cursor.execute("SELECT messages FROM conversations WHERE thread_id = ?", (args.export,))
    result = cursor.fetchone()
    
    if result:
        try:
            messages = json.loads(result['messages'])
            output_file = f"thread_{args.export}_export.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Thread Export: {args.export}\n")
                f.write("="*60 + "\n\n")
                
                for msg in messages:
                    role = msg.get('role', 'unknown').upper()
                    content = msg.get('content', '')
                    f.write(f"[{role}]:\n{content}\n\n" + "-"*40 + "\n\n")
            
            print(f"✅ Thread exported to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to export thread: {e}")
    else:
        print(f"❌ Thread not found: {args.export}")
    sys.exit(0)

# ─── Overall Statistics ────────────────────────────────────────────────────────

# Get basic statistics
cursor.execute("""
    SELECT 
        COUNT(DISTINCT c.thread_id) as total_threads,
        COUNT(DISTINCT tm.creator_id) as unique_users,
        MIN(tm.created_at) as first_thread,
        MAX(c.last_updated) as last_activity
    FROM conversations c
    LEFT JOIN thread_meta tm ON c.thread_id = tm.thread_id
""")

stats = cursor.fetchone()

print("💬 Conversation Database Statistics")
print("─" * 50)
print(f"Total threads:       {stats['total_threads']}")
print(f"Unique users:        {stats['unique_users'] or 'Unknown'}")
print(f"First thread:        {format_date(stats['first_thread']) if stats['first_thread'] else 'Unknown'}")
print(f"Last activity:       {format_date(stats['last_activity']) if stats['last_activity'] else 'Unknown'}")

# Get message statistics
cursor.execute("SELECT messages, last_updated FROM conversations")
all_threads = cursor.fetchall()

total_messages = 0
total_user_messages = 0
total_assistant_messages = 0
total_chars = 0
all_commands = []
active_threads = 0
retention_days = 7  # Default retention

for thread in all_threads:
    info = parse_messages(thread['messages'])
    total_messages += info['total_messages']
    total_user_messages += info['user_messages']
    total_assistant_messages += info['assistant_messages']
    total_chars += info['total_length']
    all_commands.extend(info['commands'])
    
    # Check if thread is active (updated in last retention period)
    age = get_thread_age(thread['last_updated'])
    if 'd' not in age or int(age.split('d')[0]) < retention_days:
        active_threads += 1

print(f"Active threads:      {active_threads} (< {retention_days} days)")
print(f"Total messages:      {total_messages:,}")
print(f"User messages:       {total_user_messages:,}")
print(f"Assistant replies:   {total_assistant_messages:,}")
print(f"Total characters:    {total_chars:,}")
print(f"Avg thread length:   {total_messages // stats['total_threads'] if stats['total_threads'] > 0 else 0} messages")
print()

# ─── Command Usage Statistics ──────────────────────────────────────────────────

if args.commands or not any([args.threads, args.active, args.timeline]):
    if all_commands:
        print("🎯 Command Usage")
        print("─" * 50)
        
        cmd_counter = Counter(all_commands)
        for cmd, count in cmd_counter.most_common(10):
            bar = "█" * (count * 30 // max(cmd_counter.values()))
            print(f"{cmd:<15} {count:>4} {bar}")
        print()

# ─── Thread List ───────────────────────────────────────────────────────────────

if args.threads or args.active:
    # Build query
    query = """
        SELECT 
            c.thread_id,
            c.messages,
            c.last_updated,
            tm.creator_id,
            tm.created_at
        FROM conversations c
        LEFT JOIN thread_meta tm ON c.thread_id = tm.thread_id
        WHERE 1=1
    """
    params = []
    
    if args.user:
        query += " AND tm.creator_id LIKE ?"
        params.append(f"%{args.user}%")
    
    if args.days:
        cutoff = datetime.now() - timedelta(days=args.days)
        query += " AND c.last_updated > ?"
        params.append(cutoff.isoformat())
    
    if args.active:
        cutoff = datetime.now() - timedelta(days=retention_days)
        query += " AND c.last_updated > ?"
        params.append(cutoff.isoformat())
    
    query += " ORDER BY c.last_updated DESC"
    
    cursor.execute(query, params)
    threads = cursor.fetchall()
    
    if threads:
        print("📋 Conversation Threads")
        print("─" * 100)
        print(f"{'Thread ID':<20} {'Creator':<15} {'Messages':<10} {'Age':<10} {'Last Active':<20} {'Status':<10}")
        print("─" * 100)
        
        for thread in threads:
            info = parse_messages(thread['messages'])
            age = get_thread_age(thread['last_updated'])
            creator = thread['creator_id'] if thread['creator_id'] else 'Unknown'
            
            # Determine status
            if 'd' in age and int(age.split('d')[0]) >= retention_days:
                status = "⏰ Expired"
            else:
                status = "✅ Active"
            
            # Truncate long IDs for display
            thread_id = thread['thread_id']
            if len(thread_id) > 18:
                thread_id = thread_id[:15] + "..."
            
            print(f"{thread_id:<20} {creator:<15} {info['total_messages']:<10} "
                  f"{age:<10} {format_date(thread['last_updated']):<20} {status:<10}")
            
            if args.verbose and info['commands']:
                print(f"    Commands used: {', '.join(info['commands'][:5])}")
        
        print("─" * 100)
        print(f"Total: {len(threads)} threads")
    else:
        print("📊 No threads found matching criteria")
    print()

# ─── Timeline Analysis ─────────────────────────────────────────────────────────

if args.timeline:
    print("📈 Conversation Timeline")
    print("─" * 50)
    
    # Get daily activity
    cursor.execute("""
        SELECT 
            DATE(last_updated) as date,
            COUNT(*) as thread_count
        FROM conversations
        WHERE last_updated > datetime('now', '-30 days')
        GROUP BY DATE(last_updated)
        ORDER BY date DESC
        LIMIT 14
    """)
    
    daily_activity = cursor.fetchall()
    
    if daily_activity:
        print("Daily Activity (Last 14 days):")
        max_count = max(row['thread_count'] for row in daily_activity)
        
        for row in reversed(daily_activity):
            bar_length = int(row['thread_count'] * 40 / max_count)
            bar = "█" * bar_length
            print(f"{row['date']} │ {bar} {row['thread_count']}")
    
    # Get hourly pattern
    print("\nHourly Activity Pattern:")
    hourly_data = defaultdict(int)
    
    for thread in all_threads:
        try:
            dt = datetime.fromisoformat(thread['last_updated'].replace('Z', '+00:00'))
            hour = dt.hour
            hourly_data[hour] += 1
        except:
            pass
    
    if hourly_data:
        max_hourly = max(hourly_data.values())
        for hour in range(24):
            count = hourly_data.get(hour, 0)
            bar_length = int(count * 30 / max_hourly) if max_hourly > 0 else 0
            bar = "█" * bar_length
            print(f"{hour:02d}:00 │ {bar} {count}")

# ─── User Statistics ───────────────────────────────────────────────────────────

if not any([args.threads, args.active, args.commands, args.timeline]):
    cursor.execute("""
        SELECT 
            tm.creator_id,
            COUNT(*) as thread_count,
            MAX(c.last_updated) as last_active
        FROM thread_meta tm
        JOIN conversations c ON tm.thread_id = c.thread_id
        GROUP BY tm.creator_id
        ORDER BY thread_count DESC
        LIMIT 10
    """)
    
    top_users = cursor.fetchall()
    
    if top_users:
        print("👥 Top Users by Thread Count")
        print("─" * 50)
        print(f"{'User ID':<20} {'Threads':<10} {'Last Active':<20}")
        print("─" * 50)
        
        for user in top_users:
            user_id = user['creator_id'] if user['creator_id'] else 'Unknown'
            if len(user_id) > 18:
                user_id = user_id[:15] + "..."
            print(f"{user_id:<20} {user['thread_count']:<10} {format_date(user['last_active']):<20}")

# ─── Cleanup ───────────────────────────────────────────────────────────────────

conn.close()