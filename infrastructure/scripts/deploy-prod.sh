#!/bin/bash
# Deploy production environment using Terraform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying ShiftAgent infrastructure (Production)"
echo "======================================================"

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
echo "🛡️  Production deployment safety checks..."
read -p "⚠️  Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Initialize Terraform with production backend
echo "🔧 Initializing Terraform with production backend..."
terraform init -backend-config=backends/prod.backend.hcl -reconfigure

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
    -var-file="environments/prod.tfvars" \
    -out="prod.tfplan" \
    -detailed-exitcode

PLAN_EXIT_CODE=$?

if [ $PLAN_EXIT_CODE -eq 0 ]; then
    echo "✅ No changes needed"
    exit 0
elif [ $PLAN_EXIT_CODE -eq 2 ]; then
    echo "📝 Changes detected"
    echo ""
    echo "🔍 Please review the plan above carefully!"
    read -p "⚠️  Proceed with production deployment? (yes/no): " proceed
    if [ "$proceed" != "yes" ]; then
        echo "❌ Deployment cancelled"
        rm -f "prod.tfplan"
        exit 1
    fi
else
    echo "❌ Plan failed"
    exit 1
fi

# Apply deployment
echo "🚀 Applying changes to production..."
terraform apply "prod.tfplan"

# Clean up plan file
rm -f "prod.tfplan"

# Show outputs
echo "📊 Production deployment outputs:"
terraform output

echo "✅ Production environment deployed successfully!"
echo ""
echo "🔗 Useful commands:"
echo "  View outputs: terraform output"
echo "  Emergency destroy: ./scripts/destroy.sh prod (USE WITH EXTREME CAUTION)"
