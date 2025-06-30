# Dev Container Makefile
.PHONY: help setup install dev run test format lint clean

# Default target
help:
	@echo "🚀 ShiftAgent Dev Container Commands:"
	@echo ""
	@echo "  setup        - Complete setup (Python, pre-commit, MCP) - run this first!"
	@echo "  run          - Start FastAPI server only"
	@echo "  run-mcp      - Start both API and MCP servers together"
	@echo "  mcp-http     - Start MCP server with HTTP transport (recommended)"
	@echo "  mcp-sse      - Start MCP server with SSE transport (deprecated)"
	@echo "  test         - Run tests"
	@echo "  format       - Format Python code"
	@echo "  tf-format    - Format Terraform files"
	@echo "  tf-format-check - Check Terraform formatting"
	@echo "  lint         - Check code"
	@echo "  clean        - Clear cache"
	@echo ""
	@echo "  Git Hooks (pre-commit):"
	@echo "  hooks-test    - Test git hooks manually"
	@echo ""
	@echo "  Additional Commands:"
	@echo "  install      - Install Python dependencies only"
	@echo "  dev          - Install development dependencies"
	@echo "  debug        - Run API in debug mode"
	@echo "  test-api     - Test API endpoints"
	@echo "  streamlit    - Start Streamlit web UI"
	@echo "  infra-init   - Initialize Terraform infrastructure"
	@echo ""
	@echo "  Docker MCP Commands:"
	@echo "  docker-mcp-build-http  - Build HTTP MCP Docker image"
	@echo "  docker-mcp-build-sse   - Build SSE MCP Docker image"
	@echo "  docker-mcp-run-http    - Run HTTP MCP in Docker"
	@echo "  docker-mcp-run-sse     - Run SSE MCP in Docker"
	@echo "  docker-mcp-stop        - Stop all Docker MCP servers"
	@echo "  docker-mcp-logs-http   - Show HTTP MCP logs"
	@echo "  docker-mcp-logs-sse    - Show SSE MCP logs"
	@echo ""
	@echo "  n8n Integration Commands:"
	@echo "  docker-n8n-build       - Build n8n integration images"
	@echo "  docker-n8n-run         - Start n8n workflow automation (port 5678)"
	@echo "  docker-n8n-stop        - Stop n8n integration stack"
	@echo "  docker-n8n-logs        - Show all n8n integration logs"
	@echo "  docker-n8n-logs-api    - Show API service logs"
	@echo "  docker-n8n-logs-mcp    - Show MCP service logs"
	@echo "  docker-n8n-logs-n8n    - Show n8n service logs"

# Development environment setup (with error handling)
setup:
	@echo "🔧 Setting up development environment..."
	@rm -f uv.lock
	@echo "📦 Installing Python dependencies (including FastMCP and pre-commit)..."
	uv sync --no-install-project
	@echo "🪝 Installing pre-commit git hooks..."
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
	@echo "✅ Setup complete!"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	uv sync --no-install-project

# Install development dependencies
dev:
	@echo "🛠 Installing development dependencies..."
	uv sync --all-extras

# Start FastAPI server
run:
	@echo "🚀 Starting FastAPI server..."
	@echo "Server URL: http://localhost:8081"
	@echo "API Documentation: http://localhost:8081/docs"
	@echo "For HTTPS: make run-https"
	PYTHONPATH=src uv run uvicorn shift_agent.api.app:app --host 0.0.0.0 --port 8081 --reload

# Start FastAPI server with HTTPS (self-signed certificate)
run-https:
	@echo "🔒 Starting FastAPI server with HTTPS..."
	@echo "Server URL: https://localhost:8081"
	@echo "API Documentation: https://localhost:8081/docs"
	@echo "Note: Browser will show security warning for self-signed certificate"
	PYTHONPATH=src uv run uvicorn shift_agent.api.app:app --host 0.0.0.0 --port 8081 --reload --ssl-keyfile=./localhost-key.pem --ssl-certfile=./localhost.pem

# Run tests
test:
	@echo "🧪 Running tests..."
	PYTHONPATH=src uv run pytest tests/ -v

# Format code
format:
	@echo "✨ Formatting code..."
	uv run ruff format .
	uv run ruff check . --fix

# Format Terraform code
tf-format:
	@echo "🏗️ Formatting Terraform files..."
	terraform fmt -recursive

# Check Terraform formatting
tf-format-check:
	@echo "🔍 Checking Terraform formatting..."
	terraform fmt -check -recursive

# Check code
lint:
	@echo "🔍 Checking code..."
	uv run ruff check . || true
	uv run mypy . || true

# Clear cache
clean:
	@echo "🧹 Clearing cache..."
	uv cache clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Check environment
check:
	@echo "🔍 Checking environment..."
	@echo "Python: $(shell python --version 2>&1 || echo 'Not found')"
	@echo "uv: $(shell uv --version 2>&1 || echo 'Not found')"
	@echo "Java: $(shell java -version 2>&1 | head -1 || echo 'Not found')"
	@echo "JAVA_HOME: $(JAVA_HOME)"
	@echo "Current directory: $(shell pwd)"
	@echo "Files: $(shell ls -la | head -5)"

# API test
test-api:
	@echo "🌐 API Test:"
	@echo "Health Check:"
	curl -s http://localhost:8081/health | jq . || curl -s http://localhost:8081/health
	@echo "\nGet Demo Data:"
	curl -s http://localhost:8081/api/shifts/demo | jq '.statistics' || echo "Server not running"

# Troubleshooting
troubleshoot:
	@echo "🔧 Troubleshooting Information:"
	@$(MAKE) check
	@echo ""
	@echo "uv environment:"
	uv show || echo "uv sync may be needed"
	@echo ""
	@echo "Solutions:"
	@echo "1. Run make setup"
	@echo "2. If error persists, run make clean && make setup"
	@echo "3. If problem continues, Rebuild Dev Container"

# Simple development flow
dev-start: setup run

# Debug mode
debug:
	@echo "🐛 Starting in debug mode..."
	PYTHONPATH=src uv run uvicorn shift_agent.api.app:app --host 0.0.0.0 --port 8081 --reload --log-level debug

# Run with MCP server
run-mcp:
	@echo "🤖 Starting MCP server..."
	@echo "MCP Server URL: http://localhost:8082"
	PYTHONPATH=src uv run python -m shift_agent_mcp.server

# Run MCP server only
mcp:
	@echo "🔧 Starting MCP server (make sure API is running)..."
	PYTHONPATH=src uv run python -m shift_agent_mcp.server

# Test MCP server
test-mcp:
	@echo "🧪 Testing MCP server..."
	@echo '{"jsonrpc":"2.0","method":"list_tools","id":1}' | PYTHONPATH=src uv run python -m shift_agent_mcp.server

# Run MCP server with HTTP transport
mcp-http:
	@echo "🌐 Starting MCP server with HTTP transport..."
	@echo "MCP HTTP URL: http://localhost:8083/mcp"
	@echo "Transport: Streamable HTTP"
	PYTHONPATH=src uv run python scripts/run_mcp_http.py

# Run MCP server with SSE transport (deprecated)
mcp-sse:
	@echo "📡 Starting MCP server with SSE transport..."
	@echo "⚠️  WARNING: SSE transport is deprecated. Use 'make mcp-http' for new deployments."
	@echo "MCP SSE URL: http://localhost:8084/sse/"
	@echo "Transport: Server-Sent Events (Legacy)"
	PYTHONPATH=src uv run python scripts/run_mcp_sse.py

# Start Streamlit app
run-streamlit:
	@echo "📊 Starting Streamlit app..."
	@echo "Streamlit URL: http://localhost:8501"
	cd src && PYTHONPATH=. uv run streamlit run shift_agent_viewer/main.py --server.port 8501

# Docker MCP Server commands
docker-mcp-build-http:
	@echo "🔨 Building MCP Docker image for HTTP transport..."
	./scripts/docker_mcp.sh build http

docker-mcp-build-sse:
	@echo "🔨 Building MCP Docker image for SSE transport..."
	./scripts/docker_mcp.sh build sse

docker-mcp-run-http:
	@echo "🚀 Running MCP server with HTTP transport in Docker..."
	./scripts/docker_mcp.sh run http

docker-mcp-run-sse:
	@echo "🚀 Running MCP server with SSE transport in Docker..."
	./scripts/docker_mcp.sh run sse

docker-mcp-stop:
	@echo "🛑 Stopping Docker MCP servers..."
	./scripts/docker_mcp.sh stop all

docker-mcp-logs-http:
	@echo "📋 Showing HTTP MCP server logs..."
	./scripts/docker_mcp.sh logs http

docker-mcp-logs-sse:
	@echo "📋 Showing SSE MCP server logs..."
	./scripts/docker_mcp.sh logs sse

# Pre-commit Git Hooks
hooks-test:
	@echo "🧪 Testing git hooks..."
	@echo "📝 Testing pre-commit hooks..."
	uv run pre-commit run --all-files || echo "Pre-commit hooks test completed"
	@echo "🔍 Testing commit message validation..."
	@echo "feat: test commit message" | uv run cz check --message || echo "Commit message validation test completed"
	@echo "✅ Hook tests completed!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose -f docker/compose/docker-compose.yml build

docker-build-mcp:
	@echo "🤖 Building MCP server Docker image..."
	docker build -f docker/dockerfiles/Dockerfile.mcp -t shiftagent-mcp-server .

docker-run:
	@echo "🚀 Starting services with Docker Compose..."
	docker-compose -f docker/compose/docker-compose.yml up -d

docker-run-mcp:
	@echo "🤖 Starting MCP server with Docker Compose..."
	docker-compose -f docker/compose/docker-compose.yml --profile mcp up -d mcp-server

docker-stop:
	@echo "🛑 Stopping Docker services..."
	docker-compose -f docker/compose/docker-compose.yml down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose -f docker/compose/docker-compose.yml logs -f

docker-logs-mcp:
	@echo "📋 Showing MCP server logs..."
	docker-compose -f docker/compose/docker-compose.yml logs -f mcp-server

# Test Docker MCP server
test-docker-mcp:
	@echo "🧪 Testing Docker MCP server..."
	@echo '{"jsonrpc":"2.0","method":"list_tools","id":1}' | docker run -i --rm --network shiftagent-network shiftagent-mcp-server:latest

# n8n integration commands
docker-n8n-build:
	@echo "🔄 Building n8n integration images..."
	docker-compose -f docker/compose/docker-compose.n8n.yml build

docker-n8n-run:
	@echo "🚀 Starting n8n integration stack..."
	docker-compose -f docker/compose/docker-compose.n8n.yml up -d
	@echo "✅ n8n is available at: http://localhost:5678"
	@echo "📡 MCP SSE endpoint: http://localhost:8084/sse/"

docker-n8n-stop:
	@echo "🛑 Stopping n8n integration stack..."
	docker-compose -f docker/compose/docker-compose.n8n.yml down

docker-n8n-logs:
	@echo "📋 Showing n8n integration logs..."
	docker-compose -f docker/compose/docker-compose.n8n.yml logs -f

docker-n8n-logs-api:
	@echo "📋 Showing n8n API logs..."
	docker-compose -f docker/compose/docker-compose.n8n.yml logs -f api

docker-n8n-logs-mcp:
	@echo "📋 Showing n8n MCP logs..."
	docker-compose -f docker/compose/docker-compose.n8n.yml logs -f mcp

docker-n8n-logs-n8n:
	@echo "📋 Showing n8n service logs..."
	docker-compose -f docker/compose/docker-compose.n8n.yml logs -f n8n
