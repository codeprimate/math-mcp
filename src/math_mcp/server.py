"""Math MCP Server - Symbolic math via SymPy."""

import os
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from math_mcp import plotting_tools, scipy_tools, sympy_tools, unit_tools

# Read transport security configuration from environment
disable_protection = os.getenv("MCP_DISABLE_DNS_REBINDING_PROTECTION", "false").lower() == "true"

if disable_protection:
    allowed_hosts = ["*"]
    enable_dns_rebinding_protection = False
else:
    allowed_hosts_str = os.getenv("MCP_ALLOWED_HOSTS", "*")
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

# Create FastMCP instance with transport security settings
mcp = FastMCP("Math", transport_security=transport_security)

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
            
            # Log the allowed hosts configuration
            print(f"[math-mcp] DNS rebinding protection: {transport_security.enable_dns_rebinding_protection}", file=sys.stderr)
            print(f"[math-mcp] Allowed hosts: {transport_security.allowed_hosts}", file=sys.stderr)
            
            # Get the app - it's already configured with transport security
            app = mcp.streamable_http_app
            
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
