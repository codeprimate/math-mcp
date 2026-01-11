# Math MCP Server

Symbolic math via SymPy. Eleven tools for algebra, calculus, fractions, unit conversion, and evaluation.

## Tools

| Tool | Purpose |
|------|---------|
| `simplify(expression)` | Simplify expression |
| `solve(equation, variable)` | Solve equation for variable |
| `derivative(expression, variable)` | Compute derivative |
| `integral(expression, variable)` | Compute integral |
| `expand(expression)` | Expand/distribute |
| `factor(expression)` | Factor into products |
| `evaluate(expression, values?)` | Compute numeric result |
| `latex(expression)` | Convert to LaTeX |
| `to_fraction(value)` | Convert decimal to fraction |
| `simplify_fraction(fraction)` | Simplify fraction to lowest terms |
| `convert_unit(value, from_unit, to_unit)` | Convert between units |

## Quick Examples

### Evaluate

```
evaluate("2 + 2")                       → 4
evaluate("sqrt(2)")                     → 1.414...
evaluate("2*pi")                        → 6.283...
evaluate("x^2 + 1", {"x": 3})           → 10
```

### Simplify

```
simplify("x^2 + 2*x + 1")               → (x + 1)**2
simplify("sin(x)^2 + cos(x)^2")         → 1
```

### Expand / Factor

```
expand("(x + 1)^2")                     → x**2 + 2*x + 1
factor("x^2 - 4")                       → (x - 2)*(x + 2)
```

### Solve

Equation is set equal to zero:

```
solve("x^2 - 4", "x")                   → [-2, 2]
solve("2*x - 8", "x")                   → [4]
```

### Derivative / Integral

```
derivative("x^3", "x")                  → 3*x**2
derivative("sin(x)", "x")               → cos(x)
integral("x^2", "x")                    → x**3/3
integral("cos(x)", "x")                 → sin(x)
```

### LaTeX

```
latex("x^2 + 1/2")                      → x^{2} + \frac{1}{2}
```

### Fractions

```
to_fraction("0.5")                       → 1/2
to_fraction("0.75")                     → 3/4
simplify_fraction("6/8")                → 3/4
simplify_fraction("(x^2-4)/(x-2)")      → x + 2
```

### Unit Conversion

```
convert_unit(100, "meter", "kilometer") → 0.1
convert_unit(32, "fahrenheit", "celsius") → 0
convert_unit(1, "hour", "minute")      → 60
convert_unit(5, "kilometer", "mile")    → 3.106855...
```

## Expression Syntax

| Want | Write |
|------|-------|
| Power | `x^2` or `x**2` |
| Multiply | `2*x` (or `2x`) |
| Functions | `sin(x)`, `cos(x)`, `log(x)`, `sqrt(x)`, `exp(x)` |
| Constants | `pi`, `E` (Euler's number) |

## Common Patterns

### "Solve 2x + 5 = 13"

Rearrange to `= 0`: `2*x + 5 - 13` → `2*x - 8`

```
solve("2*x - 8", "x")  → [4]
```

### Check if expressions are equal

If they simplify to 0, they're equal:

```
simplify("(a+b)^2 - (a^2 + 2*a*b + b^2)")  → 0
```

### Evaluate a derivative at a point

```
derivative("x^3", "x")           → 3*x**2
evaluate("3*x^2", {"x": 2})      → 12
```
