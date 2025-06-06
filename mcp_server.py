#!/usr/bin/env python3
"""
MCP Server entry point for Shift Scheduler
"""
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from natural_shift_planner.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
