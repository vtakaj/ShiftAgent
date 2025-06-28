#!/usr/bin/env python3
"""
Run MCP server with SSE transport for legacy clients
Note: SSE transport is deprecated. Use HTTP transport for new deployments.
"""

import os
import sys

# Set SSE transport environment variables
os.environ["MCP_TRANSPORT"] = "sse"
os.environ["MCP_SSE_HOST"] = os.getenv("MCP_SSE_HOST", "0.0.0.0")
os.environ["MCP_SSE_PORT"] = os.getenv("MCP_SSE_PORT", "8084")

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# Import and run the MCP server
from shift_agent_mcp.server import main

if __name__ == "__main__":
    print(
        "⚠️  WARNING: SSE transport is deprecated. Consider using HTTP transport instead."
    )
    print(
        f"Starting MCP server with SSE transport on {os.environ['MCP_SSE_HOST']}:{os.environ['MCP_SSE_PORT']}"
    )
    main()
