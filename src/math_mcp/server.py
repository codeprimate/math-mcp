"""Math MCP Server - Symbolic math via SymPy."""

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from sympy import (
    E,
    I,
    diff,
    expand,
    factor,
    integrate,
    latex,
    pi,
    simplify,
    solve,
    symbols,
    sympify,
)
from sympy.core.sympify import SympifyError

mcp = FastMCP("Math")


def parse_expr(expression: str):
    """Parse expression with common substitutions."""
    # Replace ^ with ** for exponentiation
    expr_str = expression.replace("^", "**")
    return sympify(expr_str, locals={"pi": pi, "E": E, "I": I})


@mcp.tool(name="simplify")
def tool_simplify(
    expression: Annotated[str, Field(description="Math expression, e.g. 'x^2 + 2*x + 1'")]
) -> str:
    """Simplify a mathematical expression.

    Examples:
    - 'x^2 + 2*x + 1' → '(x + 1)**2'
    - 'sin(x)^2 + cos(x)^2' → '1'
    """
    try:
        expr = parse_expr(expression)
        result = simplify(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="solve")
def tool_solve(
    equation: Annotated[str, Field(description="Equation to solve, e.g. 'x^2 - 4' (equals zero)")],
    variable: Annotated[str, Field(description="Variable to solve for, e.g. 'x'")],
) -> list[str]:
    """Solve an equation for a variable.

    The equation is assumed equal to zero: 'x^2 - 4' means x² - 4 = 0.

    Examples:
    - equation='x^2 - 4', variable='x' → ['-2', '2']
    - equation='2*x - 8', variable='x' → ['4']
    """
    try:
        expr = parse_expr(equation)
        var = symbols(variable)
        solutions = solve(expr, var)
        return [str(s) for s in solutions]
    except SympifyError as e:
        return [f"Error: Could not parse expression: {e}"]


@mcp.tool(name="derivative")
def tool_derivative(
    expression: Annotated[str, Field(description="Expression to differentiate, e.g. 'x^3'")],
    variable: Annotated[str, Field(description="Variable to differentiate with respect to")],
) -> str:
    """Compute the derivative of an expression.

    Examples:
    - expression='x^3', variable='x' → '3*x**2'
    - expression='sin(x)', variable='x' → 'cos(x)'
    """
    try:
        expr = parse_expr(expression)
        var = symbols(variable)
        result = diff(expr, var)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="integral")
def tool_integral(
    expression: Annotated[str, Field(description="Expression to integrate, e.g. 'x^2'")],
    variable: Annotated[str, Field(description="Variable to integrate with respect to")],
) -> str:
    """Compute the indefinite integral of an expression.

    Examples:
    - expression='x^2', variable='x' → 'x**3/3'
    - expression='cos(x)', variable='x' → 'sin(x)'
    """
    try:
        expr = parse_expr(expression)
        var = symbols(variable)
        result = integrate(expr, var)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="expand")
def tool_expand(
    expression: Annotated[str, Field(description="Expression to expand, e.g. '(x+1)^2'")]
) -> str:
    """Expand an expression (multiply out, distribute).

    Examples:
    - '(x + 1)^2' → 'x**2 + 2*x + 1'
    - '(a + b)*(a - b)' → 'a**2 - b**2'
    """
    try:
        expr = parse_expr(expression)
        result = expand(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="factor")
def tool_factor(
    expression: Annotated[str, Field(description="Expression to factor, e.g. 'x^2 - 4'")]
) -> str:
    """Factor an expression into products.

    Examples:
    - 'x^2 - 4' → '(x - 2)*(x + 2)'
    - 'x^2 + 2*x + 1' → '(x + 1)**2'
    """
    try:
        expr = parse_expr(expression)
        result = factor(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="evaluate")
def tool_evaluate(
    expression: Annotated[str, Field(description="Expression to evaluate, e.g. '2*pi' or 'x^2 + 1'")],
    values: Annotated[dict[str, float] | None, Field(description="Variable values, e.g. {'x': 3}")] = None,
) -> str:
    """Evaluate an expression numerically.

    Examples:
    - expression='2*pi' → '6.28318530717959'
    - expression='x^2 + 1', values={'x': 3} → '10'
    """
    try:
        expr = parse_expr(expression)
        if values:
            subs = {symbols(k): v for k, v in values.items()}
            expr = expr.subs(subs)
        result = expr.evalf()
        # Return integer if it's a whole number
        if result == int(result):
            return str(int(result))
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="latex")
def tool_latex(
    expression: Annotated[str, Field(description="Expression to convert, e.g. 'x^2 + 1/2'")]
) -> str:
    """Convert expression to LaTeX format.

    Examples:
    - 'x^2 + 1/2' → 'x^{2} + \\frac{1}{2}'
    - 'sqrt(x)' → '\\sqrt{x}'
    """
    try:
        expr = parse_expr(expression)
        return latex(expr)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
