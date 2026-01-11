# Math MCP Server Specification

## Overview

Minimal MCP server wrapping SymPy. Provides symbolic math for AI agents.

## Design Principles

### LLM-Friendly API

MCP exposes tools via:
1. **Tool name** — clear, verb-based names
2. **Tool description** — the docstring (what LLMs read to decide which tool to use)
3. **Parameter schema** — generated from type hints
4. **Parameter descriptions** — rich descriptions with examples

**Examples in descriptions are the best "hint" for LLMs.**

## Tools

### `simplify`

Simplify a mathematical expression.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Math expression, e.g. `x^2 + 2*x + 1` |

**Examples:**
- `x^2 + 2*x + 1` → `(x + 1)**2`
- `sin(x)^2 + cos(x)^2` → `1`

---

### `solve`

Solve an equation for a variable. Equation is assumed equal to zero.

| Parameter | Type | Description |
|-----------|------|-------------|
| `equation` | string | Equation to solve, e.g. `x^2 - 4` (means x² - 4 = 0) |
| `variable` | string | Variable to solve for |

**Examples:**
- `equation="x^2 - 4", variable="x"` → `[-2, 2]`
- `equation="2*x - 8", variable="x"` → `[4]`

---

### `derivative`

Compute the derivative of an expression.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Expression to differentiate |
| `variable` | string | Variable to differentiate with respect to |

**Examples:**
- `expression="x^3", variable="x"` → `3*x**2`
- `expression="sin(x)", variable="x"` → `cos(x)`

---

### `integral`

Compute the indefinite integral of an expression.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Expression to integrate |
| `variable` | string | Variable to integrate with respect to |

**Examples:**
- `expression="x^2", variable="x"` → `x**3/3`
- `expression="cos(x)", variable="x"` → `sin(x)`

---

### `expand`

Expand an expression (multiply out, distribute).

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Expression to expand |

**Examples:**
- `(x + 1)^2` → `x**2 + 2*x + 1`
- `(a + b)*(a - b)` → `a**2 - b**2`

---

### `factor`

Factor an expression into products.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Expression to factor |

**Examples:**
- `x^2 - 4` → `(x - 2)*(x + 2)`
- `x^2 + 2*x + 1` → `(x + 1)**2`

---

### `evaluate`

Evaluate an expression numerically.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Expression to evaluate |
| `values` | object (optional) | Variable substitutions, e.g. `{"x": 3}` |

**Examples:**
- `expression="2*pi"` → `6.283185...`
- `expression="x^2 + 1", values={"x": 3}` → `10`

---

### `latex`

Convert expression to LaTeX format.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Expression to convert |

**Examples:**
- `x^2 + 1/2` → `x^{2} + \frac{1}{2}`
- `sqrt(x)` → `\sqrt{x}`

---

## Expression Syntax

SymPy's parser handles:

| Syntax | Examples |
|--------|----------|
| Power | `x^2` or `x**2` |
| Multiply | `2*x` (or `2x`) |
| Functions | `sin(x)`, `cos(x)`, `log(x)`, `sqrt(x)`, `exp(x)` |
| Constants | `pi`, `E`, `I` |

## Response Format

All tools return:

```json
{
  "result": "answer",
  "error": null
}
```

## Dependencies

- `sympy>=1.12`
- `mcp[cli]>=1.0.0`
