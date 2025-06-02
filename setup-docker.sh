# Docker Buildx Configuration
#!/bin/bash

set -e

echo "🐳 Setting up Docker environment"

# Docker Buildx setup
setup_buildx() {
    echo "🔧 Setting up Docker Buildx..."
    
    # Check if Buildx is available
    if ! docker buildx version > /dev/null 2>&1; then
        echo "❌ Docker Buildx is not available. Please update Docker Desktop to the latest version."
        exit 1
    fi
    
    # Create multi-platform builder
    if ! docker buildx inspect multiplatform > /dev/null 2>&1; then
        echo "📱 Creating multi-platform builder..."
        docker buildx create --name multiplatform --platform linux/amd64,linux/arm64
    fi
    
    # Start using the builder
    docker buildx use multiplatform
    
    echo "✅ Docker Buildx setup complete"
}

# Platform detection
detect_platform() {
    echo "🔍 Detecting platform..."
    
    ARCH=$(uname -m)
    case $ARCH in
        arm64|aarch64)
            echo "✅ ARM64 detected"
            PLATFORM="linux/arm64"
            ;;
        x86_64|amd64)
            echo "ℹ️ x86_64 detected"
            PLATFORM="linux/amd64"
            ;;
        *)
            echo "⚠️ Unknown architecture: $ARCH"
            PLATFORM="linux/amd64"
            ;;
    esac
    
    echo "Platform: $PLATFORM"
}

# Build Dev Container
build_dev_container() {
    echo "🐳 Building Dev Container..."
    
    cd .devcontainer
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --file Dockerfile \
        --tag shift-scheduler-dev:latest \
        --load \
        ..
    cd ..
    
    echo "✅ Dev Container build complete"
}

# Build Production Container
build_production_container() {
    echo "🚀 Building Production Container..."
    
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --file Dockerfile \
        --tag shift-scheduler:latest \
        --tag shift-scheduler:$(date +%Y%m%d) \
        --load \
        .
    
    echo "✅ Production Container build complete"
}

# Check Docker Environment
check_docker_environment() {
    echo "🔍 Checking Docker environment..."
    
    # Check if Docker Desktop is running
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version > /dev/null 2>&1; then
        echo "❌ Docker Compose is not available."
        exit 1
    fi
    
    echo "Docker version: $(docker --version)"
    echo "Docker Compose version: $(docker compose version)"
    echo "✅ Docker environment check complete"
}

# Main process
main() {
    echo "🎯 Starting Shift Scheduler Docker Environment Setup"
    echo "=================================================="
    
    detect_platform
    check_docker_environment
    setup_buildx
    
    case "${1:-all}" in
        "dev")
            build_dev_container
            ;;
        "prod")
            build_production_container
            ;;
        "all")
            build_dev_container
            build_production_container
            ;;
        *)
            echo "Usage: $0 [dev|prod|all]"
            echo "  dev  - Build Dev Container only"
            echo "  prod - Build Production Container only"
            echo "  all  - Build both (default)"
            exit 1
            ;;
    esac
    
    echo ""
    echo "🎉 Setup complete!"
    echo "You can start the Dev Container with:"
    echo "  make dev-up"
    echo "  code . (then 'Dev Containers: Reopen in Container')"
}

# Execute script
main "$@"