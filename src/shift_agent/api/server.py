#!/usr/bin/env python3
"""
FastAPI server entry point for ShiftAgent
"""

import uvicorn

from .app import app
from .routes import *  # noqa: F401, F403 - Import all routes to register them


def main():
    """Main entry point for the shift-agent-api console script"""
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")


if __name__ == "__main__":
    main()
