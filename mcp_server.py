#!/usr/bin/env python3
"""
MCP Server entry point for Shift Scheduler
This file serves as the entry point for Claude Desktop MCP integration.
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import and run the MCP server
from natural_shift_planner_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
