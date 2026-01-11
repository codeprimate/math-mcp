"""Tests for math_mcp tools."""

import pytest

from math_mcp.server import (
    tool_derivative,
    tool_evaluate,
    tool_expand,
    tool_factor,
    tool_integral,
    tool_latex,
    tool_simplify,
    tool_solve,
)


class TestSimplify:
    def test_basic(self):
        assert tool_simplify("x + x") == "2*x"

    def test_trig_identity(self):
        assert tool_simplify("sin(x)**2 + cos(x)**2") == "1"

    def test_simplify_fraction(self):
        assert tool_simplify("(x**2 - 1)/(x - 1)") == "x + 1"


class TestSolve:
    def test_linear(self):
        assert tool_solve("x - 5", "x") == ["5"]

    def test_quadratic(self):
        result = tool_solve("x**2 - 4", "x")
        assert set(result) == {"-2", "2"}

    def test_no_real_solution(self):
        result = tool_solve("x**2 + 1", "x")
        assert set(result) == {"-I", "I"}


class TestDerivative:
    def test_polynomial(self):
        assert tool_derivative("x**3", "x") == "3*x**2"

    def test_trig(self):
        assert tool_derivative("sin(x)", "x") == "cos(x)"

    def test_chain_rule(self):
        assert tool_derivative("sin(x**2)", "x") == "2*x*cos(x**2)"


class TestIntegral:
    def test_polynomial(self):
        assert tool_integral("x**2", "x") == "x**3/3"

    def test_trig(self):
        assert tool_integral("cos(x)", "x") == "sin(x)"


class TestExpand:
    def test_square(self):
        assert tool_expand("(x + 1)**2") == "x**2 + 2*x + 1"

    def test_difference_of_squares(self):
        assert tool_expand("(a + b)*(a - b)") == "a**2 - b**2"


class TestFactor:
    def test_difference_of_squares(self):
        assert tool_factor("x**2 - 4") == "(x - 2)*(x + 2)"

    def test_perfect_square(self):
        assert tool_factor("x**2 + 2*x + 1") == "(x + 1)**2"


class TestEvaluate:
    def test_constant(self):
        result = float(tool_evaluate("2 + 2"))
        assert result == 4.0

    def test_pi(self):
        result = float(tool_evaluate("pi"))
        assert abs(result - 3.14159) < 0.001

    def test_with_substitution(self):
        result = float(tool_evaluate("x**2 + 1", {"x": 3}))
        assert result == 10.0


class TestLatex:
    def test_fraction(self):
        assert tool_latex("1/2") == r"\frac{1}{2}"

    def test_sqrt(self):
        assert tool_latex("sqrt(x)") == r"\sqrt{x}"

    def test_power(self):
        assert tool_latex("x**2") == "x^{2}"
