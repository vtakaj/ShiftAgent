#!/bin/bash
# Build and push Docker image to Azure Container Registry

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
IMAGE_NAME="shift-scheduler"
TAG="latest"
PULUMI_STACK=""
REGISTRY=""
BUILD_ARGS=()
PUSH_ARGS=()

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
Build and push Docker image to Azure Container Registry

Usage: $0 [OPTIONS]

Options:
    -i, --image-name NAME       Image name (default: shift-scheduler)
    -t, --tag TAG              Image tag (default: latest)
    -s, --stack STACK          Pulumi stack name (dev/prod)
    -r, --registry REGISTRY    Registry URL (overrides stack detection)
    --no-cache                 Build without cache
    --force-login              Force registry login
    --build-only               Build only, don't push
    --push-only                Push only, don't build
    --dry-run                  Show what would be done
    -h, --help                 Show this help

Build-specific options:
    -f, --dockerfile PATH      Path to Dockerfile
    -c, --context PATH         Build context path
    -p, --platform PLATFORM    Target platform
    --quiet                    Suppress build output

Examples:
    $0 -s dev                            # Build and push to dev registry
    $0 -s prod -t v1.0.0                 # Build and push version to prod
    $0 --build-only -t test              # Build only
    $0 --push-only -s dev -t latest      # Push existing image
    $0 --dry-run -s prod                 # Show what would be done

Environment Variables:
    BUILD_NUMBER     - Appended to tag if set
    CI               - Set to 'true' for CI builds
EOF
}

# Parse command line arguments
BUILD_ONLY=false
PUSH_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image-name)
            IMAGE_NAME="$2"
            BUILD_ARGS+=("--image-name" "$2")
            PUSH_ARGS+=("--image-name" "$2")
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            BUILD_ARGS+=("--tag" "$2")
            PUSH_ARGS+=("--tag" "$2")
            shift 2
            ;;
        -s|--stack)
            PULUMI_STACK="$2"
            BUILD_ARGS+=("--stack" "$2")
            PUSH_ARGS+=("--stack" "$2")
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            PUSH_ARGS+=("--registry" "$2")
            shift 2
            ;;
        -f|--dockerfile)
            BUILD_ARGS+=("--dockerfile" "$2")
            shift 2
            ;;
        -c|--context)
            BUILD_ARGS+=("--context" "$2")
            shift 2
            ;;
        -p|--platform)
            BUILD_ARGS+=("--platform" "$2")
            shift 2
            ;;
        --no-cache)
            BUILD_ARGS+=("--no-cache")
            shift
            ;;
        --quiet)
            BUILD_ARGS+=("--quiet")
            shift
            ;;
        --force-login)
            PUSH_ARGS+=("--force-login")
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --push-only)
            PUSH_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            BUILD_ARGS+=("--dry-run")
            PUSH_ARGS+=("--dry-run")
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

# Validate mutually exclusive options
if [[ "${BUILD_ONLY}" == "true" && "${PUSH_ONLY}" == "true" ]]; then
    log_error "Cannot specify both --build-only and --push-only"
    exit 1
fi

# Main execution
START_TIME=$(date +%s)

log_info "Starting build and push process..."
log_info "Image: ${IMAGE_NAME}:${TAG}"
log_info "Stack: ${PULUMI_STACK:-"(auto-detect)"}"
log_info "Registry: ${REGISTRY:-"(from stack)"}"

if [[ "${DRY_RUN}" == "true" ]]; then
    log_warning "DRY RUN MODE - No actual changes will be made"
fi

# Build phase
if [[ "${PUSH_ONLY}" != "true" ]]; then
    log_info "=== BUILD PHASE ==="
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "Would execute: ${SCRIPT_DIR}/build-image.sh ${BUILD_ARGS[*]}"
    else
        if ! "${SCRIPT_DIR}/build-image.sh" "${BUILD_ARGS[@]}"; then
            log_error "Build failed"
            exit 1
        fi
    fi
    
    log_success "Build phase completed"
fi

# Push phase
if [[ "${BUILD_ONLY}" != "true" ]]; then
    log_info "=== PUSH PHASE ==="
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "Would execute: ${SCRIPT_DIR}/push-image.sh ${PUSH_ARGS[*]}"
    else
        if ! "${SCRIPT_DIR}/push-image.sh" "${PUSH_ARGS[@]}"; then
            log_error "Push failed"
            exit 1
        fi
    fi
    
    log_success "Push phase completed"
fi

# Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_info "=== SUMMARY ==="
log_success "Process completed successfully!"
log_info "Duration: ${DURATION} seconds"
log_info "Image: ${IMAGE_NAME}:${TAG}"

if [[ "${BUILD_ONLY}" == "true" ]]; then
    log_info "Action: Build only"
elif [[ "${PUSH_ONLY}" == "true" ]]; then
    log_info "Action: Push only"
else
    log_info "Action: Build and push"
fi

if [[ "${DRY_RUN}" == "true" ]]; then
    log_warning "DRY RUN - No actual changes were made"
fi