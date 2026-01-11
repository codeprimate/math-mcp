"""SciPy/NumPy-based numerical computation tools."""

import json
from typing import Annotated

import numpy as np
from pydantic import Field
from scipy.integrate import solve_ivp
from scipy.optimize import root_scalar
from sympy import diff, symbols
from sympy.core.sympify import SympifyError

from math_mcp.utils import parse_expr


# Tool function implementations (exported for testing)
def tool_solve_ode(
        equations: Annotated[list[str], Field(description="List of differential equations. Each equation should be in the form 'dx/dt = expression' or 'dy/dt = expression', where the left side specifies the derivative variable and the right side is a mathematical expression. Variables can be any symbols (x, y, z, etc.) and the independent variable is 't' by default. Examples: ['dx/dt = -x + y', 'dy/dt = x - y'] or ['dx/dt = -0.5*x'].")],
        initial_conditions: Annotated[dict[str, float], Field(description="Dictionary mapping variable names to their initial values at t=0. Example: {'x': 1.0, 'y': 0.0} or {'x': 1.0}.")],
        time_span: Annotated[list[float], Field(description="Time span for integration as [t_start, t_end]. Example: [0.0, 10.0].")],
        method: Annotated[str, Field(description="Numerical integration method. Options: 'rk45' (default, adaptive Runge-Kutta 4/5), 'rk4' (fixed-step Runge-Kutta 4), 'euler' (Euler's method).")] = "rk45",
    ) -> str:
        """Solve a system of ordinary differential equations (ODEs) numerically.
        
        This tool integrates systems of differential equations over time using numerical methods. Essential for physics simulations, engineering problems, and any scenario requiring time-dependent solutions.
        
        Use this when:
        - Solving systems of differential equations (e.g., dx/dt = f(x,y,t))
        - Simulating physical systems over time
        - Solving initial value problems (IVPs)
        - Modeling dynamic systems (mechanical, electrical, biological, etc.)
        - When symbolic solutions are not available or too complex
        
        Examples:
        - equations=['dx/dt = -x'], initial_conditions={'x': 1.0}, time_span=[0.0, 5.0] → Exponential decay
        - equations=['dx/dt = -x + y', 'dy/dt = x - y'], initial_conditions={'x': 1.0, 'y': 0.0}, time_span=[0.0, 10.0] → Coupled system
        - equations=['dx/dt = -0.5*x'], initial_conditions={'x': 2.0}, time_span=[0.0, 10.0], method='rk4' → Using RK4 method
        """
        try:
            if len(time_span) != 2:
                return "Error: time_span must be a list of two numbers [t_start, t_end]"
            
            t_start, t_end = time_span[0], time_span[1]
            
            # Parse equations to extract derivative variables and expressions
            derivative_vars = []
            derivative_exprs = []
            all_vars = set()
            
            for eq in equations:
                # Parse equation like "dx/dt = expression" or "dx/dt=expression"
                if "=" not in eq:
                    return f"Error: Equation '{eq}' must contain '=' sign"
                
                left, right = eq.split("=", 1)
                left = left.strip()
                right = right.strip()
                
                # Parse left side to get derivative variable (e.g., "dx/dt" -> "x")
                if "/dt" not in left and "/d t" not in left:
                    return f"Error: Left side '{left}' must be in form 'dx/dt' or 'dy/dt'"
                
                # Extract variable name
                var_name = left.split("/")[0].strip()
                if var_name.startswith("d"):
                    var_name = var_name[1:]  # Remove 'd' from 'dx'
                var_name = var_name.strip()
                
                if not var_name:
                    return f"Error: Could not extract variable name from '{left}'"
                
                derivative_vars.append(var_name)
                derivative_exprs.append(right)
                all_vars.add(var_name)
            
            # Check that all initial conditions are provided
            missing = set(derivative_vars) - set(initial_conditions.keys())
            if missing:
                return f"Error: Missing initial conditions for variables: {missing}"
            
            # Get all variables (state variables + time)
            state_vars = sorted(derivative_vars)
            all_symbols = symbols(" ".join(state_vars) + " t")
            var_dict = {var: sym for var, sym in zip(state_vars + ["t"], all_symbols)}
            
            # Convert expressions to SymPy expressions and then to callable functions
            def rhs_func(t, y):
                """Right-hand side function for ODE system."""
                # Create substitution dictionary: {x: y[0], y: y[1], ...}
                subs_dict = {var_dict[var]: y[i] for i, var in enumerate(state_vars)}
                subs_dict[var_dict["t"]] = t
                
                # Evaluate each derivative expression
                result = []
                for expr_str in derivative_exprs:
                    try:
                        expr = parse_expr(expr_str)
                        # Substitute values
                        expr_val = expr.subs(subs_dict)
                        # Convert to float
                        result.append(float(expr_val.evalf()))
                    except Exception as e:
                        raise ValueError(f"Error evaluating expression '{expr_str}': {e}")
                
                return np.array(result)
            
            # Prepare initial condition vector
            y0 = np.array([initial_conditions[var] for var in state_vars])
            
            # Map method names to scipy methods
            method_map = {
                "rk45": "RK45",
                "rk4": "DOP853",  # Use DOP853 as a high-order method, or implement RK4
                "euler": None,  # Custom implementation
            }
            
            method_lower = method.lower()
            
            # For Euler method, use a simple fixed-step implementation
            if method_lower == "euler":
                dt = 0.01  # Fixed step size
                t_points = np.arange(t_start, t_end + dt, dt)
                y_points = np.zeros((len(t_points), len(state_vars)))
                y_points[0] = y0
                
                for i in range(1, len(t_points)):
                    y_points[i] = y_points[i-1] + dt * rhs_func(t_points[i-1], y_points[i-1])
                
                # Format result
                result = {
                    "time": t_points.tolist(),
                    "state": {var: y_points[:, i].tolist() for i, var in enumerate(state_vars)},
                    "method": "euler",
                    "success": True,
                }
                return json.dumps(result)
            
            # For RK4 method, use a fixed-step RK4 implementation
            if method_lower == "rk4":
                dt = 0.01  # Fixed step size
                t_points = np.arange(t_start, t_end + dt, dt)
                y_points = np.zeros((len(t_points), len(state_vars)))
                y_points[0] = y0
                
                for i in range(1, len(t_points)):
                    t_curr = t_points[i-1]
                    y_curr = y_points[i-1]
                    
                    # RK4 method: k1, k2, k3, k4
                    k1 = rhs_func(t_curr, y_curr)
                    k2 = rhs_func(t_curr + dt/2, y_curr + dt*k1/2)
                    k3 = rhs_func(t_curr + dt/2, y_curr + dt*k2/2)
                    k4 = rhs_func(t_curr + dt, y_curr + dt*k3)
                    
                    y_points[i] = y_curr + dt * (k1 + 2*k2 + 2*k3 + k4) / 6
                
                # Format result
                result = {
                    "time": t_points.tolist(),
                    "state": {var: y_points[:, i].tolist() for i, var in enumerate(state_vars)},
                    "method": "rk4",
                    "success": True,
                }
                return json.dumps(result)
            
            # Use scipy for adaptive methods (rk45)
            scipy_method = method_map.get(method_lower, "RK45")
            
            # Use scipy for other methods
            sol = solve_ivp(
                rhs_func,
                [t_start, t_end],
                y0,
                method=scipy_method,
                dense_output=True,
            )
            
            if not sol.success:
                return f"Error: Integration failed: {sol.message}"
            
            # Format result
            result = {
                "time": sol.t.tolist(),
                "state": {var: sol.y[i].tolist() for i, var in enumerate(state_vars)},
                "method": method.lower(),
                "success": True,
                "message": sol.message,
            }
            
            return json.dumps(result)
        except Exception as e:
            return f"Error: {str(e)}"


def tool_find_root(
        function: Annotated[str, Field(description="Mathematical function expression to find the root of. The function should be written as an expression equal to zero. Use 'x' as the variable. Examples: 'x^2 - 4', 'sin(x) - 0.5', 'exp(x) - 2'.")],
        initial_guess: Annotated[float, Field(description="Initial guess for the root value. For bracketing methods (bisection, brentq), this is the left bound of the bracket. Example: 1.0.")] = 0.0,
        bracket: Annotated[list[float] | None, Field(description="Optional bracket [a, b] where the function changes sign (f(a) and f(b) have opposite signs). Required for bisection and brentq methods. If not provided, will try to find a bracket automatically. Example: [0.0, 2.0].")] = None,
        method: Annotated[str, Field(description="Root finding method. Options: 'newton' (Newton-Raphson, requires derivative), 'bisection' or 'bisect' (requires bracket), 'brentq' (Brent's method, requires bracket, recommended), 'secant' (secant method). Default: 'brentq' if bracket provided, otherwise 'newton'.")] = "auto",
    ) -> str:
        """Find a numerical root (zero) of a function.
        
        This tool finds where a function equals zero using numerical methods. Essential when symbolic solutions are not available or when you need a numeric approximation.
        
        Use this when:
        - Finding zeros of functions that can't be solved symbolically
        - Solving equations numerically (rewrite as f(x) = 0)
        - Finding intersection points
        - When symbolic solve() doesn't work or is too slow
        - Finding critical points numerically
        
        Examples:
        - function='x^2 - 4', initial_guess=1.0, bracket=[0.0, 3.0] → Finds root near x=2
        - function='sin(x) - 0.5', initial_guess=0.5, bracket=[0.0, 2.0] → Finds root near x=0.524
        - function='exp(x) - 2', initial_guess=0.5, method='newton' → Uses Newton-Raphson method
        - function='x^3 - 8', initial_guess=2.0, bracket=[0.0, 3.0], method='brentq' → Finds x=2
        """
        try:
            # Parse function expression
            expr = parse_expr(function)
            x_sym = symbols("x")
            
            # Convert to callable function
            f_lambda = parse_expr(function)
            f_func = lambda x_val: float(f_lambda.subs(x_sym, x_val).evalf())
            
            # Auto-select method if not specified
            if method == "auto":
                if bracket is not None:
                    method = "brentq"
                else:
                    method = "newton"
            
            method_lower = method.lower()
            
            # Handle different methods
            if method_lower in ("bisect", "bisection", "brentq"):
                # Map bisection to bisect for scipy
                scipy_method = "bisect" if method_lower == "bisection" else method_lower
                
                if bracket is None:
                    # Try to find a bracket automatically
                    # Search around initial_guess
                    search_range = 10.0
                    step = 0.1
                    a, b = initial_guess - search_range, initial_guess + search_range
                    
                    # Try to find sign change
                    found_bracket = False
                    for test_a in np.arange(initial_guess - search_range, initial_guess + search_range, step):
                        for test_b in np.arange(test_a + step, initial_guess + search_range, step):
                            try:
                                if f_func(test_a) * f_func(test_b) < 0:
                                    a, b = test_a, test_b
                                    found_bracket = True
                                    break
                            except:
                                continue
                        if found_bracket:
                            break
                    
                    if not found_bracket:
                        return "Error: Could not find a bracket (interval where function changes sign). Please provide a bracket parameter."
                else:
                    if len(bracket) != 2:
                        return "Error: bracket must be a list of two numbers [a, b]"
                    a, b = bracket[0], bracket[1]
                
                # Verify bracket
                try:
                    fa, fb = f_func(a), f_func(b)
                except Exception as e:
                    return f"Error: Could not evaluate function at bracket endpoints: {e}"
                
                if fa * fb > 0:
                    return f"Error: Function must have opposite signs at bracket endpoints. f({a})={fa}, f({b})={fb}"
                
                # Use scipy root_scalar
                try:
                    result = root_scalar(f_func, bracket=[a, b], method=scipy_method)
                    if not result.converged:
                        return f"Error: Root finding did not converge: {result.flag}"
                    
                    # function_value might not always be present, use root evaluation
                    func_val = f_func(result.root)
                    
                    return json.dumps({
                        "root": float(result.root),
                        "function_value": float(func_val),
                        "iterations": result.iterations if hasattr(result, 'iterations') else None,
                        "method": method_lower,
                        "success": True,
                    })
                except Exception as e:
                    return f"Error: Root finding failed: {e}"
            
            elif method_lower == "newton":
                # Newton-Raphson method requires derivative
                try:
                    df_expr = diff(expr, x_sym)
                    df_func = lambda x_val: float(df_expr.subs(x_sym, x_val).evalf())
                except Exception as e:
                    return f"Error: Could not compute derivative for Newton method: {e}"
                
                # Use scipy root_scalar with Newton method
                try:
                    result = root_scalar(
                        f_func,
                        fprime=df_func,
                        x0=initial_guess,
                        method="newton",
                    )
                    if not result.converged:
                        return f"Error: Newton method did not converge: {result.flag}"
                    
                    func_val = f_func(result.root)
                    
                    return json.dumps({
                        "root": float(result.root),
                        "function_value": float(func_val),
                        "iterations": result.iterations if hasattr(result, 'iterations') else None,
                        "method": "newton",
                        "success": True,
                    })
                except Exception as e:
                    return f"Error: Newton method failed: {e}"
            
            elif method_lower == "secant":
                # Secant method (approximates derivative)
                if bracket is None:
                    # Need two initial points
                    x0, x1 = initial_guess, initial_guess + 0.1
                else:
                    x0, x1 = bracket[0], bracket[1]
                
                try:
                    result = root_scalar(
                        f_func,
                        x0=x0,
                        x1=x1,
                        method="secant",
                    )
                    if not result.converged:
                        return f"Error: Secant method did not converge: {result.flag}"
                    
                    func_val = f_func(result.root)
                    
                    return json.dumps({
                        "root": float(result.root),
                        "function_value": float(func_val),
                        "iterations": result.iterations if hasattr(result, 'iterations') else None,
                        "method": "secant",
                        "success": True,
                    })
                except Exception as e:
                    return f"Error: Secant method failed: {e}"
            
            else:
                return f"Error: Unknown method '{method}'. Supported methods: newton, bisection (or bisect), brentq, secant"
        
        except SympifyError as e:
            return f"Error: Could not parse function expression: {e}"
        except Exception as e:
            return f"Error: {str(e)}"


def register_scipy_tools(mcp):
    """Register SciPy/NumPy-based numerical tools with the MCP server."""
    mcp.tool(name="solve_ode")(tool_solve_ode)
    mcp.tool(name="find_root")(tool_find_root)
