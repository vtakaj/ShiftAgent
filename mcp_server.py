#!/usr/bin/env python3
"""
MCP Server entry point for ShiftAgent
This file serves as the entry point for Claude Desktop MCP integration.
"""

import argparse
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import and run the MCP server
from shift_agent_mcp.server import logger, mcp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Server for ShiftAgent")
    parser.add_argument(
        "--transport", default="stdio", choices=["stdio", "sse", "http"]
    )
    parser.add_argument("--sse-host", default="127.0.0.1")
    parser.add_argument("--sse-port", type=int, default=8084)
    parser.add_argument("--http-host", default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=8083)
    parser.add_argument("--http-path", default="/mcp")

    args = parser.parse_args()

    if args.transport == "sse":
        logger.warning(
            "SSE transport is deprecated. Consider using HTTP transport instead."
        )
        logger.info(
            f"Starting MCP server with SSE transport on {args.sse_host}:{args.sse_port}"
        )
        mcp.run(transport="sse", host=args.sse_host, port=args.sse_port)
    elif args.transport == "http":
        logger.info(
            f"Starting MCP server with HTTP transport on {args.http_host}:{args.http_port}{args.http_path}"
        )
        mcp.run(
            transport="http",
            host=args.http_host,
            port=args.http_port,
            path=args.http_path,
        )
    else:
        logger.info("Starting MCP server with stdio transport")
        mcp.run()
