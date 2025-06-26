import os
import sys
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# ─── Load Environment Variables ────────────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("OPENAI_ADMIN_KEY")

if not API_KEY:
    print("❌ OPENAI_ADMIN_KEY not set in .env file!", file=sys.stderr)
    sys.exit(1)

# ─── Calculate Time Range ──────────────────────────────────────────────────────

# Start of current month (UTC)
now = datetime.now(timezone.utc)
start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
start_time = int(start_of_month.timestamp())
end_time = int(now.timestamp())

print(f"📅 Querying usage from {start_of_month} to {now}")

# ─── Hit the API ───────────────────────────────────────────────────────────────

url = (
    "https://api.openai.com/v1/organization/usage/completions"
    f"?start_time={start_time}&end_time={end_time}&limit=31"
)
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

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
    # Pretty print JSON
    print(json.dumps(data, indent=2))
except Exception as e:
    print("❌ Failed to parse JSON response:", e)
    print(body)
    sys.exit(1)