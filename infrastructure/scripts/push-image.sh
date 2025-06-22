#!/bin/bash
# Push Docker image to Azure Container Registry

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_DIR="${SCRIPT_DIR}/.."

# Default values
IMAGE_NAME="shift-scheduler"
TAG="latest"
PULUMI_STACK=""
REGISTRY=""
FORCE_LOGIN=false

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
Push Docker image to Azure Container Registry

Usage: $0 [OPTIONS]

Options:
    -i, --image-name NAME       Local image name (default: shift-scheduler)
    -t, --tag TAG              Image tag (default: latest)
    -s, --stack STACK          Pulumi stack name (dev/prod) - auto-detects registry
    -r, --registry REGISTRY    Registry URL (overrides stack detection)
    --force-login              Force registry login even if already logged in
    --dry-run                  Show what would be pushed without actually pushing
    -h, --help                 Show this help

Examples:
    $0                                    # Push with defaults using current stack
    $0 -s dev -t latest                  # Push to dev registry
    $0 -s prod -t v1.0.0                 # Push to production registry
    $0 -r myregistry.azurecr.io -t v1.0.0 # Push to specific registry
    $0 --dry-run -s prod                 # Show what would be pushed

Environment Variables:
    PULUMI_STACK_NAME    - Default stack name if not specified
    AZURE_CLIENT_ID      - Azure service principal client ID
    AZURE_CLIENT_SECRET  - Azure service principal client secret
    AZURE_TENANT_ID      - Azure tenant ID
EOF
}

get_registry_from_stack() {
    local stack_name="$1"
    
    # Change to infrastructure directory
    cd "${INFRASTRUCTURE_DIR}"
    
    # Check if stack exists
    if ! pulumi stack ls | grep -q "^${stack_name}"; then
        log_error "Pulumi stack '${stack_name}' not found"
        log_info "Available stacks:"
        pulumi stack ls
        return 1
    fi
    
    # Select the stack
    pulumi stack select "${stack_name}" >/dev/null 2>&1
    
    # Get registry login server
    local login_server
    login_server=$(pulumi stack output container_registry_login_server 2>/dev/null)
    
    if [[ -z "${login_server}" ]]; then
        log_error "Could not retrieve registry login server from stack '${stack_name}'"
        log_info "Make sure the infrastructure is deployed and exports 'container_registry_login_server'"
        return 1
    fi
    
    echo "${login_server}"
}

login_to_registry() {
    local registry="$1"
    
    log_info "Logging into registry: ${registry}"
    
    # Check if already logged in (unless forced)
    if [[ "${FORCE_LOGIN}" == "false" ]] && docker system info | grep -q "${registry}"; then
        log_info "Already logged into ${registry}"
        return 0
    fi
    
    # Try different authentication methods
    
    # Method 1: Azure CLI (most common)
    if command -v az >/dev/null 2>&1; then
        log_info "Attempting login via Azure CLI..."
        if az acr login --name "${registry}" 2>/dev/null; then
            log_success "Successfully logged in via Azure CLI"
            return 0
        fi
    fi
    
    # Method 2: Service Principal (for CI/CD)
    if [[ -n "${AZURE_CLIENT_ID:-}" && -n "${AZURE_CLIENT_SECRET:-}" && -n "${AZURE_TENANT_ID:-}" ]]; then
        log_info "Attempting login via Service Principal..."
        if az login --service-principal \
            --username "${AZURE_CLIENT_ID}" \
            --password "${AZURE_CLIENT_SECRET}" \
            --tenant "${AZURE_TENANT_ID}" >/dev/null 2>&1; then
            
            if az acr login --name "${registry}" 2>/dev/null; then
                log_success "Successfully logged in via Service Principal"
                return 0
            fi
        fi
    fi
    
    # Method 3: Admin credentials (development only)
    log_warning "Attempting login via admin credentials (development only)..."
    
    # Get admin credentials from Pulumi stack
    cd "${INFRASTRUCTURE_DIR}"
    local admin_creds
    admin_creds=$(pulumi stack output container_registry_admin_credentials 2>/dev/null || echo "")
    
    if [[ -n "${admin_creds}" ]]; then
        # Extract username and password from admin credentials
        local username password
        username=$(echo "${admin_creds}" | jq -r '.username // empty' 2>/dev/null || echo "")
        password=$(echo "${admin_creds}" | jq -r '.passwords[0].value // empty' 2>/dev/null || echo "")
        
        if [[ -n "${username}" && -n "${password}" ]]; then
            if echo "${password}" | docker login "${registry}" --username "${username}" --password-stdin >/dev/null 2>&1; then
                log_success "Successfully logged in via admin credentials"
                return 0
            fi
        fi
    fi
    
    log_error "Failed to login to registry: ${registry}"
    log_info "Please ensure you have:"
    log_info "1. Azure CLI installed and logged in (az login)"
    log_info "2. Service Principal credentials set (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)"
    log_info "3. Admin user enabled on the registry (development only)"
    return 1
}

# Parse command line arguments
DRY_RUN=false

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
        -s|--stack)
            PULUMI_STACK="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        --force-login)
            FORCE_LOGIN=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
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

# Determine stack name
if [[ -z "${PULUMI_STACK}" ]]; then
    PULUMI_STACK="${PULUMI_STACK_NAME:-}"
fi

# Determine registry
if [[ -z "${REGISTRY}" ]]; then
    if [[ -z "${PULUMI_STACK}" ]]; then
        log_error "Either --stack or --registry must be specified"
        show_help
        exit 1
    fi
    
    log_info "Getting registry from Pulumi stack: ${PULUMI_STACK}"
    REGISTRY=$(get_registry_from_stack "${PULUMI_STACK}")
    if [[ $? -ne 0 ]]; then
        exit 1
    fi
fi

# Validate registry format
if [[ ! "${REGISTRY}" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]\.azurecr\.io$ ]]; then
    log_error "Invalid registry format: ${REGISTRY}"
    log_info "Expected format: <registry-name>.azurecr.io"
    exit 1
fi

# Generate image names
LOCAL_IMAGE="${IMAGE_NAME}:${TAG}"
REMOTE_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

# Check if local image exists
if ! docker image inspect "${LOCAL_IMAGE}" >/dev/null 2>&1; then
    log_error "Local image not found: ${LOCAL_IMAGE}"
    log_info "Please build the image first using build-image.sh"
    exit 1
fi

log_info "Preparing to push image..."
log_info "Local image: ${LOCAL_IMAGE}"
log_info "Remote image: ${REMOTE_IMAGE}"
log_info "Registry: ${REGISTRY}"

if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would execute the following steps:"
    log_info "1. Login to registry: ${REGISTRY}"
    log_info "2. Tag image: ${LOCAL_IMAGE} -> ${REMOTE_IMAGE}"
    log_info "3. Push image: ${REMOTE_IMAGE}"
    exit 0
fi

# Login to registry
if ! login_to_registry "${REGISTRY}"; then
    exit 1
fi

# Tag the image for the registry
log_info "Tagging image: ${LOCAL_IMAGE} -> ${REMOTE_IMAGE}"
if ! docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"; then
    log_error "Failed to tag image"
    exit 1
fi

# Push the image
log_info "Pushing image: ${REMOTE_IMAGE}"
if docker push "${REMOTE_IMAGE}"; then
    log_success "Successfully pushed image: ${REMOTE_IMAGE}"
    
    # Show push details
    log_info "Image pushed to: ${REGISTRY}"
    log_info "Repository: ${IMAGE_NAME}"
    log_info "Tag: ${TAG}"
    
    # Output for scripting
    echo "REMOTE_IMAGE=${REMOTE_IMAGE}"
    echo "REGISTRY=${REGISTRY}"
    
else
    log_error "Failed to push image: ${REMOTE_IMAGE}"
    exit 1
fi

log_success "Push completed successfully!"