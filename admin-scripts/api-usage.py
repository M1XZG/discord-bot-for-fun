import os
import sys
import requests
import json
import argparse
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# ─── Parse Command Line Arguments ──────────────────────────────────────────────

parser = argparse.ArgumentParser(
    description='📊 Query OpenAI API usage statistics',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  %(prog)s                    # Current month
  %(prog)s -m 3               # March of current year
  %(prog)s -m 12 -y 2023      # December 2023
  %(prog)s --month 1 --year 2024  # January 2024
  %(prog)s -h                 # Show this help

Note: Requires OPENAI_ADMIN_KEY in .env file
    """
)

parser.add_argument(
    '-m', '--month',
    type=int,
    choices=range(1, 13),
    help='Month to query (1-12). Default: current month',
    metavar='MONTH'
)

parser.add_argument(
    '-y', '--year',
    type=int,
    help='Year to query (e.g., 2024). Default: current year',
    metavar='YEAR'
)

parser.add_argument(
    '--model',
    choices=['gpt-4', 'gpt-4o', 'gpt-3.5'],
    default='gpt-4o',
    help='Model pricing to use for cost estimation (default: gpt-4o)'
)

parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='Show detailed output including empty days'
)

args = parser.parse_args()

# ─── Load Environment Variables ────────────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("OPENAI_ADMIN_KEY")

if not API_KEY:
    print("❌ OPENAI_ADMIN_KEY not set in .env file!", file=sys.stderr)
    print("💡 Add to .env: OPENAI_ADMIN_KEY=your_admin_api_key", file=sys.stderr)
    sys.exit(1)

# ─── Calculate Time Range ──────────────────────────────────────────────────────

now = datetime.now(timezone.utc)

# Determine the month and year to query
if args.month:
    month = args.month
    year = args.year if args.year else now.year
else:
    month = now.month
    year = now.year

# Create start and end timestamps for the specified month
try:
    start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
    # Get first day of next month, then subtract one second for end of current month
    end_of_month = start_of_month + relativedelta(months=1) - relativedelta(seconds=1)
    
    # If querying future month, limit to current time
    if end_of_month > now:
        end_of_month = now
        
    start_time = int(start_of_month.timestamp())
    end_time = int(end_of_month.timestamp())
    
except ValueError as e:
    print(f"❌ Invalid date: {e}", file=sys.stderr)
    sys.exit(1)

print(f"📅 Querying usage for {start_of_month.strftime('%B %Y')}")
print(f"   From: {start_of_month.strftime('%Y-%m-%d %H:%M')} UTC")
print(f"   To:   {end_of_month.strftime('%Y-%m-%d %H:%M')} UTC")
print()

# ─── Hit the API ───────────────────────────────────────────────────────────────

url = (
    "https://api.openai.com/v1/organization/usage/completions"
    f"?start_time={start_time}&end_time={end_time}&limit=31"
)
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

if args.verbose:
    print(f"🔗 API URL: {url}")
    print()

response = requests.get(url, headers=headers)
status = response.status_code
body = response.text

# ─── Handle Response ───────────────────────────────────────────────────────────

if status != 200:
    print(f"❌ Request failed with HTTP {status}")
    print("🔍 Response:")
    print(body)
    sys.exit(1)

try:
    data = response.json()
    
    # Extract buckets (each bucket is a day)
    buckets = data.get('data', [])
    
    if not buckets:
        print("📊 No usage data found for this period")
        sys.exit(0)
    
    # ─── Display Table ─────────────────────────────────────────────────────────
    
    print("┌────────────┬─────────────────┬──────────────────┬─────────────────┐")
    print("│    Date    │  Input Tokens   │  Output Tokens   │  Total Tokens   │")
    print("├────────────┼─────────────────┼──────────────────┼─────────────────┤")
    
    total_input = 0
    total_output = 0
    total_all = 0
    days_with_usage = 0
    
    for bucket in buckets:
        # Convert start_time to date
        timestamp = bucket.get('start_time', 0)
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d')
        
        # Get results for this day
        results = bucket.get('results', [])
        
        # Sum tokens for all results in this bucket
        day_input = 0
        day_output = 0
        
        for result in results:
            day_input += result.get('input_tokens', 0)
            day_output += result.get('output_tokens', 0)
        
        # Skip days with no usage unless verbose
        if day_input == 0 and day_output == 0 and not args.verbose:
            continue
            
        if day_input > 0 or day_output > 0:
            days_with_usage += 1
            
        day_total = day_input + day_output
        
        # Add to totals
        total_input += day_input
        total_output += day_output
        total_all += day_total
        
        # Format numbers with commas
        input_str = f"{day_input:,}".rjust(15)
        output_str = f"{day_output:,}".rjust(16)
        total_str = f"{day_total:,}".rjust(15)
        
        print(f"│ {date} │ {input_str} │ {output_str} │ {total_str} │")
    
    # Display totals
    print("├────────────┼─────────────────┼──────────────────┼─────────────────┤")
    total_input_str = f"{total_input:,}".rjust(15)
    total_output_str = f"{total_output:,}".rjust(16)
    total_all_str = f"{total_all:,}".rjust(15)
    print(f"│   TOTAL    │ {total_input_str} │ {total_output_str} │ {total_all_str} │")
    print("└────────────┴─────────────────┴──────────────────┴─────────────────┘")
    
    # ─── Cost Estimation ───────────────────────────────────────────────────────
    
    # Pricing based on model selection
    pricing = {
        'gpt-4': {
            'input': 0.03,    # $0.03 per 1K input tokens
            'output': 0.06    # $0.06 per 1K output tokens
        },
        'gpt-4o': {
            'input': 0.01,    # $0.01 per 1K input tokens
            'output': 0.03    # $0.03 per 1K output tokens
        },
        'gpt-3.5': {
            'input': 0.0005,  # $0.0005 per 1K input tokens
            'output': 0.0015  # $0.0015 per 1K output tokens
        }
    }
    
    model_pricing = pricing[args.model]
    INPUT_PRICE_PER_1K = model_pricing['input']
    OUTPUT_PRICE_PER_1K = model_pricing['output']
    
    input_cost = (total_input / 1000) * INPUT_PRICE_PER_1K
    output_cost = (total_output / 1000) * OUTPUT_PRICE_PER_1K
    total_cost = input_cost + output_cost
    
    print()
    print(f"💰 Estimated Cost ({args.model} pricing):")
    print(f"   Input:  ${input_cost:.2f} (${INPUT_PRICE_PER_1K:.4f}/1K tokens)")
    print(f"   Output: ${output_cost:.2f} (${OUTPUT_PRICE_PER_1K:.4f}/1K tokens)")
    print(f"   Total:  ${total_cost:.2f}")
    
    # ─── Additional Stats ──────────────────────────────────────────────────────
    
    print()
    print(f"📊 Usage Statistics:")
    print(f"   Month: {start_of_month.strftime('%B %Y')}")
    print(f"   Days with usage: {days_with_usage}")
    if days_with_usage > 0:
        print(f"   Average tokens/day: {total_all // days_with_usage:,}")
        if total_output > 0:
            print(f"   Input/Output ratio: {total_input/total_output:.2f}:1")
        else:
            print(f"   Input/Output ratio: N/A (no output tokens)")
    
    # ─── Model Request Stats ───────────────────────────────────────────────────
    
    total_requests = 0
    for bucket in buckets:
        for result in bucket.get('results', []):
            total_requests += result.get('num_model_requests', 0)
    
    if total_requests > 0:
        print(f"   Total API requests: {total_requests}")
        print(f"   Average tokens/request: {total_all // total_requests:,}")
        
    # ─── Daily Average Cost ────────────────────────────────────────────────────
    
    if days_with_usage > 0:
        daily_avg_cost = total_cost / days_with_usage
        print(f"   Average cost/day: ${daily_avg_cost:.2f}")
        
        # Project monthly cost (based on 30 days)
        projected_monthly = daily_avg_cost * 30
        print(f"   Projected monthly cost: ${projected_monthly:.2f} (30-day estimate)")
    
except Exception as e:
    print("❌ Failed to parse JSON response:", e)
    if args.verbose:
        print("📋 Full response:")
        print(body)
    sys.exit(1)