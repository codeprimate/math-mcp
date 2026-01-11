"""Math MCP Server - Symbolic math via SymPy."""

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from sympy import (
    E,
    I,
    Rational,
    diff,
    expand,
    factor,
    integrate,
    latex,
    nsimplify,
    pi,
    simplify,
    solve,
    symbols,
    sympify,
)
from sympy.core.sympify import SympifyError
from sympy.physics import units
from sympy.physics.units import convert_to

mcp = FastMCP("Math")


def parse_expr(expression: str):
    """Parse expression with common substitutions."""
    # Replace ^ with ** for exponentiation
    expr_str = expression.replace("^", "**")
    return sympify(expr_str, locals={"pi": pi, "E": E, "I": I})


@mcp.tool(name="simplify")
def tool_simplify(
    expression: Annotated[str, Field(description="Mathematical expression to simplify. Supports polynomials, trigonometric identities, algebraic fractions, and more. Use ^ for exponentiation (e.g. 'x^2 + 2*x + 1' or 'sin(x)^2 + cos(x)^2').")]
) -> str:
    """Simplify a mathematical expression to its most compact form.

    This tool is essential for reducing complex expressions, verifying identities, and cleaning up algebraic results. It automatically applies trigonometric identities, combines like terms, reduces fractions, and performs other algebraic simplifications.

    Use this when:
    - You need to reduce an expression to its simplest form
    - Verifying that two expressions are equivalent (difference simplifies to 0)
    - Cleaning up results from other operations
    - Simplifying trigonometric or logarithmic expressions

    Examples:
    - 'x^2 + 2*x + 1' → '(x + 1)**2' (perfect square factorization)
    - 'sin(x)^2 + cos(x)^2' → '1' (Pythagorean identity)
    - '(x^2 - 4)/(x - 2)' → 'x + 2' (rational simplification)
    """
    try:
        expr = parse_expr(expression)
        result = simplify(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="solve")
def tool_solve(
    equation: Annotated[str, Field(description="Equation to solve, written as an expression equal to zero. For '2x + 5 = 13', rewrite as '2*x - 8' (moving all terms to one side). Examples: 'x^2 - 4', '2*x - 8', 'x^3 - 27'.")],
    variable: Annotated[str, Field(description="Variable to solve for. Typically 'x', but can be any symbol like 'y', 't', 'theta', etc.")],
) -> list[str]:
    """Solve an equation for a variable, finding all real and complex solutions.

    This is your go-to tool for finding roots, solving for unknowns, and answering "what value of x makes this true?" questions. Handles linear, quadratic, polynomial, and many transcendental equations.

    The equation is assumed equal to zero: 'x^2 - 4' means x² - 4 = 0.

    Use this when:
    - Finding roots or zeros of functions
    - Solving for unknown variables in equations
    - Determining when an expression equals zero
    - Answering "solve for x" type questions

    Examples:
    - equation='x^2 - 4', variable='x' → ['-2', '2'] (quadratic with two solutions)
    - equation='2*x - 8', variable='x' → ['4'] (linear equation)
    - equation='x^3 - 27', variable='x' → ['3'] (cubic equation)
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
    expression: Annotated[str, Field(description="Mathematical expression to differentiate. Supports polynomials, trigonometric functions (sin, cos, tan), exponentials, logarithms, and more. Examples: 'x^3', 'sin(x)', 'exp(x)', 'log(x)'.")],
    variable: Annotated[str, Field(description="Variable to differentiate with respect to. Usually 'x', but can be any variable symbol.")],
) -> str:
    """Compute the derivative (rate of change) of an expression with respect to a variable.

    Essential for calculus problems, optimization, finding slopes, and analyzing function behavior. Returns the symbolic derivative that can be evaluated, simplified, or used in further calculations.

    Use this when:
    - Finding the slope or rate of change of a function
    - Computing derivatives for calculus problems
    - Finding critical points (set derivative = 0 and solve)
    - Analyzing function behavior (increasing/decreasing)
    - Computing gradients or partial derivatives

    Examples:
    - expression='x^3', variable='x' → '3*x**2' (power rule)
    - expression='sin(x)', variable='x' → 'cos(x)' (trigonometric derivative)
    - expression='exp(x)', variable='x' → 'exp(x)' (exponential derivative)
    - expression='x*log(x)', variable='x' → 'log(x) + 1' (product rule)
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
    expression: Annotated[str, Field(description="Mathematical expression to integrate. Supports polynomials, trigonometric functions, exponentials, and many standard functions. Examples: 'x^2', 'cos(x)', 'exp(x)', '1/x'.")],
    variable: Annotated[str, Field(description="Variable to integrate with respect to. Usually 'x', but can be any variable symbol.")],
) -> str:
    """Compute the indefinite integral (antiderivative) of an expression.

    Perfect for finding antiderivatives, computing areas under curves, solving differential equations, and integration problems. Returns the symbolic integral with the constant of integration implied.

    Use this when:
    - Finding antiderivatives or integrals
    - Computing areas under curves (with definite integrals via evaluate)
    - Solving differential equations
    - Reversing derivative operations
    - Integration by parts or substitution problems

    Examples:
    - expression='x^2', variable='x' → 'x**3/3' (power rule for integration)
    - expression='cos(x)', variable='x' → 'sin(x)' (trigonometric integral)
    - expression='exp(x)', variable='x' → 'exp(x)' (exponential integral)
    - expression='1/x', variable='x' → 'log(x)' (logarithmic integral)
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
    expression: Annotated[str, Field(description="Expression to expand by multiplying out and distributing. Works with polynomials, products, powers, and more. Examples: '(x+1)^2', '(a+b)*(a-b)', '(x+1)*(x+2)*(x+3)'.")]
) -> str:
    """Expand an expression by multiplying out parentheses and distributing terms.

    Transforms factored or compact forms into expanded polynomial form. Essential for polynomial manipulation, verifying algebraic identities, and preparing expressions for further operations.

    Use this when:
    - Multiplying out parentheses in polynomials
    - Expanding binomials like (x+1)^2 or (a+b)^3
    - Distributing multiplication over addition
    - Converting factored form to standard polynomial form
    - Verifying that expand then factor returns the original

    Examples:
    - '(x + 1)^2' → 'x**2 + 2*x + 1' (binomial expansion)
    - '(a + b)*(a - b)' → 'a**2 - b**2' (difference of squares)
    - '(x + 1)*(x + 2)' → 'x**2 + 3*x + 2' (polynomial multiplication)
    """
    try:
        expr = parse_expr(expression)
        result = expand(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="factor")
def tool_factor(
    expression: Annotated[str, Field(description="Polynomial or expression to factor into products. Works with quadratics, difference of squares, perfect squares, and many polynomial forms. Examples: 'x^2 - 4', 'x^2 + 2*x + 1', 'x^3 - 8'.")]
) -> str:
    """Factor an expression into a product of simpler factors.

    The inverse of expand - converts expanded polynomials into factored form. Essential for finding roots, simplifying rational expressions, and solving equations by factoring.

    Use this when:
    - Factoring polynomials to find roots
    - Simplifying rational expressions (cancel common factors)
    - Converting expanded form to factored form
    - Identifying perfect squares or special factorizations
    - Preparing expressions for partial fraction decomposition

    Examples:
    - 'x^2 - 4' → '(x - 2)*(x + 2)' (difference of squares)
    - 'x^2 + 2*x + 1' → '(x + 1)**2' (perfect square trinomial)
    - 'x^3 - 8' → '(x - 2)*(x**2 + 2*x + 4)' (difference of cubes)
    """
    try:
        expr = parse_expr(expression)
        result = factor(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="evaluate")
def tool_evaluate(
    expression: Annotated[str, Field(description="Mathematical expression to evaluate numerically. Can include constants (pi, E), functions (sin, cos, sqrt, log, exp), and variables. Examples: '2*pi', 'sqrt(2)', 'sin(pi/2)', 'x^2 + 1'.")],
    values: Annotated[dict[str, float] | None, Field(description="Optional dictionary mapping variable names to numeric values for substitution. Use when expression contains variables. Example: {'x': 3} or {'x': 2.5, 'y': 1.0}.")] = None,
) -> str:
    """Evaluate a mathematical expression to a numeric result.

    Converts symbolic expressions into concrete numeric values. Perfect for computing final answers, checking work, evaluating functions at specific points, and getting decimal approximations of symbolic results.

    Use this when:
    - Computing final numeric answers from symbolic expressions
    - Evaluating functions at specific points (e.g., f(3) when f(x) = x^2 + 1)
    - Getting decimal approximations of constants or expressions
    - Checking if two expressions are equal (evaluate their difference)
    - Computing definite integrals (integrate then evaluate at bounds)
    - Verifying solutions by plugging values back into equations

    Examples:
    - expression='2*pi' → '6.28318530717959' (numeric approximation of 2π)
    - expression='sqrt(2)' → '1.41421356237310' (square root of 2)
    - expression='x^2 + 1', values={'x': 3} → '10' (substitute x=3)
    - expression='sin(pi/2)' → '1' (trigonometric evaluation)
    - expression='exp(1)' → '2.71828182845905' (Euler's number e)
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
    expression: Annotated[str, Field(description="Mathematical expression to convert to LaTeX format. Works with all standard math notation. Examples: 'x^2 + 1/2', 'sqrt(x)', 'integral(x^2, x)', 'sum(n, n, 1, 10)'.")]
) -> str:
    """Convert a mathematical expression to LaTeX format for typesetting.

    Produces publication-quality mathematical notation that can be used in documents, presentations, or rendered in markdown. Essential for displaying math in a professional format.

    Use this when:
    - Formatting math for documentation or markdown files
    - Creating mathematical expressions for presentations
    - Generating LaTeX code for academic papers
    - Displaying results in a typeset format
    - Converting between symbolic and typeset representations

    Examples:
    - 'x^2 + 1/2' → 'x^{2} + \\frac{1}{2}' (proper fraction formatting)
    - 'sqrt(x)' → '\\sqrt{x}' (square root notation)
    - 'integral(x^2, x)' → '\\int x^{2}\\, dx' (integral notation)
    - '(x+1)/(x-1)' → '\\frac{x + 1}{x - 1}' (rational expression)
    """
    try:
        expr = parse_expr(expression)
        return latex(expr)
    except SympifyError as e:
        return f"Error: Could not parse expression: {e}"


@mcp.tool(name="to_fraction")
def tool_to_fraction(
    value: Annotated[str, Field(description="Decimal number or numeric expression to convert to a rational fraction. Can be a decimal like '0.5', '0.333', '1.25', or an expression that evaluates to a number. Examples: '0.5', '0.75', '1.25', '0.333'.")]
) -> str:
    """Convert a decimal number to an exact rational fraction.

    Transforms floating-point decimals into exact fractional form, preserving precision. Essential for exact arithmetic, avoiding floating-point errors, and working with rational numbers in symbolic math.

    Use this when:
    - Converting decimals to exact fractions (e.g., 0.5 → 1/2)
    - Avoiding floating-point precision issues
    - Working with exact rational arithmetic
    - Converting approximate values to fractions
    - Getting exact representations of repeating decimals

    Examples:
    - value='0.5' → '1/2' (exact fraction)
    - value='0.75' → '3/4' (simplified fraction)
    - value='1.25' → '5/4' (mixed number as fraction)
    - value='0.333' → '333/1000' (approximate decimal to fraction)
    """
    try:
        # Parse as a number first
        num_value = float(value)
        # Use nsimplify to find a rational approximation
        # For exact decimals, Rational works better
        if '.' in value:
            # Try to find exact fraction
            rational = nsimplify(num_value, tolerance=1e-10, rational=True)
        else:
            # Already an integer or expression
            expr = parse_expr(value)
            if expr.is_number:
                rational = nsimplify(expr, tolerance=1e-10, rational=True)
            else:
                return f"Error: '{value}' is not a numeric value"
        
        # Convert to Rational and simplify
        if isinstance(rational, Rational):
            return str(rational)
        else:
            # Fallback: convert float to Rational
            rational = Rational(str(num_value))
            return str(rational)
    except (ValueError, SympifyError) as e:
        return f"Error: Could not convert '{value}' to fraction: {e}"


@mcp.tool(name="simplify_fraction")
def tool_simplify_fraction(
    fraction: Annotated[str, Field(description="Fraction expression to simplify to lowest terms. Can be a simple fraction like '6/8' or '12/18', or an algebraic fraction like '(x^2-4)/(x-2)'. Examples: '6/8', '12/18', '(x^2-4)/(x-2)'.")]
) -> str:
    """Simplify a fraction to its lowest terms.

    Reduces fractions by canceling common factors between numerator and denominator. Works with both numeric and algebraic fractions. Essential for presenting results in simplest form and simplifying rational expressions.

    Use this when:
    - Reducing numeric fractions to lowest terms (6/8 → 3/4)
    - Simplifying algebraic fractions
    - Canceling common factors in rational expressions
    - Presenting results in simplest form
    - Preparing fractions for further operations

    Examples:
    - fraction='6/8' → '3/4' (numeric simplification)
    - fraction='12/18' → '2/3' (cancel common factor of 6)
    - fraction='(x^2-4)/(x-2)' → 'x + 2' (algebraic simplification, if x ≠ 2)
    - fraction='(2*x + 4)/(x + 2)' → '2' (factor and cancel)
    """
    try:
        expr = parse_expr(fraction)
        # Simplify the expression (this handles both numeric and algebraic fractions)
        result = simplify(expr)
        return str(result)
    except SympifyError as e:
        return f"Error: Could not parse fraction: {e}"


@mcp.tool(name="convert_unit")
def tool_convert_unit(
    value: Annotated[float, Field(description="Numeric value to convert. The quantity in the source unit. Examples: 100, 5, 32, 1.")],
    from_unit: Annotated[str, Field(description="Source unit name. Supported units include: length (meter, kilometer, centimeter, millimeter, mile, foot, inch, yard), mass (kilogram, gram, pound), time (second, minute, hour, day), temperature (celsius, fahrenheit, kelvin), volume (liter, milliliter, quart), speed (meter_per_second, kilometer_per_hour, mile_per_hour). Examples: 'meter', 'kilogram', 'second', 'celsius'.")],
    to_unit: Annotated[str, Field(description="Target unit name. Must be compatible with from_unit (same category). Examples: 'kilometer', 'pound', 'minute', 'fahrenheit'.")],
) -> str:
    """Convert a quantity from one unit to another.

    Transforms measurements between compatible units within the same category (length, mass, time, temperature, etc.). Handles all standard unit conversions with exact precision where possible. Temperature conversions handle offset correctly (Celsius/Fahrenheit require offset, not just scaling).

    Use this when:
    - Converting between metric and imperial units
    - Converting between different scales (e.g., meters to kilometers)
    - Converting temperature between Celsius, Fahrenheit, and Kelvin
    - Converting time units (seconds, minutes, hours, days)
    - Converting speed, volume, or mass units
    - Answering "how many X in Y?" questions

    Examples:
    - value=100, from_unit='meter', to_unit='kilometer' → '0.1' (100m = 0.1km)
    - value=5, from_unit='kilometer', to_unit='mile' → '3.10685596118667' (approx 3.1 miles)
    - value=32, from_unit='fahrenheit', to_unit='celsius' → '0' (freezing point)
    - value=1, from_unit='hour', to_unit='minute' → '60' (1 hour = 60 minutes)
    - value=2.5, from_unit='kilogram', to_unit='pound' → '5.51155655462194' (approx 5.5 lbs)
    """
    try:
        from_lower = from_unit.lower()
        to_lower = to_unit.lower()
        
        # Handle temperature conversions manually (they require offset, not just scaling)
        temp_units = {'celsius', 'fahrenheit', 'kelvin'}
        if from_lower in temp_units or to_lower in temp_units:
            # Convert to Kelvin first, then to target
            if from_lower == 'celsius':
                kelvin = value + 273.15
            elif from_lower == 'fahrenheit':
                kelvin = (value - 32) * 5/9 + 273.15
            elif from_lower == 'kelvin':
                kelvin = value
            else:
                return f"Error: Invalid temperature unit '{from_unit}'"
            
            # Convert from Kelvin to target
            if to_lower == 'celsius':
                result = kelvin - 273.15
            elif to_lower == 'fahrenheit':
                result = (kelvin - 273.15) * 9/5 + 32
            elif to_lower == 'kelvin':
                result = kelvin
            else:
                return f"Error: Invalid temperature unit '{to_unit}'"
            
            # Round to reasonable precision for temperature
            if abs(result - round(result)) < 1e-10:
                return str(int(round(result)))
            return str(round(result, 10))
        
        # Unit mapping for common units (only those available in SymPy)
        unit_map = {
            # Length
            'meter': units.meter,
            'metre': units.meter,  # British spelling
            'meters': units.meter,
            'metres': units.meter,
            'kilometer': units.kilometer,
            'kilometre': units.kilometer,
            'kilometers': units.kilometer,
            'kilometres': units.kilometer,
            'centimeter': units.centimeter,
            'centimetre': units.centimeter,
            'centimeters': units.centimeter,
            'centimetres': units.centimeter,
            'millimeter': units.millimeter,
            'millimetre': units.millimeter,
            'millimeters': units.millimeter,
            'millimetres': units.millimeter,
            'mile': units.mile,
            'miles': units.mile,
            'foot': units.foot,
            'feet': units.foot,
            'inch': units.inch,
            'inches': units.inch,
            'yard': units.yard,
            'yards': units.yard,
            # Mass
            'kilogram': units.kilogram,
            'kilograms': units.kilogram,
            'gram': units.gram,
            'grams': units.gram,
            'pound': units.pound,
            'pounds': units.pound,
            # Time
            'second': units.second,
            'seconds': units.second,
            'minute': units.minute,
            'minutes': units.minute,
            'hour': units.hour,
            'hours': units.hour,
            'day': units.day,
            'days': units.day,
            # Volume
            'liter': units.liter,
            'litre': units.liter,
            'liters': units.liter,
            'litres': units.liter,
            'milliliter': units.milliliter,
            'millilitre': units.milliliter,
            'milliliters': units.milliliter,
            'millilitres': units.milliliter,
            'quart': units.quart,
            'quarts': units.quart,
            # Speed
            'meter_per_second': units.meter / units.second,
            'metre_per_second': units.meter / units.second,
            'meters_per_second': units.meter / units.second,
            'metres_per_second': units.meter / units.second,
            'kilometer_per_hour': units.kilometer / units.hour,
            'kilometre_per_hour': units.kilometer / units.hour,
            'kilometers_per_hour': units.kilometer / units.hour,
            'kilometres_per_hour': units.kilometer / units.hour,
            'mile_per_hour': units.mile / units.hour,
            'miles_per_hour': units.mile / units.hour,
        }
        
        from_unit_obj = unit_map.get(from_lower)
        to_unit_obj = unit_map.get(to_lower)
        
        if from_unit_obj is None:
            available = sorted(set(k for k in unit_map.keys() if not (k.endswith('s') and k[:-1] in unit_map)))
            return f"Error: Unknown source unit '{from_unit}'. Supported units: {', '.join(available)}"
        
        if to_unit_obj is None:
            available = sorted(set(k for k in unit_map.keys() if not (k.endswith('s') and k[:-1] in unit_map)))
            return f"Error: Unknown target unit '{to_unit}'. Supported units: {', '.join(available)}"
        
        # Create quantity with source unit
        quantity = value * from_unit_obj
        
        # Convert to target unit
        result = convert_to(quantity, to_unit_obj)
        
        # Extract numeric value by dividing by target unit (removes unit, leaves number)
        # Result is a Mul like (0.1 * kilometer), so divide by the unit to get just the number
        numeric_result = float((result / to_unit_obj).evalf())
        
        # Return as string, with reasonable precision
        if abs(numeric_result - round(numeric_result)) < 1e-10:
            return str(int(round(numeric_result)))
        return str(numeric_result)
    except Exception as e:
        return f"Error: Could not convert {value} {from_unit} to {to_unit}: {e}"


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
