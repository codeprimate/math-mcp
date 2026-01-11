"""Shared utilities for math MCP tools."""

from sympy import E, I, pi, sympify
from sympy.core.sympify import SympifyError


def parse_expr(expression: str):
    """Parse expression with common substitutions."""
    # Replace ^ with ** for exponentiation
    expr_str = expression.replace("^", "**")
    return sympify(expr_str, locals={"pi": pi, "E": E, "I": I})
