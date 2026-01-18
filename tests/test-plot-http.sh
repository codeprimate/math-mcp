#!/usr/bin/env bash
# Test plot image persistence: 24-month hardware store bar chart via MCP HTTP.
# Prereq: MCP server on http://localhost:8008 (e.g. docker compose up -d with streamable-http)

# 1. Initialize and capture session ID (README: HTTP Usage)
RESPONSE=$(curl -s -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -D - \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')

SESSION_ID=$(echo "$RESPONSE" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r')

# 2. Call plot_bar_chart: 24 months, currency with commas, value labels, plain-English months
curl -s -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_bar_chart","arguments":{"categories":["January 2024","February 2024","March 2024","April 2024","May 2024","June 2024","July 2024","August 2024","September 2024","October 2024","November 2024","December 2024","January 2025","February 2025","March 2025","April 2025","May 2025","June 2025","July 2025","August 2025","September 2025","October 2025","November 2025","December 2025"],"values":[52000,48000,58000,62000,65000,72000,71000,68000,55000,58000,62000,78000,54000,50000,60000,64000,67000,74000,73000,70000,56000,60000,65000,82000],"title":"Hardware Store Monthly Sales","xlabel":"Month","ylabel":"Sales ($)","show_values":true,"value_format":"$,.0f","xlabel_rotation":45}}}' \
  | grep -o 'Chart available at: http[^"]*' || true
