"""Matplotlib-based visualization tools for data analysis."""

import base64
import io
import json
from typing import Annotated

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from mcp.types import ImageContent
from pydantic import Field

# Use non-interactive backend for server use
matplotlib.use('Agg')


def _create_image_content(buf: io.BytesIO) -> ImageContent:
    """Helper to create ImageContent from BytesIO buffer."""
    buf.seek(0)
    image_data = base64.b64encode(buf.read()).decode('utf-8')
    return ImageContent(
        type="image",
        data=image_data,
        mimeType="image/png"
    )


def tool_plot_timeseries(
    timestamps: Annotated[list[str], Field(description="ISO 8601 timestamps or numeric string values for x-axis points. Example: ['2026-01-01T10:00:00Z', '2026-01-01T11:00:00Z', ...]")],
    series: Annotated[dict[str, list[float]], Field(description="Dictionary of series names to their values. Each series will be plotted as a separate line. Example: {'temperature': [20.5, 21.3, 19.8], 'humidity': [65, 68, 62]}")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis.")] = "Time",
    ylabel: Annotated[str, Field(description="Label for the y-axis.")] = "Value",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 6),
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
    """
    try:
        # Input validation
        if not timestamps:
            raise ValueError("timestamps list cannot be empty")
        if not series:
            raise ValueError("series dictionary cannot be empty")
        
        # Validate all series have same length as timestamps
        for name, values in series.items():
            if len(values) != len(timestamps):
                raise ValueError(f"Series '{name}' has {len(values)} values but timestamps has {len(timestamps)}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot each series
        for name, values in series.items():
            ax.plot(range(len(timestamps)), values, label=name, linewidth=2, marker='o')
        
        # Set x-axis labels (rotate if timestamps are long)
        ax.set_xticks(range(len(timestamps)))
        ax.set_xticklabels(timestamps, rotation=45, ha='right')
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
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
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 6),
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
    """
    try:
        # Input validation
        if not categories:
            raise ValueError("categories list cannot be empty")
        if len(categories) != len(values):
            raise ValueError(f"categories has {len(categories)} items but values has {len(values)}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot bars
        if horizontal:
            ax.barh(categories, values, color='steelblue')
            ax.set_ylabel(xlabel, fontsize=12)
            ax.set_xlabel(ylabel, fontsize=12)
        else:
            ax.bar(categories, values, color='steelblue')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
        
        # Styling
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y' if not horizontal else 'x')
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating bar chart: {str(e)}")


def tool_plot_histogram(
    data: Annotated[list[float], Field(description="Data values to create histogram from. Example: [12.5, 14.8, 16.2, 13.1, 18.5, 15.2, ...]")],
    bins: Annotated[int, Field(description="Number of bins (bars) in the histogram.")] = 30,
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    xlabel: Annotated[str, Field(description="Label for the x-axis.")] = "Value",
    ylabel: Annotated[str, Field(description="Label for the y-axis.")] = "Frequency",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 6),
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
        if not data:
            raise ValueError("data list cannot be empty")
        if bins <= 0:
            raise ValueError("bins must be positive")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot histogram
        n, bins_edges, patches = ax.hist(data, bins=bins, color='steelblue', edgecolor='black', alpha=0.7)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add statistics text
        mean_val = np.mean(data)
        median_val = np.median(data)
        std_val = np.std(data)
        stats_text = f'Mean: {mean_val:.2f}\nMedian: {median_val:.2f}\nStd: {std_val:.2f}'
        ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=10)
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
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
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 6),
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
        if not x_data or not y_data:
            raise ValueError("x_data and y_data cannot be empty")
        if len(x_data) != len(y_data):
            raise ValueError(f"x_data has {len(x_data)} values but y_data has {len(y_data)}")
        if labels is not None and len(labels) != len(x_data):
            raise ValueError(f"labels has {len(labels)} values but data has {len(x_data)} points")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot scatter
        scatter = ax.scatter(x_data, y_data, s=100, alpha=0.6, c='steelblue', edgecolors='black', linewidth=1)
        
        # Add labels if provided
        if labels:
            for i, label in enumerate(labels):
                ax.annotate(label, (x_data[i], y_data[i]), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, alpha=0.8)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Calculate and display correlation coefficient
        if len(x_data) > 1:
            correlation = np.corrcoef(x_data, y_data)[0, 1]
            ax.text(0.02, 0.98, f'Correlation: {correlation:.3f}', 
                   transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   fontsize=10)
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating scatter plot: {str(e)}")


def tool_plot_heatmap(
    data: Annotated[list[list[float]], Field(description="2D array of values as list of rows. Example: [[1, 2, 3], [4, 5, 6], [7, 8, 9]]")],
    x_labels: Annotated[list[str] | None, Field(description="Labels for x-axis (columns). If None, uses indices. Example: ['A', 'B', 'C']")] = None,
    y_labels: Annotated[list[str] | None, Field(description="Labels for y-axis (rows). If None, uses indices. Example: ['Row 1', 'Row 2', 'Row 3', 'Row 4']")] = None,
    title: Annotated[str | None, Field(description="Title for the plot. If None, no title is displayed.")] = None,
    colormap: Annotated[str, Field(description="Matplotlib colormap name.")] = "viridis",
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 8),
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
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot heatmap
        im = ax.imshow(data_array, cmap=colormap, aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.ax.tick_params(labelsize=10)
        
        # Set ticks and labels
        if x_labels:
            ax.set_xticks(range(n_cols))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        else:
            ax.set_xticks(range(n_cols))
        
        if y_labels:
            ax.set_yticks(range(n_rows))
            ax.set_yticklabels(y_labels)
        else:
            ax.set_yticks(range(n_rows))
        
        # Styling
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Add text annotations for small heatmaps
        if n_rows <= 20 and n_cols <= 20:
            for i in range(n_rows):
                for j in range(n_cols):
                    text = ax.text(j, i, f'{data_array[i, j]:.1f}',
                                 ha="center", va="center", color="w", fontsize=8)
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
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
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 6),
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
    """
    try:
        # Input validation
        if not categories:
            raise ValueError("categories list cannot be empty")
        if not series:
            raise ValueError("series dictionary cannot be empty")
        
        # Validate all series have same length as categories
        for name, values in series.items():
            if len(values) != len(categories):
                raise ValueError(f"Series '{name}' has {len(values)} values but categories has {len(categories)}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Prepare data for stacking
        series_names = list(series.keys())
        series_data = [series[name] for name in series_names]
        
        # Define colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(series_names)))
        
        # Plot stacked bars
        if horizontal:
            x_pos = np.arange(len(categories))
            left = np.zeros(len(categories))
            
            for i, (name, values) in enumerate(zip(series_names, series_data)):
                ax.barh(x_pos, values, left=left, label=name, color=colors[i])
                left += np.array(values)
            
            ax.set_yticks(x_pos)
            ax.set_yticklabels(categories)
            ax.set_ylabel(xlabel, fontsize=12)
            ax.set_xlabel(ylabel, fontsize=12)
        else:
            x_pos = np.arange(len(categories))
            bottom = np.zeros(len(categories))
            
            for i, (name, values) in enumerate(zip(series_names, series_data)):
                ax.bar(x_pos, values, bottom=bottom, label=name, color=colors[i])
                bottom += np.array(values)
            
            ax.set_xticks(x_pos)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
        
        # Styling
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, axis='y' if not horizontal else 'x')
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating stacked bar chart: {str(e)}")


def tool_plot_ode_solution(
    ode_result: Annotated[str, Field(description="JSON string output from the solve_ode tool. Must contain 't' (time points) and variable arrays.")],
    title: Annotated[str | None, Field(description="Title for the plot. If None, uses 'ODE Solution'.")] = None,
    figsize: Annotated[tuple[int, int], Field(description="Figure size in inches as (width, height).")] = (10, 6),
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
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot each variable
        for var_name in variable_names:
            values = result[var_name]
            if len(values) != len(t):
                raise ValueError(f"Variable '{var_name}' has {len(values)} values but time has {len(t)} points")
            ax.plot(t, values, label=var_name, linewidth=2, marker='o', markersize=4)
        
        # Styling
        ax.set_xlabel('Time (t)', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        else:
            ax.set_title('ODE Solution', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Add method info if available
        if 'method' in result:
            method_text = f"Method: {result['method']}"
            ax.text(0.02, 0.98, method_text, transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   fontsize=10)
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Free memory
        
        # Return ImageContent object
        return _create_image_content(buf)
        
    except json.JSONDecodeError as e:
        plt.close('all')
        raise ValueError(f"Invalid JSON in ode_result: {str(e)}")
    except Exception as e:
        plt.close('all')  # Clean up any figures
        raise ValueError(f"Error creating ODE solution plot: {str(e)}")


def register_plotting_tools(mcp):
    """Register matplotlib-based plotting tools with the MCP server."""
    mcp.tool(name="plot_timeseries")(tool_plot_timeseries)
    mcp.tool(name="plot_bar_chart")(tool_plot_bar_chart)
    mcp.tool(name="plot_histogram")(tool_plot_histogram)
    mcp.tool(name="plot_scatter")(tool_plot_scatter)
    mcp.tool(name="plot_heatmap")(tool_plot_heatmap)
    mcp.tool(name="plot_stacked_bar")(tool_plot_stacked_bar)
    mcp.tool(name="plot_ode_solution")(tool_plot_ode_solution)
