"""Matplotlib-based visualization tools for data analysis."""

import base64
import io
import json
from typing import Annotated

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from mcp.types import ImageContent
from pydantic import Field

# Use non-interactive backend for server use
matplotlib.use('Agg')

# Font size constants
VALUE_LABEL_FONTSIZE = 8
AXIS_LABEL_FONTSIZE = 12
TITLE_FONTSIZE = 14
ANNOTATION_FONTSIZE = 10

# Figure size constants (in pixels)
FIGURE_DPI = 100
DEFAULT_FIGSIZE_PX = (1000, 600)  # Default figure size in pixels (width, height)
DEFAULT_FIGSIZE_LARGE_PX = (1000, 800)  # Default for heatmaps and pie charts

def _pixels_to_inches(size_px: tuple[int, int], dpi: int = FIGURE_DPI) -> tuple[float, float]:
    """Convert figure size from pixels to inches for matplotlib.
    
    Args:
        size_px: Tuple of (width, height) in pixels
        dpi: Dots per inch (default: FIGURE_DPI)
        
    Returns:
        Tuple of (width, height) in inches
    """
    return (size_px[0] / dpi, size_px[1] / dpi)

def _create_image_content(buf: io.BytesIO, format: str = 'png') -> ImageContent:
    """Helper to create ImageContent from BytesIO buffer.
    
    Args:
        buf: BytesIO buffer containing image data
        format: Image format ('png' or 'svg'). Defaults to 'png'.
        
    Returns:
        ImageContent object with appropriate mimeType
    """
    buf.seek(0)
    image_data = base64.b64encode(buf.read()).decode('utf-8')
    mime_type = "image/png" if format == 'png' else "image/svg+xml"
    return ImageContent(
        type="image",
        data=image_data,
        mimeType=mime_type
    )


def _validate_color(color: str) -> None:
    """Validate that a color string is valid for matplotlib.
    
    Args:
        color: Color string (named color or hex)
        
    Raises:
        ValueError: If color is invalid
    """
    if not mcolors.is_color_like(color):
        raise ValueError(f"Invalid color: '{color}'. Must be a named color (e.g., 'red', 'steelblue') or hex value (e.g., '#FF5733')")


def _get_tab10_colors_no_yellow() -> list[str]:
    """Get tab10 palette colors excluding yellow.
    
    Returns:
        List of color strings from tab10 palette (9 colors, yellow excluded)
    """
    # Get tab10 colors as RGB tuples
    tab10_rgb = plt.cm.tab10.colors
    
    # Convert to hex and filter out yellow
    # Yellow in tab10 typically has high saturation and hue around 0.17 (60 degrees)
    colors = []
    for rgb in tab10_rgb:
        # Convert RGB tuple to hex
        hex_color = mcolors.rgb2hex(rgb[:3])  # Only use RGB, ignore alpha if present
        
        # Convert to HSV to check if it's yellow
        hsv = mcolors.rgb_to_hsv(rgb[:3])
        hue, saturation, value = hsv
        
        # Yellow has hue around 0.17 (60 degrees) with high saturation
        # Exclude colors that are yellow-like
        is_yellow = (0.1 <= hue <= 0.25) and (saturation > 0.5) and (value > 0.5)
        
        if not is_yellow:
            colors.append(hex_color)
    
    # Ensure we have at least some colors (fallback if filtering removed everything)
    if not colors:
        # Fallback: manually exclude index 6 (typically yellow in tab10)
        tab10_hex = [mcolors.rgb2hex(c[:3]) for c in tab10_rgb]
        colors = tab10_hex[:6] + tab10_hex[7:] if len(tab10_hex) > 6 else tab10_hex
    
    return colors


def _color_to_hsv(color: str) -> tuple[float, float, float]:
    """Convert a color string to HSV values.
    
    Args:
        color: Color string (named or hex)
        
    Returns:
        Tuple of (hue, saturation, value) in range [0, 1]
    """
    rgb = mcolors.to_rgb(color)
    return mcolors.rgb_to_hsv(rgb)


def _hsv_distance(hsv1: tuple[float, float, float], hsv2: tuple[float, float, float]) -> float:
    """Calculate HSV distance between two colors, accounting for circular hue.
    
    Args:
        hsv1: First color as (h, s, v) tuple
        hsv2: Second color as (h, s, v) tuple
        
    Returns:
        Euclidean distance in HSV space
    """
    h1, s1, v1 = hsv1
    h2, s2, v2 = hsv2
    
    # Handle circular hue: distance can be either |h1-h2| or 1-|h1-h2|
    h_diff = min(abs(h1 - h2), 1 - abs(h1 - h2))
    s_diff = abs(s1 - s2)
    v_diff = abs(v1 - v2)
    
    return np.sqrt(h_diff**2 + s_diff**2 + v_diff**2)


def _normalize_format_string(format_str: str) -> str:
    """Normalize format string by removing leading/trailing quotes.
    
    Handles cases where format strings are passed with extra quotes,
    e.g., "',.0f'" -> ",.0f" or "',d'" -> ",d"
    
    Args:
        format_str: Format string that may have extra quotes
        
    Returns:
        Normalized format string without extra quotes
    """
    # Remove leading and trailing single or double quotes
    format_str = format_str.strip()
    if (format_str.startswith("'") and format_str.endswith("'")) or \
       (format_str.startswith('"') and format_str.endswith('"')):
        format_str = format_str[1:-1]
    return format_str


def _normalize_grid_parameter(grid: bool | str) -> bool | str:
    """Normalize grid parameter to handle string "true"/"false".
    
    Args:
        grid: Grid parameter (bool, str "true"/"false", or str "x"/"y"/"both")
        
    Returns:
        Normalized grid parameter (bool or str)
    """
    if isinstance(grid, str):
        grid_lower = grid.lower()
        if grid_lower == "true":
            return True
        elif grid_lower == "false":
            return False
    return grid


def _format_value(value: float, format_str: str) -> str:
    """Format a numeric value using Python format specifier.
    
    Supports standard formats (e.g., '.2f') and currency ('$.2f' -> '$1234.56').
    Matplotlib only accepts strings, so we format here before passing to ax.text().
    """
    # Normalize format string to handle cases with extra quotes
    format_str = _normalize_format_string(format_str)
    
    if format_str.startswith('$'):
        return f"${value:{format_str[1:]}}"
    return f"{value:{format_str}}"


def _pad_colors_with_hsv_distance(provided_colors: list[str], num_needed: int) -> list[str]:
    """Pad color list using HSV distance to avoid similar colors.
    
    Args:
        provided_colors: List of color strings already provided
        num_needed: Total number of colors needed
        
    Returns:
        List of colors with padding using tab10 palette (excluding yellow)
    """
    # Validate all provided colors
    for color in provided_colors:
        _validate_color(color)
    
    if len(provided_colors) >= num_needed:
        return provided_colors[:num_needed]
    
    # Get tab10 colors (excluding yellow)
    tab10_colors = _get_tab10_colors_no_yellow()
    
    # Convert provided colors to HSV
    provided_hsv = [_color_to_hsv(c) for c in provided_colors]
    used_colors = list(provided_colors)
    
    # For each remaining slot, find the color with maximum minimum distance
    for _ in range(num_needed - len(provided_colors)):
        best_color = None
        best_min_distance = -1
        
        for candidate in tab10_colors:
            # Skip if already used
            if candidate in used_colors:
                continue
            
            candidate_hsv = _color_to_hsv(candidate)
            
            # Find minimum distance to any already-used color
            min_distance = min(
                _hsv_distance(candidate_hsv, used_hsv)
                for used_hsv in provided_hsv
            )
            
            if min_distance > best_min_distance:
                best_min_distance = min_distance
                best_color = candidate
        
        # If we ran out of tab10 colors, cycle through them
        if best_color is None:
            # Find any unused tab10 color
            for color in tab10_colors:
                if color not in used_colors:
                    best_color = color
                    break
            # If still None, cycle through all tab10 colors
            if best_color is None:
                # Use modulo to cycle
                idx = len(used_colors) % len(tab10_colors)
                best_color = tab10_colors[idx]
        
        used_colors.append(best_color)
        provided_hsv.append(_color_to_hsv(best_color))
    
    return used_colors


def tool_plot_timeseries(
    timestamps: Annotated[list[str], Field(description="ISO 8601 timestamps or numeric string values for x-axis points. Example: ['2026-01-01T10:00:00Z', '2026-01-01T11:00:00Z', ...]")],
    series: Annotated[dict[str, list[float]], Field(description="Dictionary of series names to their values. Each series will be plotted as a separate line. Example: {'temperature': [20.5, 21.3, 19.8], 'humidity': [65, 68, 62]}")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis.")] = "Time",
    ylabel: Annotated[str, Field(description="Label for the y-axis.")] = "Value",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    colors: Annotated[list[str] | None, Field(description="List of named colors or hex values. If None, uses tab10 palette (excluding yellow). If provided but shorter than series count, pads with unused tab10 colors using HSV distance.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    legend_loc: Annotated[str | None, Field(description="Legend location: 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center', or None to hide.")] = "best",
    linestyles: Annotated[list[str] | None, Field(description="List of linestyle strings ('-', '--', '-.', ':'), one per series. If None, uses solid lines. Cycles if shorter than series count.")] = None,
    secondary_y: Annotated[dict[str, str] | None, Field(description="Dictionary mapping series names to y-axis labels for secondary axis. Example: {'temperature': 'Temperature (°C)'}")] = None,
    xlabel_rotation: Annotated[int | float, Field(description="Rotation angle in degrees for x-axis labels (0-90 typical).")] = 45,
    show_values: Annotated[bool, Field(description="If True, display the value of each data point on the line chart.")] = False,
    value_format: Annotated[str, Field(description="Python format specifier. Examples: 'd' (integers), '.1f' (1 decimal), '.2f' (2 decimals), '$.2f' (currency).")] = '.1f',
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot time-series data with multiple series.
    
    Use this when:
    - Visualizing data that changes over time
    - Analyzing trends and patterns in sequential data
    - Comparing multiple time series on the same plot
    - Plotting measurements or observations taken at regular or irregular intervals
    
    Examples:
    - timestamps=['2026-01-01T10:00', '2026-01-01T11:00'], series={'temperature': [20.5, 21.3]}
    - timestamps=['0', '1', '2', '3'], series={'signal_a': [1.2, 2.1, 1.9, 2.3], 'signal_b': [3.1, 2.8, 3.2, 2.9]}
    - timestamps=['Q1', 'Q2', 'Q3'], series={'sales': [100, 120, 115]}, show_values=True, value_format='.0f'
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not timestamps:
            raise ValueError("timestamps list cannot be empty")
        if not series:
            raise ValueError("series dictionary cannot be empty")
        
        # Validate all series have same length as timestamps
        for name, values in series.items():
            if len(values) != len(timestamps):
                raise ValueError(f"Series '{name}' has {len(values)} values but timestamps has {len(timestamps)}")
        
        # Get number of series early for validation
        num_series = len(series)
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Validate linestyles
        valid_linestyles = {"-", "--", "-.", ":"}
        if linestyles is not None:
            if len(linestyles) > num_series:
                raise ValueError(f"linestyles list has {len(linestyles)} items but only {num_series} series provided")
            for ls in linestyles:
                if ls not in valid_linestyles:
                    raise ValueError(f"Invalid linestyle '{ls}'. Must be one of {valid_linestyles}")
        
        # Validate secondary_y
        if secondary_y is not None:
            for series_name in secondary_y.keys():
                if series_name not in series:
                    raise ValueError(f"secondary_y key '{series_name}' not found in series dictionary")
        
        # Normalize and validate value_format if show_values is True
        if show_values:
            # Normalize format string to remove extra quotes
            value_format = _normalize_format_string(value_format)
            try:
                # Test the format string with a sample value
                test_value = 123.456
                _format_value(test_value, value_format)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value_format '{value_format}': {str(e)}")
        
        # Handle colors
        if colors is not None:
            if len(colors) > num_series:
                raise ValueError(f"colors list has {len(colors)} items but only {num_series} series provided")
            # Validate all colors
            for color in colors:
                _validate_color(color)
            # Pad colors if needed
            colors = _pad_colors_with_hsv_distance(colors, num_series)
        else:
            # Use tab10 palette (excluding yellow)
            tab10_colors = _get_tab10_colors_no_yellow()
            # Cycle if needed
            colors = [tab10_colors[i % len(tab10_colors)] for i in range(num_series)]
        
        # Handle linestyles - cycle if shorter than series count
        if linestyles is None:
            linestyles_list = ["-"] * num_series
        else:
            linestyles_list = linestyles[:]
            # Cycle if needed
            while len(linestyles_list) < num_series:
                linestyles_list.extend(linestyles)
            linestyles_list = linestyles_list[:num_series]
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Determine which series go on primary vs secondary axis
        primary_series = {}
        secondary_series = {}
        if secondary_y is not None:
            for name, values in series.items():
                if name in secondary_y:
                    secondary_series[name] = values
                else:
                    primary_series[name] = values
        else:
            primary_series = series
        
        # Get series names in order
        series_names = list(series.keys())
        primary_names = list(primary_series.keys())
        secondary_names = list(secondary_series.keys())
        
        # Plot primary axis series
        for idx, (name, values) in enumerate(primary_series.items()):
            series_idx = series_names.index(name)
            ax.plot(range(len(timestamps)), values, label=name, linewidth=2, marker='o', 
                   color=colors[series_idx], linestyle=linestyles_list[series_idx])
        
        # Create secondary axis if needed
        ax2 = None
        if secondary_series:
            ax2 = ax.twinx()
            for idx, (name, values) in enumerate(secondary_series.items()):
                series_idx = series_names.index(name)
                ax2.plot(range(len(timestamps)), values, label=name, linewidth=2, marker='o',
                        color=colors[series_idx], linestyle=linestyles_list[series_idx])
            # Set secondary y-axis label
            if secondary_names:
                # Use the label from secondary_y dict, or combine if multiple
                if len(secondary_names) == 1:
                    ax2.set_ylabel(secondary_y[secondary_names[0]], fontsize=AXIS_LABEL_FONTSIZE)
                else:
                    # Multiple series on secondary axis - use combined label or first
                    ax2.set_ylabel(secondary_y[secondary_names[0]], fontsize=AXIS_LABEL_FONTSIZE)
        
        # Add value labels if requested
        if show_values:
            x_positions = range(len(timestamps))
            
            # Add labels for primary axis series
            for name, values in primary_series.items():
                for x_pos, value in zip(x_positions, values):
                    formatted_value = _format_value(value, value_format)
                    # Place label above the point with a small offset
                    ax.text(x_pos, value, formatted_value,
                           ha='center', va='bottom', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Add labels for secondary axis series
            if ax2 is not None:
                for name, values in secondary_series.items():
                    for x_pos, value in zip(x_positions, values):
                        formatted_value = _format_value(value, value_format)
                        # Place label above the point with a small offset
                        ax2.text(x_pos, value, formatted_value,
                               ha='center', va='bottom', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Apply same formatting to axis labels as value labels
            def axis_formatter(x, pos):
                """Format axis tick labels using the same format as value labels."""
                return _format_value(x, value_format)
            
            # Format the y-axis (which shows values)
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(axis_formatter))
            if ax2 is not None:
                ax2.yaxis.set_major_formatter(ticker.FuncFormatter(axis_formatter))
        
        # Set x-axis labels with rotation
        ax.set_xticks(range(len(timestamps)))
        ax.set_xticklabels(timestamps, rotation=xlabel_rotation, ha='right')
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
        ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3)
            if ax2 is not None:
                ax2.grid(True, alpha=0.3)
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Legend
        if legend_loc is not None:
            # Combine legends from both axes if secondary axis exists
            if ax2 is not None:
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc=legend_loc)
            else:
                ax.legend(loc=legend_loc)
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating time series plot: {str(e)}")


def tool_plot_bar_chart(
    categories: Annotated[list[str], Field(description="Category labels for each bar. Example: ['Category A', 'Category B', 'Category C']")],
    values: Annotated[list[float], Field(description="Values for each category. Must have same length as categories. Example: [25.5, 18.9, 32.1]")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis (or y-axis if horizontal=True).")] = "Category",
    ylabel: Annotated[str, Field(description="Label for the y-axis (or x-axis if horizontal=True).")] = "Value",
    horizontal: Annotated[bool, Field(description="If True, create horizontal bars instead of vertical.")] = False,
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    color: Annotated[str | None, Field(description="Named color (e.g., 'steelblue') or hex (e.g., '#FF5733'). If None, uses 'steelblue'.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    xlabel_rotation: Annotated[int | float, Field(description="Rotation angle in degrees for x-axis labels (0-90 typical).")] = 45,
    show_values: Annotated[bool, Field(description="If True, display the value of each bar on top of (or next to) the bar.")] = True,
    value_format: Annotated[str, Field(description="Python format specifier. Examples: 'd' (integers), '.1f' (1 decimal), '.2f' (2 decimals), '$.2f' (currency).")] = '.1f',
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a bar chart comparing categorical data.
    
    Use this when:
    - Comparing values across different categories
    - Visualizing discrete measurements or counts
    - Showing quantities by group or classification
    - Displaying totals or aggregates by category
    
    Examples:
    - categories=['Group A', 'Group B', 'Group C'], values=[25.5, 18.9, 32.1]
    - categories=['Item 1', 'Item 2', 'Item 3'], values=[45, 120, 12], horizontal=True
    - categories=['A', 'B', 'C'], values=[10, 20, 15], show_values=True, value_format='.0f'
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not categories:
            raise ValueError("categories list cannot be empty")
        if len(categories) != len(values):
            raise ValueError(f"categories has {len(categories)} items but values has {len(values)}")
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Normalize and validate value_format if show_values is True
        if show_values:
            # Normalize format string to remove extra quotes
            value_format = _normalize_format_string(value_format)
            try:
                # Test the format string with a sample value
                test_value = 123.456
                _format_value(test_value, value_format)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value_format '{value_format}': {str(e)}")
        
        # Validate and set color
        if color is None:
            color = 'steelblue'
        else:
            _validate_color(color)
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Plot bars
        if horizontal:
            bars = ax.barh(categories, values, color=color)
            ax.set_ylabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
            ax.set_xlabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        else:
            bars = ax.bar(categories, values, color=color)
            ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
            ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
            # Rotate x-axis labels
            plt.xticks(rotation=xlabel_rotation, ha='right')
        
        # Add value labels on bars if requested
        if show_values:
            for i, (bar, value) in enumerate(zip(bars, values)):
                # Format the value
                formatted_value = _format_value(value, value_format)
                
                if horizontal:
                    # For horizontal bars, place text to the right of the bar
                    x_pos = value
                    y_pos = bar.get_y() + bar.get_height() / 2
                    ax.text(x_pos, y_pos, formatted_value,
                           ha='left', va='center', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold')
                else:
                    # For vertical bars, place text on top of the bar
                    x_pos = bar.get_x() + bar.get_width() / 2
                    y_pos = bar.get_height()
                    ax.text(x_pos, y_pos, formatted_value,
                           ha='center', va='bottom', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold')
        
        # Apply same formatting to axis labels as bar labels
        def axis_formatter(x, pos):
            """Format axis tick labels using the same format as bar labels."""
            return _format_value(x, value_format)
        
        if horizontal:
            # For horizontal bars, format the x-axis (which shows values)
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(axis_formatter))
        else:
            # For vertical bars, format the y-axis (which shows values)
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(axis_formatter))
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3, axis='y' if not horizontal else 'x')
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating bar chart: {str(e)}")


def tool_plot_histogram(
    data: Annotated[list[float], Field(description="Data values to create histogram from. Example: [12.5, 14.8, 16.2, 13.1, 18.5, 15.2, ...]")],
    bins: Annotated[int, Field(description="Number of bins (bars) in the histogram.")] = 30,
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis.")] = "Value",
    ylabel: Annotated[str, Field(description="Label for the y-axis.")] = "Frequency",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    color: Annotated[str | None, Field(description="Named color (e.g., 'steelblue') or hex (e.g., '#FF5733'). If None, uses 'steelblue'.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a histogram to visualize data distribution.
    
    Use this when:
    - Analyzing the distribution of numerical data
    - Understanding the shape and spread of data
    - Identifying outliers or unusual patterns
    - Visualizing frequency of values in ranges
    
    Examples:
    - data=[12.5, 14.8, 16.2, 13.1, 18.5, ...], bins=20, title='Data Distribution'
    - data=[0.5, 1.2, 0.8, 2.3, 1.1, ...], xlabel='Measurement', ylabel='Count'
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not data:
            raise ValueError("data list cannot be empty")
        if bins <= 0:
            raise ValueError("bins must be positive")
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Validate and set color
        if color is None:
            color = 'steelblue'
        else:
            _validate_color(color)
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Plot histogram
        n, bins_edges, patches = ax.hist(data, bins=bins, color=color, edgecolor='black', alpha=0.7)
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
        ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3, axis='y')
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Add statistics text
        mean_val = np.mean(data)
        median_val = np.median(data)
        std_val = np.std(data)
        stats_text = f'Mean: {mean_val:.2f}\nMedian: {median_val:.2f}\nStd: {std_val:.2f}'
        ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=ANNOTATION_FONTSIZE)
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating histogram: {str(e)}")


def tool_plot_scatter(
    x_data: Annotated[list[float], Field(description="X-axis values. Example: [1.0, 2.0, 3.0, 4.0, 5.0]")],
    y_data: Annotated[list[float], Field(description="Y-axis values. Must have same length as x_data. Example: [2.3, 4.8, 5.1, 7.9, 9.2]")],
    labels: Annotated[list[str] | None, Field(description="Optional labels for each point. If provided, must have same length as x_data.")] = None,
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis.")] = "X",
    ylabel: Annotated[str, Field(description="Label for the y-axis.")] = "Y",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    color: Annotated[str | None, Field(description="Named color (e.g., 'steelblue') or hex (e.g., '#FF5733'). If None, uses 'steelblue'.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a scatter plot to show relationship between two variables.
    
    Use this when:
    - Analyzing correlation between two variables
    - Visualizing relationships between paired measurements
    - Identifying patterns, trends, or clusters in data
    - Exploring dependencies between variables
    
    Examples:
    - x_data=[1.0, 2.0, 3.0], y_data=[2.3, 4.8, 5.1], xlabel='Variable X', ylabel='Variable Y'
    - x_data=[5.0, 6.0, 7.0], y_data=[14.5, 12.0, 9.8], labels=['Point A', 'Point B', 'Point C']
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not x_data or not y_data:
            raise ValueError("x_data and y_data cannot be empty")
        if len(x_data) != len(y_data):
            raise ValueError(f"x_data has {len(x_data)} values but y_data has {len(y_data)}")
        if labels is not None and len(labels) != len(x_data):
            raise ValueError(f"labels has {len(labels)} values but data has {len(x_data)} points")
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Validate and set color
        if color is None:
            color = 'steelblue'
        else:
            _validate_color(color)
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Plot scatter
        scatter = ax.scatter(x_data, y_data, s=100, alpha=0.6, c=color, edgecolors='black', linewidth=1)
        
        # Add labels if provided
        if labels:
            for i, label in enumerate(labels):
                ax.annotate(label, (x_data[i], y_data[i]), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=VALUE_LABEL_FONTSIZE, alpha=0.8)
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
        ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3)
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Calculate and display correlation coefficient
        if len(x_data) > 1:
            correlation = np.corrcoef(x_data, y_data)[0, 1]
            ax.text(0.02, 0.98, f'Correlation: {correlation:.3f}', 
                   transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   fontsize=ANNOTATION_FONTSIZE)
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating scatter plot: {str(e)}")


def tool_plot_heatmap(
    data: Annotated[list[list[float]], Field(description="2D array of values as list of rows. Example: [[1, 2, 3], [4, 5, 6], [7, 8, 9]]")],
    x_labels: Annotated[list[str] | None, Field(description="Labels for x-axis (columns). If None, uses indices. Example: ['A', 'B', 'C']")] = None,
    y_labels: Annotated[list[str] | None, Field(description="Labels for y-axis (rows). If None, uses indices. Example: ['Row 1', 'Row 2', 'Row 3', 'Row 4']")] = None,
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    colormap: Annotated[str, Field(description="Matplotlib colormap name.")] = "viridis",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_LARGE_PX,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    xlabel_rotation: Annotated[int | float, Field(description="Rotation angle in degrees for x-axis labels (0-90 typical).")] = 45,
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a heatmap to visualize 2D patterns in matrix data.
    
    Use this when:
    - Visualizing 2D arrays or matrices
    - Showing relationships between two categorical variables
    - Displaying intensity or density across two dimensions
    - Analyzing correlation matrices or confusion matrices
    
    Examples:
    - data=[[10, 20], [30, 40]], x_labels=['A', 'B'], y_labels=['X', 'Y']
    - data=[[1.2, 3.4, 2.1], [2.8, 4.5, 3.2]], x_labels=['Col 1', 'Col 2', 'Col 3'], y_labels=['Row 1', 'Row 2']
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not data:
            raise ValueError("data cannot be empty")
        if not all(isinstance(row, list) for row in data):
            raise ValueError("data must be a list of lists")
        
        # Convert to numpy array for easier manipulation
        data_array = np.array(data)
        if data_array.ndim != 2:
            raise ValueError("data must be 2-dimensional")
        
        n_rows, n_cols = data_array.shape
        
        # Validate labels if provided
        if x_labels is not None and len(x_labels) != n_cols:
            raise ValueError(f"x_labels has {len(x_labels)} items but data has {n_cols} columns")
        if y_labels is not None and len(y_labels) != n_rows:
            raise ValueError(f"y_labels has {len(y_labels)} items but data has {n_rows} rows")
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Plot heatmap
        im = ax.imshow(data_array, cmap=colormap, aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.ax.tick_params(labelsize=ANNOTATION_FONTSIZE)
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Set ticks and labels
        if x_labels:
            ax.set_xticks(range(n_cols))
            ax.set_xticklabels(x_labels, rotation=xlabel_rotation, ha='right')
        else:
            ax.set_xticks(range(n_cols))
        
        if y_labels:
            ax.set_yticks(range(n_rows))
            ax.set_yticklabels(y_labels)
        else:
            ax.set_yticks(range(n_rows))
        
        # Styling
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3)
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Add text annotations for small heatmaps
        if n_rows <= 20 and n_cols <= 20:
            for i in range(n_rows):
                for j in range(n_cols):
                    text = ax.text(j, i, f'{data_array[i, j]:.1f}',
                                 ha="center", va="center", color="w", fontsize=VALUE_LABEL_FONTSIZE)
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating heatmap: {str(e)}")


def tool_plot_stacked_bar(
    categories: Annotated[list[str], Field(description="Category labels for each bar. Example: ['Group 1', 'Group 2', 'Group 3']")],
    series: Annotated[dict[str, list[float]], Field(description="Dictionary of series names to their values. Each series becomes a segment in the stacked bars. Example: {'component_a': [10.5, 12.3, 11.8], 'component_b': [5.2, 4.8, 6.1]}")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis (or y-axis if horizontal=True).")] = "Category",
    ylabel: Annotated[str, Field(description="Label for the y-axis (or x-axis if horizontal=True).")] = "Value",
    horizontal: Annotated[bool, Field(description="If True, create horizontal stacked bars instead of vertical.")] = False,
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    colors: Annotated[list[str] | None, Field(description="List of named colors or hex values. If None, uses tab10 palette (excluding yellow). If provided but shorter than series count, pads with unused tab10 colors using HSV distance.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    legend_loc: Annotated[str | None, Field(description="Legend location: 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center', or None to hide.")] = "best",
    xlabel_rotation: Annotated[int | float, Field(description="Rotation angle in degrees for x-axis labels (0-90 typical).")] = 45,
    show_values: Annotated[bool, Field(description="If True, display values on the stacked bars. Can show segment values, total values, or both depending on show_segment_values and show_total.")] = True,
    show_segment_values: Annotated[bool, Field(description="If True and show_values=True, display individual segment values within each bar segment.")] = False,
    show_total: Annotated[bool, Field(description="If True and show_values=True, display the total value on top of (or next to) each stacked bar.")] = True,
    value_format: Annotated[str, Field(description="Python format specifier. Examples: 'd' (integers), '.1f' (1 decimal), '.2f' (2 decimals), '$.2f' (currency).")] = '.2f',
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a stacked bar chart to show composition of totals across categories.
    
    Use this when:
    - Showing how total values are composed of multiple parts
    - Comparing component contributions across categories
    - Visualizing part-to-whole relationships over categories
    - Displaying breakdown of aggregates by subgroup
    
    Examples:
    - categories=['Category A', 'Category B'], series={'part_1': [10.5, 8.3], 'part_2': [5.2, 3.8], 'part_3': [2.1, 1.5]}
    - categories=['Period 1', 'Period 2'], series={'component_x': [15, 20], 'component_y': [8, 6]}
    - categories=['A', 'B'], series={'x': [10, 15], 'y': [5, 8]}, show_values=True, show_total=True, show_segment_values=True
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not categories:
            raise ValueError("categories list cannot be empty")
        if not series:
            raise ValueError("series dictionary cannot be empty")
        
        # Validate all series have same length as categories
        for name, values in series.items():
            if len(values) != len(categories):
                raise ValueError(f"Series '{name}' has {len(values)} values but categories has {len(categories)}")
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Normalize and validate value_format if show_values is True
        if show_values:
            # Normalize format string to remove extra quotes
            value_format = _normalize_format_string(value_format)
            try:
                # Test the format string with a sample value
                test_value = 123.456
                _format_value(test_value, value_format)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value_format '{value_format}': {str(e)}")
        
        # Handle colors
        series_names = list(series.keys())
        num_series = len(series_names)
        if colors is not None:
            if len(colors) > num_series:
                raise ValueError(f"colors list has {len(colors)} items but only {num_series} series provided")
            # Validate all colors
            for color in colors:
                _validate_color(color)
            # Pad colors if needed
            colors = _pad_colors_with_hsv_distance(colors, num_series)
        else:
            # Use tab10 palette (excluding yellow)
            tab10_colors = _get_tab10_colors_no_yellow()
            # Cycle if needed
            colors = [tab10_colors[i % len(tab10_colors)] for i in range(num_series)]
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Prepare data for stacking
        series_data = [series[name] for name in series_names]
        
        # Plot stacked bars
        if horizontal:
            x_pos = np.arange(len(categories))
            left = np.zeros(len(categories))
            
            for i, (name, values) in enumerate(zip(series_names, series_data)):
                bars = ax.barh(x_pos, values, left=left, label=name, color=colors[i])
                
                # Add segment value labels if requested
                if show_values and show_segment_values:
                    for j, (bar, value) in enumerate(zip(bars, values)):
                        if value > 0:  # Only show if segment has value
                            x_label_pos = left[j] + value / 2
                            y_label_pos = bar.get_y() + bar.get_height() / 2
                            formatted_value = _format_value(value, value_format)
                            ax.text(x_label_pos, y_label_pos, formatted_value,
                                   ha='center', va='center', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold',
                                   color='white')
                
                left += np.array(values)
            
            # Add total value labels if requested
            if show_values and show_total:
                totals = np.sum(series_data, axis=0)
                for j, (cat_pos, total) in enumerate(zip(x_pos, totals)):
                    formatted_total = _format_value(total, value_format)
                    ax.text(total, cat_pos, formatted_total,
                           ha='left', va='center', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold')
            
            ax.set_yticks(x_pos)
            ax.set_yticklabels(categories)
            ax.set_ylabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
            ax.set_xlabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        else:
            x_pos = np.arange(len(categories))
            bottom = np.zeros(len(categories))
            
            for i, (name, values) in enumerate(zip(series_names, series_data)):
                bars = ax.bar(x_pos, values, bottom=bottom, label=name, color=colors[i])
                
                # Add segment value labels if requested
                if show_values and show_segment_values:
                    for j, (bar, value) in enumerate(zip(bars, values)):
                        if value > 0:  # Only show if segment has value
                            x_label_pos = bar.get_x() + bar.get_width() / 2
                            y_label_pos = bottom[j] + value / 2
                            formatted_value = _format_value(value, value_format)
                            ax.text(x_label_pos, y_label_pos, formatted_value,
                                   ha='center', va='center', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold',
                                   color='white')
                
                bottom += np.array(values)
            
            # Add total value labels if requested
            if show_values and show_total:
                totals = np.sum(series_data, axis=0)
                for j, (cat_pos, total) in enumerate(zip(x_pos, totals)):
                    formatted_total = _format_value(total, value_format)
                    ax.text(cat_pos, total, formatted_total,
                           ha='center', va='bottom', fontsize=VALUE_LABEL_FONTSIZE, fontweight='bold')
            
            ax.set_xticks(x_pos)
            ax.set_xticklabels(categories, rotation=xlabel_rotation, ha='right')
            ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
            ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Legend
        if legend_loc is not None:
            ax.legend(loc=legend_loc)
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3, axis='y' if not horizontal else 'x')
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating stacked bar chart: {str(e)}")


def tool_plot_ode_solution(
    ode_result: Annotated[str, Field(description="JSON string output from the solve_ode tool. Must contain 't' (time points) and variable arrays.")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, uses 'ODE Solution'.")] = None,
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    colors: Annotated[list[str] | None, Field(description="List of named colors or hex values. If None, uses tab10 palette (excluding yellow). If provided but shorter than series count, pads with unused tab10 colors using HSV distance.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    legend_loc: Annotated[str | None, Field(description="Legend location: 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center', or None to hide.")] = "best",
    linestyles: Annotated[list[str] | None, Field(description="List of linestyle strings ('-', '--', '-.', ':'), one per series. If None, uses solid lines. Cycles if shorter than series count.")] = None,
    secondary_y: Annotated[dict[str, str] | None, Field(description="Dictionary mapping variable names to y-axis labels for secondary axis. Example: {'x': 'Position (m)'}")] = None,
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot the solution of differential equations from solve_ode tool.
    
    Use this when:
    - Visualizing results from solve_ode tool
    - Analyzing behavior of dynamical systems
    - Comparing multiple solution variables over time
    
    Examples:
    - ode_result='{"t": [0, 1, 2], "x": [1, 0.5, 0.25], "success": true}'
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        
        # Parse the JSON result
        result = json.loads(ode_result)
        
        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError("ode_result must be a JSON object")
        if 't' not in result:
            raise ValueError("ode_result must contain 't' (time) array")
        
        # Extract time points
        t = result['t']
        if not t:
            raise ValueError("Time array 't' cannot be empty")
        
        # Find all variable arrays (anything that's not 't', 'success', 'method', etc.)
        metadata_keys = {'t', 'success', 'method', 'n_points'}
        variable_names = [key for key in result.keys() if key not in metadata_keys]
        
        if not variable_names:
            raise ValueError("No solution variables found in ode_result")
        
        num_variables = len(variable_names)
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Validate linestyles
        valid_linestyles = {"-", "--", "-.", ":"}
        if linestyles is not None:
            if len(linestyles) > num_variables:
                raise ValueError(f"linestyles list has {len(linestyles)} items but only {num_variables} variables found")
            for ls in linestyles:
                if ls not in valid_linestyles:
                    raise ValueError(f"Invalid linestyle '{ls}'. Must be one of {valid_linestyles}")
        
        # Validate secondary_y
        if secondary_y is not None:
            for var_name in secondary_y.keys():
                if var_name not in variable_names:
                    raise ValueError(f"secondary_y key '{var_name}' not found in variable names")
        
        # Handle colors
        if colors is not None:
            if len(colors) > num_variables:
                raise ValueError(f"colors list has {len(colors)} items but only {num_variables} variables found")
            # Validate all colors
            for color in colors:
                _validate_color(color)
            # Pad colors if needed
            colors = _pad_colors_with_hsv_distance(colors, num_variables)
        else:
            # Use tab10 palette (excluding yellow)
            tab10_colors = _get_tab10_colors_no_yellow()
            # Cycle if needed
            colors = [tab10_colors[i % len(tab10_colors)] for i in range(num_variables)]
        
        # Handle linestyles - cycle if shorter than variable count
        if linestyles is None:
            linestyles_list = ["-"] * num_variables
        else:
            linestyles_list = linestyles[:]
            # Cycle if needed
            while len(linestyles_list) < num_variables:
                linestyles_list.extend(linestyles)
            linestyles_list = linestyles_list[:num_variables]
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Determine which variables go on primary vs secondary axis
        primary_vars = {}
        secondary_vars = {}
        if secondary_y is not None:
            for var_name in variable_names:
                values = result[var_name]
                if len(values) != len(t):
                    raise ValueError(f"Variable '{var_name}' has {len(values)} values but time has {len(t)} points")
                if var_name in secondary_y:
                    secondary_vars[var_name] = values
                else:
                    primary_vars[var_name] = values
        else:
            for var_name in variable_names:
                values = result[var_name]
                if len(values) != len(t):
                    raise ValueError(f"Variable '{var_name}' has {len(values)} values but time has {len(t)} points")
                primary_vars[var_name] = values
        
        # Get variable names in order
        primary_names = list(primary_vars.keys())
        secondary_names = list(secondary_vars.keys())
        
        # Plot primary axis variables
        for var_name, values in primary_vars.items():
            var_idx = variable_names.index(var_name)
            ax.plot(t, values, label=var_name, linewidth=2, marker='o', markersize=4,
                   color=colors[var_idx], linestyle=linestyles_list[var_idx])
        
        # Create secondary axis if needed
        ax2 = None
        if secondary_vars:
            ax2 = ax.twinx()
            for var_name, values in secondary_vars.items():
                var_idx = variable_names.index(var_name)
                ax2.plot(t, values, label=var_name, linewidth=2, marker='o', markersize=4,
                        color=colors[var_idx], linestyle=linestyles_list[var_idx])
            # Set secondary y-axis label
            if secondary_names:
                # Use the label from secondary_y dict, or combine if multiple
                if len(secondary_names) == 1:
                    ax2.set_ylabel(secondary_y[secondary_names[0]], fontsize=AXIS_LABEL_FONTSIZE)
                else:
                    # Multiple variables on secondary axis - use first label
                    ax2.set_ylabel(secondary_y[secondary_names[0]], fontsize=AXIS_LABEL_FONTSIZE)
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        ax.set_xlabel('Time (t)', fontsize=AXIS_LABEL_FONTSIZE)
        ax.set_ylabel('Value', fontsize=AXIS_LABEL_FONTSIZE)
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        else:
            ax.set_title('ODE Solution', fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3)
            if ax2 is not None:
                ax2.grid(True, alpha=0.3)
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Legend
        if legend_loc is not None:
            # Combine legends from both axes if secondary axis exists
            if ax2 is not None:
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc=legend_loc)
            else:
                ax.legend(loc=legend_loc)
        
        # Add method info if available
        if 'method' in result:
            method_text = f"Method: {result['method']}"
            ax.text(0.02, 0.98, method_text, transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   fontsize=ANNOTATION_FONTSIZE)
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except json.JSONDecodeError as e:
        plt.close('all')
        raise ValueError(f"Invalid JSON in ode_result: {str(e)}")
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating ODE solution plot: {str(e)}")


def tool_plot_stackplot(
    x_data: Annotated[list[float] | list[str], Field(description="X-axis values (numeric or string labels). Example: [0, 1, 2, 3] or ['Jan', 'Feb', 'Mar']")],
    series: Annotated[dict[str, list[float]], Field(description="Dictionary of series names to their values. Each series becomes a layer in the stack. Example: {'component_a': [10.5, 12.3, 11.8, 13.2], 'component_b': [5.2, 4.8, 6.1, 5.5]}")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis.")] = "X",
    ylabel: Annotated[str, Field(description="Label for the y-axis.")] = "Value",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_PX,
    colors: Annotated[list[str] | None, Field(description="List of named colors or hex values. If None, uses tab10 palette (excluding yellow). If provided but shorter than series count, pads with unused tab10 colors using HSV distance.")] = None,
    xlim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for x-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    ylim: Annotated[tuple[float, float] | None, Field(description="Tuple of (min, max) for y-axis limits. If None, uses matplotlib auto-scaling.")] = None,
    grid: Annotated[bool | str, Field(description="Grid control: True (both axes), False (hide), 'x' (x-axis only), 'y' (y-axis only), 'both' (both axes).")] = True,
    legend_loc: Annotated[str | None, Field(description="Legend location: 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center', or None to hide.")] = "best",
    baseline: Annotated[str, Field(description="Baseline for stacking: 'zero' (stack from zero), 'sym' (symmetric around zero), 'wiggle' (minimize wiggle), 'weighted_wiggle'.")] = "zero",
    alpha: Annotated[float, Field(description="Transparency of the filled areas (0.0-1.0).")] = 0.7,
    xlabel_rotation: Annotated[int | float, Field(description="Rotation angle in degrees for x-axis labels (0-90 typical).")] = 45,
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a stacked area chart to show composition over a continuous variable.
    
    Use this when:
    - Showing how multiple components contribute to a total over time or another continuous variable
    - Visualizing the evolution of composition across a range
    - Comparing multiple series where you want to see both individual values and cumulative totals
    - Displaying trends in part-to-whole relationships
    
    Examples:
    - x_data=[0, 1, 2, 3], series={'component_a': [10.5, 12.3, 11.8, 13.2], 'component_b': [5.2, 4.8, 6.1, 5.5]}
    - x_data=['Q1', 'Q2', 'Q3', 'Q4'], series={'product_x': [100, 120, 110, 130], 'product_y': [80, 90, 95, 100]}
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not x_data:
            raise ValueError("x_data list cannot be empty")
        if not series:
            raise ValueError("series dictionary cannot be empty")
        
        # Validate all series have same length as x_data
        for name, values in series.items():
            if len(values) != len(x_data):
                raise ValueError(f"Series '{name}' has {len(values)} values but x_data has {len(x_data)}")
        
        # Validate axis limits
        if xlim is not None:
            if len(xlim) != 2 or xlim[0] >= xlim[1]:
                raise ValueError("xlim must be a tuple (min, max) where min < max")
        if ylim is not None:
            if len(ylim) != 2 or ylim[0] >= ylim[1]:
                raise ValueError("ylim must be a tuple (min, max) where min < max")
        
        # Normalize and validate grid parameter
        grid = _normalize_grid_parameter(grid)
        valid_grid_values = {True, False, "x", "y", "both"}
        if grid not in valid_grid_values:
            raise ValueError(f"grid must be one of {valid_grid_values}")
        
        # Validate baseline parameter
        valid_baselines = {"zero", "sym", "wiggle", "weighted_wiggle"}
        if baseline not in valid_baselines:
            raise ValueError(f"baseline must be one of {valid_baselines}")
        
        # Validate alpha
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("alpha must be between 0.0 and 1.0")
        
        # Handle colors
        series_names = list(series.keys())
        num_series = len(series_names)
        if colors is not None:
            if len(colors) > num_series:
                raise ValueError(f"colors list has {len(colors)} items but only {num_series} series provided")
            # Validate all colors
            for color in colors:
                _validate_color(color)
            # Pad colors if needed
            colors = _pad_colors_with_hsv_distance(colors, num_series)
        else:
            # Use tab10 palette (excluding yellow)
            tab10_colors = _get_tab10_colors_no_yellow()
            # Cycle if needed
            colors = [tab10_colors[i % len(tab10_colors)] for i in range(num_series)]
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Prepare data for stacking - need to convert to arrays
        series_data = [series[name] for name in series_names]
        
        # Handle x_data - if strings, use numeric indices for plotting
        if isinstance(x_data[0], str):
            x_numeric = np.arange(len(x_data))
            use_string_labels = True
        else:
            x_numeric = np.array(x_data)
            use_string_labels = False
        
        # Plot stacked area chart
        ax.stackplot(x_numeric, *series_data, labels=series_names, colors=colors, 
                    alpha=alpha, baseline=baseline)
        
        # Set x-axis labels
        if use_string_labels:
            ax.set_xticks(x_numeric)
            ax.set_xticklabels(x_data, rotation=xlabel_rotation, ha='right')
        elif xlabel_rotation != 0:
            # Apply rotation even for numeric labels if requested
            plt.xticks(rotation=xlabel_rotation, ha='right')
        
        # Set axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
        ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Legend
        if legend_loc is not None:
            ax.legend(loc=legend_loc)
        
        # Grid control
        if grid is True or grid == "both":
            ax.grid(True, alpha=0.3)
        elif grid == "x":
            ax.grid(True, alpha=0.3, axis='x')
        elif grid == "y":
            ax.grid(True, alpha=0.3, axis='y')
        # grid == False: no grid
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating stackplot: {str(e)}")


def tool_plot_pie_chart(
    labels: Annotated[list[str], Field(description="Labels for each pie slice. Example: ['Category A', 'Category B', 'Category C']")],
    values: Annotated[list[float], Field(description="Values for each slice. Must have same length as labels. Example: [25.5, 18.9, 32.1]")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    figsize: Annotated[tuple[int, int], Field(description="Figure size in pixels as (width, height).")] = DEFAULT_FIGSIZE_LARGE_PX,
    colors: Annotated[list[str] | None, Field(description="List of named colors or hex values. If None, uses tab10 palette (excluding yellow). If provided but shorter than labels count, pads with unused tab10 colors using HSV distance.")] = None,
    autopct: Annotated[str | None, Field(description="Format string for percentage display (e.g., '%1.1f%%', '%0.0f%%'). If None, no percentages are shown.")] = '%1.1f%%',
    startangle: Annotated[float, Field(description="Starting angle in degrees for the first slice (0-360).")] = 90,
    explode: Annotated[list[float] | None, Field(description="List of explode values (0-1) to offset slices. If None, no slices are exploded. Example: [0.1, 0, 0, 0.2]")] = None,
    legend_loc: Annotated[str | None, Field(description="Legend location: 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center', or None to hide.")] = "best",
    shadow: Annotated[bool, Field(description="If True, adds shadow effect to the pie chart.")] = False,
    output_format: Annotated[str, Field(description="Output image format: 'png' or 'svg'. Defaults to 'png'.")] = 'png',
) -> ImageContent:
    """Plot a pie chart to show proportional composition of data.
    
    Use this when:
    - Showing parts of a whole
    - Visualizing proportional distributions
    - Comparing relative sizes of categories
    - Displaying percentage breakdowns
    
    Examples:
    - labels=['Category A', 'Category B', 'Category C'], values=[25.5, 18.9, 32.1]
    - labels=['Group 1', 'Group 2'], values=[45, 120], autopct='%0.0f%%', explode=[0.1, 0]
    """
    try:
        # Input validation
        if output_format not in ('png', 'svg'):
            raise ValueError("output_format must be 'png' or 'svg'")
        if not labels:
            raise ValueError("labels list cannot be empty")
        if len(labels) != len(values):
            raise ValueError(f"labels has {len(labels)} items but values has {len(values)}")
        
        # Validate all values are non-negative
        if any(v < 0 for v in values):
            raise ValueError("All values must be non-negative")
        
        # Check if all values are zero
        if all(v == 0 for v in values):
            raise ValueError("At least one value must be greater than zero")
        
        # Validate startangle
        if not (0 <= startangle <= 360):
            raise ValueError("startangle must be between 0 and 360 degrees")
        
        # Validate explode
        if explode is not None:
            if len(explode) != len(labels):
                raise ValueError(f"explode has {len(explode)} items but labels has {len(labels)}")
            if any(e < 0 or e > 1 for e in explode):
                raise ValueError("All explode values must be between 0 and 1")
        
        # Handle colors
        num_slices = len(labels)
        if colors is not None:
            if len(colors) > num_slices:
                raise ValueError(f"colors list has {len(colors)} items but only {num_slices} labels provided")
            # Validate all colors
            for color in colors:
                _validate_color(color)
            # Pad colors if needed
            colors = _pad_colors_with_hsv_distance(colors, num_slices)
        else:
            # Use tab10 palette (excluding yellow)
            tab10_colors = _get_tab10_colors_no_yellow()
            # Cycle if needed
            colors = [tab10_colors[i % len(tab10_colors)] for i in range(num_slices)]
        
        # Create figure (convert pixels to inches)
        fig, ax = plt.subplots(figsize=_pixels_to_inches(figsize))
        
        # Plot pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct,
            startangle=startangle,
            explode=explode,
            shadow=shadow
        )
        
        # Style the percentage text
        if autopct is not None:
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(ANNOTATION_FONTSIZE)
        
        # Styling
        if title:
            ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold')
        
        # Legend
        if legend_loc is not None:
            ax.legend(wedges, labels, loc=legend_loc)
        
        # Equal aspect ratio ensures pie is drawn as a circle
        ax.axis('equal')
        
        # Save to memory buffer
        buf = io.BytesIO()
        if output_format == 'svg':
            fig.savefig(buf, format='svg', bbox_inches='tight')
        else:
            fig.savefig(buf, format='png', dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf, format=output_format)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating pie chart: {str(e)}")


def register_plotting_tools(mcp):
    """Register matplotlib-based plotting tools with the MCP server."""
    mcp.tool(name="plot_timeseries")(tool_plot_timeseries)
    mcp.tool(name="plot_bar_chart")(tool_plot_bar_chart)
    mcp.tool(name="plot_histogram")(tool_plot_histogram)
    mcp.tool(name="plot_scatter")(tool_plot_scatter)
    mcp.tool(name="plot_heatmap")(tool_plot_heatmap)
    mcp.tool(name="plot_stacked_bar")(tool_plot_stacked_bar)
    mcp.tool(name="plot_stackplot")(tool_plot_stackplot)
    mcp.tool(name="plot_ode_solution")(tool_plot_ode_solution)
    mcp.tool(name="plot_pie_chart")(tool_plot_pie_chart)
