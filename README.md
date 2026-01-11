# Math MCP Server

Minimal MCP server for symbolic math using SymPy.

## Quick Start with Docker

```bash
# Build
docker build -t math-mcp .

# Test
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker run -i --rm math-mcp
```

## Add to Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "math": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "math-mcp"]
    }
  }
}
```

Then restart Cursor.

## Tools

| Tool | Purpose |
|------|---------|
| `simplify` | Simplify expression |
| `solve` | Solve equation for variable |
| `derivative` | Compute derivative |
| `integral` | Compute integral |
| `expand` | Expand expression |
| `factor` | Factor expression |
| `evaluate` | Evaluate numerically |
| `latex` | Convert to LaTeX |

## Examples

```
simplify(expression="x^2 + 2*x + 1")     → (x + 1)**2
solve(equation="x^2 - 4", variable="x")  → [-2, 2]
derivative(expression="x^3", variable="x") → 3*x**2
evaluate(expression="2*pi")              → 6.28318530717959
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
