#!/bin/bash

# Script to run both API and MCP server

echo "🚀 Starting Shift Scheduler API and MCP Server..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $API_PID $MCP_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Start API server in background
echo "🌐 Starting API server on port 8081..."
uv run uvicorn main:app --host 0.0.0.0 --port 8081 --reload &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        echo "✅ API server is ready!"
        break
    fi
    sleep 1
done

# Start MCP server
echo "🔧 Starting MCP server..."
SHIFT_SCHEDULER_API_URL=http://localhost:8081 uv run python mcp_server.py &
MCP_PID=$!

echo ""
echo "✅ Both servers are running!"
echo "   - API Server: http://localhost:8081"
echo "   - API Docs: http://localhost:8081/docs"
echo "   - MCP Server: Running on stdio (Python/FastMCP)"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait