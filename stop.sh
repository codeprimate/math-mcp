#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
docker compose down
echo "math-mcp service stopped"
