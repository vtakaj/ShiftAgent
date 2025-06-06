"""
Main server entry point
"""

from .app import app
from .routes import *  # noqa: F401, F403 - Import all routes to register them

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
