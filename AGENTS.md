# AGENTS.md - Development Guide

Python MCP server providing 27+ tools for symbolic mathematics, statistical analysis, and visualization.

## Quick Start

This project uses **uv** for environment and dependency management.

```bash
# Setup (first time)
uv venv
source .venv/bin/activate
uv sync

# Daily workflow
source .venv/bin/activate
ruff check --fix src/ tests/
PYTHONPATH=src pytest tests/ -v
```

Or use `uv run` so you don't need to activate the venv:

```bash
uv run ruff check --fix src/ tests/
PYTHONPATH=src uv run pytest tests/ -v
```

## Critical Requirements

1. **Use uv:** Create venv with `uv venv`, install deps with `uv sync`. Optionally use `uv run` for commands instead of activating the venv.
2. **Always run linter:** `ruff check --fix src/ tests/` after code changes
3. **Tests require PYTHONPATH:** `PYTHONPATH=src pytest tests/ -v`

## Project Structure

```
src/math_mcp/     # Source code
tests/            # Test suite
pyproject.toml    # Project config
```

## Key Files & Documentation

- **[README.md](./README.md)** - Main project documentation, tool descriptions, usage examples
- **[pyproject.toml](./pyproject.toml)** - Project configuration, dependencies, coverage settings
- **[env.example](./env.example)** - Environment variable reference for HTTP mode
- **[docs/mcp.json](./docs/mcp.json)** - Example Cursor/Claude Desktop config (stdio Docker)
- **[docs/mcp.json.http](./docs/mcp.json.http)** - Example HTTP endpoint config
- **[docs/claude_desktop_config.json](./docs/claude_desktop_config.json)** - Claude Desktop example
- **[docker-compose.yml](./docker-compose.yml)** - Docker Compose configuration

## Development Workflow

1. **Research** - Understand requirements and plan
2. **Implement** - Code in `src/math_mcp/`, tests in `tests/`
3. **Lint** - `ruff check --fix src/ tests/`
4. **Test** - `PYTHONPATH=src pytest tests/ -v`
5. **Iterate** - Repeat until complete
6. **Docker** - `docker-compose build && docker-compose restart`

## Commands

### Setup
```bash
uv venv
source .venv/bin/activate
uv sync
```

### Linting
```bash
ruff check src/ tests/
ruff check --fix src/ tests/
```

### Testing
```bash
# Unit tests
PYTHONPATH=src pytest tests/ -v
PYTHONPATH=src pytest tests/ --cov=src --cov-report=json

# Integration test (requires HTTP server running)
docker-compose build && docker-compose up -d  # Start HTTP server
./tests/test-plot-http.sh  # Test plot via HTTP endpoint
```

### Server
```bash
# Stdio mode
python -m math_mcp.server

# HTTP mode
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8008 python -m math_mcp.server
```

### Docker
```bash
docker-compose build
docker-compose restart  # or docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Dependencies

- **sympy** (>=1.12): Symbolic math
- **scipy** (>=1.10): Scientific computing
- **numpy** (>=1.24): Numerical computing
- **matplotlib** (>=3.7.0): Plotting
- **mcp[cli]** (>=1.0.0): MCP protocol
- **pydantic** (>=2.0): Validation

## Configuration

Environment variables (see `env.example`):
- `MCP_TRANSPORT`: `stdio` or `streamable-http`
- `MCP_HOST`: HTTP host (default: `0.0.0.0`)
- `MCP_PORT`: HTTP port (default: `8008`)

## Important Notes

- Use **uv** for venv and dependencies (`.venv`); run `uv sync` after pulling changes
- Source: `src/math_mcp/` (not `math_mcp/`)
- Tests: `tests/` (not `test/`)
- Entry point: `python -m math_mcp.server`
- Python: >=3.10
- Linter: ruff
- Test framework: pytest
