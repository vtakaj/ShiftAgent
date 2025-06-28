#!/bin/bash
# Destroy Terraform infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"

ENVIRONMENT=${1:-"dev"}

if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "❌ Invalid environment. Use 'dev' or 'prod'"
    echo "Usage: $0 <environment>"
    echo "Example: $0 dev"
    exit 1
fi

echo "💥 Destroying ShiftAgent infrastructure ($ENVIRONMENT)"
echo "=================================================="

# Change to infrastructure directory
cd "$TERRAFORM_DIR"

# Check if Azure CLI is authenticated
echo "🔐 Checking Azure authentication..."
if ! az account show >/dev/null 2>&1; then
    echo "❌ Please authenticate with Azure CLI: az login"
    exit 1
fi

# Show current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo "📋 Using Azure subscription: $SUBSCRIPTION"

# Production safety checks
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🛡️  PRODUCTION DESTRUCTION WARNING!"
    echo "⚠️  This will destroy ALL production resources!"
    echo "⚠️  This action is IRREVERSIBLE!"
    echo ""
    read -p "Type 'DESTROY PRODUCTION' to confirm: " confirm
    if [ "$confirm" != "DESTROY PRODUCTION" ]; then
        echo "❌ Destruction cancelled"
        exit 1
    fi
else
    echo "⚠️  This will destroy all $ENVIRONMENT resources!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Destruction cancelled"
        exit 1
    fi
fi

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
fi

# Plan destruction
echo "📋 Planning destruction..."
terraform plan \
    -var-file="environments/${ENVIRONMENT}.tfvars" \
    -destroy \
    -out="${ENVIRONMENT}-destroy.tfplan"

# Apply destruction
echo "💥 Destroying infrastructure..."
terraform apply "${ENVIRONMENT}-destroy.tfplan"

# Clean up plan file
rm -f "${ENVIRONMENT}-destroy.tfplan"

echo "✅ Infrastructure destroyed successfully!"

if [ "$ENVIRONMENT" = "prod" ]; then
    echo ""
    echo "🚨 PRODUCTION INFRASTRUCTURE HAS BEEN DESTROYED!"
    echo "🚨 Make sure to update any external dependencies!"
fi
