#!/bin/bash
# Validate Terraform configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "✅ Validating Terraform configuration"
echo "====================================="

# Change to infrastructure directory
cd "$TERRAFORM_DIR"

# Initialize if needed (for validation)
if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform for validation..."
    terraform init -backend=false
fi

echo "🔍 Running Terraform validation..."

# Validate syntax and configuration
echo "  • Checking syntax..."
terraform validate

# Format check
echo "  • Checking formatting..."
if terraform fmt -check; then
    echo "    ✅ Formatting is correct"
else
    echo "    ⚠️  Formatting issues found (run 'terraform fmt' to fix)"
fi

# Validate environment configurations
echo "  • Validating development environment..."
if terraform plan -var-file="environments/dev.tfvars" -detailed-exitcode >/dev/null 2>&1; then
    echo "    ✅ Development configuration is valid"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 2 ]; then
        echo "    ✅ Development configuration is valid (changes detected)"
    else
        echo "    ❌ Development configuration has errors"
        terraform plan -var-file="environments/dev.tfvars"
        exit 1
    fi
fi

echo "  • Validating production environment..."
if terraform plan -var-file="environments/prod.tfvars" -detailed-exitcode >/dev/null 2>&1; then
    echo "    ✅ Production configuration is valid"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 2 ]; then
        echo "    ✅ Production configuration is valid (changes detected)"
    else
        echo "    ❌ Production configuration has errors"
        terraform plan -var-file="environments/prod.tfvars"
        exit 1
    fi
fi

# Security checks
echo "  • Running security checks..."

# Check for hardcoded secrets
echo "    • Checking for hardcoded secrets..."
if grep -r -i "password\|secret\|key" --include="*.tf" --include="*.tfvars" . | grep -v "variable\|description\|output" | grep -v "#"; then
    echo "    ⚠️  Potential hardcoded secrets found (review above)"
else
    echo "    ✅ No hardcoded secrets detected"
fi

# Check for public access
echo "    • Checking for public access configurations..."
if grep -r "public_network_access.*true\|container_access_type.*public" --include="*.tf" .; then
    echo "    ⚠️  Public access configurations found (review for security)"
else
    echo "    ✅ No public access configurations found"
fi

# Module validation
echo "  • Validating modules..."
for module_dir in modules/*/; do
    if [ -d "$module_dir" ]; then
        module_name=$(basename "$module_dir")
        echo "    • Validating module: $module_name"
        cd "$module_dir"
        terraform validate
        cd "$TERRAFORM_DIR"
    fi
done

echo ""
echo "✅ All validations passed!"
echo ""
echo "🔗 Next steps:"
echo "  • Deploy dev: ./scripts/deploy-dev.sh"
echo "  • Deploy prod: ./scripts/deploy-prod.sh"
echo "  • Format code: terraform fmt"
