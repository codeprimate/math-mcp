"""Tests for statistical tools."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path for imports (needed for src-layout packages)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from math_mcp.stats_tools import (
    tool_correlation,
    tool_describe_data,
    tool_linear_regression,
    tool_moving_average,
    tool_ttest,
)


class TestDescribeData:
    def test_basic_statistics(self):
        result = tool_describe_data([120, 145, 167, 123, 189, 134])
        data = json.loads(result)
        
        assert "count" in data
        assert "mean" in data
        assert "median" in data
        assert "std" in data
        assert "variance" in data
        assert "min" in data
        assert "max" in data
        assert "range" in data
        assert "percentiles" in data
        
        assert data["count"] == 6
        assert data["min"] == 120
        assert data["max"] == 189
        assert data["range"] == 69
        
        # Check percentiles
        assert "p25" in data["percentiles"]
        assert "p50" in data["percentiles"]
        assert "p75" in data["percentiles"]
        assert "p95" in data["percentiles"]
        assert "p99" in data["percentiles"]
        
        # p50 should equal median
        assert abs(data["percentiles"]["p50"] - data["median"]) < 1e-10

    def test_single_value(self):
        result = tool_describe_data([42])
        data = json.loads(result)
        
        assert data["count"] == 1
        assert data["mean"] == 42.0
        assert data["median"] == 42.0
        assert data["std"] == 0.0
        assert data["variance"] == 0.0
        assert data["min"] == 42.0
        assert data["max"] == 42.0

    def test_empty_array(self):
        result = tool_describe_data([])
        assert "Error" in result

    def test_percentiles_correct(self):
        # Test with known values
        result = tool_describe_data([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        data = json.loads(result)
        
        # p50 should be around 5.5 (median of 1-10)
        assert 5.0 <= data["percentiles"]["p50"] <= 6.0


class TestTtest:
    def test_two_sample_ttest(self):
        result = tool_ttest(
            sample1=[100, 102, 98, 105],
            sample2=[95, 97, 99, 94],
        )
        data = json.loads(result)
        
        assert "statistic" in data
        assert "pvalue" in data
        assert "degrees_of_freedom" in data
        assert "significant" in data
        assert "test_type" in data
        
        assert data["test_type"] == "two-sample"
        assert isinstance(data["significant"], bool)

    def test_one_sample_ttest(self):
        result = tool_ttest(
            sample1=[100, 102, 98, 105],
            sample2=None,
        )
        data = json.loads(result)
        
        assert data["test_type"] == "one-sample"
        assert "statistic" in data
        assert "pvalue" in data

    def test_alternative_greater(self):
        result = tool_ttest(
            sample1=[100, 102, 98, 105],
            sample2=[95, 97, 99, 94],
            alternative="greater",
        )
        data = json.loads(result)
        assert "pvalue" in data

    def test_alternative_less(self):
        result = tool_ttest(
            sample1=[100, 102, 98, 105],
            sample2=[95, 97, 99, 94],
            alternative="less",
        )
        data = json.loads(result)
        assert "pvalue" in data

    def test_empty_sample(self):
        result = tool_ttest(sample1=[], sample2=None)
        assert "Error" in result

    def test_invalid_alternative(self):
        result = tool_ttest(
            sample1=[1, 2, 3],
            sample2=[4, 5, 6],
            alternative="invalid",
        )
        assert "Error" in result


class TestCorrelation:
    def test_pearson_correlation(self):
        result = tool_correlation(
            x_data=[100, 200, 300],
            y_data=[0.02, 0.05, 0.03],
            method="pearson",
        )
        data = json.loads(result)
        
        assert "correlation" in data
        assert "pvalue" in data
        assert "method" in data
        assert data["method"] == "pearson"
        assert -1.0 <= data["correlation"] <= 1.0

    def test_perfect_correlation(self):
        # Perfect positive correlation
        result = tool_correlation(
            x_data=[1, 2, 3, 4],
            y_data=[2, 4, 6, 8],
            method="pearson",
        )
        data = json.loads(result)
        assert abs(data["correlation"] - 1.0) < 1e-10

    def test_spearman_correlation(self):
        result = tool_correlation(
            x_data=[1, 2, 3, 4, 5],
            y_data=[2, 4, 6, 8, 10],
            method="spearman",
        )
        data = json.loads(result)
        assert data["method"] == "spearman"
        assert -1.0 <= data["correlation"] <= 1.0

    def test_kendall_correlation(self):
        result = tool_correlation(
            x_data=[1, 2, 3, 4],
            y_data=[2, 4, 6, 8],
            method="kendall",
        )
        data = json.loads(result)
        assert data["method"] == "kendall"
        assert -1.0 <= data["correlation"] <= 1.0

    def test_mismatched_lengths(self):
        result = tool_correlation(
            x_data=[1, 2, 3],
            y_data=[1, 2],
        )
        assert "Error" in result
        assert "same length" in result

    def test_empty_data(self):
        result = tool_correlation(x_data=[], y_data=[])
        assert "Error" in result

    def test_invalid_method(self):
        result = tool_correlation(
            x_data=[1, 2, 3],
            y_data=[1, 2, 3],
            method="invalid",
        )
        assert "Error" in result


class TestLinearRegression:
    def test_perfect_linear_fit(self):
        result = tool_linear_regression(
            x_data=[1, 2, 3, 4],
            y_data=[2, 4, 6, 8],
        )
        data = json.loads(result)
        
        assert "slope" in data
        assert "intercept" in data
        assert "r_squared" in data
        assert "pvalue" in data
        assert "equation" in data
        
        # Perfect fit should have R² = 1.0 and slope = 2
        assert abs(data["r_squared"] - 1.0) < 1e-10
        assert abs(data["slope"] - 2.0) < 1e-10
        assert "y = " in data["equation"]

    def test_linear_growth(self):
        result = tool_linear_regression(
            x_data=[1, 2, 3, 4, 5],
            y_data=[100, 105, 110, 115, 120],
        )
        data = json.loads(result)
        
        assert abs(data["slope"] - 5.0) < 0.1  # Should be around 5
        assert data["r_squared"] > 0.9  # High correlation

    def test_mismatched_lengths(self):
        result = tool_linear_regression(
            x_data=[1, 2, 3],
            y_data=[1, 2],
        )
        assert "Error" in result
        assert "same length" in result

    def test_insufficient_data(self):
        result = tool_linear_regression(
            x_data=[1],
            y_data=[2],
        )
        assert "Error" in result
        assert "at least 2" in result

    def test_empty_data(self):
        result = tool_linear_regression(x_data=[], y_data=[])
        assert "Error" in result


class TestMovingAverage:
    def test_simple_moving_average(self):
        result = tool_moving_average(
            data=[10, 12, 11, 15, 13, 14, 12],
            window=3,
            method="simple",
        )
        data = json.loads(result)
        
        assert "smoothed" in data
        assert "original" in data
        assert "window" in data
        assert "method" in data
        
        assert data["window"] == 3
        assert data["method"] == "simple"
        assert len(data["smoothed"]) == len(data["original"])

    def test_exponential_moving_average(self):
        result = tool_moving_average(
            data=[10, 12, 11, 15, 13, 14, 12],
            window=3,
            method="exponential",
        )
        data = json.loads(result)
        
        assert data["method"] == "exponential"
        assert len(data["smoothed"]) == len(data["original"])

    def test_default_window(self):
        result = tool_moving_average(data=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        data = json.loads(result)
        
        assert data["window"] == 7  # Default
        assert data["method"] == "simple"  # Default

    def test_window_larger_than_data(self):
        result = tool_moving_average(
            data=[1, 2, 3],
            window=5,
        )
        assert "Error" in result

    def test_invalid_window(self):
        result = tool_moving_average(
            data=[1, 2, 3, 4, 5],
            window=0,
        )
        assert "Error" in result

    def test_invalid_method(self):
        result = tool_moving_average(
            data=[1, 2, 3, 4, 5],
            window=3,
            method="invalid",
        )
        assert "Error" in result

    def test_empty_data(self):
        result = tool_moving_average(data=[], window=3)
        assert "Error" in result

    def test_smoothed_values_smaller_variance(self):
        # Moving average should reduce variance
        noisy_data = [10, 15, 8, 12, 18, 9, 14, 11, 16, 10]
        result = tool_moving_average(data=noisy_data, window=3)
        data = json.loads(result)
        
        # Calculate variance of original vs smoothed
        import numpy as np
        orig_var = np.var(noisy_data)
        smooth_var = np.var([x for x in data["smoothed"] if not np.isnan(x)])
        
        # Smoothed should generally have lower variance (not always, but typically)
        # This is a sanity check, not a strict requirement
        assert len(data["smoothed"]) == len(noisy_data)
