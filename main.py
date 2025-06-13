#!/usr/bin/env python3
"""
Main entry point for the Shift Scheduler API
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

from natural_shift_planner.api.server import app  # noqa: E402


def main():
    """Main entry point for uvx support"""
    import uvicorn

    # Configure uvicorn logging
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level=log_level.lower())


if __name__ == "__main__":
    main()
