# Math MCP Server

Powerful symbolic mathematics and statistical analysis for Cursor AI and Claude Desktop. Solve equations, compute derivatives and integrals, perform statistical tests, analyze data, and more—all through natural language requests. Powered by SymPy and SciPy.

## What This Does

The Math MCP server provides Cursor and Claude Desktop with powerful symbolic and numerical math capabilities. Instead of guessing at math or writing code, you can ask natural language questions and get accurate mathematical results.

### Available Tools (4-tool interface)

The server exposes **4 tools** via `list_tools`. Discovery and execution use these:

| Tool | Purpose |
|------|---------|
| `math_ls` | List available math tools. Call with no args for categories and a flat list (name + intent). Call `math_ls(category)` for full descriptors (name, description, inputSchema) for every tool in that category. |
| `math_man` | Return the full descriptor (name, description, inputSchema) for a named math tool. Use after `math_ls()` to get parameters. |
| `math` | Execute a math tool by name. Call `math(name, arguments)` with a tool from `math_ls()` and its arguments. |
| `math_batch` | Run multiple tools in one request; results in call order. Pass `calls`: list of `{name, arguments}`. |

**Discovery flow:** Call `math_ls()` to see all 26 internal tools (algebra, calculus, numbers, stats, ode, charts, output). Use `math_man(name)` for one tool’s parameters or `math_ls(category)` for a full category. Then call `math(name, arguments)` to run.

Internal tools (26) include: `simplify`, `solve`, `factor`, `expand`, `derivative`, `integral`, `evaluate`, `to_fraction`, `convert_unit`, `find_root`, `describe_data`, `ttest`, `correlation`, `linear_regression`, `moving_average`, `solve_ode`, `plot_ode_solution`, `plot_timeseries`, `plot_bar`, `plot_histogram`, `plot_scatter`, `plot_heatmap`, `plot_stacked_bar`, `plot_stackplot`, `plot_pie`, `latex`.

### Example Usage

Once configured, you can ask math questions naturally:

- **"Solve x^2 - 4 = 0"** → Finds roots using `solve` tool
- **"What's the derivative of x^3?"** → Computes derivative using `derivative` tool
- **"Simplify sin(x)^2 + cos(x)^2"** → Simplifies expression using `simplify` tool
- **"Evaluate 2*pi"** → Evaluates numerically using `evaluate` tool
- **"Factor x^2 - 4"** → Factors expression using `factor` tool
- **"Integrate x^2"** → Computes integral using `integral` tool
- **"Convert x^2 + 1/2 to LaTeX"** → Converts to LaTeX using `latex` tool
- **"Convert 0.5 to a fraction"** → Converts decimal using `to_fraction` tool
- **"Simplify 6/8"** → Simplifies fraction using `simplify` tool (e.g. `math("simplify", {"expression": "6/8"})` → "3/4")
- **"Convert 100 meters to kilometers"** → Converts units using `convert_unit` tool
- **"Solve dx/dt = -x with x(0)=1 from t=0 to t=5"** → Solves ODE using `solve_ode` tool
- **"Find the root of x^2 - 4 near x=1"** → Finds root using `find_root` tool
- **"What's the p95 response time for these values?"** → Computes descriptive statistics using `describe_data` tool
- **"Is there a significant difference between these two samples?"** → Performs t-test using `ttest` tool
- **"What's the correlation between traffic and error rate?"** → Calculates correlation using `correlation` tool
- **"Fit a linear trend to this data"** → Performs regression using `linear_regression` tool
- **"Smooth these metrics with a moving average"** → Applies smoothing using `moving_average` tool
- **"Plot this time series data"** → Creates visualization using `plot_timeseries` tool
- **"Create a bar chart of these categories"** → Creates chart using `math("plot_bar", {...})`
- **"Show me a histogram of these values"** → Creates histogram using `plot_histogram` tool
- **"Plot this data with custom colors: red for series A, blue for series B"** → Uses `colors` parameter in plotting tools
- **"Create a bar chart with green bars"** → Uses `color` parameter for single-color plots
- **"Plot this time series with the legend in the upper right corner"** → Uses `legend_loc` parameter
- **"Show this data with a secondary y-axis for temperature"** → Uses `secondary_y` parameter for dual-axis plots
- **"Plot with dashed lines for the first series and solid for the second"** → Uses `linestyles` parameter
- **"Create a bar chart with horizontal bars"** → Uses `horizontal=True` parameter
- **"Plot this data with x-axis limits from 0 to 100"** → Uses `xlim` parameter to set axis range
- **"Show this histogram with y-axis from 0 to 50"** → Uses `ylim` parameter to set axis range
- **"Plot with no grid lines"** → Uses `grid=False` parameter
- **"Create a chart with only vertical grid lines"** → Uses `grid='y'` parameter
- **"Plot this time series with rotated x-axis labels at 90 degrees"** → Uses `xlabel_rotation` parameter
- **"Create a larger plot, 1200 by 800 pixels"** → Uses `figsize` parameter to control plot dimensions (in pixels)
- **"Plot this time series with values displayed on each point"** → Uses `show_values=True` parameter to display data point values
- **"Format values as currency with 2 decimals"** → Uses `value_format='$.2f'` parameter for currency formatting
- **"Run simplify, evaluate, and solve in one go"** → Use `math_batch` with `calls`: list of `{name, arguments}`; results are returned in the same order

Cursor and Claude Desktop see the 4 tools; use `math_ls()` then `math(name, arguments)` or `math_man(name)` to discover and run the 26 math capabilities.

Perfect for code that involves math, physics simulations, data analysis, statistical testing, performance monitoring, engineering problems, or any task requiring mathematical computation.

## Quick Start

Get up and running with Math MCP in Cursor or Claude Desktop using Docker stdio (recommended).

### Step 1: Build the Docker Image

```bash
docker build -t math-mcp .
```

### Step 2: Configure Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`):

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

**If you already have other MCP servers configured**, just add `"math-mcp"` to your existing `mcpServers` object:

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

**Restart Cursor** for the changes to take effect.

### Step 3: Configure Claude Desktop

Add to your Claude Desktop MCP settings. The configuration file location varies by OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

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

**Restart Claude Desktop** for the changes to take effect.

### That's It!

Once configured, you can ask math questions naturally in Cursor or Claude. See [Example Usage](#example-usage) above for examples.

---

## Using the Cursor skill (in-repo)

This repo includes a **Cursor skill tree** in [`docs/skills/math-mcp/`](./docs/skills/math-mcp/) that guides AI agents on when and how to use the Math MCP server: 4-tool interface, problem classification, data preparation, analysis workflow, visualization, and batching.

### What’s included

| Path | Purpose |
|------|---------|
| [docs/skills/math-mcp/SKILL.md](./docs/skills/math-mcp/SKILL.md) | Main skill: when to use math-mcp, tool discovery (`math_ls`, `math_man`, `math`, `math_batch`), tool reference, execution guidelines |
| [docs/skills/math-mcp/references/data-preparation.md](./docs/skills/math-mcp/references/data-preparation.md) | DuckDB + jq data pipeline, MCP artifacts pattern |
| [docs/skills/math-mcp/references/analysis-workflow.md](./docs/skills/math-mcp/references/analysis-workflow.md) | Step-by-step analysis, data size, multi-variable and complex problems |
| [docs/skills/math-mcp/references/visualization.md](./docs/skills/math-mcp/references/visualization.md) | Chart design, graph type selection, color and quality checklist |

### Use in this repo

With the Math MCP server configured (see [Quick Start](#quick-start) or [HTTP Endpoint Setup](#http-endpoint-setup-alternative)), Cursor can use the skill when working in this workspace. Reference the skill so the agent loads it for math-related tasks, for example:

- In **Cursor rules**: add a rule that points at `docs/skills/math-mcp/SKILL.md` for math, statistics, or data visualization tasks.
- In **AGENTS.md**: list `docs/skills/math-mcp/SKILL.md` under key docs so agents read it when handling math or analysis.

### Use in other projects (global install)

To make the math-mcp skill available in all Cursor projects:

```bash
# From this repo root
cp -r docs/skills/math-mcp ~/.cursor/skills/math-mcp
```

Or symlink to stay in sync with the repo:

```bash
ln -s "$(pwd)/docs/skills/math-mcp" ~/.cursor/skills/math-mcp
```

Then ensure the Math MCP server is configured in each project (or globally) where you want to use it. The skill will tell the agent to use `math_ls()` → `math_man(name)` / `math_ls(category)` → `math(name, arguments)` and `math_batch` for batched calls.

---

## HTTP Endpoint Setup (Alternative)

For users who want a persistent MCP server accessible via HTTP, use Docker Compose to run a long-lived container. This is useful when:
- You want a single server instance shared across multiple clients
- You're integrating with other applications or services
- You prefer managing the server lifecycle independently

### Step 1: Start the Server with Docker Compose

```bash
# Build the image (first time only)
docker build -t math-mcp .

# Start the persistent server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server when done
docker-compose down
```

**Configuration:**
- The server runs on port 8008 by default (configurable via `.env` file)
- See `env.example` for all available environment variables
- Copy `env.example` to `.env` to customize settings

### Step 2: Configure Cursor or Claude Desktop

To connect to the HTTP endpoint, you'll use the `mcp-remote` package which acts as a proxy between the stdio-based MCP client and your HTTP server.

**Note:** `mcp-remote` requires Node.js 20 or higher. Make sure you have a compatible version installed before configuring the HTTP endpoint.

#### For Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "math-mcp": {
      "command": "/path/to/node",
      "args": ["/path/to/npx", "-y", "mcp-remote", "http://localhost:8008/mcp"]
    }
  }
}
```

**Note:** Replace `/path/to/node` and `/path/to/npx` with actual paths on your system. To find the paths:
- **macOS/Linux**: Run `which node` and `which npx` in your terminal
- **Windows**: Run `where node` and `where npx` in your command prompt

For example, on macOS/Linux:
```bash
which node   # Returns something like: /usr/local/bin/node
which npx    # Returns something like: /usr/local/bin/npx
```

Then use those paths in your configuration.

**Example configuration files:**
- [`docs/mcp.json`](./docs/mcp.json) - stdio Docker configuration (recommended for most users)
- [`docs/mcp.json.http`](./docs/mcp.json.http) - HTTP endpoint configuration (requires persistent server)

#### For Claude Desktop

The configuration is the same format. Add to your Claude Desktop MCP settings:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "math-mcp": {
      "command": "/path/to/node",
      "args": ["/path/to/npx", "-y", "mcp-remote", "http://localhost:8008/mcp"]
    }
  }
}
```

**Note:** Replace `/path/to/node` and `/path/to/npx` with actual paths. Use `which node` and `which npx` (macOS/Linux) or `where node` and `where npx` (Windows) to find them.

**Example configuration files:**
- [`docs/claude_desktop_config.json`](./docs/claude_desktop_config.json) - HTTP endpoint configuration example
- Same format as Cursor's `mcp.json` (see `docs/mcp.json` for stdio Docker mode)

### Step 3: Restart and Test

**Restart Cursor or Claude Desktop** for the changes to take effect. The client will now connect to your persistent HTTP server.

### Managing the Server

```bash
# Check server status
docker-compose ps

# View logs
docker-compose logs -f math-mcp

# Restart server
docker-compose restart

# Stop server
docker-compose down

# Update and rebuild
docker build -t math-mcp .
docker-compose up -d
```

### Troubleshooting

- **Connection refused**: Ensure the server is running with `docker-compose ps`
- **Port conflict**: Change `MCP_HOST_PORT` in `.env` file and update the URL in your config
- **Node/npx not found**: Install Node.js from [nodejs.org](https://nodejs.org/) or use your system package manager
- **mcp-remote errors**: `mcp-remote` requires Node.js 20 or higher. Check your version with `node --version` and upgrade if needed

---

## Running the Server

The server supports two transport modes:
- **stdio** (default): For CLI usage and Cursor/Claude Desktop integration via Docker
- **streamable-http**: For persistent hosting accessible via HTTP from Docker networks and host applications

### CLI & Docker CLI (stdio mode)

Perfect for command-line usage and Cursor/Claude Desktop integration.

#### Build the Docker Image

```bash
docker build -t math-mcp .
```

#### Test the Server

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker run -i --rm math-mcp
```

#### Local Python (Alternative to Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m math_mcp.server
```

### HTTP Mode

For persistent hosting accessible from Docker networks and host applications.

#### Option 1: Docker Compose (Recommended)

```bash
# Start the server (uses docker-compose.yml)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

**Configuration:**
- Create a `.env` file or set environment variables
- See `docker-compose.yml` for all available options
- Default: HTTP server on port 8008, accessible from host and Docker network

**Example .env file:**
```bash
# Copy env.example to .env and customize
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8008
MCP_HOST_PORT=8008
MCP_PATH=/mcp
```

**Accessing from other containers:**
```bash
# Server is accessible at: http://math-mcp-server:8008/mcp
# (or use the container name and your configured port)
```

#### Option 2: Docker CLI

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
- `MCP_OUTPUT_DIR=/outputs/` - Base directory for plot output files (default: /outputs/)
- `MCP_OUTPUT_VOLUME=./outputs` - Output volume mount path (bind mount or named volume)

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

# Run server in network
docker run -d --name math-mcp-server --network math-network \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8008 \
  math-mcp

# Other containers in the same network can access:
# http://math-mcp-server:<MCP_PORT>/mcp
```

#### Option 3: Local Python

```bash
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8008 python -m math_mcp.server
```

## Add to Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`) to enable the math server (4 tools: math_ls, math_man, math, math_batch). See [What This Does](#what-this-does) above for discovery and capabilities.

### CLI/Docker CLI Configuration (Recommended for Cursor)

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

**Note:** 
- Make sure you've built the Docker image first: `docker build -t math-mcp .`
- **Initialization is automatic**: Cursor automatically handles the MCP protocol initialization handshake. You don't need to do anything manually.

### Local Python Configuration

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

See example configuration file:
- [`docs/mcp.json`](./docs/mcp.json) - Docker CLI configuration

You can copy it to `~/.cursor/mcp.json` and customize as needed.

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

## Add to Claude Desktop

Add to your Claude Desktop MCP settings. The configuration file location varies by OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration

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

**Note:** 
- Make sure you've built the Docker image first: `docker build -t math-mcp .`
- **Initialization is automatic**: Claude Desktop automatically handles the MCP protocol initialization handshake. You don't need to do anything manually.

After updating the configuration file, restart Claude Desktop for the changes to take effect.

## Statistical Analysis

The Math MCP server includes powerful statistical analysis tools for data analysis, A/B testing, and performance monitoring. All tools use `scipy.stats` for reliable, production-ready statistical computations.

### Available Statistical Tools

**1. Descriptive Statistics (`describe_data`)**
- Compute comprehensive summary statistics
- Calculate percentiles (p25, p50, p75, p95, p99) critical for SLAs
- Perfect for: API response times, query performance, user session lengths
- Returns: count, mean, median, std, variance, min, max, range, percentiles
- Example: `data=[120, 145, 167, 123, 189, 134]` → Full statistics summary

**2. T-Test (`ttest`)**
- Perform one-sample or two-sample t-tests
- Determine if differences are statistically significant
- Perfect for: A/B testing, before/after comparisons, feature impact analysis
- Supports: two-sided, greater, less alternatives
- Returns: statistic, p-value, degrees of freedom, significance (α=0.05)
- Example: `sample1=[100, 102, 98, 105], sample2=[95, 97, 99, 94]` → Two-sample comparison

**3. Correlation (`correlation`)**
- Calculate correlation coefficients between variables
- Methods: Pearson (linear), Spearman (monotonic), Kendall (rank-based)
- Perfect for: Traffic vs errors, cache hit rate vs response time, metric relationships
- Returns: correlation coefficient, p-value, method used
- Example: `x_data=[100, 200, 300], y_data=[0.02, 0.05, 0.03]` → Pearson correlation

**4. Linear Regression (`linear_regression`)**
- Fit linear models and analyze trends
- Perfect for: Capacity planning, trend analysis, growth forecasting
- Returns: slope, intercept, R², p-value, equation string
- Example: `x_data=[1, 2, 3, 4], y_data=[2, 4, 6, 8]` → Perfect fit (R²=1.0)

**5. Moving Average (`moving_average`)**
- Smooth time series data to filter noise
- Methods: Simple (equal weights) or Exponential (weighted toward recent)
- Perfect for: Smoothing error rates, response time trends, cleaner dashboards
- Returns: smoothed values, original data, window size, method
- Example: `data=[10, 12, 11, 15, 13, 14, 12], window=3` → 3-period average

### Use Cases for Web Developers

- **Performance Monitoring**: Analyze response times, calculate p95/p99 latencies
- **A/B Testing**: Compare conversion rates, feature adoption, user engagement
- **Capacity Planning**: Forecast growth, predict when scaling is needed
- **Anomaly Detection**: Identify trends vs. random fluctuations
- **Metric Relationships**: Understand correlations between system metrics

## Plotting & Visualization

The Math MCP server includes powerful plotting tools for data visualization. All plots are returned as inline images that appear directly in your conversation.

### Available Plot Types

**1. Time Series (`plot_timeseries`)**
- Plot metrics over time with multiple series
- Perfect for: response times, traffic patterns, error rates
- Features: Display values on data points, currency formatting, secondary y-axis, custom linestyles
- Example: `timestamps=['2026-01-01T10:00', '2026-01-01T11:00'], series={'cpu': [45, 67], 'memory': [60, 62]}`
- Example with values: `timestamps=['Q1', 'Q2', 'Q3'], series={'sales': [1000, 1200, 1150]}, show_values=True, value_format='$.0f'`

**2. Bar Charts (`plot_bar` via math)**
- Compare values across categories
- Perfect for: endpoint usage, error counts by type, feature adoption
- Features: Display values on bars, currency formatting, both vertical and horizontal orientations
- Example: `categories=['Endpoint A', 'Endpoint B'], values=[1250, 890]`
- Example with currency: `categories=['Q1', 'Q2'], values=[1000, 1200], value_format='$.0f'`

**3. Histograms (`plot_histogram`)**
- Visualize data distribution and frequency
- Perfect for: response time distributions, latency analysis
- Includes automatic statistics (mean, median, std dev)
- Example: `data=[120, 145, 167, 123, 189, ...]`

**4. Scatter Plots (`plot_scatter`)**
- Show correlation between two variables
- Perfect for: traffic vs errors, cache hit rate vs response time
- Displays correlation coefficient
- Optional point labels
- Example: `x_data=[100, 200, 300], y_data=[0.02, 0.05, 0.03]`

**5. Heatmaps (`plot_heatmap`)**
- Visualize 2D patterns
- Perfect for: request patterns by hour/day, geographic distribution, error hotspots
- Customizable colormaps
- Example: `data=[[10, 20], [30, 40]], x_labels=['Mon', 'Tue'], y_labels=['Morning', 'Evening']`

**6. Stacked Bar Charts (`plot_stacked_bar`)**
- Compare multiple series across categories
- Perfect for: status code breakdown, multi-environment comparison
- Supports both vertical and horizontal orientations
- Example: `categories=['Jan', 'Feb'], series={'success': [100, 120], 'error': [10, 8]}`

**7. Stacked Area Charts (`plot_stackplot`)**
- Show composition of multiple components over a continuous variable
- Perfect for: revenue breakdown over time, resource usage composition, multi-component trends
- Supports customizable colors and baseline options
- Example: `x_data=[0, 1, 2, 3], series={'component_a': [10.5, 12.3, 11.8, 13.2], 'component_b': [5.2, 4.8, 6.1, 5.5]}`

**8. Pie Charts (`plot_pie` via math)**
- Display proportional data and percentage breakdowns
- Perfect for: market share, status code distribution, category proportions
- Supports slice explosion, custom colors, and percentage display
- Example: `labels=['Category A', 'Category B', 'Category C'], values=[25.5, 18.9, 32.1]`

**9. ODE Solution Plots (`plot_ode_solution`)**
- Visualize differential equation solutions
- Automatically plots all variables from `solve_ode` output
- Example: `ode_result='{"t": [0, 1, 2], "x": [1, 0.5, 0.25], ...}'`

### Integration with ODE Solver

You can solve differential equations and immediately visualize the results:

```bash
# 1. Solve ODE
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"solve_ode","arguments":{"equations":["dx/dt = -x"],"initial_conditions":{"x":1.0},"time_span":[0.0,5.0]}}}') | \
 docker run -i --rm math-mcp

# 2. Plot the solution (pass the JSON result from step 1)
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_ode_solution","arguments":{"ode_result":"<paste result here>"}}}') | \
 docker run -i --rm math-mcp
```

### Features

- **In-memory only**: No disk I/O, all images generated in memory
- **Automatic display**: Images appear inline in Cursor/Claude conversations
- **Consistent styling**: Professional appearance with grid lines, labels, and legends
- **Memory efficient**: Figures are immediately closed after saving
- **IT-focused**: Designed for operational data visualization
- **Value display**: Show data point values on charts with customizable formatting (including currency)
- **Pixel-based sizing**: Figure sizes specified in pixels for consistent display across devices
- **Format flexibility**: Support for PNG and SVG output formats

## Examples

### CLI & Docker CLI Usage

The MCP server communicates via JSON-RPC over stdio. 

**Note:** When using with Cursor or Claude Desktop, initialization is handled automatically by the client. The examples below are for **manual CLI/testing** scenarios where you're directly sending JSON-RPC messages to the server.

For manual usage, you must initialize the server before calling tools.

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

#### List Available Tools

To see all available tools, use the `tools/list` method:

```bash
# List all available tools
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}') | \
 docker run -i --rm math-mcp
```

Expected response includes the 4 meta-tools (math_ls, math_man, math, math_batch). Use `math_ls()` to discover the 26 internal tools:
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{...},"serverInfo":{"name":"Math","version":"1.25.0"}}}
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"math_ls","description":"List available math tools..."},{"name":"math_man",...},{"name":"math",...},{"name":"math_batch",...}]}}
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

# Plot time series with custom colors
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_timeseries","arguments":{"timestamps":["2026-01-01T10:00","2026-01-01T11:00","2026-01-01T12:00"],"series":{"cpu":[45,67,52],"memory":[60,62,58]},"colors":["red","blue"],"title":"System Metrics"}}}') | \
 docker run -i --rm math-mcp

# Create bar chart with custom color and horizontal orientation (via math dispatcher)
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"math","arguments":{"tool":"plot_bar","arguments":{"categories":["Endpoint A","Endpoint B","Endpoint C"],"values":[1250,890,1100],"color":"#FF5733","horizontal":true,"title":"Request Counts"}}}}') | \
 docker run -i --rm math-mcp

# Plot histogram with axis limits and no grid
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_histogram","arguments":{"data":[120,145,167,123,189,134,156,178,145,167],"bins":10,"xlim":[100,200],"ylim":[0,5],"grid":false,"title":"Response Time Distribution"}}}') | \
 docker run -i --rm math-mcp

# Plot time series with secondary y-axis and custom linestyles
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_timeseries","arguments":{"timestamps":["10:00","11:00","12:00","13:00"],"series":{"requests":[100,200,150,180],"temperature":[20.5,21.3,22.1,21.8]},"secondary_y":{"temperature":"Temperature (°C)"},"linestyles":["-","--"],"legend_loc":"upper left"}}}') | \
 docker run -i --rm math-mcp

# Create scatter plot with custom figure size (in pixels) and rotated labels
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_scatter","arguments":{"x_data":[100,200,300,400,500],"y_data":[0.02,0.05,0.03,0.06,0.04],"color":"steelblue","figsize":[1200,800],"title":"Traffic vs Error Rate","xlabel":"Requests per second","ylabel":"Error Rate"}}}') | \
docker run -i --rm math-mcp

# Plot time series with values displayed on each point and currency formatting
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_timeseries","arguments":{"timestamps":["Q1","Q2","Q3"],"series":{"sales":[1000,1200,1150]},"show_values":true,"value_format":"$.0f","title":"Quarterly Sales"}}}') | \
docker run -i --rm math-mcp

# Plot stacked bar chart with custom colors and legend
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_stacked_bar","arguments":{"categories":["Jan","Feb","Mar"],"series":{"success":[100,120,110],"error":[10,8,12],"warning":[5,3,4]},"colors":["green","red","orange"],"legend_loc":"upper right","xlabel_rotation":0}}}') | \
docker run -i --rm math-mcp

# Create stacked area chart showing composition over time
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"plot_stackplot","arguments":{"x_data":["Q1","Q2","Q3","Q4"],"series":{"product_x":[100,120,110,130],"product_y":[80,90,95,100]},"title":"Revenue by Product"}}}') | \
docker run -i --rm math-mcp

# Create pie chart with percentage display and custom colors (via math dispatcher)
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"math","arguments":{"tool":"plot_pie","arguments":{"labels":["Category A","Category B","Category C"],"values":[25.5,18.9,32.1],"title":"Distribution","colors":["steelblue","coral","lightgreen"]}}}}') | \
docker run -i --rm math-mcp
```

**Note:** For local Python usage, replace `docker run -i --rm math-mcp` with `python -m math_mcp.server`.

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

### HTTP Usage

When running in HTTP mode, the server exposes a REST endpoint using Streamable HTTP transport. First, start the server (see [HTTP Mode](#http-mode) section above).

**Important:** The streamable-http transport requires:
- `Accept: application/json, text/event-stream` header
- Session ID management via `mcp-session-id` header (extract from initialization response)

#### Initialize and Call Tools via HTTP

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

# Expected response (Streamable HTTP format):
# event: message
# data: {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"1"}],...}}
```

#### Complete Example with Multiple Tool Calls

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

#### From Other Docker Containers

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

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run in stdio mode (default)
python -m math_mcp.server

# Run in HTTP mode
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8008 python -m math_mcp.server
```

## Testing

```bash
source .venv/bin/activate
PYTHONPATH=src pytest tests/ -v
```

See [docs/TESTING.md](./docs/TESTING.md) for details.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

Copyright (c) 2026 codeprimate

## Docs

- [AGENTS.md](./AGENTS.md) — Development guide for AI agents (build, test, lint)
- [docs/skills/math-mcp/](./docs/skills/math-mcp/) — Cursor skill tree for using Math MCP (see [Using the Cursor skill](#using-the-cursor-skill-in-repo))
- [docs/SPEC.md](./docs/SPEC.md) — Specification
- [docs/TESTING.md](./docs/TESTING.md) — Testing guide
