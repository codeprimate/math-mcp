"""Math MCP Server - Symbolic math via SymPy."""

from mcp.server.fastmcp import FastMCP

from math_mcp import plotting_tools, scipy_tools, sympy_tools, unit_tools

mcp = FastMCP("Math")

# Register all tools from their respective modules
sympy_tools.register_sympy_tools(mcp)
unit_tools.register_unit_tools(mcp)
scipy_tools.register_scipy_tools(mcp)
plotting_tools.register_plotting_tools(mcp)


def main():
    """Run the MCP server.
    
    Transport mode is controlled by environment variables:
    - MCP_TRANSPORT: "stdio" (default) or "http" or "streamable-http"
    - MCP_HOST: Host to bind to (default: "0.0.0.0" for HTTP, ignored for stdio)
    - MCP_PORT: Port to listen on (default: 8008 for HTTP, ignored for stdio)
    
    HTTP mode uses Server-Sent Events (SSE) for streaming responses.
    """
    import os
    import sys
    
    try:
        transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
        
        if transport in ("http", "streamable-http"):
            # Get configuration from environment variables
            host = os.getenv("MCP_HOST", "0.0.0.0")
            port_str = os.getenv("MCP_PORT", "8008")
            port = int(port_str)
            
            # Log startup info to stderr for debugging
            print(f"[math-mcp] Starting HTTP server on {host}:{port}", file=sys.stderr)
            print(f"[math-mcp] Transport mode: {transport}", file=sys.stderr)
            
            import uvicorn
            
            # Use FastMCP's native HTTP app - it handles everything
            app = mcp.streamable_http_app
            
            # Run uvicorn with proper configuration
            # Note: Uvicorn doesn't support HTTP/2, but FastMCP's streamable_http_app
            # works with HTTP/1.1 using Server-Sent Events for streaming
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                # Ensure we don't close connections prematurely
                timeout_keep_alive=75,
                timeout_graceful_shutdown=30,
                # Enable access logging to see all requests
                access_log=True
            )
        else:
            print(f"[math-mcp] Starting stdio server", file=sys.stderr)
            mcp.run(transport="stdio")
    except Exception as e:
        # Log errors to stderr so they appear in MCP logs
        print(f"[math-mcp] Error starting server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
