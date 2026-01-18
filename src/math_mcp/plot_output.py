"""Plot output helpers for saving files and generating URLs."""

from __future__ import annotations

import base64
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

import mcp.types as types
from mcp.server.fastmcp import Context


logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "/outputs"
OUTPUT_URL_PREFIX = "/outputs"
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

PLOT_TOOL_NAMES = {
    "plot_timeseries",
    "plot_bar_chart",
    "plot_histogram",
    "plot_scatter",
    "plot_heatmap",
    "plot_stacked_bar",
    "plot_stackplot",
    "plot_ode_solution",
    "plot_pie_chart",
}


def maybe_save_plot_output(
    content: Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource],
    context: Context | None,
) -> str | None:
    """Save plot output to disk and return a URL if request info is available.
    
    Args:
        content: Sequence of content items (should include ImageContent for plots)
        context: MCP context with request information for URL generation
        
    Returns:
        URL string if file was saved successfully, None otherwise.
        Returns None if no image content found or if context doesn't have request info.
    """
    image = _find_image_content(content)
    if image is None:
        logger.debug("No image content found in plot output")
        return None

    return _save_image_content(image, context)


def _find_image_content(
    content: Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource],
) -> types.ImageContent | None:
    for item in content:
        if isinstance(item, types.ImageContent):
            return item
    return None


def _save_image_content(
    image: types.ImageContent,
    context: Context | None,
) -> str | None:
    """Save image content to disk and return a URL.
    
    Returns:
        URL string if successful, None otherwise. Errors are logged but don't raise.
    """
    # Extract request info for URL generation
    request, headers = _extract_request_and_headers(context)
    base_url = _get_base_url(request, headers)
    if not base_url:
        logger.debug("No request base URL available; skipping plot file save.")
        return None

    # Get session ID for organizing files
    session_id = _extract_session_id(context, headers)
    session_id = _sanitize_session_id(session_id)

    # Determine file extension from mime type
    ext = _infer_extension(image)
    if not ext:
        logger.warning("Unsupported image mime type: %s", image.mimeType)
        return None

    # Prepare output directory structure
    date_str, timestamp = _utc_date_and_timestamp()
    output_dir = _get_output_dir()
    target_dir = output_dir / "charts" / date_str / session_id

    # Create directory (with parents if needed)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("Failed to create output directory %s: %s", target_dir, exc)
        return None

    # Decode base64 image data
    try:
        image_bytes = base64.b64decode(image.data)
    except Exception as exc:
        logger.error("Failed to decode image data: %s", exc)
        return None

    # Write file with unique name
    file_path = _build_unique_path(target_dir, timestamp, ext)
    try:
        with open(file_path, "wb") as handle:
            handle.write(image_bytes)
    except OSError as exc:
        logger.error("Failed to write plot file %s: %s", file_path, exc)
        return None

    # Generate and return URL
    url = _build_output_url(base_url, date_str, session_id, file_path.name)
    logger.info("Saved plot output to %s (URL: %s)", file_path, url)
    return url


def _get_output_dir() -> Path:
    output_dir = os.getenv("MCP_OUTPUT_DIR", DEFAULT_OUTPUT_DIR).strip()
    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR
    return Path(output_dir)


def _infer_extension(image: types.ImageContent) -> str | None:
    mime_type = (image.mimeType or "").lower()
    if mime_type == "image/png":
        return "png"
    if mime_type == "image/svg+xml":
        return "svg"
    return None


def _utc_date_and_timestamp() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d"), now.strftime("%Y%m%d%H%M%S")


def _build_unique_path(target_dir: Path, timestamp: str, ext: str) -> Path:
    base_name = f"chart-{timestamp}"
    candidate = target_dir / f"{base_name}.{ext}"
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = target_dir / f"{base_name}-{counter}.{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def _build_output_url(base_url: str, date_str: str, session_id: str, filename: str) -> str:
    prefix = OUTPUT_URL_PREFIX.rstrip("/")
    return f"{base_url}{prefix}/charts/{date_str}/{session_id}/{filename}"


def _sanitize_session_id(raw_session_id: str | None) -> str:
    if not raw_session_id:
        return _generate_session_id()

    if SESSION_ID_PATTERN.match(raw_session_id):
        return raw_session_id

    sanitized = re.sub(r"[^A-Za-z0-9_-]", "", raw_session_id)
    return sanitized or _generate_session_id()


def _generate_session_id() -> str:
    return f"session-{uuid4().hex}"


def _extract_session_id(
    context: Context | None,
    headers: Mapping[str, str] | None,
) -> str | None:
    header_session = _get_header(headers, "mcp-session-id")
    if header_session:
        return header_session

    if context is None:
        return None

    request_context = getattr(context, "request_context", None)
    if request_context is None:
        return None

    meta = getattr(request_context, "meta", None)
    if meta is not None:
        for key in ("mcp-session-id", "mcp_session_id", "session_id"):
            value = _get_meta_value(meta, key)
            if value:
                return value

    session = getattr(request_context, "session", None)
    session_id = getattr(session, "session_id", None)
    if session_id:
        return str(session_id)

    return None


def _get_base_url(
    request: Any | None,
    headers: Mapping[str, str] | None,
) -> str | None:
    protocol = _get_header(headers, "x-forwarded-proto") if headers else None
    host = _get_header(headers, "x-forwarded-host") if headers else None
    if headers and not host:
        host = _get_header(headers, "host")

    if protocol:
        protocol = protocol.split(",")[0].strip()
    if host:
        host = host.split(",")[0].strip()

    url = None
    if request is not None:
        url = getattr(request, "url", None)
        if not host and url is not None:
            host = _host_from_url(url)
        if not protocol and url is not None:
            protocol = getattr(url, "scheme", None)

    if not host:
        return None

    if protocol not in ("http", "https"):
        protocol = "https" if url is not None and getattr(url, "scheme", "") == "https" else "http"

    return f"{protocol}://{host}"


def _host_from_url(url: Any) -> str | None:
    hostname = getattr(url, "hostname", None)
    port = getattr(url, "port", None)
    if not hostname:
        return None
    if port:
        return f"{hostname}:{port}"
    return str(hostname)


def _extract_request_and_headers(
    context: Context | None,
) -> tuple[Any | None, Mapping[str, str] | None]:
    """Extract request object and headers from context.
    
    Returns:
        Tuple of (request_object, headers_dict) or (None, None) if not available.
    """
    if context is None:
        return None, None

    # Try to get request object first (most direct)
    request = _find_request_object(context)
    if request is not None:
        headers = getattr(request, "headers", None)
        if headers is not None:
            return request, headers

    # Fallback: try to extract headers from context structure
    headers = _headers_from_context(context)
    return request, headers


def _find_request_object(context: Context) -> Any | None:
    """Find request object in context hierarchy.
    
    Checks multiple possible locations where request might be stored.
    """
    candidates = [
        getattr(context, "request", None),
    ]
    
    # Check request_context.request
    request_context = getattr(context, "request_context", None)
    if request_context is not None:
        candidates.append(getattr(request_context, "request", None))
        
        # Check session.request
        session = getattr(request_context, "session", None)
        if session is not None:
            candidates.append(getattr(session, "request", None))
    
    # Return first candidate that has headers attribute
    for candidate in candidates:
        if candidate is not None and hasattr(candidate, "headers"):
            return candidate
    return None


def _headers_from_context(context: Context) -> Mapping[str, str] | None:
    """Extract headers from context structure.
    
    Tries multiple locations where headers might be stored in the context.
    """
    request_context = getattr(context, "request_context", None)
    if request_context is None:
        return None

    # Try session.scope.headers (ASGI/Starlette pattern)
    session = getattr(request_context, "session", None)
    if session is not None:
        scope = getattr(session, "scope", None)
        if isinstance(scope, dict) and "headers" in scope:
            headers = _headers_from_scope(scope.get("headers"))
            if headers:
                return headers

    # Try meta.headers or meta.http.headers
    meta = getattr(request_context, "meta", None)
    if meta is not None:
        # Direct headers in meta
        headers = _get_meta_value(meta, "headers")
        if isinstance(headers, dict):
            return headers

        # Headers nested in http meta
        http_meta = _get_meta_value(meta, "http")
        if isinstance(http_meta, dict):
            headers = http_meta.get("headers")
            if isinstance(headers, dict):
                return headers

    return None


def _headers_from_scope(raw_headers: Any) -> dict[str, str] | None:
    if not isinstance(raw_headers, list):
        return None

    headers: dict[str, str] = {}
    for item in raw_headers:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        key, value = item
        if isinstance(key, bytes):
            key = key.decode("latin-1")
        if isinstance(value, bytes):
            value = value.decode("latin-1")
        headers[str(key)] = str(value)

    return headers or None


def _get_header(headers: Mapping[str, str] | None, name: str) -> str | None:
    if headers is None:
        return None
    if hasattr(headers, "get"):
        value = headers.get(name)
        if value is None:
            value = headers.get(name.lower())
        if value is None:
            value = headers.get(name.upper())
        if value is not None:
            return value
        name_lower = name.lower()
        for key, header_value in headers.items():
            if key.lower() == name_lower:
                return header_value
    return None


def _get_meta_value(meta: Any, key: str) -> Any:
    if hasattr(meta, "model_dump"):
        meta_dict = meta.model_dump()
        if key in meta_dict:
            return meta_dict.get(key)
    return getattr(meta, key, None)
