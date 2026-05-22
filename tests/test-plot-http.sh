#!/usr/bin/env bash
# Test plot image persistence via MCP HTTP.
# Prereq: Rebuild the image and start the server so the running code has the latest tools:
#   docker compose build && docker compose up -d --force-recreate
# Then ensure the MCP server is on http://localhost:8008 (streamable-http).

set -euo pipefail

MCP_URL="${MCP_URL:-http://localhost:8008/mcp}"

init_session() {
  local response
  response=$(curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -D - \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')
  echo "$response" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r'
}

extract_chart_url() {
  grep -oE 'http://[^"\\]+/outputs/charts/[^"\\]+' | head -1 || true
}

call_tool_and_extract_url() {
  local session_id="$1"
  local body="$2"
  curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "mcp-session-id: $session_id" \
    -d "$body" \
    | extract_chart_url
}

PLOT_ARGS='{"categories":["January 2024","February 2024","March 2024","April 2024","May 2024","June 2024","July 2024","August 2024","September 2024","October 2024","November 2024","December 2024","January 2025","February 2025","March 2025","April 2025","May 2025","June 2025","July 2025","August 2025","September 2025","October 2025","November 2025","December 2025"],"values":[52000,48000,58000,62000,65000,72000,71000,68000,55000,58000,62000,78000,54000,50000,60000,64000,67000,74000,73000,70000,56000,60000,65000,82000],"title":"Hardware Store Monthly Sales","xlabel":"Month","ylabel":"Sales ($)","show_values":true,"value_format":"$,.0f","xlabel_rotation":45}'

SESSION_ID="$(init_session)"

echo "=== via math dispatcher ==="
MATH_BODY=$(jq -n --argjson args "$PLOT_ARGS" '{jsonrpc:"2.0",id:2,method:"tools/call",params:{name:"math",arguments:{tool:"plot_bar",arguments:$args}}}')
MATH_URL="$(call_tool_and_extract_url "$SESSION_ID" "$MATH_BODY")"
if [[ -z "$MATH_URL" ]]; then
  echo "FAIL: math(plot_bar) did not return download_url" >&2
  exit 1
fi
echo "$MATH_URL"

echo "=== direct plot_bar tool ==="
DIRECT_BODY=$(jq -n --argjson args "$PLOT_ARGS" '{jsonrpc:"2.0",id:3,method:"tools/call",params:{name:"plot_bar",arguments:$args}}')
DIRECT_URL="$(call_tool_and_extract_url "$SESSION_ID" "$DIRECT_BODY")"
if [[ -z "$DIRECT_URL" ]]; then
  echo "FAIL: direct plot_bar did not return download_url" >&2
  exit 1
fi
echo "$DIRECT_URL"

echo "PASS"
