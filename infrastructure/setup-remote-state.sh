#!/bin/bash
# Script to set up Azure remote state storage for Terraform

set -e

echo "🏗️  Setting up Azure remote state storage for Terraform..."

# Configuration
RESOURCE_GROUP="rg-nss-tfstate-001"
STORAGE_ACCOUNT="stnsstfstate001"
CONTAINER_NAME="tfstate"
LOCATION="Japan East"

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Container: $CONTAINER_NAME"
echo "  Location: $LOCATION"
echo ""

# Check if Azure CLI is logged in
if ! az account show >/dev/null 2>&1; then
    echo "❌ Please log in to Azure CLI first:"
    echo "   az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"

# Create resource group for Terraform state
echo "🏗️  Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags purpose="terraform-state" project="nss" managed_by="terraform"

echo "✅ Resource group created"

# Create storage account for Terraform state
echo "🗄️  Creating storage account..."
az storage account create \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --kind StorageV2 \
    --access-tier Hot \
    --https-only true \
    --min-tls-version TLS1_2 \
    --allow-blob-public-access false \
    --tags purpose="terraform-state" project="nss" managed_by="terraform"

echo "✅ Storage account created"

# Create blob container for state files
echo "📦 Creating blob container..."
az storage container create \
    --name "$CONTAINER_NAME" \
    --account-name "$STORAGE_ACCOUNT" \
    --public-access off

echo "✅ Blob container created"

# Enable versioning for state file protection
echo "🔄 Enabling blob versioning..."
az storage account blob-service-properties update \
    --account-name "$STORAGE_ACCOUNT" \
    --enable-versioning true

echo "✅ Blob versioning enabled"

echo ""
echo "🎉 Remote state storage setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Uncomment the backend configuration in versions.tf"
echo "2. Run 'terraform init' to migrate state to Azure"
echo "3. Commit and push the updated versions.tf"
echo ""
echo "🔐 Backend configuration to uncomment:"
echo 'backend "azurerm" {'
echo '  resource_group_name  = "'$RESOURCE_GROUP'"'
echo '  storage_account_name = "'$STORAGE_ACCOUNT'"'
echo '  container_name       = "'$CONTAINER_NAME'"'
echo '  key                  = "shift-scheduler.tfstate"'
echo '}'
