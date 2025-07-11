import os
import sys
import sqlite3
import json
import argparse
from datetime import datetime

# ─── Parse Command Line Arguments ──────────────────────────────────────────────

parser = argparse.ArgumentParser(
    description='📋 Dump conversation database to table format',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  %(prog)s                    # Dump all conversations
  %(prog)s -n 20             # Show only 20 records
  %(prog)s --csv             # Export as CSV
  %(prog)s --json            # Export as JSON
  %(prog)s -o output.txt     # Save to file
    """
)

parser.add_argument(
    '-n', '--number',
    type=int,
    help='Limit number of records (default: all)'
)

parser.add_argument(
    '--csv',
    action='store_true',
    help='Output in CSV format'
)

parser.add_argument(
    '--json',
    action='store_true',
    help='Output in JSON format'
)

parser.add_argument(
    '-o', '--output',
    type=str,
    help='Output to file instead of console'
)

parser.add_argument(
    '--db',
    type=str,
    default='conversations.db',
    help='Path to database file (default: conversations.db)'
)

parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='Include full message content'
)

args = parser.parse_args()

# ─── Check Database ────────────────────────────────────────────────────────────

if not os.path.exists(args.db):
    print(f"❌ Database not found: {args.db}", file=sys.stderr)
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
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp)

def parse_messages(messages_json):
    """Parse JSON messages and get summary"""
    try:
        messages = json.loads(messages_json)
        user_msgs = sum(1 for m in messages if m.get('role') == 'user')
        assistant_msgs = sum(1 for m in messages if m.get('role') == 'assistant')
        total_chars = sum(len(m.get('content', '')) for m in messages)
        
        # Get first user message as preview
        first_msg = next((m['content'] for m in messages if m.get('role') == 'user'), '')
        preview = first_msg[:50] + '...' if len(first_msg) > 50 else first_msg
        preview = preview.replace('\n', ' ')
        
        return {
            'user_msgs': user_msgs,
            'assistant_msgs': assistant_msgs,
            'total_chars': total_chars,
            'preview': preview,
            'messages': messages if args.verbose else None
        }
    except:
        return {
            'user_msgs': 0,
            'assistant_msgs': 0,
            'total_chars': 0,
            'preview': 'Error parsing',
            'messages': None
        }

# ─── Query Database ────────────────────────────────────────────────────────────

query = """
    SELECT 
        c.thread_id,
        c.messages,
        c.last_updated,
        tm.creator_id,
        tm.created_at
    FROM conversations c
    LEFT JOIN thread_meta tm ON c.thread_id = tm.thread_id
    ORDER BY c.last_updated DESC
"""

if args.number:
    query += f" LIMIT {args.number}"

cursor.execute(query)
results = cursor.fetchall()

# ─── Output Formats ────────────────────────────────────────────────────────────

output_lines = []

if args.csv:
    # CSV Format
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    headers = ['thread_id', 'creator_id', 'created_at', 'last_updated', 
               'user_messages', 'assistant_messages', 'total_chars', 'preview']
    if args.verbose:
        headers.append('full_messages')
    
    writer.writerow(headers)
    
    # Data
    for row in results:
        info = parse_messages(row['messages'])
        data = [
            row['thread_id'],
            row['creator_id'] or 'Unknown',
            format_date(row['created_at']) if row['created_at'] else 'Unknown',
            format_date(row['last_updated']),
            info['user_msgs'],
            info['assistant_msgs'],
            info['total_chars'],
            info['preview']
        ]
        if args.verbose:
            data.append(json.dumps(info['messages']) if info['messages'] else '')
        
        writer.writerow(data)
    
    output_lines.append(output.getvalue())

elif args.json:
    # JSON Format
    data = []
    for row in results:
        info = parse_messages(row['messages'])
        record = {
            'thread_id': row['thread_id'],
            'creator_id': row['creator_id'] or 'Unknown',
            'created_at': format_date(row['created_at']) if row['created_at'] else 'Unknown',
            'last_updated': format_date(row['last_updated']),
            'user_messages': info['user_msgs'],
            'assistant_messages': info['assistant_msgs'],
            'total_chars': info['total_chars'],
            'preview': info['preview']
        }
        if args.verbose:
            record['messages'] = info['messages']
        
        data.append(record)
    
    output_lines.append(json.dumps(data, indent=2, ensure_ascii=False))

else:
    # Table Format (default)
    output_lines.append("📋 Conversation Database Dump")
    output_lines.append("=" * 140)
    
    # Header
    header = f"{'Thread ID':<25} {'Creator':<15} {'Created':<20} {'Updated':<20} {'Msgs':<6} {'Chars':<8} {'Preview':<40}"
    output_lines.append(header)
    output_lines.append("-" * 140)
    
    # Data rows
    for row in results:
        info = parse_messages(row['messages'])
        
        # Truncate thread ID for display
        thread_id = row['thread_id']
        if len(thread_id) > 23:
            thread_id = thread_id[:20] + "..."
        
        creator = row['creator_id'] or 'Unknown'
        if len(creator) > 13:
            creator = creator[:10] + "..."
        
        created = format_date(row['created_at']) if row['created_at'] else 'Unknown'
        updated = format_date(row['last_updated'])
        total_msgs = info['user_msgs'] + info['assistant_msgs']
        
        line = f"{thread_id:<25} {creator:<15} {created:<20} {updated:<20} {total_msgs:<6} {info['total_chars']:<8} {info['preview']:<40}"
        output_lines.append(line)
        
        # Add verbose message content if requested
        if args.verbose and info['messages']:
            output_lines.append("\n  Messages:")
            for msg in info['messages']:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                # Limit content length for display
                if len(content) > 100:
                    content = content[:97] + "..."
                content = content.replace('\n', ' ')
                output_lines.append(f"    [{role}]: {content}")
            output_lines.append("")
    
    output_lines.append("-" * 140)
    output_lines.append(f"Total records: {len(results)}")

# ─── Output Results ────────────────────────────────────────────────────────────

output_text = '\n'.join(output_lines)

if args.output:
    # Write to file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"✅ Output written to: {args.output}")
    except Exception as e:
        print(f"❌ Failed to write file: {e}", file=sys.stderr)
        sys.exit(1)
else:
    # Print to console
    print(output_text)

# ─── Cleanup ───────────────────────────────────────────────────────────────────

conn.close()