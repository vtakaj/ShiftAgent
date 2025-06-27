#!/bin/bash
# Docker MCP Server Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

show_help() {
    echo "Usage: $0 [COMMAND] [TRANSPORT]"
    echo ""
    echo "Commands:"
    echo "  build     Build Docker images for MCP server"
    echo "  run       Run MCP server with specified transport"
    echo "  stop      Stop running MCP server"
    echo "  logs      Show logs for running MCP server"
    echo "  clean     Stop and remove containers and images"
    echo ""
    echo "Transport modes:"
    echo "  stdio     STDIO transport for Claude Desktop (default)"
    echo "  http      HTTP transport for web clients (recommended)"
    echo "  sse       SSE transport for legacy clients (deprecated)"
    echo ""
    echo "Examples:"
    echo "  $0 build http          # Build HTTP transport image"
    echo "  $0 run http            # Run with HTTP transport"
    echo "  $0 run sse             # Run with SSE transport"
    echo "  $0 logs http           # Show HTTP server logs"
    echo "  $0 stop http           # Stop HTTP server"
    echo ""
}

build_image() {
    local transport=${1:-stdio}
    echo "🔨 Building MCP server image for $transport transport..."
    
    case $transport in
        stdio)
            docker-compose -f docker-compose.mcp.yml --profile stdio build mcp-stdio
            ;;
        http)
            docker-compose -f docker-compose.mcp.yml --profile http build mcp-http
            ;;
        sse)
            echo "⚠️  WARNING: SSE transport is deprecated. Consider using HTTP transport."
            docker-compose -f docker-compose.mcp.yml --profile sse build mcp-sse
            ;;
        *)
            echo "❌ Unknown transport: $transport"
            show_help
            exit 1
            ;;
    esac
    echo "✅ Build complete for $transport transport"
}

run_server() {
    local transport=${1:-stdio}
    echo "🚀 Starting MCP server with $transport transport..."
    
    case $transport in
        stdio)
            echo "📌 STDIO mode - for Claude Desktop integration"
            docker-compose -f docker-compose.mcp.yml --profile stdio up mcp-stdio
            ;;
        http)
            echo "🌐 HTTP mode - accessible at http://localhost:8083/mcp"
            docker-compose -f docker-compose.mcp.yml --profile http up -d mcp-http
            echo "✅ MCP HTTP server started on port 8083"
            echo "🔗 MCP endpoint: http://localhost:8083/mcp"
            ;;
        sse)
            echo "⚠️  WARNING: SSE transport is deprecated. Consider using HTTP transport."
            echo "📡 SSE mode - accessible at http://localhost:8084/sse/"
            docker-compose -f docker-compose.mcp.yml --profile sse up -d mcp-sse
            echo "✅ MCP SSE server started on port 8084"
            echo "🔗 SSE endpoint: http://localhost:8084/sse/"
            ;;
        *)
            echo "❌ Unknown transport: $transport"
            show_help
            exit 1
            ;;
    esac
}

stop_server() {
    local transport=${1:-all}
    echo "🛑 Stopping MCP server..."
    
    if [ "$transport" = "all" ]; then
        docker-compose -f docker-compose.mcp.yml --profile stdio --profile http --profile sse down
    else
        docker-compose -f docker-compose.mcp.yml --profile $transport down
    fi
    echo "✅ MCP server stopped"
}

show_logs() {
    local transport=${1:-stdio}
    echo "📋 Showing logs for $transport transport..."
    
    case $transport in
        stdio)
            docker-compose -f docker-compose.mcp.yml --profile stdio logs -f mcp-stdio
            ;;
        http)
            docker-compose -f docker-compose.mcp.yml --profile http logs -f mcp-http
            ;;
        sse)
            docker-compose -f docker-compose.mcp.yml --profile sse logs -f mcp-sse
            ;;
        *)
            echo "❌ Unknown transport: $transport"
            show_help
            exit 1
            ;;
    esac
}

clean_all() {
    echo "🧹 Cleaning up all MCP containers and images..."
    docker-compose -f docker-compose.mcp.yml --profile stdio --profile http --profile sse down --rmi all --volumes --remove-orphans
    echo "✅ Cleanup complete"
}

# Main script logic
case ${1:-help} in
    build)
        build_image ${2:-stdio}
        ;;
    run)
        run_server ${2:-stdio}
        ;;
    stop)
        stop_server ${2:-all}
        ;;
    logs)
        show_logs ${2:-stdio}
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac