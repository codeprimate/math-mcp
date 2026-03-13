"""Tests for batch_tools module."""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import mcp.types as types

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from math_mcp.batch_tools import (
    MAX_BATCH_SIZE,
    CallSpec,
    _max_concurrent,
    _run_one_tool,
    _serialize_content,
    create_batch_tool,
)


class TestSerializeContent:
    """Tests for _serialize_content."""

    def test_text_content(self):
        content = [types.TextContent(type="text", text="hello")]
        out = _serialize_content(content)
        assert out == [{"type": "text", "text": "hello"}]

    def test_image_content(self):
        content = [
            types.ImageContent(
                type="image", data="base64data", mimeType="image/png"
            )
        ]
        out = _serialize_content(content)
        assert len(out) == 1
        assert out[0]["type"] == "image"
        assert out[0]["mimeType"] == "image/png"
        assert out[0]["data"] == "base64data"

    def test_mixed_content(self):
        content = [
            types.TextContent(type="text", text="result"),
            types.ImageContent(
                type="image", data="x", mimeType="image/svg+xml"
            ),
        ]
        out = _serialize_content(content)
        assert out == [
            {"type": "text", "text": "result"},
            {"type": "image", "mimeType": "image/svg+xml", "data": "x"},
        ]


class TestMaxConcurrent:
    """Tests for _max_concurrent."""

    def test_at_least_one(self):
        with patch("math_mcp.batch_tools.os.cpu_count", return_value=1):
            assert _max_concurrent() == 1

    def test_cpu_count_minus_one(self):
        with patch("math_mcp.batch_tools.os.cpu_count", return_value=4):
            assert _max_concurrent() == 3

    def test_cpu_count_none_uses_one(self):
        with patch("math_mcp.batch_tools.os.cpu_count", return_value=None):
            assert _max_concurrent() == 1


class TestRunOneTool:
    """Tests for _run_one_tool."""

    def test_success_returns_content_and_no_error(self):
        app = MagicMock()
        app.call_tool = AsyncMock(return_value="2")
        app.get_context = MagicMock(return_value=None)

        async def run():
            return await _run_one_tool(
                app, "evaluate", {"expression": "1+1"}
            )

        content, is_error = asyncio.run(run())
        assert is_error is False
        assert len(content) == 1
        assert content[0].text == "2"
        app.call_tool.assert_awaited_once_with("evaluate", {"expression": "1+1"})

    def test_exception_returns_error_content(self):
        app = MagicMock()
        app.call_tool = AsyncMock(side_effect=ValueError("bad input"))

        async def run():
            return await _run_one_tool(app, "unknown_tool", {})

        content, is_error = asyncio.run(run())
        assert is_error is True
        assert len(content) == 1
        assert "bad input" in content[0].text

    def test_list_result_normalized(self):
        app = MagicMock()
        app.call_tool = AsyncMock(return_value=["a", "b"])
        app.get_context = MagicMock(return_value=None)

        async def run():
            return await _run_one_tool(app, "some_tool", {})

        content, is_error = asyncio.run(run())
        assert is_error is False
        assert len(content) == 2


class TestCallSpec:
    """Tests for CallSpec model."""

    def test_default_arguments(self):
        spec = CallSpec(name="simplify")
        assert spec.arguments == {}

    def test_with_arguments(self):
        spec = CallSpec(name="solve", arguments={"equation": "x^2-4", "variable": "x"})
        assert spec.name == "solve"
        assert spec.arguments["variable"] == "x"


class TestCreateBatchTool:
    """Tests for create_batch_tool / tool_batch_tools."""

    def _run(self, tool_func, *args, **kwargs):
        return asyncio.run(tool_func(*args, **kwargs))

    def test_empty_calls_returns_empty_array(self):
        app = MagicMock()
        handler = create_batch_tool(app)
        result = self._run(handler, calls=[])
        assert result == "[]"
        result = self._run(handler, calls=None)
        assert result == "[]"

    def test_results_in_same_order_as_calls(self):
        app = MagicMock()
        app.call_tool = AsyncMock(side_effect=["first", "second", "third"])
        app.get_context = MagicMock(return_value=None)
        handler = create_batch_tool(app)
        calls = [
            {"name": "a", "arguments": {}},
            {"name": "b", "arguments": {}},
            {"name": "c", "arguments": {}},
        ]
        result = self._run(handler, calls=calls)
        data = json.loads(result)
        assert len(data) == 3
        assert data[0]["name"] == "a" and data[0]["content"][0]["text"] == "first"
        assert data[1]["name"] == "b" and data[1]["content"][0]["text"] == "second"
        assert data[2]["name"] == "c" and data[2]["content"][0]["text"] == "third"

    def test_one_failure_others_still_return(self):
        app = MagicMock()
        call_count = 0

        async def side_effect(name, args):
            nonlocal call_count
            call_count += 1
            if name == "fail":
                raise RuntimeError("tool failed")
            return f"ok-{name}"

        app.call_tool = AsyncMock(side_effect=side_effect)
        app.get_context = MagicMock(return_value=None)
        handler = create_batch_tool(app)
        calls = [
            {"name": "a", "arguments": {}},
            {"name": "fail", "arguments": {}},
            {"name": "c", "arguments": {}},
        ]
        result = self._run(handler, calls=calls)
        data = json.loads(result)
        assert len(data) == 3
        assert data[0]["isError"] is False and "ok-a" in data[0]["content"][0]["text"]
        assert data[1]["isError"] is True and "tool failed" in data[1]["content"][0]["text"]
        assert data[2]["isError"] is False and "ok-c" in data[2]["content"][0]["text"]

    def test_max_batch_size_rejected(self):
        app = MagicMock()
        handler = create_batch_tool(app)
        calls = [{"name": "x", "arguments": {}}] * (MAX_BATCH_SIZE + 1)
        result = self._run(handler, calls=calls)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["isError"] is True
        assert str(MAX_BATCH_SIZE) in data[0]["content"][0]["text"]

    def test_invalid_call_spec_returns_error(self):
        app = MagicMock()
        handler = create_batch_tool(app)
        calls = [{"wrong_key": "no name"}]
        result = self._run(handler, calls=calls)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["isError"] is True


class TestBatchToolsIntegration:
    """Integration-style tests using real mcp server tools."""

    def _run(self, tool_func, *args, **kwargs):
        return asyncio.run(tool_func(*args, **kwargs))

    def test_batch_simplify_and_evaluate_returns_valid_json(self):
        from math_mcp.server import mcp

        handler = create_batch_tool(mcp)
        calls = [
            {"name": "simplify", "arguments": {"expression": "x + 0"}},
            {"name": "evaluate", "arguments": {"expression": "2 + 2"}},
        ]
        result = self._run(handler, calls=calls)
        data = json.loads(result)
        assert len(data) == 2
        assert data[0]["name"] == "simplify" and data[0]["isError"] is False
        assert data[1]["name"] == "evaluate" and data[1]["isError"] is False
        assert "x" in data[0]["content"][0]["text"]
        assert "4" in data[1]["content"][0]["text"]
