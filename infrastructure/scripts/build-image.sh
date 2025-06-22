#!/bin/bash
# Build Docker image for the Shift Scheduler application

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INFRASTRUCTURE_DIR="${SCRIPT_DIR}/.."

# Default values
IMAGE_NAME="shift-scheduler"
TAG="latest"
DOCKERFILE="Dockerfile"
BUILD_CONTEXT="${PROJECT_ROOT}"
PULUMI_STACK=""
PLATFORM="linux/amd64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Build Docker image for the Shift Scheduler application

Usage: $0 [OPTIONS]

Options:
    -i, --image-name NAME       Image name (default: shift-scheduler)
    -t, --tag TAG              Image tag (default: latest)
    -f, --dockerfile PATH      Path to Dockerfile (default: Dockerfile)
    -c, --context PATH         Build context path (default: project root)
    -s, --stack STACK          Pulumi stack name (dev/prod)
    -p, --platform PLATFORM    Target platform (default: linux/amd64)
    --no-cache                 Build without cache
    --quiet                    Suppress build output
    -h, --help                 Show this help

Examples:
    $0                                    # Build with defaults
    $0 -t v1.0.0                         # Build with specific tag
    $0 -s dev -t latest                  # Build for development stack
    $0 -i my-scheduler -t v2.0.0         # Build with custom image name
    $0 --no-cache -t rebuild             # Build without cache

Environment Variables:
    BUILD_NUMBER     - Appended to tag if set
    CI               - Set to 'true' for CI builds
    DOCKER_BUILDKIT  - Enable BuildKit (default: 1)
EOF
}

# Parse command line arguments
NO_CACHE=false
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -f|--dockerfile)
            DOCKERFILE="$2"
            shift 2
            ;;
        -c|--context)
            BUILD_CONTEXT="$2"
            shift 2
            ;;
        -s|--stack)
            PULUMI_STACK="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ ! -f "${BUILD_CONTEXT}/${DOCKERFILE}" ]]; then
    log_error "Dockerfile not found: ${BUILD_CONTEXT}/${DOCKERFILE}"
    exit 1
fi

if [[ ! -d "${BUILD_CONTEXT}" ]]; then
    log_error "Build context directory not found: ${BUILD_CONTEXT}"
    exit 1
fi

# Set Docker BuildKit
export DOCKER_BUILDKIT=1

# Generate full image tag
FULL_TAG="${TAG}"
if [[ -n "${BUILD_NUMBER:-}" ]]; then
    FULL_TAG="${TAG}-${BUILD_NUMBER}"
fi

# Add stack suffix if specified
if [[ -n "${PULUMI_STACK}" ]]; then
    FULL_TAG="${FULL_TAG}-${PULUMI_STACK}"
fi

FULL_IMAGE_NAME="${IMAGE_NAME}:${FULL_TAG}"

log_info "Building Docker image..."
log_info "Image: ${FULL_IMAGE_NAME}"
log_info "Dockerfile: ${BUILD_CONTEXT}/${DOCKERFILE}"
log_info "Context: ${BUILD_CONTEXT}"
log_info "Platform: ${PLATFORM}"

# Build Docker build command
BUILD_CMD=(
    docker build
    --platform "${PLATFORM}"
    --file "${BUILD_CONTEXT}/${DOCKERFILE}"
    --tag "${FULL_IMAGE_NAME}"
)

# Add cache options
if [[ "${NO_CACHE}" == "true" ]]; then
    BUILD_CMD+=(--no-cache)
fi

# Add quiet option
if [[ "${QUIET}" == "true" ]]; then
    BUILD_CMD+=(--quiet)
fi

# Add build context
BUILD_CMD+=("${BUILD_CONTEXT}")

# Execute build
log_info "Executing: ${BUILD_CMD[*]}"
if "${BUILD_CMD[@]}"; then
    log_success "Successfully built image: ${FULL_IMAGE_NAME}"
    
    # Show image details
    log_info "Image details:"
    docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -2
    
    # Output image name for scripting
    echo "IMAGE_NAME=${FULL_IMAGE_NAME}"
    
    # Export for use in other scripts
    export BUILT_IMAGE_NAME="${FULL_IMAGE_NAME}"
    
else
    log_error "Failed to build image: ${FULL_IMAGE_NAME}"
    exit 1
fi

log_success "Build completed successfully!"