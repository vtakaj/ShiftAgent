#!/bin/bash
# Test script for MCP SSE endpoint

echo "🧪 Testing MCP SSE Server..."
echo ""

# Check if server is running
echo "1. Checking if MCP server is reachable..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/sse | grep -q "200"; then
    echo "✅ SSE endpoint is reachable"
else
    echo "❌ SSE endpoint is not reachable. Make sure to run: make mcp-sse"
    exit 1
fi

echo ""
echo "2. Testing SSE connection..."
echo "Connecting to SSE stream (press Ctrl+C to stop)..."
echo ""

# Connect to SSE stream and show events
curl -N -H "Accept: text/event-stream" http://localhost:8082/sse