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

### `to_fraction`

Convert a decimal number or expression to a rational fraction (exact form).

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | string | Decimal number or expression to convert to fraction, e.g. `0.5`, `0.333`, `1.25` |

**Examples:**
- `0.5` → `1/2`
- `0.333` → `333/1000` (or simplified if exact)
- `1.25` → `5/4`
- `0.75` → `3/4`

---

### `simplify_fraction`

Simplify a fraction to its lowest terms.

| Parameter | Type | Description |
|-----------|------|-------------|
| `fraction` | string | Fraction expression to simplify, e.g. `6/8`, `12/18`, `(x^2-4)/(x-2)` |

**Examples:**
- `6/8` → `3/4`
- `12/18` → `2/3`
- `(x^2-4)/(x-2)` → `x + 2` (if x ≠ 2)

---

### `convert_unit`

Convert a quantity from one unit to another.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | number | Numeric value to convert |
| `from_unit` | string | Source unit (e.g. `meter`, `kilogram`, `second`, `celsius`) |
| `to_unit` | string | Target unit (e.g. `foot`, `pound`, `minute`, `fahrenheit`) |

**Supported unit categories:**
- **Length**: `meter`, `kilometer`, `centimeter`, `millimeter`, `mile`, `foot`, `inch`, `yard`
- **Mass**: `kilogram`, `gram`, `pound`
- **Time**: `second`, `minute`, `hour`, `day`
- **Temperature**: `celsius`, `fahrenheit`, `kelvin` (handles offset conversions correctly)
- **Volume**: `liter`, `milliliter`, `quart`
- **Speed**: `meter_per_second`, `kilometer_per_hour`, `mile_per_hour`

**Examples:**
- `value=100, from_unit="meter", to_unit="kilometer"` → `0.1`
- `value=5, from_unit="kilometer", to_unit="mile"` → `3.106855...`
- `value=32, from_unit="fahrenheit", to_unit="celsius"` → `0`
- `value=1, from_unit="hour", to_unit="minute"` → `60`

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
