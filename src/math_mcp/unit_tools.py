"""Unit conversion tools using SymPy units."""

from typing import Annotated

import numpy as np
from pydantic import Field
from sympy.physics import units
from sympy.physics.units import convert_to

from math_mcp.utils import parse_expr


# Tool function implementation (exported for testing)
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


def register_unit_tools(mcp):
    """Register unit conversion tools with the MCP server."""
    mcp.tool(name="convert_unit")(tool_convert_unit)
