# Docker MCP Server Guide

This guide explains how to run the MCP (Model Context Protocol) server in Docker containers with different transport modes.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- ShiftAgent API running (accessible at `http://host.docker.internal:8081`)

### Available Transport Modes

| Transport | Port | Use Case | Status |
|-----------|------|----------|--------|
| **HTTP** | 8083 | Web clients, multiple connections | ✅ Recommended |
| **SSE** | 8084 | Legacy clients | ⚠️ Deprecated |
| **STDIO** | N/A | Claude Desktop | ✅ Default |

## 🌐 HTTP Transport (Recommended)

### Build and Run
```bash
# Build HTTP Docker image
make docker-mcp-build-http

# Run HTTP MCP server
make docker-mcp-run-http

# Check logs
make docker-mcp-logs-http

# Stop server
make docker-mcp-stop
```

### Manual Docker Commands
```bash
# Build image
docker-compose -f docker-compose.mcp.yml --profile http build mcp-http

# Run container
docker-compose -f docker-compose.mcp.yml --profile http up -d mcp-http

# Check status
docker ps | grep mcp-http

# View logs
docker-compose -f docker-compose.mcp.yml --profile http logs -f mcp-http

# Stop container
docker-compose -f docker-compose.mcp.yml --profile http down
```

### Configuration
Environment variables for HTTP transport:
- `MCP_TRANSPORT=http`
- `MCP_HTTP_HOST=0.0.0.0` (bind to all interfaces)
- `MCP_HTTP_PORT=8083` (exposed port)
- `MCP_HTTP_PATH=/mcp` (endpoint path)

### Accessing HTTP MCP Server
- **Endpoint**: `http://localhost:8083/mcp`
- **Health Check**: Container includes built-in health monitoring
- **Client Connection**: Use FastMCP client or curl for testing

## 📡 SSE Transport (Deprecated)

### Build and Run
```bash
# Build SSE Docker image
make docker-mcp-build-sse

# Run SSE MCP server (with deprecation warning)
make docker-mcp-run-sse

# Check logs
make docker-mcp-logs-sse

# Stop server
make docker-mcp-stop
```

### Configuration
Environment variables for SSE transport:
- `MCP_TRANSPORT=sse`
- `MCP_SSE_HOST=0.0.0.0`
- `MCP_SSE_PORT=8084`

### Accessing SSE MCP Server
- **Endpoint**: `http://localhost:8084/sse/`
- **Note**: SSE is deprecated, migrate to HTTP transport

## 🔧 Advanced Usage

### Custom Configuration
```bash
# Custom HTTP port
docker run -d \
  -p 9000:9000 \
  -e MCP_HTTP_PORT=9000 \
  -e SHIFT_AGENT_API_URL=http://host.docker.internal:8081 \
  shiftagent-mcp-http:latest

# Custom SSE port
docker run -d \
  -p 9001:9001 \
  -e MCP_SSE_PORT=9001 \
  -e SHIFT_AGENT_API_URL=http://host.docker.internal:8081 \
  shiftagent-mcp-sse:latest
```

### Using Docker Compose Override
Create a `docker-compose.override.yml` file:
```yaml
version: '3.8'
services:
  mcp-http:
    ports:
      - "9000:9000"
    environment:
      - MCP_HTTP_PORT=9000
      - LOG_LEVEL=DEBUG
```

### Helper Script Usage
```bash
# Use the helper script directly
./scripts/docker_mcp.sh build http      # Build HTTP image
./scripts/docker_mcp.sh run http        # Run HTTP server
./scripts/docker_mcp.sh logs http       # Show logs
./scripts/docker_mcp.sh stop http       # Stop HTTP server
./scripts/docker_mcp.sh clean           # Clean all containers and images
```

## 🔗 Client Integration

### FastMCP Python Client
```python
from fastmcp import Client

# Connect to HTTP transport
async with Client("http://localhost:8083/mcp") as client:
    # List available tools
    tools = await client.list_tools()

    # Call a tool
    result = await client.call_tool("solve_schedule_sync", {
        "schedule_input": {
            "employees": [...],
            "shifts": [...]
        }
    })
```

### Claude Desktop Configuration
For HTTP transport, create `claude_desktop_config.json`:
```json
{
    "mcpServers": {
        "shiftagent-http": {
            "command": "curl",
            "args": [
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "--no-buffer",
                "http://localhost:8083/mcp"
            ]
        }
    }
}
```

### cURL Testing
```bash
# Test HTTP endpoint
curl -X GET http://localhost:8083/mcp

# Test SSE endpoint (deprecated)
curl -X GET http://localhost:8084/sse/
```

## 🐳 Docker Architecture

### HTTP Transport Container
- **Base Image**: `python:3.11-slim`
- **Port**: 8083
- **Health Check**: Built-in HTTP health monitoring
- **User**: Non-root user (`app`) for security

### SSE Transport Container
- **Base Image**: `python:3.11-slim`
- **Port**: 8084
- **Health Check**: Basic SSE endpoint check
- **User**: Non-root user (`app`) for security

### Security Features
- Non-root user execution
- Minimal system dependencies
- Health checks for monitoring
- Proper signal handling

## 📊 Monitoring and Troubleshooting

### Health Checks
```bash
# Check container health
docker ps | grep mcp-http

# Manual health check
curl -f http://localhost:8083/mcp/health || echo "Health check failed"
```

### Common Issues

1. **Port conflicts**: Change ports in environment variables
2. **API connectivity**: Ensure ShiftAgent API is running on port 8081
3. **Permission issues**: Containers run as non-root user

### Logs and Debugging
```bash
# View real-time logs
make docker-mcp-logs-http

# Debug with verbose logging
docker run -e LOG_LEVEL=DEBUG shiftagent-mcp-http:latest

# Container shell access
docker exec -it shiftagent-mcp-http /bin/bash
```

## 🚦 Production Deployment

### Recommendations
1. **Use HTTP transport** (SSE is deprecated)
2. **Enable health checks** for container orchestration
3. **Set appropriate resource limits**
4. **Use secrets management** for API URLs
5. **Monitor container performance**

### Example Production Compose
```yaml
version: '3.8'
services:
  mcp-http:
    image: shiftagent-mcp-http:latest
    restart: unless-stopped
    ports:
      - "8083:8083"
    environment:
      - MCP_TRANSPORT=http
      - SHIFT_AGENT_API_URL=${API_URL}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8083/mcp/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

This completes the Docker setup for both HTTP and SSE transport modes. HTTP transport is recommended for new deployments due to better performance and ongoing support.
