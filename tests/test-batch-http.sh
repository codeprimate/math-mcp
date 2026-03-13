#!/usr/bin/env bash
# Test batch_tools via MCP HTTP (localhost:8008).
# Prereq: math-mcp server on http://localhost:8008 (e.g. docker-compose up -d).

set -e
BASE_URL="${BASE_URL:-http://localhost:8008}"
MCP_URL="${BASE_URL}/mcp"

echo "=== 1. Initialize session ==="
RESPONSE=$(curl -s -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -D - \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-batch","version":"1.0"}}}')

SESSION_ID=$(echo "$RESPONSE" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r')
if [ -z "$SESSION_ID" ]; then
  echo "Failed to get mcp-session-id. Response headers:"
  echo "$RESPONSE" | head -20
  exit 1
fi
echo "Session: $SESSION_ID"

echo ""
echo "=== 2. Call batch_tools (simplify + evaluate + solve) ==="
BODY='{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"batch_tools","arguments":{"calls":[{"name":"simplify","arguments":{"expression":"x + x"}},{"name":"evaluate","arguments":{"expression":"1+1"}},{"name":"solve","arguments":{"equation":"x^2 - 4","variable":"x"}}]}}}'
RAW=$(curl -s -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d "$BODY")

# Response is SSE: extract first "data: {...}" line and parse JSON
DATA_LINE=$(echo "$RAW" | grep -m1 "^data:")
if [ -z "$DATA_LINE" ]; then
  echo "No data line in response. Raw:"
  echo "$RAW"
  exit 1
fi
JSON="${DATA_LINE#data:}"
echo "$JSON" | python3 -m json.tool

echo ""
echo "Done."
