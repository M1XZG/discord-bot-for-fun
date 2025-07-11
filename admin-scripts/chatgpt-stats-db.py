import sqlite3
import os
from datetime import datetime, timezone
import argparse

# ─── Database Setup ────────────────────────────────────────────────────────────

def init_stats_db(db_path="chatgpt_stats.db"):
    """Initialize the ChatGPT statistics database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Create main stats table
    c.execute("""
        CREATE TABLE IF NOT EXISTS command_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            command TEXT NOT NULL,
            input_chars INTEGER NOT NULL,
            output_chars INTEGER NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            thread_id TEXT,
            is_thread_message BOOLEAN DEFAULT 0
        )
    """)
    
    # Create thread summary table
    c.execute("""
        CREATE TABLE IF NOT EXISTS thread_stats (
            thread_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            closed_at DATETIME,
            total_messages INTEGER DEFAULT 0,
            total_input_chars INTEGER DEFAULT 0,
            total_output_chars INTEGER DEFAULT 0,
            total_prompt_tokens INTEGER DEFAULT 0,
            total_completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            close_reason TEXT
        )
    """)
    
    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_command_stats_user ON command_stats(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_command_stats_timestamp ON command_stats(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_command_stats_command ON command_stats(command)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_thread_stats_user ON thread_stats(user_id)")
    
    conn.commit()
    conn.close()
    print(f"✅ Initialized stats database: {db_path}")

def backup_stats_db(db_path="chatgpt_stats.db"):
    """Create a backup of the stats database."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Created backup: {backup_path}")

def get_db_info(db_path="chatgpt_stats.db"):
    """Show information about the database."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print(f"💡 Run with --init to create it")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Add this line to enable dictionary-style access
    c = conn.cursor()
    
    # Get file size
    file_size = os.path.getsize(db_path)
    print(f"📊 Database: {db_path}")
    print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Get record counts
    c.execute("SELECT COUNT(*) FROM command_stats")
    command_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM thread_stats")
    thread_count = c.fetchone()[0]
    
    # Get date range
    c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM command_stats")
    date_range = c.fetchone()
    
    print(f"   Command records: {command_count:,}")
    print(f"   Thread records: {thread_count:,}")
    
    if date_range[0]:
        # Format dates to be more readable
        try:
            start_date = datetime.fromisoformat(date_range[0].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(date_range[1].replace('Z', '+00:00'))
            print(f"   Date range: {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            # Fallback if date parsing fails
            print(f"   Date range: {date_range[0]} to {date_range[1]}")
    
    # Get some additional stats
    if command_count > 0:
        # Total tokens used
        c.execute("SELECT SUM(total_tokens) FROM command_stats")
        total_tokens = c.fetchone()[0] or 0
        print(f"   Total tokens used: {total_tokens:,}")
        
        # Most active user
        c.execute("""
            SELECT user_name, COUNT(*) as count 
            FROM command_stats 
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 1
        """)
        top_user = c.fetchone()
        if top_user:
            print(f"   Most active user: {top_user['user_name']} ({top_user['count']} commands)")
        
        # Most used command
        c.execute("""
            SELECT command, COUNT(*) as count 
            FROM command_stats 
            GROUP BY command 
            ORDER BY count DESC 
            LIMIT 1
        """)
        top_command = c.fetchone()
        if top_command:
            print(f"   Most used command: {top_command['command']} ({top_command['count']} times)")
    
    conn.close()

# ─── Command Line Interface ────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage ChatGPT statistics database",
        epilog="Default action: Show database information"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize the database (safe - won't delete existing data)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="⚠️  DANGER: Reset the database (delete ALL existing data)"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of the current database"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show database information (default action)"
    )
    parser.add_argument(
        "--db",
        default="chatgpt_stats.db",
        help="Database file path (default: chatgpt_stats.db)"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        # Add extra confirmation for reset
        print("⚠️  WARNING: This will DELETE ALL historical statistics data!")
        print("This action cannot be undone.")
        confirm = input("Type 'DELETE ALL STATS' to confirm: ")
        
        if confirm == "DELETE ALL STATS":
            if os.path.exists(args.db):
                # Create automatic backup before deletion
                backup_stats_db(args.db)
                os.remove(args.db)
                print(f"🗑️  Deleted existing database: {args.db}")
            init_stats_db(args.db)
        else:
            print("❌ Reset cancelled.")
    elif args.init:
        init_stats_db(args.db)
    elif args.backup:
        backup_stats_db(args.db)
    else:
        # Default action - show info
        get_db_info(args.db)