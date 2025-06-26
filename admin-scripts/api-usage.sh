#!/bin/bash

# ─── Load Environment Variables ────────────────────────────────────────────────

if [ ! -f .env ]; then
  echo "❌ .env file not found! Make sure it's in the current directory."
  exit 1
fi

export $(grep '^OPENAI_ADMIN_KEY=' .env | xargs)

if [ -z "$OPENAI_ADMIN_KEY" ]; then
  echo "❌ OPENAI_ADMIN_KEY not set in .env file!"
  exit 1
fi

# ─── Calculate Time Range ──────────────────────────────────────────────────────

# Start of current month (UTC)
start_time=$(date -u -d "$(date +%Y-%m-01)" +%s)

# Current time (UTC)
end_time=$(date -u +%s)

echo "📅 Querying usage from $(date -u -d @$start_time) to $(date -u -d @$end_time)"
echo "🔑 Using admin key: ${OPENAI_ADMIN_KEY:0:8}... (truncated)"

# ─── Hit the API ───────────────────────────────────────────────────────────────

response=$(curl -s -w "\n%{http_code}" "https://api.openai.com/v1/organization/usage/completions?start_time=${start_time}&end_time=${end_time}&limit=31" \
  -H "Authorization: Bearer $OPENAI_ADMIN_KEY" \
  -H "Content-Type: application/json")

# Separate body and status code
body=$(echo "$response" | sed '$d')
status=$(echo "$response" | tail -n1)

# ─── Handle Response ───────────────────────────────────────────────────────────

if [ "$status" -ne 200 ]; then
  echo "❌ Request failed with HTTP $status"
  echo "🔍 Response:"
  echo "$body"
  exit 1
fi

# Pretty print JSON if jq is installed
if command -v jq >/dev/null; then
  echo "$body" | jq
else
  echo "$body"
fi
