#!/bin/bash

# Deploy development environment
set -e

echo "🚀 Deploying Shift Scheduler Infrastructure - Development"

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

# Initialize and select dev stack
echo "🔧 Setting up development stack..."
pulumi stack init dev --non-interactive || true
pulumi stack select dev

# Set development configuration
echo "⚙️ Configuring development environment..."
pulumi config set azure-native:location "East US"
pulumi config set shift-scheduler-infra:environment "development"
pulumi config set shift-scheduler-infra:instance_count 1
pulumi config set shift-scheduler-infra:sku_size "Basic"

# Preview changes
echo "👀 Previewing changes..."
pulumi preview

# Ask for confirmation
read -p "🤔 Do you want to proceed with deployment? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Deploy infrastructure
echo "🚀 Deploying infrastructure..."
pulumi up --yes

# Show outputs
echo "✅ Deployment complete! Here are the outputs:"
pulumi stack output

echo "🎉 Development environment is ready!"
echo "📋 Next steps:"
echo "  1. Configure container registry credentials"
echo "  2. Build and push Docker images"
echo "  3. Deploy application to Container Apps"