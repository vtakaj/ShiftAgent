#!/bin/bash

# Deploy production environment
set -e

echo "🚀 Deploying Shift Scheduler Infrastructure - Production"

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Ensure we're in the correct directory
if [ ! -f "Pulumi.yaml" ]; then
    echo "❌ Error: Not in infrastructure directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize and select prod stack
echo "🔧 Setting up production stack..."
pulumi stack init prod --non-interactive || true
pulumi stack select prod

# Set production configuration
echo "⚙️ Configuring production environment..."
pulumi config set azure-native:location "East US"
pulumi config set shift-scheduler-infra:environment "production"
pulumi config set shift-scheduler-infra:instance_count 3
pulumi config set shift-scheduler-infra:sku_size "Standard"

# Preview changes
echo "👀 Previewing changes..."
pulumi preview

# Ask for confirmation with additional warning
echo "⚠️  WARNING: You are about to deploy to PRODUCTION!"
echo "⚠️  This will create billable Azure resources."
read -p "🤔 Are you sure you want to proceed? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Deploy infrastructure
echo "🚀 Deploying production infrastructure..."
pulumi up --yes

# Show outputs
echo "✅ Deployment complete! Here are the outputs:"
pulumi stack output

echo "🎉 Production environment is ready!"
echo "📋 Next steps:"
echo "  1. Configure container registry credentials"
echo "  2. Set up CI/CD pipeline"
echo "  3. Configure monitoring and alerts"
echo "  4. Set up backup and disaster recovery"