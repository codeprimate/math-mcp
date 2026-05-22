"""Tests for HTTP plot responses and handler regressions."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp import types
from mcp.types import ImageContent, TextContent

from math_mcp import plot_output
from math_mcp.server import mcp

PLOT_ARGS = {
    "categories": ["Q1", "Q2", "Q3"],
    "values": [10.0, 20.0, 15.0],
    "title": "Quarterly Sales",
}


class DummyRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


class DummyContext:
    def __init__(self, request: DummyRequest | None = None):
        self.request = request


class RaisingRequestContextContext:
    """Mimics FastMCP Context: .request works, .request_context raises."""

    def __init__(self, request):
        self.request = request

    @property
    def request_context(self):
        raise ValueError("Context is not available outside of a request")


def _assert_no_base64_image_payload(result: types.CallToolResult) -> None:
    for item in result.content or []:
        assert not isinstance(item, types.ImageContent), (
            "ImageContent should not be returned over HTTP"
        )
        if isinstance(item, types.TextContent):
            assert plot_output.DOWNLOAD_URL_JSON_KEY in item.text

    structured = result.structuredContent or {}
    assert "data" not in structured, "structuredContent must not contain base64 image data"


@pytest.mark.asyncio
async def test_plot_bar_handler_sets_structured_content_download_url(
    tmp_path, monkeypatch
):
    """Direct plot_bar HTTP handler must replace structuredContent, not only content."""
    monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
    headers = {"host": "localhost:8008", "mcp-session-id": "plot-handler-test"}
    monkeypatch.setattr(
        "math_mcp.server._safe_plot_context",
        lambda _app: DummyContext(DummyRequest(headers=headers)),
    )

    handler = mcp._mcp_server.request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(name="plot_bar", arguments=PLOT_ARGS),
    )

    result = await handler(request)
    tool_result = result.root
    assert not tool_result.isError, tool_result

    _assert_no_base64_image_payload(tool_result)
    assert plot_output.DOWNLOAD_URL_JSON_KEY in tool_result.structuredContent
    assert tool_result.structuredContent[plot_output.MIME_TYPE_JSON_KEY] == "image/png"


@pytest.mark.asyncio
async def test_math_plot_bar_returns_download_url_without_base64(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
    headers = {"host": "localhost:8008", "mcp-session-id": "math-plot-test"}
    ctx = DummyContext(DummyRequest(headers=headers))
    monkeypatch.setattr(mcp, "get_context", lambda: ctx)

    handler = mcp._mcp_server.request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(
            name="math",
            arguments={"tool": "plot_bar", "arguments": PLOT_ARGS},
        ),
    )

    result = await handler(request)
    tool_result = result.root
    assert not tool_result.isError, tool_result

    _assert_no_base64_image_payload(tool_result)
    payload = json.loads(tool_result.content[0].text)
    assert plot_output.DOWNLOAD_URL_JSON_KEY in payload
    assert "data" not in (tool_result.structuredContent or {})


class TestPlotOutputContextSafety:
    def test_safe_request_context_handles_fastmcp_value_error(self):
        context = RaisingRequestContextContext(request=object())
        assert plot_output._safe_request_context(context) is None

    def test_transform_works_when_request_context_raises_but_request_has_headers(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setattr(
            plot_output,
            "_utc_date_and_timestamp",
            lambda: ("2026-01-15", "20260115143025"),
        )

        image = ImageContent(
            type="image",
            data=base64.b64encode(b"plot-bytes").decode("utf-8"),
            mimeType="image/png",
        )
        headers = {
            "host": "localhost:8008",
            "mcp-session-id": "abc123",
        }
        context = RaisingRequestContextContext(
            request=type("Req", (), {"headers": headers})()
        )

        content, structured = plot_output.transform_plot_response([image], context)
        assert structured is not None
        assert plot_output.DOWNLOAD_URL_JSON_KEY in structured
        assert isinstance(content[0], TextContent)
        assert plot_output.DOWNLOAD_URL_JSON_KEY in content[0].text
