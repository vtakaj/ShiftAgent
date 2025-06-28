# Main Terraform configuration for Shift Scheduler infrastructure

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
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Local values for common configuration
locals {
  # Project configuration
  project_name = "nss"
  environment  = var.environment
  location     = var.location
  instance     = var.instance

  # Naming convention helpers
  resource_group_name             = "rg-${local.project_name}-${local.environment}-${local.instance}"
  storage_account_name            = "st${local.project_name}data${local.environment}${local.instance}"
  container_registry_name         = "cr${local.project_name}${local.environment}${local.instance}"
  container_apps_environment_name = "cae-${local.project_name}-${local.environment}-${local.instance}"
  log_analytics_workspace_name    = "log-${local.project_name}-${local.environment}-${local.instance}"

  # Common tags following CAF naming convention
  common_tags = {
    project     = local.project_name
    environment = local.environment
    location    = local.location
    managed_by  = "terraform"
    owner       = "nss-team"
    application = "nss"
    cost_center = "${local.project_name}-${local.environment}"
    created_by  = "infrastructure-as-code"
  }
}

# Resource Group
module "resource_group" {
  source = "./modules/resource_group"

  name     = local.resource_group_name
  location = local.location
  tags = merge(local.common_tags, {
    Purpose = "Main infrastructure components"
  })
}

# Storage Account for job data and logs
module "storage" {
  source = "./modules/storage"

  name                = local.storage_account_name
  resource_group_name = module.resource_group.name
  location            = local.location
  purpose             = "data"
  tags = merge(local.common_tags, {
    Purpose = "Job data and application storage"
  })

  depends_on = [module.resource_group]
}

# Log Analytics Workspace
module "log_analytics" {
  source = "./modules/log_analytics"

  name                = local.log_analytics_workspace_name
  resource_group_name = module.resource_group.name
  location            = local.location
  retention_in_days   = var.log_retention_days
  tags = merge(local.common_tags, {
    Purpose = "Container Apps logging and monitoring"
  })

  depends_on = [module.resource_group]
}

# Container Registry
module "container_registry" {
  source = "./modules/container_registry"

  name                          = local.container_registry_name
  resource_group_name           = module.resource_group.name
  location                      = local.location
  sku                           = var.registry_sku
  environment                   = local.environment
  enable_admin_user             = var.enable_registry_admin_user
  enable_vulnerability_scanning = var.enable_vulnerability_scanning
  retention_days                = var.image_retention_days
  tags = merge(local.common_tags, {
    Purpose = "Container image registry"
  })

  depends_on = [module.resource_group]
}

# Container Apps Environment
module "container_apps" {
  source = "./modules/container_apps"

  name                        = local.container_apps_environment_name
  resource_group_name         = module.resource_group.name
  location                    = local.location
  log_analytics_workspace_id  = module.log_analytics.workspace_id
  log_analytics_workspace_key = module.log_analytics.primary_shared_key
  zone_redundant              = var.zone_redundant
  tags = merge(local.common_tags, {
    Purpose = "Container Apps hosting environment"
  })

  depends_on = [module.log_analytics]
}