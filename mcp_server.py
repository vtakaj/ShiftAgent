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

# Specifically configure Timefold logging if solver log level is set
solver_log_level = os.getenv("SOLVER_LOG_LEVEL", "INFO")
if solver_log_level == "DEBUG":
    logging.getLogger("timefold").setLevel(logging.DEBUG)
    logging.getLogger("natural_shift_planner.api.solver").setLevel(logging.DEBUG)

from natural_shift_planner.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
