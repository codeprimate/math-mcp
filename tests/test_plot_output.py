"""Tests for plot output helpers."""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from mcp.types import ImageContent

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from math_mcp import plot_output


class DummyURL:
    def __init__(self, scheme: str, hostname: str, port: int | None = None):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port


class DummyRequest:
    def __init__(self, headers: dict[str, str] | None = None, url: DummyURL | None = None):
        self.headers = headers or {}
        self.url = url


class DummyContext:
    def __init__(self, request: DummyRequest | None = None):
        self.request = request


def test_get_base_url_prefers_forwarded_headers():
    headers = {
        "x-forwarded-proto": "https, http",
        "x-forwarded-host": "api.example.com, proxy.local",
    }
    base_url = plot_output._get_base_url(None, headers)
    assert base_url == "https://api.example.com"


def test_get_base_url_falls_back_to_host_header():
    headers = {"Host": "localhost:8008"}
    base_url = plot_output._get_base_url(None, headers)
    assert base_url == "http://localhost:8008"


def test_get_base_url_uses_request_url_when_headers_missing():
    request = DummyRequest(url=DummyURL("https", "example.com", 8443))
    base_url = plot_output._get_base_url(request, None)
    assert base_url == "https://example.com:8443"


def test_sanitize_session_id_preserves_valid_value():
    assert plot_output._sanitize_session_id("abc-123_DEF") == "abc-123_DEF"


def test_sanitize_session_id_strips_invalid_chars():
    sanitized = plot_output._sanitize_session_id("abc/../def")
    assert "/" not in sanitized
    assert sanitized


def test_sanitize_session_id_generates_when_empty():
    generated = plot_output._sanitize_session_id("")
    assert generated.startswith("session-")


def test_build_unique_path_adds_counter_when_needed(tmp_path):
    target_dir = tmp_path / "charts"
    target_dir.mkdir()
    existing = target_dir / "chart-20260101010101.png"
    existing.write_text("existing")

    path = plot_output._build_unique_path(target_dir, "20260101010101", "png")
    assert path.name == "chart-20260101010101-1.png"


def test_maybe_save_plot_output_writes_file_and_returns_url(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(
        plot_output,
        "_utc_date_and_timestamp",
        lambda: ("2026-01-15", "20260115143025"),
    )

    payload = b"plot-bytes"
    image = ImageContent(
        type="image",
        data=base64.b64encode(payload).decode("utf-8"),
        mimeType="image/png",
    )
    headers = {
        "x-forwarded-proto": "https",
        "x-forwarded-host": "api.example.com",
        "mcp-session-id": "abc123",
    }
    context = DummyContext(DummyRequest(headers=headers))

    url = plot_output.maybe_save_plot_output([image], context)
    assert (
        url
        == "https://api.example.com/outputs/charts/2026-01-15/abc123/chart-20260115143025.png"
    )

    saved_path = (
        tmp_path
        / "charts"
        / "2026-01-15"
        / "abc123"
        / "chart-20260115143025.png"
    )
    assert saved_path.read_bytes() == payload


def test_maybe_save_plot_output_returns_none_without_base_url():
    image = ImageContent(
        type="image",
        data=base64.b64encode(b"plot-bytes").decode("utf-8"),
        mimeType="image/png",
    )
    assert plot_output.maybe_save_plot_output([image], None) is None
