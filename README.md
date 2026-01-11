# Math MCP Server

Powerful symbolic mathematics for Cursor AI. Solve equations, compute derivatives and integrals, simplify expressions, and more—all through natural language requests. Powered by SymPy.

## Quick Start with Docker

```bash
# Build
docker build -t math-mcp .

# Test
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker run -i --rm math-mcp
```

## Add to Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`). This enables Cursor to use 8 powerful math tools for solving equations, computing derivatives/integrals, simplifying expressions, and more.

**What this adds:** Symbolic mathematics server powered by SymPy with tools for:
- Solving equations and finding roots
- Computing derivatives and integrals
- Simplifying and manipulating algebraic expressions
- Evaluating expressions numerically
- Converting to LaTeX format
- Converting decimals to fractions and simplifying fractions
- Converting between measurement units (length, mass, time, temperature, etc.)

### Option 1: Docker (Recommended)

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

### Option 2: Local Python

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

See [`mcp.json.example`](./mcp.json.example) for a complete example configuration file. You can copy it to `~/.cursor/mcp.json` and customize as needed.

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

Cursor automatically discovers all 11 tools and chooses the right one based on your question.

## Why Use This?

This MCP server gives Cursor powerful symbolic math capabilities powered by SymPy. Instead of guessing at math or writing code, Cursor can:

- **Solve equations** - Find roots, solve for variables, answer "what is x?" questions
- **Do calculus** - Compute derivatives and integrals symbolically
- **Simplify expressions** - Reduce complex math to simplest form
- **Evaluate numerically** - Get concrete answers from symbolic expressions
- **Format math** - Convert to LaTeX for documentation

Perfect for code that involves math, physics simulations, data analysis, or any task requiring mathematical computation.

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

## Examples

### Basic Operations

```python
# Simplify expressions
simplify(expression="x^2 + 2*x + 1")           → "(x + 1)**2"
simplify(expression="sin(x)^2 + cos(x)^2")     → "1"

# Solve equations (equation = 0)
solve(equation="x^2 - 4", variable="x")         → ["-2", "2"]
solve(equation="2*x - 8", variable="x")        → ["4"]

# Calculus
derivative(expression="x^3", variable="x")    → "3*x**2"
integral(expression="x^2", variable="x")       → "x**3/3"

# Evaluate numerically
evaluate(expression="2*pi")                    → "6.28318530717959"
evaluate(expression="x^2 + 1", values={"x": 3}) → "10"

# Fractions
to_fraction(value="0.5")                      → "1/2"
to_fraction(value="0.75")                    → "3/4"
simplify_fraction(fraction="6/8")            → "3/4"
simplify_fraction(fraction="(x^2-4)/(x-2)")  → "x + 2"

# Unit conversion
convert_unit(value=100, from_unit="meter", to_unit="kilometer") → "0.1"
convert_unit(value=32, from_unit="fahrenheit", to_unit="celsius") → "0"
convert_unit(value=1, from_unit="hour", to_unit="minute") → "60"
```

### Real-World Use Cases

**Solving word problems:**
```python
# "If 2x + 5 = 13, what is x?"
# Rearrange: 2x + 5 - 13 = 0 → 2x - 8 = 0
solve(equation="2*x - 8", variable="x")  → ["4"]
```

**Finding critical points:**
```python
# Find where f(x) = x^3 - 3x has zero derivative
derivative(expression="x^3 - 3*x", variable="x")  → "3*x**2 - 3"
solve(equation="3*x^2 - 3", variable="x")         → ["-1", "1"]
```

**Verifying identities:**
```python
# Check if (a+b)^2 = a^2 + 2ab + b^2
simplify(expression="(a+b)^2 - (a^2 + 2*a*b + b^2)")  → "0"  # They're equal!
```

**Formatting for documentation:**
```python
latex(expression="x^2 + 1/2")  → "x^{2} + \\frac{1}{2}"
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m math_mcp.server
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
