#!/usr/bin/env python3
"""
MCP Server entry point for Shift Scheduler
"""

import logging
import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging based on environment
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from natural_shift_planner.mcp.server import mcp  # noqa: E402


def main():
    """Main entry point for uvx support"""
    mcp.run()


if __name__ == "__main__":
    main()
