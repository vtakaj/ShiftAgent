# Terraform backend configuration
# Note: Provider requirements are defined in main.tf

terraform {
  # Backend configuration for remote state storage in Azure
  # Use environment-specific backend files:
  # - Development: terraform init -backend-config=backends/dev.backend.hcl
  # - Production:  terraform init -backend-config=backends/prod.backend.hcl
  backend "azurerm" {}
}
