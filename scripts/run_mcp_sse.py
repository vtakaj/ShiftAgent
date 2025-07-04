#!/usr/bin/env python3
"""
Run MCP server with SSE transport for legacy clients
Note: SSE transport is deprecated. Use HTTP transport for new deployments.
"""

import os

# Set SSE transport environment variables
os.environ["MCP_TRANSPORT"] = "sse"
os.environ["MCP_SSE_HOST"] = os.getenv("MCP_SSE_HOST", "0.0.0.0")
os.environ["MCP_SSE_PORT"] = os.getenv("MCP_SSE_PORT", "8084")

# Import and run the MCP server
from shiftagent_mcp.server import main

if __name__ == "__main__":
    print(
        "⚠️  WARNING: SSE transport is deprecated. Consider using HTTP transport instead."
    )
    print(
        f"Starting MCP server with SSE transport on {os.environ['MCP_SSE_HOST']}:{os.environ['MCP_SSE_PORT']}"
    )
    main()
