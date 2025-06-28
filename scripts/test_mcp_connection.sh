#!/bin/bash

echo "=== MCP Connection Test ==="

# Check if containers are running
echo -e "\n1. Checking container status:"
docker-compose -f docker-compose.n8n.yml ps

# Test API health
echo -e "\n2. Testing API health:"
docker-compose -f docker-compose.n8n.yml exec -T n8n curl -s http://api:8081/health || echo "API health check failed"

# Test MCP SSE endpoint
echo -e "\n3. Testing MCP SSE endpoint:"
docker-compose -f docker-compose.n8n.yml exec -T n8n curl -s -I http://mcp:8084 || echo "MCP SSE check failed"

# Check MCP logs
echo -e "\n4. Recent MCP logs:"
docker-compose -f docker-compose.n8n.yml logs --tail=20 mcp

# Test from host
echo -e "\n5. Testing from host:"
curl -s http://localhost:8084 || echo "Host MCP check failed"