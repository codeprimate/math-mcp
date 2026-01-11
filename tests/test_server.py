"""Tests for math_mcp tools."""

import pytest

from math_mcp.server import (
    tool_convert_unit,
    tool_derivative,
    tool_evaluate,
    tool_expand,
    tool_factor,
    tool_integral,
    tool_latex,
    tool_simplify,
    tool_simplify_fraction,
    tool_solve,
    tool_to_fraction,
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


class TestToFraction:
    def test_simple_decimal(self):
        assert tool_to_fraction("0.5") == "1/2"

    def test_decimal_three_fourths(self):
        assert tool_to_fraction("0.75") == "3/4"

    def test_mixed_number(self):
        assert tool_to_fraction("1.25") == "5/4"

    def test_approximate_decimal(self):
        # Should convert to fraction representation
        result = tool_to_fraction("0.333")
        assert "/" in result  # Should be a fraction


class TestSimplifyFraction:
    def test_numeric_fraction(self):
        assert tool_simplify_fraction("6/8") == "3/4"

    def test_another_numeric(self):
        assert tool_simplify_fraction("12/18") == "2/3"

    def test_algebraic_fraction(self):
        assert tool_simplify_fraction("(x**2 - 4)/(x - 2)") == "x + 2"

    def test_algebraic_with_factor(self):
        assert tool_simplify_fraction("(2*x + 4)/(x + 2)") == "2"


class TestConvertUnit:
    def test_length_meter_to_kilometer(self):
        result = float(tool_convert_unit(100.0, "meter", "kilometer"))
        assert abs(result - 0.1) < 1e-10

    def test_length_kilometer_to_mile(self):
        result = float(tool_convert_unit(5.0, "kilometer", "mile"))
        assert abs(result - 3.106855) < 0.01  # Approximately 3.1 miles

    def test_temperature_fahrenheit_to_celsius(self):
        result = float(tool_convert_unit(32.0, "fahrenheit", "celsius"))
        assert abs(result - 0.0) < 1e-10  # Freezing point

    def test_time_hour_to_minute(self):
        result = float(tool_convert_unit(1.0, "hour", "minute"))
        assert result == 60.0

    def test_mass_kilogram_to_pound(self):
        result = float(tool_convert_unit(1.0, "kilogram", "pound"))
        assert abs(result - 2.20462) < 0.01  # Approximately 2.2 lbs

    def test_invalid_unit(self):
        result = tool_convert_unit(1.0, "invalid_unit", "meter")
        assert "Error" in result
