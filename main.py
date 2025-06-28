#!/usr/bin/env python3
"""
FastAPI server entry point for ShiftAgent
"""

import uvicorn

from shift_agent.api.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
