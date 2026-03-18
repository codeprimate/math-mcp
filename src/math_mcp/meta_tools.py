"""Meta-tools for discovery and dispatch: math_ls, math_man, math; list_tools shows only these plus math_batch."""

from __future__ import annotations

import json
from typing import Annotated, Any

from mcp.types import ImageContent, TextContent
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from math_mcp import plot_output

# Single source of truth: category id -> ordered list of internal tool names (26 tools, 7 categories).
CATALOG: dict[str, list[str]] = {
    "algebra": ["simplify", "solve", "factor", "expand"],
    "calculus": ["derivative", "integral"],
    "numbers": ["evaluate", "to_fraction", "convert_unit", "find_root"],
    "stats": ["describe_data", "ttest", "correlation", "linear_regression", "moving_average"],
    "ode": ["solve_ode", "plot_ode_solution"],
    "charts": [
        "plot_timeseries",
        "plot_bar",
        "plot_histogram",
        "plot_scatter",
        "plot_heatmap",
        "plot_stacked_bar",
        "plot_stackplot",
        "plot_pie",
    ],
    "output": ["latex"],
}

# One-line intent phrase per tool (for math_ls flat listing).
TOOL_INTENTS: dict[str, str] = {
    "simplify": "Simplify or reduce a symbolic expression.",
    "solve": "Solve an equation for a variable; all exact solutions.",
    "factor": "Factor a polynomial or expression.",
    "expand": "Expand an expression into a sum or product form.",
    "derivative": "Compute the derivative of an expression with respect to a variable.",
    "integral": "Compute the definite or indefinite integral of an expression.",
    "evaluate": "Evaluate a numeric or symbolic expression, optionally with substitutions.",
    "to_fraction": "Convert a decimal or value to an exact fraction.",
    "convert_unit": "Convert a numeric value from one unit to another.",
    "find_root": "Find a root of a function in an interval or via Newton's method.",
    "describe_data": "Compute comprehensive descriptive statistics for a dataset.",
    "ttest": "Compare means; A/B testing and before/after analysis.",
    "correlation": "Compute Pearson, Spearman, or Kendall correlation between two samples.",
    "linear_regression": "Fit a linear regression and return slope, intercept, and R².",
    "moving_average": "Compute simple or exponential moving average over a series.",
    "solve_ode": "Solve an ODE system numerically with given initial conditions.",
    "plot_ode_solution": "Plot solution curves of an ODE system over time.",
    "plot_timeseries": "Line chart of one or more series over time or sequence.",
    "plot_bar": "Bar chart for categorical or grouped data.",
    "plot_histogram": "Histogram of a single dataset with configurable bins.",
    "plot_scatter": "Scatter plot of two variables with optional grouping.",
    "plot_heatmap": "Heatmap of a 2D matrix or grid of values.",
    "plot_stacked_bar": "Stacked bar chart for composition over categories.",
    "plot_stackplot": "Stacked area chart over a common x-axis.",
    "plot_pie": "Pie chart for proportions of a single variable.",
    "latex": "Render an expression as LaTeX string.",
}

# Names that list_tools should expose (all other tools are hidden).
META_TOOL_NAMES = frozenset({"math_ls", "math_man", "math", "math_batch"})


def _all_internal_tool_names() -> set[str]:
    """Set of all internal tool names from CATALOG (for validation)."""
    out: set[str] = set()
    for names in CATALOG.values():
        out.update(names)
    return out


def _tool_descriptor(app: FastMCP, name: str) -> dict[str, Any] | None:
    """Build {name, description, inputSchema} from app._tool_manager.get_tool(name). Returns None if unknown."""
    t = app._tool_manager.get_tool(name)
    if t is None:
        return None
    return {
        "name": t.name,
        "description": t.description or "",
        "inputSchema": t.parameters if isinstance(t.parameters, dict) else {},
    }


def _math_ls_no_args() -> dict[str, Any]:
    """Build math_ls() response: hint, categories, tools (name + intent)."""
    categories = [{"id": cid, "tools": list(tools)} for cid, tools in CATALOG.items()]
    tools_flat = [
        {"name": name, "intent": TOOL_INTENTS.get(name, "")}
        for names in CATALOG.values()
        for name in names
    ]
    return {
        "hint": (
            "Match a tool from 'tools' to your task. For one tool's parameters use math_man(name). "
            "For all tools in a category use math_ls(category). Then call math(name, arguments) to run."
        ),
        "categories": categories,
        "tools": tools_flat,
    }


def _math_ls_category(app: FastMCP, category: str) -> dict[str, Any]:
    """Build math_ls(category) response: hint, category, tools (full descriptors). Unknown category -> error."""
    if category not in CATALOG:
        return {
            "error": f"Unknown category: {category}",
            "available": list(CATALOG.keys()),
        }
    tools = []
    for name in CATALOG[category]:
        desc = _tool_descriptor(app, name)
        if desc is not None:
            tools.append(desc)
    return {
        "hint": "Call math(name, arguments) to run any tool listed above.",
        "category": category,
        "tools": tools,
    }


def register_meta_tools(mcp_app: FastMCP, app: FastMCP) -> None:
    """Register math_ls, math_man, math (and rely on math_batch already registered). Call after all other tools."""

    def tool_math_ls(
        category: Annotated[
            str | None,
            Field(description="Optional category id. If omitted, returns all categories and a flat list of tools with name and intent."),
        ] = None,
    ) -> str:
        """List available math tools. No args: categories + flat list (name, intent). With category: full descriptors for that category."""
        if category is None or category == "":
            out = _math_ls_no_args()
        else:
            out = _math_ls_category(app, category)
        return json.dumps(out)

    def tool_math_man(
        tool: Annotated[str, Field(description="Name of the math tool to describe.")],
    ) -> str:
        """Return full descriptor (name, description, inputSchema) for a named math tool."""
        if tool in META_TOOL_NAMES or tool not in _all_internal_tool_names():
            return json.dumps({
                "error": f"Unknown tool: {tool}. Call math_ls() to browse available tools.",
            })
        desc = _tool_descriptor(app, tool)
        if desc is None:
            return json.dumps({
                "error": f"Unknown tool: {tool}. Call math_ls() to browse available tools.",
            })
        return json.dumps(desc)

    async def tool_math(
        tool: Annotated[str, Field(description="Name of the math tool to run.")],
        arguments: Annotated[
            dict[str, Any] | None,
            Field(description="Arguments for the tool as a JSON object. Omit or {} for no arguments."),
        ] = None,
    ) -> str | list[TextContent | ImageContent]:
        """Execute a math tool by name. Use math_ls() first to discover tools, math_man(name) for parameters."""
        args = arguments if isinstance(arguments, dict) else {}
        internal = _all_internal_tool_names()
        if tool not in internal:
            return json.dumps({
                "error": f"Unknown tool: {tool}. Call math_ls() to browse available tools.",
            })
        result = await app.call_tool(tool, args)
        # call_tool returns (content_list, metadata) tuple
        if isinstance(result, (list, tuple)) and len(result) >= 1:
            content = list(result[0]) if isinstance(result[0], (list, tuple)) else [result[0]]
        else:
            content = [result] if not isinstance(result, (list, tuple)) else list(result)
        # Normalize to list of TextContent | ImageContent
        normalized: list[TextContent | ImageContent] = []
        for item in content:
            if isinstance(item, TextContent):
                normalized.append(item)
            elif isinstance(item, ImageContent):
                normalized.append(item)
            else:
                normalized.append(TextContent(type="text", text=str(item)))
        if tool in plot_output.PLOT_TOOL_NAMES:
            try:
                url = plot_output.maybe_save_plot_output(normalized, app.get_context())
                if url:
                    url_text = TextContent(
                        type="text", text=f"Chart available at: {url}"
                    )
                    # Some MCP clients (e.g. Cursor) fail on image/svg+xml with
                    # "Mime type application/xml does not support decoding",
                    # which aborts the whole result. Return only the URL for SVG
                    # so the agent always gets the link; they can open it to view.
                    has_svg = any(
                        getattr(c, "mimeType", "") == "image/svg+xml"
                        for c in normalized
                        if isinstance(c, ImageContent)
                    )
                    if has_svg:
                        return url_text.text
                    normalized.insert(0, url_text)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "Failed to save plot output for %s: %s", tool, exc, exc_info=True
                )
        # Return content list so MCP can serialize (image + text). If single text, caller may expect str.
        if len(normalized) == 1 and isinstance(normalized[0], TextContent):
            return normalized[0].text
        return normalized

    mcp_app.tool(
        name="math_ls",
        description=(
            "List available math tools. Call with no args to get categories and a flat list of all tools (name, intent). "
            "Then: use math_man(name) for one tool's parameters, or math_ls(category) for full descriptors (name, description, inputSchema) "
            "for every tool in that category. Finally call math(name, arguments) to run."
        ),
    )(tool_math_ls)

    mcp_app.tool(
        name="math_man",
        description=(
            "Return the full descriptor (name, description, inputSchema) for a named math tool. "
            "Use after math_ls() to get parameters for a chosen tool, then call math(name, arguments) to run."
        ),
    )(tool_math_man)

    mcp_app.tool(
        name="math",
        description=(
            "Execute a math tool by name. Discovery: call math_ls() first to get tool names and intents; "
            "get parameters via math_man(name) or math_ls(category); then call math(name, arguments) with the chosen tool name and its arguments."
        ),
    )(tool_math)


def _override_list_tools_handler(app: FastMCP) -> None:
    """Override list_tools so only meta-tools (math_ls, math_man, math, math_batch) are returned.
    Internal tools remain registered and callable via app.call_tool.
    """
    import mcp.types as types

    original_handler = app._mcp_server.request_handlers.get(types.ListToolsRequest)
    if original_handler is None:
        return

    async def filtered_handler(req: types.ListToolsRequest):
        result = await original_handler(req)
        filtered_tools = [t for t in result.root.tools if t.name in META_TOOL_NAMES]
        updated = result.root.model_copy(update={"tools": filtered_tools})
        return result.model_copy(update={"root": updated})

    app._mcp_server.request_handlers[types.ListToolsRequest] = filtered_handler
