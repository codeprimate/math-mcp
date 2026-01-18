"""Statistical analysis tools using scipy.stats."""

import json
from typing import Annotated

import numpy as np
from pydantic import Field
from scipy import stats
from scipy.stats import linregress


# Tool function implementations (exported for testing)
def tool_describe_data(
        data: Annotated[list[float], Field(description="Array of numeric values to analyze. Examples: [120, 145, 167, 123, 189, 134] for response times, [10.5, 12.3, 11.8, 13.1] for query performance.")],
    ) -> str:
        """Compute comprehensive descriptive statistics for a dataset.
        
        Essential for analyzing API response times, database query performance, user session lengths, and any numeric metric. Provides summary statistics including percentiles critical for SLAs (p95, p99).
        
        Use this when:
        - Analyzing performance metrics (response times, query durations)
        - Understanding data distributions
        - Calculating percentiles for SLAs
        - Getting quick summaries of numeric datasets
        - Analyzing user behavior metrics (session lengths, engagement)
        
        Examples:
        - data=[120, 145, 167, 123, 189, 134] → Statistics summary with mean, median, std, percentiles
        - data=[10.5, 12.3, 11.8, 13.1, 9.9] → Descriptive statistics for query performance
        """
        try:
            if not data:
                return "Error: Data array cannot be empty"
            
            if len(data) < 1:
                return "Error: Data array must contain at least one value"
            
            arr = np.array(data, dtype=float)
            
            # Basic statistics
            count = len(arr)
            mean = float(np.mean(arr))
            median = float(np.median(arr))
            if count < 2:
                std = 0.0
                variance = 0.0
            else:
                std = float(np.std(arr, ddof=1))  # Sample standard deviation
                variance = float(np.var(arr, ddof=1))  # Sample variance
            min_val = float(np.min(arr))
            max_val = float(np.max(arr))
            range_val = max_val - min_val
            
            # Percentiles
            percentiles = {
                "p25": float(np.percentile(arr, 25)),
                "p50": float(np.percentile(arr, 50)),  # Same as median
                "p75": float(np.percentile(arr, 75)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
            }
            
            result = {
                "count": count,
                "mean": mean,
                "median": median,
                "std": std,
                "variance": variance,
                "min": min_val,
                "max": max_val,
                "range": range_val,
                "percentiles": percentiles,
            }
            
            return json.dumps(result)
        except Exception as e:
            return f"Error: {str(e)}"


def tool_ttest(
        sample1: Annotated[list[float], Field(description="First sample data. For one-sample test, this is the only sample. For two-sample test, this is the first group. Examples: [100, 102, 98, 105] for response times, [0.45, 0.52, 0.48, 0.51] for conversion rates.")],
        sample2: Annotated[list[float] | None, Field(description="Optional second sample for two-sample t-test. If not provided, performs one-sample t-test (tests if sample1 mean differs from 0). Example: [95, 97, 99, 94] for comparison group.")] = None,
        alternative: Annotated[str, Field(description="Alternative hypothesis. Options: 'two-sided' (default, mean differs), 'greater' (mean is greater), 'less' (mean is less).")] = "two-sided",
    ) -> str:
        """Perform t-test for comparing means (one-sample, two-sample, or paired).
        
        Essential for A/B testing, comparing performance before/after deployments, and determining if differences are statistically significant or just random variance.
        
        Use this when:
        - A/B testing (comparing conversion rates, click-through rates)
        - Before/after deployment comparisons
        - Feature flag impact analysis
        - Determining if performance changes are significant
        - Testing if a sample mean differs from a value
        
        Examples:
        - sample1=[100, 102, 98, 105], sample2=[95, 97, 99, 94] → Two-sample t-test comparing groups
        - sample1=[100, 102, 98, 105], sample2=None → One-sample t-test (tests if mean differs from 0)
        - sample1=[0.45, 0.52, 0.48], sample2=[0.38, 0.41, 0.39] → A/B test comparison
        """
        try:
            if not sample1:
                return "Error: sample1 cannot be empty"
            
            arr1 = np.array(sample1, dtype=float)
            
            # Map alternative to scipy format
            alt_map = {
                "two-sided": "two-sided",
                "greater": "greater",
                "less": "less",
            }
            if alternative not in alt_map:
                return f"Error: alternative must be one of: {list(alt_map.keys())}"
            
            scipy_alternative = alt_map[alternative]
            
            if sample2 is None:
                # One-sample t-test (test if mean differs from 0)
                result = stats.ttest_1samp(arr1, popmean=0.0, alternative=scipy_alternative)
                statistic = float(result.statistic)
                pvalue = float(result.pvalue)
                degrees_of_freedom = len(arr1) - 1
            else:
                # Two-sample t-test
                if not sample2:
                    return "Error: sample2 cannot be empty"
                
                arr2 = np.array(sample2, dtype=float)
                result = stats.ttest_ind(arr1, arr2, alternative=scipy_alternative)
                statistic = float(result.statistic)
                pvalue = float(result.pvalue)
                degrees_of_freedom = len(arr1) + len(arr2) - 2
            
            # Determine significance at α=0.05
            significant = pvalue < 0.05
            
            return json.dumps({
                "statistic": statistic,
                "pvalue": pvalue,
                "degrees_of_freedom": degrees_of_freedom,
                "significant": significant,
                "test_type": "one-sample" if sample2 is None else "two-sample",
            })
        except Exception as e:
            return f"Error: {str(e)}"


def tool_correlation(
        x_data: Annotated[list[float], Field(description="First variable values. Examples: [100, 200, 300] for traffic volume, [0.85, 0.92, 0.78] for cache hit rates.")],
        y_data: Annotated[list[float], Field(description="Second variable values. Must have same length as x_data. Examples: [0.02, 0.05, 0.03] for error rates, [120, 145, 167] for response times.")],
        method: Annotated[str, Field(description="Correlation method. Options: 'pearson' (default, linear correlation), 'spearman' (rank-based, monotonic relationships), 'kendall' (rank-based, robust to outliers).")] = "pearson",
    ) -> str:
        """Calculate correlation coefficient between two variables.
        
        Essential for understanding relationships between metrics, identifying factors that impact performance, and discovering dependencies in system behavior.
        
        Use this when:
        - Analyzing relationships between metrics (traffic vs errors)
        - Understanding if cache hit rate correlates with response time
        - Finding factors that impact user engagement
        - Discovering dependencies between system metrics
        - Identifying correlated performance indicators
        
        Examples:
        - x_data=[100, 200, 300], y_data=[0.02, 0.05, 0.03] → Pearson correlation between traffic and error rate
        - x_data=[0.85, 0.92, 0.78], y_data=[120, 145, 167] → Correlation between cache hit rate and response time
        """
        try:
            if not x_data or not y_data:
                return "Error: Both x_data and y_data must be non-empty"
            
            if len(x_data) != len(y_data):
                return f"Error: x_data and y_data must have the same length. Got {len(x_data)} and {len(y_data)}"
            
            arr_x = np.array(x_data, dtype=float)
            arr_y = np.array(y_data, dtype=float)
            
            # Map method to scipy function
            method_map = {
                "pearson": lambda x, y: stats.pearsonr(x, y),
                "spearman": lambda x, y: stats.spearmanr(x, y),
                "kendall": lambda x, y: stats.kendalltau(x, y),
            }
            
            if method not in method_map:
                return f"Error: method must be one of: {list(method_map.keys())}"
            
            result = method_map[method](arr_x, arr_y)
            
            # Handle different return types
            if method == "kendall":
                correlation = float(result.correlation)
                pvalue = float(result.pvalue)
            else:
                correlation = float(result.statistic)
                pvalue = float(result.pvalue)
            
            return json.dumps({
                "correlation": correlation,
                "pvalue": pvalue,
                "method": method,
            })
        except Exception as e:
            return f"Error: {str(e)}"


def tool_linear_regression(
        x_data: Annotated[list[float], Field(description="Independent variable values. Examples: [1, 2, 3, 4] for time periods, [100, 200, 300] for traffic volume.")],
        y_data: Annotated[list[float], Field(description="Dependent variable values. Must have same length as x_data. Examples: [2, 4, 6, 8] for linear growth, [120, 145, 167] for response times over time.")],
    ) -> str:
        """Fit a linear regression model and return coefficients, R², and predictions.
        
        Essential for capacity planning, trend analysis, growth forecasting, and understanding how one variable changes with another.
        
        Use this when:
        - Capacity planning (when will we hit database limits?)
        - Trend analysis (is performance degrading over time?)
        - Growth forecasting (predicting user growth, revenue)
        - Understanding linear relationships between variables
        - Predicting future values based on trends
        
        Examples:
        - x_data=[1, 2, 3, 4], y_data=[2, 4, 6, 8] → Perfect linear fit (R²=1.0, slope=2)
        - x_data=[1, 2, 3, 4, 5], y_data=[100, 105, 110, 115, 120] → Linear growth trend
        """
        try:
            if not x_data or not y_data:
                return "Error: Both x_data and y_data must be non-empty"
            
            if len(x_data) != len(y_data):
                return f"Error: x_data and y_data must have the same length. Got {len(x_data)} and {len(y_data)}"
            
            if len(x_data) < 2:
                return "Error: Need at least 2 data points for regression"
            
            arr_x = np.array(x_data, dtype=float)
            arr_y = np.array(y_data, dtype=float)
            
            # Perform linear regression
            result = linregress(arr_x, arr_y)
            
            slope = float(result.slope)
            intercept = float(result.intercept)
            r_squared = float(result.rvalue ** 2)
            pvalue = float(result.pvalue)
            
            # Format equation string
            if intercept >= 0:
                equation = f"y = {slope:.6f}*x + {intercept:.6f}"
            else:
                equation = f"y = {slope:.6f}*x - {abs(intercept):.6f}"
            
            return json.dumps({
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "pvalue": pvalue,
                "equation": equation,
            })
        except Exception as e:
            return f"Error: {str(e)}"


def tool_moving_average(
        data: Annotated[list[float], Field(description="Time series data values. Examples: [10, 12, 11, 15, 13, 14, 12] for daily error rates, [120, 145, 167, 123, 189] for response times over time.")],
        window: Annotated[int, Field(description="Number of periods for moving average window. Default: 7. Examples: 3 for 3-period average, 7 for weekly average, 30 for monthly average.")] = 7,
        method: Annotated[str, Field(description="Moving average method. Options: 'simple' (default, equal weights), 'exponential' (exponentially weighted, more weight to recent values).")] = "simple",
    ) -> str:
        """Calculate moving average to smooth time series data.
        
        Essential for filtering noise from metrics, identifying actual trends vs random fluctuations, and creating cleaner visualizations for monitoring dashboards.
        
        Use this when:
        - Smoothing error rates to see actual trends
        - Filtering noise from response time metrics
        - Creating cleaner dashboards and alerts
        - Identifying sustained changes vs one-off spikes
        - Analyzing time series trends
        
        Examples:
        - data=[10, 12, 11, 15, 13, 14, 12], window=3 → 3-period moving average
        - data=[0.02, 0.05, 0.03, 0.04, 0.06], window=3, method='exponential' → Exponentially weighted average
        """
        try:
            if not data:
                return "Error: Data array cannot be empty"
            
            if window < 1:
                return "Error: window must be at least 1"
            
            if window > len(data):
                return f"Error: window ({window}) cannot be larger than data length ({len(data)})"
            
            arr = np.array(data, dtype=float)
            
            if method == "simple":
                # Simple moving average using convolution
                weights = np.ones(window) / window
                smoothed = np.convolve(arr, weights, mode='valid')
                # Pad the beginning to match original length
                # Use the first smoothed value for padding, or first data value if smoothed is empty
                if len(smoothed) < len(arr):
                    if len(smoothed) > 0:
                        padding_value = smoothed[0]
                    else:
                        padding_value = arr[0]
                    padding = [padding_value] * (len(arr) - len(smoothed))
                    smoothed = np.concatenate([padding, smoothed])
            elif method == "exponential":
                # Exponentially weighted moving average
                # Using pandas-like approach with alpha = 2/(window+1)
                alpha = 2.0 / (window + 1.0)
                smoothed = np.zeros_like(arr)
                smoothed[0] = arr[0]
                for i in range(1, len(arr)):
                    smoothed[i] = alpha * arr[i] + (1 - alpha) * smoothed[i-1]
            else:
                return f"Error: method must be 'simple' or 'exponential', got '{method}'"
            
            return json.dumps({
                "smoothed": [float(x) for x in smoothed],
                "original": [float(x) for x in arr],
                "window": window,
                "method": method,
            })
        except Exception as e:
            return f"Error: {str(e)}"


def register_stats_tools(mcp):
    """Register statistical analysis tools with the MCP server."""
    mcp.tool(name="describe_data")(tool_describe_data)
    mcp.tool(name="ttest")(tool_ttest)
    mcp.tool(name="correlation")(tool_correlation)
    mcp.tool(name="linear_regression")(tool_linear_regression)
    mcp.tool(name="moving_average")(tool_moving_average)
