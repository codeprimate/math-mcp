"""Tests for HTTP/streamable-http transport."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from math_mcp.server import _wrap_http_app, mcp


@pytest.mark.skipif(
    not hasattr(mcp, "streamable_http_app"),
    reason="mcp.streamable_http_app not available",
)
class TestStreamableHttpApp:
    """streamable_http_app is a method that returns a Starlette app; it must be called.

    Passing mcp.streamable_http_app (no call) to Mount causes:
    TypeError: ... takes 1 positional argument but 4 were given
    when a request is handled.
    """

    def test_streamable_http_app_returns_starlette(self):
        # Must call streamable_http_app() to get the app, not pass the method
        app = mcp.streamable_http_app()
        assert app is not None
        assert hasattr(app, "routes")
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/mcp" in paths

    def test_wrapped_app_mounts_starlette_not_method(self):
        # _wrap_http_app(mcp.streamable_http_app()) — root Mount must receive
        # a Starlette (has .routes), not the raw method (no .routes)
        wrapped = _wrap_http_app(mcp.streamable_http_app())
        # Find the Mount that wraps the MCP app (it has /mcp); exclude /outputs
        mcp_mount = next(
            (
                r
                for r in wrapped.routes
                if hasattr(r, "app")
                and hasattr(getattr(r.app, "routes", None), "__iter__")
                and any(
                    getattr(x, "path", None) == "/mcp"
                    for x in getattr(r.app, "routes", [])
                )
            ),
            None,
        )
        assert mcp_mount is not None
        assert hasattr(
            mcp_mount.app, "routes"
        ), "root Mount app must be Starlette from streamable_http_app()"

    def test_initialize_returns_200_and_session_id(self):
        """Integration test: POST /mcp initialize should return 200 and mcp-session-id.

        This test verifies that the StreamableHTTPSessionManager's task group is
        properly initialized via the app's lifespan. Without the lifespan fix,
        this would return 500 with "Task group is not initialized".
        """
        from starlette.testclient import TestClient

        # Build wrapped app with lifespan (same as main())
        mcp_app = mcp.streamable_http_app()
        lifespan = getattr(mcp_app, "lifespan", None)
        if lifespan is None:
            if getattr(mcp, "session_manager", None) is None:
                pytest.skip("MCP streamable_http_app() did not provide lifespan and session_manager is missing")
            lifespan = lambda app: mcp.session_manager.run()
        wrapped = _wrap_http_app(mcp_app, lifespan=lifespan)

        # TestClient runs the app's lifespan when used as a context manager
        with TestClient(wrapped) as client:
            resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        # MCP streamable-http returns mcp-session-id header
        assert "mcp-session-id" in resp.headers or "MCP-Session-ID" in resp.headers, (
            f"Expected mcp-session-id header, got headers: {list(resp.headers.keys())}"
        )
