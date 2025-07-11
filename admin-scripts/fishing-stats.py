import os
import sys
import sqlite3
import argparse
from datetime import datetime
from collections import defaultdict

# ─── Parse Command Line Arguments ──────────────────────────────────────────────

parser = argparse.ArgumentParser(
    description='🎣 Display fishing game statistics from the database',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  %(prog)s                    # Show top 10 by points
  %(prog)s -n 20             # Show top 20
  %(prog)s --sort weight     # Sort by weight
  %(prog)s --user @username  # Show specific user's catches
  %(prog)s --fish Bass       # Show only Bass catches
  %(prog)s --all             # Show all catches
  %(prog)s --summary         # Show summary statistics only
  
Sorting options: points (default), weight, date, user
    """
)

parser.add_argument(
    '-n', '--number',
    type=int,
    default=10,
    help='Number of records to display (default: 10)'
)

parser.add_argument(
    '-s', '--sort',
    choices=['points', 'weight', 'date', 'user'],
    default='points',
    help='Sort by field (default: points)'
)

parser.add_argument(
    '-u', '--user',
    type=str,
    help='Filter by username'
)

parser.add_argument(
    '-f', '--fish',
    type=str,
    help='Filter by fish type'
)

parser.add_argument(
    '--all',
    action='store_true',
    help='Show all records (overrides -n)'
)

parser.add_argument(
    '--summary',
    action='store_true',
    help='Show summary statistics only'
)

parser.add_argument(
    '--leaderboard',
    action='store_true',
    help='Show user leaderboard'
)

parser.add_argument(
    '--biggest',
    action='store_true',
    help='Show biggest catches by species'
)

parser.add_argument(
    '--db',
    type=str,
    default='fishing_game.db',
    help='Path to database file (default: fishing_game.db)'
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

# ─── Functions ─────────────────────────────────────────────────────────────────

def format_weight(weight):
    """Format weight with appropriate units"""
    if weight < 1:
        return f"{weight*1000:.0f}g"
    else:
        return f"{weight:.1f}kg"

def format_date(timestamp):
    """Format timestamp to readable date"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return timestamp

# ─── Summary Statistics ────────────────────────────────────────────────────────

if args.summary or args.leaderboard or args.biggest:
    # Get overall statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_catches,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT catch_name) as unique_species,
            SUM(CASE WHEN catch_type = 'fish' THEN 1 ELSE 0 END) as fish_catches,
            SUM(CASE WHEN catch_type = 'user' THEN 1 ELSE 0 END) as user_catches,
            MAX(weight) as biggest_weight,
            MAX(points) as highest_points,
            AVG(weight) as avg_weight,
            AVG(points) as avg_points
        FROM catches
    """)
    
    stats = cursor.fetchone()
    
    if args.summary:
        print("🎣 Fishing Game Statistics")
        print("─" * 40)
        print(f"Total catches:      {stats['total_catches']:,}")
        print(f"Unique players:     {stats['unique_users']}")
        print(f"Fish species:       {stats['unique_species']}")
        print(f"Fish caught:        {stats['fish_catches']:,}")
        print(f"Members caught:     {stats['user_catches']:,}")
        print(f"Biggest catch:      {format_weight(stats['biggest_weight'] or 0)}")
        print(f"Highest points:     {stats['highest_points']:,}")
        print(f"Average weight:     {format_weight(stats['avg_weight'] or 0)}")
        print(f"Average points:     {stats['avg_points']:.0f}")
        print()

# ─── User Leaderboard ──────────────────────────────────────────────────────────

if args.leaderboard:
    print("🏆 Top Anglers Leaderboard")
    print("─" * 70)
    print(f"{'Rank':<6} {'Player':<20} {'Catches':<10} {'Points':<12} {'Biggest':<10}")
    print("─" * 70)
    
    cursor.execute("""
        SELECT 
            user_name,
            COUNT(*) as total_catches,
            SUM(points) as total_points,
            MAX(weight) as biggest_catch
        FROM catches
        GROUP BY user_id, user_name
        ORDER BY total_points DESC
        LIMIT 20
    """)
    
    rank = 1
    for row in cursor:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, f"{rank}.")
        print(f"{medal:<6} {row['user_name']:<20} {row['total_catches']:<10} "
              f"{row['total_points']:<12,} {format_weight(row['biggest_catch']):<10}")
        rank += 1
    print()

# ─── Biggest Catches by Species ────────────────────────────────────────────────

if args.biggest:
    print("🐟 Biggest Catches by Species")
    print("─" * 70)
    print(f"{'Fish':<20} {'Weight':<10} {'Points':<10} {'Caught by':<20} {'Date':<15}")
    print("─" * 70)
    
    cursor.execute("""
        SELECT 
            c1.catch_name,
            c1.weight,
            c1.points,
            c1.user_name,
            c1.timestamp
        FROM catches c1
        INNER JOIN (
            SELECT catch_name, MAX(weight) as max_weight
            FROM catches
            WHERE catch_type = 'fish'
            GROUP BY catch_name
        ) c2 ON c1.catch_name = c2.catch_name AND c1.weight = c2.max_weight
        ORDER BY c1.weight DESC
    """)
    
    for row in cursor:
        print(f"{row['catch_name']:<20} {format_weight(row['weight']):<10} "
              f"{row['points']:<10} {row['user_name']:<20} "
              f"{format_date(row['timestamp']):<15}")
    print()

# ─── Main Catch Display ────────────────────────────────────────────────────────

if not (args.summary or args.leaderboard or args.biggest):
    # Build query
    query = "SELECT * FROM catches WHERE 1=1"
    params = []
    
    if args.user:
        query += " AND user_name LIKE ?"
        params.append(f"%{args.user}%")
    
    if args.fish:
        query += " AND catch_name LIKE ?"
        params.append(f"%{args.fish}%")
    
    # Add sorting
    sort_columns = {
        'points': 'points DESC',
        'weight': 'weight DESC',
        'date': 'timestamp DESC',
        'user': 'user_name ASC, timestamp DESC'
    }
    query += f" ORDER BY {sort_columns[args.sort]}"
    
    # Add limit
    if not args.all:
        query += f" LIMIT {args.number}"
    
    # Execute query
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    if not results:
        print("📊 No catches found matching criteria")
    else:
        # Display header
        title = "🎣 Fishing Catches"
        if args.user:
            title += f" (User: {args.user})"
        if args.fish:
            title += f" (Fish: {args.fish})"
        print(title)
        print("─" * 100)
        print(f"{'Date':<16} {'Player':<20} {'Type':<8} {'Catch':<20} {'Weight':<10} {'Points':<8}")
        print("─" * 100)
        
        # Display catches
        for row in results:
            catch_type = "🐟" if row['catch_type'] == 'fish' else "👤"
            date_str = format_date(row['timestamp'])
            weight_str = format_weight(row['weight'])
            
            print(f"{date_str:<16} {row['user_name']:<20} {catch_type:<8} "
                  f"{row['catch_name']:<20} {weight_str:<10} {row['points']:<8,}")
        
        print("─" * 100)
        print(f"Showing {len(results)} catches" + 
              (f" (sorted by {args.sort})" if args.sort != 'points' else ""))

# ─── Additional Stats ──────────────────────────────────────────────────────────

if not args.summary and not args.leaderboard and not args.biggest:
    print()
    # Show catch distribution
    cursor.execute("""
        SELECT 
            catch_name,
            COUNT(*) as count
        FROM catches
        WHERE catch_type = 'fish'
        GROUP BY catch_name
        ORDER BY count DESC
        LIMIT 5
    """)
    
    print("🎯 Most Common Catches:")
    for row in cursor:
        print(f"   {row['catch_name']}: {row['count']} times")

# ─── Cleanup ───────────────────────────────────────────────────────────────────

conn.close()