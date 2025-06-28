# Terraform backend configuration
# Note: Provider requirements are defined in main.tf

terraform {
  # Backend configuration - uncomment and configure for remote state
  # backend "azurerm" {
  #   resource_group_name  = "rg-nss-tfstate-001"
  #   storage_account_name = "stnsstfstate001"
  #   container_name       = "tfstate"
  #   key                  = "shift-scheduler.tfstate"
  # }
}