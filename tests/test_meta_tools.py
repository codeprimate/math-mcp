"""Tests for meta-tools: math_ls, math_man, math; list_tools returns only 4 tools."""

import asyncio
import json
import sys
from pathlib import Path

import mcp.types as types

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from math_mcp.meta_tools import CATALOG, META_TOOL_NAMES
from math_mcp.server import mcp


def _run(coro):
    return asyncio.run(coro)


class TestListToolsReturnsFourMetaTools:
    """Smoke test: list_tools returns exactly 4 meta-tools."""

    def test_list_tools_returns_four_tools(self):
        async def run():
            req = types.ListToolsRequest(method="tools/list", params=None)
            handler = mcp._mcp_server.request_handlers.get(types.ListToolsRequest)
            assert handler is not None
            result = await handler(req)
            tools = result.root.tools
            names = {t.name for t in tools}
            assert len(names) == 4, f"Expected 4 tools, got {len(names)}: {names}"
            assert names == META_TOOL_NAMES, f"Expected {META_TOOL_NAMES}, got {names}"

        _run(run())


class TestMathLs:
    """Unit tests for math_ls (no args, with category, unknown category)."""

    def test_math_ls_no_args_has_hint_categories_and_tools(self):
        async def run():
            out = await mcp.call_tool("math_ls", {})
            content = out[0][0]
            data = json.loads(content.text)
            assert "hint" in data
            assert len(data["categories"]) == 7
            assert len(data["tools"]) == 26
            for cat in data["categories"]:
                assert "id" in cat and "tools" in cat
            for t in data["tools"]:
                assert "name" in t and "intent" in t

        _run(run())

    def test_math_ls_stats_returns_five_tools_with_full_descriptors(self):
        async def run():
            out = await mcp.call_tool("math_ls", {"category": "stats"})
            content = out[0][0]
            data = json.loads(content.text)
            assert "hint" in data
            assert data["category"] == "stats"
            assert len(data["tools"]) == 5
            for t in data["tools"]:
                assert "name" in t and "description" in t and "inputSchema" in t

        _run(run())

    def test_math_ls_unknown_category_returns_error_and_available(self):
        async def run():
            out = await mcp.call_tool("math_ls", {"category": "unknown"})
            content = out[0][0]
            data = json.loads(content.text)
            assert "error" in data
            assert "available" in data
            assert set(data["available"]) == set(CATALOG.keys())

        _run(run())


class TestMathMan:
    """Unit tests for math_man (valid tool, meta-tool name, unknown)."""

    def test_math_man_ttest_returns_full_descriptor(self):
        async def run():
            out = await mcp.call_tool("math_man", {"tool": "ttest"})
            content = out[0][0]
            data = json.loads(content.text)
            assert data.get("name") == "ttest"
            assert "description" in data
            assert "inputSchema" in data

        _run(run())

    def test_math_man_meta_tool_returns_error(self):
        async def run():
            out = await mcp.call_tool("math_man", {"tool": "math_ls"})
            content = out[0][0]
            data = json.loads(content.text)
            assert "error" in data
            assert "math_ls" in data["error"] or "Unknown" in data["error"]

        _run(run())

    def test_math_man_unknown_returns_error(self):
        async def run():
            out = await mcp.call_tool("math_man", {"tool": "nonexistent_tool"})
            content = out[0][0]
            data = json.loads(content.text)
            assert "error" in data

        _run(run())


class TestMathDispatcher:
    """Unit tests for math dispatcher (simplify, unknown tool)."""

    def test_math_simplify_returns_result(self):
        async def run():
            out = await mcp.call_tool(
                "math", {"tool": "simplify", "arguments": {"expression": "x + x"}}
            )
            text = out[0][0].text
            assert "2*x" in text

        _run(run())

    def test_math_unknown_tool_returns_error(self):
        async def run():
            out = await mcp.call_tool(
                "math", {"tool": "unknown_tool", "arguments": {}}
            )
            text = out[0][0].text
            data = json.loads(text)
            assert "error" in data

        _run(run())


class TestMathBatch:
    """math_batch is one of the 4 tools and can be invoked."""

    def test_math_batch_is_in_list_tools(self):
        async def run():
            req = types.ListToolsRequest(method="tools/list", params=None)
            handler = mcp._mcp_server.request_handlers.get(types.ListToolsRequest)
            result = await handler(req)
            names = {t.name for t in result.root.tools}
            assert "math_batch" in names

        _run(run())

    def test_math_batch_invokable_returns_results_in_order(self):
        async def run():
            out = await mcp.call_tool(
                "math_batch",
                {
                    "calls": [
                        {"name": "simplify", "arguments": {"expression": "x + 0"}},
                        {"name": "evaluate", "arguments": {"expression": "2 + 2"}},
                    ]
                },
            )
            content = out[0][0]
            data = json.loads(content.text)
            assert len(data) == 2
            assert data[0]["name"] == "simplify" and data[0]["isError"] is False
            assert data[1]["name"] == "evaluate" and data[1]["isError"] is False
            assert "x" in data[0]["content"][0]["text"]
            assert "4" in data[1]["content"][0]["text"]

        _run(run())
