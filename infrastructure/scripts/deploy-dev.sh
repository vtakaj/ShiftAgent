#!/bin/bash
# Deploy development environment using Terraform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying Shift Scheduler infrastructure (Development)"
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

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
else
    echo "🔧 Terraform already initialized"
fi

# Validate configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Format check
echo "🎨 Checking Terraform formatting..."
if ! terraform fmt -check; then
    echo "⚠️  Formatting issues found. Running terraform fmt..."
    terraform fmt
fi

# Plan deployment
echo "📋 Planning deployment..."
terraform plan \
    -var-file="environments/dev.tfvars" \
    -out="dev.tfplan" \
    -detailed-exitcode

PLAN_EXIT_CODE=$?

if [ $PLAN_EXIT_CODE -eq 0 ]; then
    echo "✅ No changes needed"
    exit 0
elif [ $PLAN_EXIT_CODE -eq 2 ]; then
    echo "📝 Changes detected, proceeding with deployment..."
else
    echo "❌ Plan failed"
    exit 1
fi

# Apply deployment
echo "🚀 Applying changes..."
terraform apply "dev.tfplan"

# Clean up plan file
rm -f "dev.tfplan"

# Show outputs
echo "📊 Deployment outputs:"
terraform output

echo "✅ Development environment deployed successfully!"
echo ""
echo "🔗 Useful commands:"
echo "  View outputs: terraform output"
echo "  Destroy: ./scripts/destroy.sh dev"
echo "  Update: ./scripts/deploy-dev.sh"
