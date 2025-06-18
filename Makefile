# Dev Container Makefile
.PHONY: help setup install dev run test format lint clean

# Default target
help:
	@echo "🚀 Shift Scheduler Dev Container Commands:"
	@echo ""
	@echo "  setup        - Complete setup (Python, Node.js, MCP) - run this first!"
	@echo "  run          - Start FastAPI server only"
	@echo "  run-mcp      - Start both API and MCP servers together"
	@echo "  test         - Run tests"
	@echo "  format       - Format code"
	@echo "  lint         - Check code"
	@echo "  clean        - Clear cache"
	@echo ""
	@echo "  Additional Commands:"
	@echo "  install      - Install Python dependencies only"
	@echo "  dev          - Install development dependencies"
	@echo "  debug        - Run API in debug mode"
	@echo "  test-api     - Test API endpoints"
	@echo "  streamlit    - Start Streamlit web UI"
	@echo "  pulumi-setup - Initialize Pulumi for infrastructure"

# Development environment setup (with error handling)
setup:
	@echo "🔧 Setting up development environment..."
	@rm -f uv.lock
	@echo "📦 Installing Python dependencies (including FastMCP)..."
	uv sync --no-install-project
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
	uv run uvicorn main:app --host 0.0.0.0 --port 8081 --reload

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run pytest -v

# Format code
format:
	@echo "✨ Formatting code..."
	uv run ruff format .
	uv run ruff check . --fix

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
	uv run uvicorn main:app --host 0.0.0.0 --port 8081 --reload --log-level debug

# Run with MCP server
run-mcp:
	@echo "🚀 Starting API and MCP Server..."
	@./run-with-mcp.sh

# Run MCP server only
mcp:
	@echo "🔧 Starting MCP server (make sure API is running)..."
	@uv run python mcp_server.py

# Test MCP server
test-mcp:
	@echo "🧪 Testing MCP server..."
	@echo '{"jsonrpc":"2.0","method":"list_tools","id":1}' | uv run python mcp_server.py

# Start Streamlit web UI
streamlit:
	@echo "🌐 Starting Streamlit web UI..."
	@echo "Make sure the FastAPI server is running (make run)"
	@echo "Web UI will be available at: http://localhost:8501"
	uv run streamlit run streamlit_main.py --server.port 8501

# Initialize Pulumi for infrastructure
pulumi-setup:
	@echo "🏗️ Setting up Pulumi infrastructure..."
	@command -v pulumi >/dev/null 2>&1 || { echo "❌ Pulumi not found. Please install Pulumi CLI first."; exit 1; }
	@echo "✅ Pulumi CLI detected"
	@cd infrastructure && pulumi version
	@echo "📝 To get started with Pulumi:"
	@echo "  1. cd infrastructure"
	@echo "  2. pulumi login  (or pulumi login --local for offline)"
	@echo "  3. pulumi stack init dev"
	@echo "  4. pulumi config set azure-native:location 'East US'"
	@echo "  5. pulumi up  (to deploy infrastructure)"