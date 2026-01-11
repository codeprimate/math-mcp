# Testing

## Setup

```bash
cd /Users/patrick/Code/math-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install sympy pydantic pytest
pip install -e .
```

## Run Tests

```bash
source .venv/bin/activate
PYTHONPATH=src pytest tests/ -v
```

Or just:

```bash
source .venv/bin/activate && PYTHONPATH=src pytest tests/ -v
```

## Test Structure

Tests are in `tests/test_server.py` and directly call the tool functions:

```python
from math_mcp.server import tool_simplify, tool_solve, ...

def test_example():
    assert tool_simplify("x + x") == "2*x"
```

No MCP protocol testing — just pure function tests against SymPy.

## Notes

- Tests do NOT run in Docker (Docker is for running the server only)
- The `.venv` is gitignored
- `PYTHONPATH=src` is needed because the package is in `src/math_mcp/`
