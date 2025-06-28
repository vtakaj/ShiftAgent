# Container Apps Environment module

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = var.name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = var.log_analytics_workspace_id
  # Note: zone_redundancy_enabled requires infrastructure_subnet_id
  # Disabled for basic deployment without custom VNet
  # zone_redundancy_enabled    = var.zone_redundant

  tags = var.tags
}
