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

# ─── Parse Optional Month/Year Arguments ───────────────────────────────────────

if [ $# -eq 2 ]; then
  year="$1"
  month="$2"
elif [ $# -eq 0 ]; then
  year=$(date -u +%Y)
  month=$(date -u +%m)
else
  echo "Usage: $0 [year month]"
  echo "Example: $0 2025 06"
  exit 1
fi

# ─── Calculate Time Range ──────────────────────────────────────────────────────

# Start of specified month (UTC)
start_time=$(date -u -d "${year}-${month}-01" +%s)

# Start of next month (UTC)
if [ "$month" -eq 12 ]; then
  next_year=$((year + 1))
  next_month=1
else
  next_year=$year
  next_month=$((10#$month + 1))
fi
end_time=$(date -u -d "${next_year}-$(printf "%02d" $next_month)-01" +%s)

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

# Pretty print as Markdown table if jq is installed
if command -v jq >/dev/null; then
  # Print table header
  echo "| Date       | Requests | Prompt Tokens | Completion Tokens | Total Tokens | Cost (USD) |"
  echo "|------------|----------|---------------|------------------|--------------|------------|"
  # Print each day's usage
  echo "$body" | jq -r '
    .data[] | 
    [
      (.timestamp | strftime("%Y-%m-%d")),
      .n_requests,
      .n_prompt_tokens,
      .n_completion_tokens,
      .n_total_tokens,
      (.cost_usd // 0 | tostring)
    ] | @tsv' | while IFS=$'\t' read -r date reqs prompt comp total cost; do
      printf "| %s | %8s | %13s | %16s | %12s | %10s |\n" "$date" "$reqs" "$prompt" "$comp" "$total" "$cost"
    done
else
  echo "$body"
fi
