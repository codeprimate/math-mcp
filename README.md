# Math MCP Server

Powerful symbolic mathematics for Cursor AI. Solve equations, compute derivatives and integrals, simplify expressions, and more—all through natural language requests. Powered by SymPy.

## Quick Start with Docker

### Option 1: Docker Compose (Recommended for HTTP Mode)

The easiest way to run the HTTP server:

```bash
# Start the server (uses docker-compose.yml)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down

# Customize configuration (optional)
# 1. Copy .env.example to .env and edit
# 2. Or edit docker-compose.yml directly
# 3. Or use docker-compose.override.yml for local overrides
```

**Configuration via environment variables:**
- Create a `.env` file or set environment variables
- See `docker-compose.yml` for all available options
- Default: HTTP server on port 8008, accessible from host and Docker network

### Option 2: Docker CLI

```bash
# Build
docker build -t math-mcp .

# Test (stdio mode - for CLI usage)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker run -i --rm math-mcp

# Run HTTP server (persistent mode)
docker run -d -p 8008:8008 --name math-mcp-server \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8008 \
  math-mcp
```

The server supports two transport modes:
- **stdio** (default): For CLI usage and Cursor integration via Docker
- **streamable-http**: For persistent hosting accessible via HTTP from Docker networks and host applications (uses Server-Sent Events)

## Add to Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`). This enables Cursor to use 8 powerful math tools for solving equations, computing derivatives/integrals, simplifying expressions, and more.

**What this adds:** Symbolic and numerical mathematics server powered by SymPy and SciPy with tools for:
- Solving equations and finding roots (symbolic and numerical)
- Computing derivatives and integrals
- Simplifying and manipulating algebraic expressions
- Evaluating expressions numerically
- Converting to LaTeX format
- Converting decimals to fractions and simplifying fractions
- Converting between measurement units (length, mass, time, temperature, etc.)
- Solving differential equations numerically (ODEs)
- Finding roots of functions numerically

### Option 1: Docker with stdio Transport (Recommended for Cursor)

This mode runs the server via Docker CLI, perfect for Cursor integration:

```json
{
  "mcpServers": {
    "math-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "math-mcp"]
    }
  }
}
```

**Note:** Make sure you've built the Docker image first:
```bash
docker build -t math-mcp .
```

### Option 1a: Docker Compose (Easiest for HTTP Mode)

**Recommended for HTTP mode** - Simple one-command startup:

```bash
# Start server with default configuration (port 8008)
docker-compose up -d

# View logs
docker-compose logs -f math-mcp

# Stop server
docker-compose down

# Customize port (edit docker-compose.yml or use .env file)
# Set MCP_HOST_PORT=9000 to use port 9000 on host
```

**Configuration:**
- Edit `docker-compose.yml` directly, or
- Create `.env` file with your settings (see `docker-compose.yml` for variable names), or
- Use `docker-compose.override.yml` for local overrides (git-ignored)

**Example .env file:**
```bash
# Copy env.example to .env and customize
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8008
MCP_HOST_PORT=8008
MCP_PATH=/mcp
```

**Quick examples:**
```bash
# Use custom port 9000
echo "MCP_HOST_PORT=9000" > .env
docker-compose up -d

# Use stdio mode (disable healthcheck, remove port mapping)
# Option 1: Set in .env file
echo "MCP_TRANSPORT=stdio" >> .env
echo "DISABLE_HEALTHCHECK=true" >> .env
# Then edit docker-compose.yml to comment out the ports section
docker-compose up -d

# Option 2: Use docker-compose.override.yml (see docker-compose.override.yml.example)
```

**Accessing from other containers:**
```bash
# Server is accessible at: http://math-mcp-server:8008/mcp
# (or use the container name and your configured port)
```

### Option 1b: Docker with HTTP Transport (For Persistent Hosting)

For persistent hosting accessible from Docker networks and host applications:

```bash
# Start persistent HTTP server (using default port 8008)
docker run -d -p 8008:8008 --name math-mcp-server \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8008 \
  -e MCP_PATH=/mcp \
  math-mcp

# Or use a custom port (e.g., 9000)
docker run -d -p 9000:9000 --name math-mcp-server \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=9000 \
  -e MCP_PATH=/mcp \
  math-mcp

# Server will be available at:
# - http://localhost:<MCP_PORT>/mcp (from host, use the port you configured)
# - http://math-mcp-server:<MCP_PORT>/mcp (from Docker network)
# - http://<container-ip>:<MCP_PORT>/mcp (from other containers)

# Stop the server
docker stop math-mcp-server
docker rm math-mcp-server
```

**Configuration options:**
- `MCP_TRANSPORT=streamable-http` - Enable Streamable HTTP transport (modern HTTP-based transport)
- `MCP_HOST=0.0.0.0` - Bind to all interfaces (accessible from host and Docker network)
- `MCP_PORT=<port>` - Port to listen on inside container (default: 8008). **Important:** Use `-p <host-port>:<container-port>` to map the port when running Docker, where `<container-port>` should match `MCP_PORT`
- `MCP_PATH=/mcp` - HTTP endpoint path (default: /mcp)

**Note:** The streamable-http transport uses Streamable HTTP (not pure SSE) and requires session management via the `mcp-session-id` header. See [HTTP Transport Usage](#http-transport-usage) section below for complete examples.

**Port mapping examples:**
```bash
# Container listens on 8008, map to host port 8008
docker run -d -p 8008:8008 -e MCP_PORT=8008 ...

# Container listens on 9000, map to host port 9000
docker run -d -p 9000:9000 -e MCP_PORT=9000 ...

# Container listens on 8008, map to different host port 3000
docker run -d -p 3000:8008 -e MCP_PORT=8008 ...
```

**Docker network usage:**
```bash
# Create a network
docker network create math-network

# Run server in network (port 8008)
docker run -d --name math-mcp-server --network math-network \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8008 \
  math-mcp

# Or use a custom port (e.g., 9000)
docker run -d --name math-mcp-server --network math-network \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=9000 \
  math-mcp

# Other containers in the same network can access:
# http://math-mcp-server:<MCP_PORT>/mcp
```

### Option 2: HTTP Endpoint (Web Server)

If you're running the server as a web service (e.g., via `docker-compose up` or Docker with HTTP transport), configure Cursor to connect via HTTP.

**Using mcp-remote (Recommended for compatibility):**

```json
{
  "mcpServers": {
    "math-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8008/mcp",
        "--transport",
        "http-only",
        "--allow-http"
      ]
    }
  }
}
```

**Important:** Use `--transport http-only` or `--transport http-first` with `mcp-remote` (not `sse-only`). FastMCP's `streamable_http_app` uses Streamable HTTP transport, which is incompatible with the deprecated SSE transport.

**Note:** Some MCP clients may support direct URL configuration, but `mcp-remote` provides the most reliable cross-client compatibility.

**Prerequisites:**
- Server must be running and accessible at `http://localhost:8008/mcp`
- Start the server first using one of these methods:
  - `docker-compose up -d` (recommended)
  - `docker run -d -p 8008:8008 ...` with HTTP transport enabled
  - Local Python with `MCP_TRANSPORT=streamable-http`

**Note:** If using a custom port, update the URL accordingly (e.g., `http://localhost:9000/mcp`).

### Option 3: Local Python

If you prefer running locally without Docker:

```json
{
  "mcpServers": {
    "math-mcp": {
      "command": "python",
      "args": ["-m", "math_mcp.server"]
    }
  }
}
```

**Note:** Requires the package to be installed: `pip install -e ".[dev]"`

### Complete Example

See example configuration files:
- [`docs/mcp.json.example`](./docs/mcp.json.example) - Docker CLI configuration (default)
- [`docs/mcp.json.http-example`](./docs/mcp.json.http-example) - HTTP endpoint configuration

You can copy either to `~/.cursor/mcp.json` and customize as needed.

## Add to Claude Desktop

Add to your Claude Desktop MCP settings. The configuration file location varies by OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### HTTP Endpoint (Web Server)

If you're running the server as a web service (e.g., via `docker-compose up` or Docker with HTTP transport), configure Claude Desktop to connect via HTTP using `mcp-remote`:

```json
{
  "mcpServers": {
    "math-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8008/mcp",
        "--transport",
        "http-only",
        "--allow-http"
      ]
    }
  }
}
```

**Important:** 
- Claude Desktop does **not** support direct URL configuration for remote MCP servers. You must use `mcp-remote` as a proxy.
- FastMCP's `streamable_http_app` uses **Streamable HTTP** transport (not SSE). Use `--transport http-only` or `--transport http-first` with `mcp-remote`. The `sse-only` transport is deprecated and incompatible with FastMCP servers.

**Prerequisites:**
- Server must be running and accessible at `http://localhost:8008/mcp`
- Start the server first using one of these methods:
  - `docker-compose up -d` (recommended)
  - `docker run -d -p 8008:8008 ...` with HTTP transport enabled
  - Local Python with `MCP_TRANSPORT=streamable-http`

**Note:** If using a custom port, update the URL accordingly (e.g., `http://localhost:9000/mcp`).

**Example configuration file:**
- [`docs/claude_desktop_config.json.example`](./docs/claude_desktop_config.json.example) - HTTP endpoint configuration for Claude Desktop

After updating the configuration file, restart Claude Desktop for the changes to take effect.

### Adding to Existing Configuration

If you already have other MCP servers configured, just add `"math-mcp"` to your existing `mcpServers` object:

```json
{
  "mcpServers": {
    "your-existing-server": {
      "command": "...",
      "args": [...]
    },
    "math-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "math-mcp"]
    }
  }
}
```

### What This Enables

Once configured and Cursor is restarted, you can ask math questions naturally:

- **"Solve x^2 - 4 = 0"** → Uses `solve` tool
- **"What's the derivative of x^3?"** → Uses `derivative` tool  
- **"Simplify sin(x)^2 + cos(x)^2"** → Uses `simplify` tool
- **"Evaluate 2*pi"** → Uses `evaluate` tool
- **"Factor x^2 - 4"** → Uses `factor` tool
- **"Integrate x^2"** → Uses `integral` tool
- **"Convert x^2 + 1/2 to LaTeX"** → Uses `latex` tool
- **"Convert 0.5 to a fraction"** → Uses `to_fraction` tool
- **"Simplify 6/8"** → Uses `simplify_fraction` tool
- **"Convert 100 meters to kilometers"** → Uses `convert_unit` tool
- **"Solve dx/dt = -x with x(0)=1 from t=0 to t=5"** → Uses `solve_ode` tool
- **"Find the root of x^2 - 4 near x=1"** → Uses `find_root` tool

Cursor automatically discovers all 13 tools and chooses the right one based on your question.

## Why Use This?

This MCP server gives Cursor powerful symbolic and numerical math capabilities powered by SymPy and SciPy. Instead of guessing at math or writing code, Cursor can:

- **Solve equations** - Find roots, solve for variables, answer "what is x?" questions (symbolic and numerical)
- **Do calculus** - Compute derivatives and integrals symbolically
- **Simplify expressions** - Reduce complex math to simplest form
- **Evaluate numerically** - Get concrete answers from symbolic expressions
- **Format math** - Convert to LaTeX for documentation
- **Solve differential equations** - Numerically integrate ODEs and systems of ODEs
- **Find roots numerically** - When symbolic methods fail or are too slow

Perfect for code that involves math, physics simulations, data analysis, engineering problems, or any task requiring mathematical computation.

## Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `simplify` | Simplify expression | Reduce complex expressions, verify identities |
| `solve` | Solve equation for variable | Find roots, solve for unknowns |
| `derivative` | Compute derivative | Calculus, optimization, rate of change |
| `integral` | Compute integral | Antiderivatives, areas, integration problems |
| `expand` | Expand expression | Multiply out parentheses, distribute terms |
| `factor` | Factor expression | Factor polynomials, find roots by factoring |
| `evaluate` | Evaluate numerically | Get numeric answers, check solutions |
| `latex` | Convert to LaTeX | Format math for documentation |
| `to_fraction` | Convert decimal to fraction | Get exact rational representation |
| `simplify_fraction` | Simplify fraction | Reduce fractions to lowest terms |
| `convert_unit` | Convert units | Convert between measurement units |
| `solve_ode` | Solve ODEs numerically | Systems of differential equations, time-dependent problems |
| `find_root` | Find root numerically | When symbolic solve fails, finding zeros of functions |

## Examples

### Command Line Usage

The MCP server communicates via JSON-RPC over stdio. You must initialize the server before calling tools.

#### Proper Initialization Sequence

MCP requires an initialization handshake before calling tools. Send all messages to a single container instance:

```bash
# Send initialization sequence + tool call together
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"simplify","arguments":{"expression":"sin(x)^2 + cos(x)^2"}}}') | \
 docker run -i --rm math-mcp
```

Expected response includes initialization result, then tool result:
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{...},"serverInfo":{"name":"Math","version":"1.25.0"}}}
{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"1"}]}}
```

#### Example Tool Calls

Each tool call requires the initialization sequence. Here are examples:

```bash
# Solve equation: x^2 - 4 = 0
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"solve","arguments":{"equation":"x^2 - 4","variable":"x"}}}') | \
 docker run -i --rm math-mcp

# Compute derivative of x^3
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"derivative","arguments":{"expression":"x^3","variable":"x"}}}') | \
 docker run -i --rm math-mcp

# Evaluate 2*pi
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"evaluate","arguments":{"expression":"2*pi"}}}') | \
 docker run -i --rm math-mcp

# Convert 100 meters to kilometers
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"convert_unit","arguments":{"value":100,"from_unit":"meter","to_unit":"kilometer"}}}') | \
 docker run -i --rm math-mcp

# Solve ODE: dx/dt = -x with x(0)=1 from t=0 to t=5
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"solve_ode","arguments":{"equations":["dx/dt = -x"],"initial_conditions":{"x":1.0},"time_span":[0.0,5.0],"method":"rk45"}}}') | \
 docker run -i --rm math-mcp

# Find root of x^2 - 4 = 0 near x=1
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_root","arguments":{"function":"x^2 - 4","initial_guess":1.0,"bracket":[0.0,3.0],"method":"brentq"}}}') | \
 docker run -i --rm math-mcp
```

**Note:** For local Python usage, replace `docker run -i --rm math-mcp` with `python -m math_mcp.server`.

#### HTTP Transport Usage

When running in HTTP mode, the server exposes a REST endpoint using Server-Sent Events (SSE). First, start the server:

```bash
# Using default port 8008
docker run -d -p 8008:8008 --name math-mcp-server \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8008 \
  math-mcp

# Or using a custom port (e.g., 9000)
docker run -d -p 9000:9000 --name math-mcp-server \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=9000 \
  math-mcp
```

**Important:** The streamable-http transport requires:
- `Accept: application/json, text/event-stream` header (for SSE)
- Session ID management (extract from initialization response)

**Example: Initialize and call tools via HTTP**

```bash
# Step 1: Initialize and capture session ID
RESPONSE=$(curl -s -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -D - \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')

# Extract session ID from response headers
SESSION_ID=$(echo "$RESPONSE" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r')

# Step 2: Call tools using the session ID
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"simplify","arguments":{"expression":"sin(x)^2 + cos(x)^2"}}}'

# Expected response (SSE format):
# event: message
# data: {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"1"}],...}}
```

**Complete example with multiple tool calls:**

```bash
# Initialize
RESPONSE=$(curl -s -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -D - \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')

SESSION_ID=$(echo "$RESPONSE" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r')

# Simplify expression
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"simplify","arguments":{"expression":"sin(x)^2 + cos(x)^2"}}}'

# Solve equation
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"solve","arguments":{"equation":"x^2 - 4","variable":"x"}}}'

# Evaluate expression
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"evaluate","arguments":{"expression":"2*pi"}}}'
```

**From other Docker containers:**
```bash
# If running in a Docker network, use the container name and configured port
# (replace 8008 with your MCP_PORT value)
RESPONSE=$(curl -s -X POST http://math-mcp-server:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -D - \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')

SESSION_ID=$(echo "$RESPONSE" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r')

curl -X POST http://math-mcp-server:8008/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"simplify","arguments":{"expression":"x + x"}}}'
```

#### Interactive Session with Multiple Requests

For multiple tool calls, send the full initialization sequence followed by your requests:

```bash
cat > requests.jsonl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"simplify","arguments":{"expression":"x + x"}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"solve","arguments":{"equation":"x^2 - 9","variable":"x"}}}
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"derivative","arguments":{"expression":"x^3","variable":"x"}}}
EOF

cat requests.jsonl | docker run -i --rm math-mcp
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run in stdio mode (default)
python -m math_mcp.server

# Run in HTTP mode
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8008 python -m math_mcp.server
```

## Testing

```bash
source .venv/bin/activate
PYTHONPATH=src pytest tests/ -v
```

See [docs/TESTING.md](./docs/TESTING.md) for details.

## Docs

- [AGENT.md](./AGENT.md) — Usage guide for AI agents
- [docs/SPEC.md](./docs/SPEC.md) — Specification
- [docs/TESTING.md](./docs/TESTING.md) — Testing guide
