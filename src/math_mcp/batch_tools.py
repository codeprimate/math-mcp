"""Batch tool: run multiple MCP tool invocations in one request with parallel execution."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Annotated, Any, Sequence

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from math_mcp import plot_output

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 64


class CallSpec(BaseModel):
    """Single tool call specification for batch_tools."""

    name: str = Field(description="MCP tool name to invoke (e.g. 'simplify', 'evaluate').")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool arguments as a JSON object. Omit or {} for no arguments.",
    )


def _serialize_content(
    content: Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource],
) -> list[dict[str, Any]]:
    """Turn MCP content items into a JSON-serializable list of dicts."""
    out: list[dict[str, Any]] = []
    for item in content:
        if isinstance(item, types.TextContent):
            out.append({"type": "text", "text": item.text})
        elif isinstance(item, types.ImageContent):
            obj: dict[str, Any] = {"type": "image", "mimeType": item.mimeType or "image/png"}
            if getattr(item, "data", None):
                obj["data"] = item.data
            if getattr(item, "url", None):
                obj["url"] = item.url
            out.append(obj)
        else:
            # EmbeddedResource or unknown: best-effort
            out.append({"type": getattr(item, "type", "unknown"), "text": str(item)})
    return out


async def _run_one_tool(
    app: FastMCP,
    name: str,
    arguments: dict[str, Any],
) -> tuple[list[types.TextContent | types.ImageContent], bool]:
    """Execute one tool and optionally apply plot URL post-processing.

    Returns:
        (content_list, is_error)
    """
    try:
        tool_result = await app.call_tool(name, arguments or {})
        raw = (
            list(tool_result)
            if isinstance(tool_result, (list, tuple))
            else [tool_result]
        )
        content: list[types.TextContent | types.ImageContent] = []
        for item in raw:
            if isinstance(item, types.TextContent):
                content.append(item)
            elif isinstance(item, types.ImageContent):
                content.append(item)
            else:
                content.append(types.TextContent(type="text", text=str(item)))

        if name in plot_output.PLOT_TOOL_NAMES:
            try:
                url = plot_output.maybe_save_plot_output(
                    content, app.get_context()
                )
                if url:
                    content.append(
                        types.TextContent(
                            type="text",
                            text=f"Chart available at: {url}",
                        )
                    )
            except Exception as exc:
                logger.warning(
                    "Failed to save plot output for %s: %s", name, exc, exc_info=True
                )

        return (content, False)
    except Exception as exc:
        return (
            [types.TextContent(type="text", text=str(exc))],
            True,
        )


def _max_concurrent() -> int:
    """Concurrency limit: cpu_count - 1, at least 1."""
    n = os.cpu_count() or 1
    return max(1, n - 1)


def create_batch_tool(app: FastMCP):
    """Create the batch_tools handler that uses the given FastMCP app."""

    async def tool_batch_tools(
        calls: Annotated[
            list[dict[str, Any]],
            Field(
                description="List of tool calls. Each item: {'name': str (required), 'arguments': dict (optional, default {}).}"
            ),
        ] = None,
    ) -> str:
        """Run multiple tools in one request; results are in the same order as the calls.

        Tools run in parallel with concurrency limited by CPU count minus one.
        Plot tools get the same URL behavior as when called singly.
        """
        # Normalize to CallSpec for validation
        if calls is None:
            calls = []
        if not isinstance(calls, list):
            return json.dumps(
                [
                    {
                        "name": "",
                        "isError": True,
                        "content": [{"type": "text", "text": "calls must be a list"}],
                    }
                ]
            )
        if len(calls) > MAX_BATCH_SIZE:
            return json.dumps(
                [
                    {
                        "name": "",
                        "isError": True,
                        "content": [
                            {
                                "type": "text",
                                "text": f"At most {MAX_BATCH_SIZE} calls allowed; got {len(calls)}",
                            }
                        ],
                    }
                ]
            )

        specs: list[CallSpec] = []
        for c in calls:
            if isinstance(c, dict):
                try:
                    specs.append(CallSpec(**c))
                except Exception as e:
                    return json.dumps(
                        [
                            {
                                "name": c.get("name", ""),
                                "isError": True,
                                "content": [{"type": "text", "text": str(e)}],
                            }
                        ]
                    )
            else:
                specs.append(c)

        if not specs:
            return json.dumps([])

        semaphore = asyncio.Semaphore(_max_concurrent())

        async def run_with_semaphore(spec: CallSpec):
            async with semaphore:
                content_list, is_error = await _run_one_tool(
                    app, spec.name, spec.arguments
                )
                return {
                    "name": spec.name,
                    "isError": is_error,
                    "content": _serialize_content(content_list),
                }

        results = await asyncio.gather(
            *[run_with_semaphore(s) for s in specs],
            return_exceptions=False,
        )
        return json.dumps(results)

    return tool_batch_tools


def register_batch_tools(mcp_app: FastMCP) -> None:
    """Register the batch_tools tool on the given FastMCP instance."""
    handler = create_batch_tool(mcp_app)
    mcp_app.tool(
        name="batch_tools",
        description=(
            "Run multiple tools in one request. Pass a list of objects with 'name' (tool name) "
            "and optional 'arguments' (dict). Results are returned in the same order. "
            f"At most {MAX_BATCH_SIZE} calls per request. "
            "Execution is parallel with concurrency limited by CPU count minus one."
        ),
    )(handler)
