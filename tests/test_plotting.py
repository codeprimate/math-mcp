"""Tests for plotting tools."""

import base64
import json
import sys
from io import BytesIO
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from math_mcp.plotting_tools import (
    tool_plot_bar_chart,
    tool_plot_heatmap,
    tool_plot_histogram,
    tool_plot_ode_solution,
    tool_plot_scatter,
    tool_plot_stacked_bar,
    tool_plot_timeseries,
)
from mcp.types import ImageContent

# Try to import PIL to verify PNG validity
try:
    from PIL import Image as PILImage

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def is_valid_png(image_content):
    """Check if ImageContent contains valid PNG data."""
    assert isinstance(image_content, ImageContent)
    assert image_content.type == "image"
    assert image_content.mimeType == "image/png"
    
    # Decode base64 data
    image_data = base64.b64decode(image_content.data)
    
    if not PIL_AVAILABLE:
        # Fallback: check PNG header
        return image_data[:8] == b"\x89PNG\r\n\x1a\n"
    try:
        img = PILImage.open(BytesIO(image_data))
        return img.format == "PNG"
    except Exception:
        return False


class TestPlotTimeseries:
    def test_basic_single_series(self):
        result = tool_plot_timeseries(
            timestamps=["2026-01-01T10:00:00Z", "2026-01-01T11:00:00Z", "2026-01-01T12:00:00Z"],
            series={"response_time": [145, 167, 123]},
        )
        assert isinstance(result, ImageContent)
        assert result.type == "image"
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_multiple_series(self):
        result = tool_plot_timeseries(
            timestamps=["T1", "T2", "T3"],
            series={"cpu": [45.2, 67.1, 89.3], "memory": [60.1, 62.3, 64.5]},
            title="System Metrics",
            xlabel="Time",
            ylabel="Percentage",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_custom_figsize(self):
        result = tool_plot_timeseries(
            timestamps=["T1", "T2"],
            series={"metric": [100, 120]},
            figsize=(12, 8),
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_empty_timestamps(self):
        with pytest.raises(ValueError, match="timestamps list cannot be empty"):
            tool_plot_timeseries(timestamps=[], series={"metric": []})

    def test_empty_series(self):
        with pytest.raises(ValueError, match="series dictionary cannot be empty"):
            tool_plot_timeseries(timestamps=["T1"], series={})

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="has.*values but timestamps has"):
            tool_plot_timeseries(
                timestamps=["T1", "T2"],
                series={"metric": [100]},  # Wrong length
            )


class TestPlotBarChart:
    def test_basic_vertical(self):
        result = tool_plot_bar_chart(
            categories=["Endpoint A", "Endpoint B", "Endpoint C"],
            values=[1250, 890, 2100],
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_horizontal_bars(self):
        result = tool_plot_bar_chart(
            categories=["Error 400", "Error 404", "Error 500"],
            values=[45, 120, 12],
            horizontal=True,
            title="Error Distribution",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_custom_labels(self):
        result = tool_plot_bar_chart(
            categories=["A", "B"],
            values=[100, 200],
            xlabel="Type",
            ylabel="Count",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_empty_categories(self):
        with pytest.raises(ValueError, match="categories list cannot be empty"):
            tool_plot_bar_chart(categories=[], values=[])

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="categories has.*items but values has"):
            tool_plot_bar_chart(categories=["A", "B"], values=[100])


class TestPlotHistogram:
    def test_basic(self):
        result = tool_plot_histogram(
            data=[120, 145, 167, 123, 189, 145, 156, 178, 134, 198],
            bins=5,
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_with_title(self):
        result = tool_plot_histogram(
            data=[1.5, 2.3, 1.8, 2.9, 1.2, 3.1, 2.7],
            bins=10,
            title="Response Time Distribution",
            xlabel="Latency (ms)",
            ylabel="Frequency",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_custom_bins(self):
        result = tool_plot_histogram(data=[1, 2, 3, 4, 5], bins=3)
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_empty_data(self):
        with pytest.raises(ValueError, match="data list cannot be empty"):
            tool_plot_histogram(data=[])

    def test_invalid_bins(self):
        with pytest.raises(ValueError, match="bins must be positive"):
            tool_plot_histogram(data=[1, 2, 3], bins=0)


class TestPlotScatter:
    def test_basic(self):
        result = tool_plot_scatter(
            x_data=[10, 20, 30, 40, 50],
            y_data=[0.02, 0.05, 0.03, 0.08, 0.04],
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_with_labels(self):
        result = tool_plot_scatter(
            x_data=[50, 60, 70],
            y_data=[145, 120, 98],
            labels=["Server A", "Server B", "Server C"],
            title="Traffic vs Response Time",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_custom_axis_labels(self):
        result = tool_plot_scatter(
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
            xlabel="Cache Hit Rate",
            ylabel="Response Time",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_empty_data(self):
        with pytest.raises(ValueError, match="x_data and y_data cannot be empty"):
            tool_plot_scatter(x_data=[], y_data=[])

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError, match="x_data has.*values but y_data has"):
            tool_plot_scatter(x_data=[1, 2], y_data=[3])

    def test_mismatched_labels(self):
        with pytest.raises(ValueError, match="labels has.*values but data has.*points"):
            tool_plot_scatter(x_data=[1, 2], y_data=[3, 4], labels=["A"])


class TestPlotHeatmap:
    def test_basic(self):
        result = tool_plot_heatmap(
            data=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_with_labels(self):
        result = tool_plot_heatmap(
            data=[[10, 20], [30, 40]],
            x_labels=["Mon", "Tue"],
            y_labels=["Morning", "Evening"],
            title="Request Patterns",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_custom_colormap(self):
        result = tool_plot_heatmap(
            data=[[1, 2], [3, 4]],
            colormap="plasma",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_large_heatmap(self):
        # Test without text annotations
        data = [[i * j for j in range(25)] for i in range(25)]
        result = tool_plot_heatmap(data=data)
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_empty_data(self):
        with pytest.raises(ValueError, match="data cannot be empty"):
            tool_plot_heatmap(data=[])

    def test_mismatched_x_labels(self):
        with pytest.raises(ValueError, match="x_labels has.*items but data has.*columns"):
            tool_plot_heatmap(data=[[1, 2], [3, 4]], x_labels=["A"])

    def test_mismatched_y_labels(self):
        with pytest.raises(ValueError, match="y_labels has.*items but data has.*rows"):
            tool_plot_heatmap(data=[[1, 2], [3, 4]], y_labels=["A"])


class TestPlotStackedBar:
    def test_basic(self):
        result = tool_plot_stacked_bar(
            categories=["Jan", "Feb", "Mar"],
            series={"success": [100, 120, 110], "error": [10, 8, 12]},
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_horizontal(self):
        result = tool_plot_stacked_bar(
            categories=["Endpoint A", "Endpoint B"],
            series={"2xx": [1000, 800], "4xx": [50, 30], "5xx": [5, 2]},
            horizontal=True,
            title="Status Code Distribution",
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_multiple_series(self):
        result = tool_plot_stacked_bar(
            categories=["Week 1", "Week 2", "Week 3"],
            series={
                "deployed": [10, 15, 12],
                "failed": [2, 1, 3],
                "rolled_back": [1, 0, 1],
            },
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_empty_categories(self):
        with pytest.raises(ValueError, match="categories list cannot be empty"):
            tool_plot_stacked_bar(categories=[], series={"a": []})

    def test_empty_series(self):
        with pytest.raises(ValueError, match="series dictionary cannot be empty"):
            tool_plot_stacked_bar(categories=["A"], series={})

    def test_mismatched_series_length(self):
        with pytest.raises(ValueError, match="Series.*has.*values but categories has"):
            tool_plot_stacked_bar(
                categories=["A", "B"],
                series={"success": [100]},  # Wrong length
            )


class TestPlotOdeSolution:
    def test_basic(self):
        ode_result = json.dumps(
            {
                "t": [0.0, 1.0, 2.0, 3.0],
                "x": [1.0, 0.5, 0.25, 0.125],
                "success": True,
                "method": "rk45",
            }
        )
        result = tool_plot_ode_solution(ode_result=ode_result)
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_multiple_variables(self):
        ode_result = json.dumps(
            {
                "t": [0.0, 1.0, 2.0],
                "x": [1.0, 0.8, 0.6],
                "y": [0.0, 0.2, 0.4],
                "success": True,
                "method": "euler",
            }
        )
        result = tool_plot_ode_solution(ode_result=ode_result, title="Coupled System")
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_custom_title(self):
        ode_result = json.dumps(
            {
                "t": [0.0, 1.0],
                "x": [1.0, 0.9],
                "success": True,
            }
        )
        result = tool_plot_ode_solution(ode_result=ode_result, title="My ODE Solution")
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0

    def test_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            tool_plot_ode_solution(ode_result="not valid json")

    def test_missing_time(self):
        ode_result = json.dumps({"x": [1.0, 0.5]})
        with pytest.raises(ValueError, match="must contain 't'"):
            tool_plot_ode_solution(ode_result=ode_result)

    def test_empty_time(self):
        ode_result = json.dumps({"t": [], "x": []})
        with pytest.raises(ValueError, match="Time array 't' cannot be empty"):
            tool_plot_ode_solution(ode_result=ode_result)

    def test_no_variables(self):
        ode_result = json.dumps({"t": [0.0, 1.0], "success": True})
        with pytest.raises(ValueError, match="No solution variables found"):
            tool_plot_ode_solution(ode_result=ode_result)

    def test_mismatched_lengths(self):
        ode_result = json.dumps(
            {
                "t": [0.0, 1.0, 2.0],
                "x": [1.0, 0.5],  # Wrong length
            }
        )
        with pytest.raises(ValueError, match="has.*values but time has.*points"):
            tool_plot_ode_solution(ode_result=ode_result)


class TestIntegrationOdePlotting:
    """Test integration between solve_ode and plot_ode_solution."""

    def test_solve_and_plot_exponential_decay(self):
        from math_mcp.scipy_tools import tool_solve_ode

        # Solve ODE
        ode_result = tool_solve_ode(
            equations=["dx/dt = -x"],
            initial_conditions={"x": 1.0},
            time_span=[0.0, 5.0],
            method="rk45",
        )

        # Verify solution is valid JSON
        data = json.loads(ode_result)
        assert data["success"] is True

        # Convert to format expected by plot_ode_solution
        plot_data = {
            "t": data["time"],
            "x": data["state"]["x"],
            "success": data["success"],
            "method": data["method"],
        }

        # Plot the solution
        result = tool_plot_ode_solution(
            ode_result=json.dumps(plot_data), title="Exponential Decay"
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0
        assert is_valid_png(result)

    def test_solve_and_plot_coupled_system(self):
        from math_mcp.scipy_tools import tool_solve_ode

        # Solve coupled ODE system
        ode_result = tool_solve_ode(
            equations=["dx/dt = -x + y", "dy/dt = x - y"],
            initial_conditions={"x": 1.0, "y": 0.0},
            time_span=[0.0, 10.0],
            method="rk45",
        )

        data = json.loads(ode_result)
        assert data["success"] is True

        # Convert to plot format
        plot_data = {
            "t": data["time"],
            "x": data["state"]["x"],
            "y": data["state"]["y"],
            "success": data["success"],
            "method": data["method"],
        }

        # Plot
        result = tool_plot_ode_solution(
            ode_result=json.dumps(plot_data), title="Coupled System"
        )
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
        assert len(result.data) > 0


class TestMemoryManagement:
    """Test that plots don't leak memory."""

    def test_multiple_plots_no_memory_leak(self):
        # Create multiple plots to ensure we're cleaning up properly
        for i in range(10):
            result = tool_plot_bar_chart(
                categories=[f"Cat{j}" for j in range(5)],
                values=[j * 10 for j in range(5)],
            )
            assert isinstance(result, ImageContent)
            assert result.mimeType == "image/png"
            assert len(result.data) > 0

    def test_error_cleanup(self):
        # Ensure we clean up even on errors
        try:
            tool_plot_timeseries(timestamps=[], series={})
        except ValueError:
            pass  # Expected

        # Should be able to create plots after error
        result = tool_plot_bar_chart(categories=["A"], values=[1])
        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"
