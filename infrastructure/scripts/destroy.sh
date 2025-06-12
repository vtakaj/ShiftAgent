#!/bin/bash

# Destroy infrastructure
set -e

echo "🗑️  Destroying Shift Scheduler Infrastructure"

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Ensure we're in the correct directory
if [ ! -f "Pulumi.yaml" ]; then
    echo "❌ Error: Not in infrastructure directory"
    exit 1
fi

# Get current stack
STACK=$(pulumi stack --show-name 2>/dev/null || echo "none")

if [ "$STACK" = "none" ]; then
    echo "❌ Error: No stack selected"
    echo "💡 Use: pulumi stack select <stack-name>"
    exit 1
fi

echo "📋 Current stack: $STACK"

# Show resources that will be destroyed
echo "👀 Resources that will be destroyed:"
pulumi preview --diff

# Warning and confirmation
echo ""
echo "⚠️  WARNING: This will permanently delete all resources in stack '$STACK'!"
echo "⚠️  This action cannot be undone!"
echo ""

read -p "🤔 Are you absolutely sure you want to destroy all resources? Type 'destroy' to confirm: " confirm

if [ "$confirm" != "destroy" ]; then
    echo "❌ Destruction cancelled"
    exit 0
fi

# Final confirmation for production
if [ "$STACK" = "prod" ] || [ "$STACK" = "production" ]; then
    echo ""
    echo "🚨 PRODUCTION ENVIRONMENT DETECTED!"
    echo "🚨 This will destroy the production infrastructure!"
    echo ""
    read -p "⚠️  Type 'destroy-production' to confirm: " prod_confirm
    
    if [ "$prod_confirm" != "destroy-production" ]; then
        echo "❌ Production destruction cancelled"
        exit 0
    fi
fi

# Destroy infrastructure
echo "🗑️  Destroying infrastructure..."
pulumi destroy --yes

echo "✅ Infrastructure destroyed successfully"
echo "💡 To remove the stack completely, run: pulumi stack rm $STACK"