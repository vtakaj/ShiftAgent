#!/usr/bin/env python3
"""
Run MCP server with HTTP transport for web-based clients
"""

import os

# Set HTTP transport environment variables
os.environ["MCP_TRANSPORT"] = "http"
os.environ["MCP_HTTP_HOST"] = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
os.environ["MCP_HTTP_PORT"] = os.getenv("MCP_HTTP_PORT", "8083")
os.environ["MCP_HTTP_PATH"] = os.getenv("MCP_HTTP_PATH", "/mcp")

# Import and run the MCP server
from shiftagent_mcp.server import main

if __name__ == "__main__":
    print(
        f"Starting MCP server with HTTP transport on {os.environ['MCP_HTTP_HOST']}:{os.environ['MCP_HTTP_PORT']}{os.environ['MCP_HTTP_PATH']}"
    )
    main()
