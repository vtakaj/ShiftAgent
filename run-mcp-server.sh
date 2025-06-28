#!/bin/bash
# MCP Server runner script for Claude Desktop

# Change to the project directory
cd "$(dirname "$0")"

# Set up Python path
export PYTHONPATH="${PWD}/src"

# Ensure dependencies are installed
if [ ! -d ".venv" ]; then
    echo "Installing dependencies..." >&2
    uv sync --no-install-project
fi

# Run the MCP server
exec uv run python -m natural_shift_planner_mcp.server
