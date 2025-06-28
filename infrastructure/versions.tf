# Terraform and provider version constraints

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  
  # Backend configuration - uncomment and configure for remote state
  # backend "azurerm" {
  #   resource_group_name  = "rg-nss-tfstate-001"
  #   storage_account_name = "stnsstfstate001"
  #   container_name       = "tfstate"
  #   key                  = "shift-scheduler.tfstate"
  # }
}