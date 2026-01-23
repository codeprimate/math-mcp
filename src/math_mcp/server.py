"""Math MCP Server - Symbolic math via SymPy."""

import os
from datetime import datetime, timedelta

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from math_mcp import plotting_tools, scipy_tools, stats_tools, sympy_tools, unit_tools
from math_mcp import plot_output

# Default configuration constants
DEFAULT_TRANSPORT = "stdio"
DEFAULT_HTTP_HOST = "0.0.0.0"
DEFAULT_HTTP_PORT = "8008"
DEFAULT_ALLOWED_HOSTS = "*"
DEFAULT_DNS_REBINDING_PROTECTION = "false"

# Read transport security configuration from environment
disable_protection = os.getenv("MCP_DISABLE_DNS_REBINDING_PROTECTION", DEFAULT_DNS_REBINDING_PROTECTION).lower() == "true"

if disable_protection:
    allowed_hosts = ["*"]
    enable_dns_rebinding_protection = False
else:
    allowed_hosts_str = os.getenv("MCP_ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS)
    if allowed_hosts_str == "*":
        allowed_hosts = ["*"]
        enable_dns_rebinding_protection = False
    else:
        allowed_hosts = [h.strip() for h in allowed_hosts_str.split(",")]
        enable_dns_rebinding_protection = True

# Configure transport security
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=enable_dns_rebinding_protection,
    allowed_hosts=allowed_hosts
)

def _attach_plot_url_handler(app: FastMCP) -> None:
    """Attach handler to save plot outputs to disk.
    
    This intercepts tool call results for plot tools and saves the image to disk.
    URLs can be retrieved via the separate /plot-urls endpoint.
    """
    # Get the original handler
    original_handler = app._mcp_server.request_handlers.get(types.CallToolRequest)
    
    async def handler(req: types.CallToolRequest):
        # Call the original handler (or default FastMCP handler)
        if original_handler:
            result = await original_handler(req)
        else:
            # Fallback: use FastMCP's default tool call mechanism
            try:
                tool_result = await app.call_tool(
                    req.params.name, (req.params.arguments or {})
                )
                # FastMCP returns a list of content items
                content = list(tool_result) if isinstance(tool_result, (list, tuple)) else [tool_result]
                result = types.ServerResult(
                    types.CallToolResult(content=content, isError=False)
                )
            except Exception as exc:
                result = types.ServerResult(
                    types.CallToolResult(
                        content=[types.TextContent(type="text", text=str(exc))],
                        isError=True,
                    )
                )
        
        # Post-process: save plot files and add URL to response
        if not result.root.isError and req.params.name in plot_output.PLOT_TOOL_NAMES:
            try:
                # Extract content from result (ServerResult.root contains CallToolResult)
                original_content = result.root.content
                content = list(original_content) if original_content else []
                
                # Save plot to file and get URL
                url = plot_output.maybe_save_plot_output(content, app.get_context())
                
                # Add URL as text content if file was saved
                if url:
                    # Add URL text to content list
                    url_text = types.TextContent(
                        type="text",
                        text=f"Chart available at: {url}"
                    )
                    content.append(url_text)
                    
                    # Update the result in place by modifying the content directly
                    # FastMCP should serialize the updated content
                    if hasattr(result.root, 'content'):
                        # Try to update content directly if it's mutable
                        try:
                            result.root.content = tuple(content) if isinstance(result.root.content, tuple) else content
                        except (AttributeError, TypeError):
                            # If direct assignment doesn't work, create new objects
                            updated_result = result.root.model_copy(update={"content": tuple(content) if isinstance(original_content, tuple) else content})
                            result = result.model_copy(update={"root": updated_result})
            except Exception as exc:
                # Log error but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to save plot output: {exc}", exc_info=True)
        
        return result

    app._mcp_server.request_handlers[types.CallToolRequest] = handler


# Module-level storage for plot URLs (session_id -> (url, timestamp))
_plot_urls: dict[str, tuple[str, datetime]] = {}
_cleanup_interval = timedelta(hours=1)


def _create_plot_url_endpoint():
    """Create a simple endpoint to get the most recent plot URL for a session."""
    from starlette.responses import JSONResponse
    from starlette.requests import Request
    from datetime import datetime
    
    async def get_plot_url(request: Request):
        """Get the most recent plot URL for the session."""
        session_id = request.headers.get("mcp-session-id") or request.query_params.get("session_id")
        if not session_id:
            return JSONResponse({"error": "session_id required"}, status_code=400)
        
        # Clean up old entries
        now = datetime.now()
        expired = [sid for sid, (_, timestamp) in _plot_urls.items() 
                  if now - timestamp > _cleanup_interval]
        for sid in expired:
            _plot_urls.pop(sid, None)
        
        url, _ = _plot_urls.get(session_id, (None, None))
        if url:
            return JSONResponse({"url": url})
        return JSONResponse({"url": None})
    
    return get_plot_url


def _wrap_http_app(app: object, *, lifespan=None) -> Starlette:
    """Wrap the MCP streamable HTTP app with /outputs and /plot-urls endpoints.

    The MCP StreamableHTTPSessionManager requires its run() context (which sets up
    the task group) to be active. That is normally done via the Starlette app's
    lifespan. When we mount the MCP app under a new root Starlette, only the root
    app's lifespan runs—the mounted app's lifespan is not invoked. So we must pass
    the MCP app's lifespan into the root Starlette so the task group is initialized.
    """
    from starlette.routing import Route
    
    output_dir = os.getenv(
        "MCP_OUTPUT_DIR", plot_output.DEFAULT_OUTPUT_DIR
    ).strip() or plot_output.DEFAULT_OUTPUT_DIR
    
    # Create plot URL endpoint
    get_plot_url = _create_plot_url_endpoint()
    
    routes = [
        Mount(
            "/outputs",
            app=StaticFiles(directory=output_dir, check_dir=False),
        ),
        Route("/plot-urls", get_plot_url, methods=["GET"]),
        Mount("/", app=app),
    ]
    return Starlette(routes=routes, lifespan=lifespan) if lifespan else Starlette(routes=routes)


# Create FastMCP instance with transport security settings
mcp = FastMCP("Math", transport_security=transport_security)

# Register all tools from their respective modules
sympy_tools.register_sympy_tools(mcp)
unit_tools.register_unit_tools(mcp)
scipy_tools.register_scipy_tools(mcp)
stats_tools.register_stats_tools(mcp)
plotting_tools.register_plotting_tools(mcp)
_attach_plot_url_handler(mcp)


def main():
    """Run the MCP server.
    
    Transport mode is controlled by environment variables:
    - MCP_TRANSPORT: "stdio" (default) or "streamable-http"
    - MCP_HOST: Host to bind to (default: "0.0.0.0" for HTTP, ignored for stdio)
    - MCP_PORT: Port to listen on (default: 8008 for HTTP, ignored for stdio)
    
    HTTP mode uses streamable-http transport with session management.
    """
    import sys
    
    try:
        transport = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT).lower()
        
        if transport in ("http", "streamable-http"):
            # Get configuration from environment variables
            host = os.getenv("MCP_HOST", DEFAULT_HTTP_HOST)
            port_str = os.getenv("MCP_PORT", DEFAULT_HTTP_PORT)
            port = int(port_str)
            
            # Log startup info to stderr for debugging
            print(f"[math-mcp] Starting HTTP server on {host}:{port}", file=sys.stderr)
            print("[math-mcp] Transport mode: streamable-http", file=sys.stderr)
            
            import uvicorn
            
            # Log the allowed hosts configuration
            print(f"[math-mcp] DNS rebinding protection: {transport_security.enable_dns_rebinding_protection}", file=sys.stderr)
            print(f"[math-mcp] Allowed hosts: {transport_security.allowed_hosts}", file=sys.stderr)
            
            # Use streamable HTTP app with session management
            # Single endpoint (/mcp) handles both streaming and JSON-RPC messages
            # streamable_http_app returns a Starlette app. Its lifespan runs
            # StreamableHTTPSessionManager.run(), which initializes the task group
            # required for handle_request. Our root Starlette must use that lifespan
            # because mounted apps' lifespans are not run.
            mcp_app = mcp.streamable_http_app()
            lifespan = getattr(mcp_app, "lifespan", None)
            if lifespan is None:
                if getattr(mcp, "session_manager", None) is None:
                    raise RuntimeError(
                        "MCP streamable_http_app() did not provide a lifespan and "
                        "session_manager is missing. StreamableHTTPSessionManager requires "
                        "run() to be used as the app lifespan. Upgrade the MCP SDK."
                    )
                lifespan = lambda app: mcp.session_manager.run()
            app = _wrap_http_app(mcp_app, lifespan=lifespan)
            print("[math-mcp] Using Streamable HTTP transport (compatible with mcp-remote)", file=sys.stderr)
            
            # Run uvicorn
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                timeout_keep_alive=75,
                timeout_graceful_shutdown=30,
                access_log=True
            )
        else:
            print("[math-mcp] Starting stdio server", file=sys.stderr)
            mcp.run(transport="stdio")
    except Exception as e:
        # Log errors to stderr so they appear in MCP logs
        print(f"[math-mcp] Error starting server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
