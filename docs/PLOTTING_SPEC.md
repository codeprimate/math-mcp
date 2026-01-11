# Plotting Tools Specification

## Overview

Add matplotlib-based visualization tools to the math MCP server for operational IT data analysis and charting arbitrary data. All plots return as in-memory base64-encoded images (no disk I/O).

## Design Principles

1. **Memory-only**: All images generated in-memory using `io.BytesIO`
2. **FastMCP Image type**: Return `Image` objects for automatic MCP content block conversion
3. **Inline display**: Images appear directly in Cursor/Claude conversations
4. **IT-focused**: Prioritize operational data visualization over mathematical function plotting
5. **Flexible input**: Accept JSON-serializable data structures (lists, dicts)

## Implementation

### New Module: `src/math_mcp/plotting_tools.py`

**Dependencies:**
- `matplotlib>=3.7.0` (add to requirements.txt)
- `fastmcp.utilities.types.Image` (already available)

**Setup:**
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
```

## Tools to Implement

### 1. `plot_timeseries` (Priority 1)
**Purpose:** Plot time-series data (most common use case for operational data)

**Parameters:**
- `timestamps: list[str]` - ISO 8601 timestamps or numeric values
- `series: dict[str, list[float]]` - Multiple series, e.g. `{"response_time": [...], "error_rate": [...]}`
- `title: str | None` - Plot title
- `xlabel: str` - X-axis label (default: "Time")
- `ylabel: str` - Y-axis label (default: "Value")
- `figsize: tuple[int, int]` - Figure size in inches (default: `(10, 6)`)

**Returns:** `Image` (PNG format, 100 DPI)

**Use cases:** Response times, traffic patterns, error rates over time

---

### 2. `plot_bar_chart` (Priority 1)
**Purpose:** Compare categorical data

**Parameters:**
- `categories: list[str]` - Category labels
- `values: list[float]` - Values for each category
- `title: str | None` - Plot title
- `xlabel: str` - X-axis label (default: "Category")
- `ylabel: str` - Y-axis label (default: "Value")
- `horizontal: bool` - Horizontal bars (default: `False`)
- `figsize: tuple[int, int]` - Figure size (default: `(10, 6)`)

**Returns:** `Image`

**Use cases:** Endpoint usage, error counts by type, feature adoption

---

### 3. `plot_histogram` (Priority 2)
**Purpose:** Visualize data distribution

**Parameters:**
- `data: list[float]` - Data values
- `bins: int` - Number of bins (default: `30`)
- `title: str | None` - Plot title
- `xlabel: str` - X-axis label (default: "Value")
- `ylabel: str` - Y-axis label (default: "Frequency")
- `figsize: tuple[int, int]` - Figure size (default: `(10, 6)`)

**Returns:** `Image`

**Use cases:** Response time distributions, latency analysis

---

### 4. `plot_scatter` (Priority 2)
**Purpose:** Show correlation between two variables

**Parameters:**
- `x_data: list[float]` - X values
- `y_data: list[float]` - Y values
- `labels: list[str] | None` - Optional point labels
- `title: str | None` - Plot title
- `xlabel: str` - X-axis label (default: "X")
- `ylabel: str` - Y-axis label (default: "Y")
- `figsize: tuple[int, int]` - Figure size (default: `(10, 6)`)

**Returns:** `Image`

**Use cases:** Correlation analysis (traffic vs errors, cache hit rate vs response time)

---

### 5. `plot_heatmap` (Priority 2)
**Purpose:** Visualize 2D patterns (time-based, geographic, etc.)

**Parameters:**
- `data: list[list[float]]` - 2D array of values
- `x_labels: list[str] | None` - X-axis labels (e.g., hours of day)
- `y_labels: list[str] | None` - Y-axis labels (e.g., days of week)
- `title: str | None` - Plot title
- `colormap: str` - Matplotlib colormap name (default: `"viridis"`)
- `figsize: tuple[int, int]` - Figure size (default: `(10, 8)`)

**Returns:** `Image`

**Use cases:** Request patterns by hour/day, geographic distribution, error hotspots

---

### 6. `plot_stacked_bar` (Priority 3)
**Purpose:** Compare multiple series across categories

**Parameters:**
- `categories: list[str]` - Category labels
- `series: dict[str, list[float]]` - Multiple series, e.g. `{"success": [...], "error": [...]}`
- `title: str | None` - Plot title
- `xlabel: str` - X-axis label (default: "Category")
- `ylabel: str` - Y-axis label (default: "Value")
- `horizontal: bool` - Horizontal bars (default: `False`)
- `figsize: tuple[int, int]` - Figure size (default: `(10, 6)`)

**Returns:** `Image`

**Use cases:** Status code breakdown, multi-environment comparison

---

### 7. `plot_ode_solution` (Priority 3 - Mathematical Integration)
**Purpose:** Visualize ODE solutions from `solve_ode` tool

**Parameters:**
- `ode_result: str` - JSON string from `solve_ode` tool
- `title: str | None` - Plot title
- `figsize: tuple[int, int]` - Figure size (default: `(10, 6)`)

**Returns:** `Image`

**Use cases:** Visualize differential equation solutions

---

## Implementation Pattern

**Standard tool structure:**
```python
def tool_plot_timeseries(
    timestamps: Annotated[list[str], Field(description="...")],
    series: Annotated[dict[str, list[float]], Field(description="...")],
    title: Annotated[str | None, Field(description="...")] = None,
    xlabel: Annotated[str, Field(description="...")] = "Time",
    ylabel: Annotated[str, Field(description="...")] = "Value",
    figsize: Annotated[tuple[int, int], Field(description="...")] = (10, 6),
) -> Image:
    """Plot time-series data.
    
    Use this when:
    - Visualizing metrics over time
    - Analyzing trends and patterns
    - Comparing multiple time series
    
    Examples:
    - timestamps=['2026-01-01T10:00:00Z', ...], series={'response_time': [145, 167, ...]}
    """
    try:
        import matplotlib.pyplot as plt
        from fastmcp.utilities.types import Image
        import io
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plotting logic here
        for name, values in series.items():
            ax.plot(timestamps, values, label=name, linewidth=2)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Important: free memory
        buf.seek(0)
        
        # Return Image object
        return Image(data=buf.read(), format="png")
        
    except Exception as e:
        # For errors, return a simple error image or raise
        raise ValueError(f"Error creating plot: {str(e)}")
```

## Error Handling

- **Input validation**: Check data dimensions, empty arrays, mismatched lengths
- **Matplotlib errors**: Catch and provide helpful error messages
- **Memory management**: Always call `plt.close(fig)` to free memory
- **Graceful degradation**: Return informative errors rather than crashing

## Testing Approach

**File:** `tests/test_plotting.py`

**Test categories:**
1. **Basic functionality**: Each tool produces valid Image output
2. **Data validation**: Empty data, mismatched dimensions, invalid inputs
3. **Image properties**: Verify format, dimensions, non-zero size
4. **Integration**: Test with ODE solver output (`plot_ode_solution`)
5. **Memory leaks**: Verify plots don't accumulate in memory

**Example test:**
```python
def test_plot_timeseries_basic():
    result = tool_plot_timeseries(
        timestamps=["2026-01-01T10:00:00Z", "2026-01-01T11:00:00Z"],
        series={"metric": [100, 120]},
    )
    assert isinstance(result, Image)
    # Could decode and verify it's valid PNG
```

## Registration

**Update `src/math_mcp/server.py`:**
```python
from math_mcp import scipy_tools, sympy_tools, unit_tools, plotting_tools

# Register all tools
plotting_tools.register_plotting_tools(mcp)
```

## Documentation

**Update `README.md`:**
- Add "Plotting & Visualization" section
- Include examples for each tool
- Show integration with other tools (e.g., plot ODE solutions)
- Note that images appear inline in Cursor/Claude

## Dependencies

**Add to `requirements.txt`:**
```
matplotlib>=3.7.0
```

## Implementation Priority

1. **Phase 1**: `plot_timeseries`, `plot_bar_chart` (most common use cases)
2. **Phase 2**: `plot_histogram`, `plot_scatter`, `plot_heatmap` (analysis tools)
3. **Phase 3**: `plot_stacked_bar`, `plot_ode_solution` (specialized tools)

## Design Constraints

- **No disk I/O**: All operations in-memory
- **Memory efficiency**: Close figures immediately after saving to buffer
- **Non-interactive backend**: Use `matplotlib.use('Agg')` for server environment
- **Consistent styling**: Use consistent colors, fonts, DPI across all plots
- **Fast generation**: Target <100ms for typical plots

## Future Considerations

- **Customization options**: Color schemes, line styles, markers
- **Advanced plots**: Box plots, violin plots, 3D surface plots
- **Statistical overlays**: Moving averages, trend lines, confidence intervals
- **Multiple subplots**: Grid layouts for comparing multiple charts
- **Animation support**: Return multiple frames or GIF (if needed)
