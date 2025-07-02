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
  
  # VNet integration (optional)
  infrastructure_subnet_id   = var.infrastructure_subnet_id
  internal_load_balancer_enabled = var.internal_load_balancer_enabled
  
  # Zone redundancy (requires VNet integration)
  zone_redundancy_enabled    = var.infrastructure_subnet_id != null ? var.zone_redundant : false

  # Workload profiles for different compute requirements
  dynamic "workload_profile" {
    for_each = var.workload_profiles
    content {
      name                  = workload_profile.value.name
      workload_profile_type = workload_profile.value.workload_profile_type
      maximum_count         = workload_profile.value.maximum_count
      minimum_count         = workload_profile.value.minimum_count
    }
  }

  tags = var.tags
}

# Diagnostic settings for Container Apps Environment
resource "azurerm_monitor_diagnostic_setting" "container_apps_env" {
  count = var.enable_diagnostic_settings ? 1 : 0

  name                       = "${var.name}-diagnostics"
  target_resource_id         = azurerm_container_app_environment.main.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "ContainerAppConsoleLogs"
  }

  enabled_log {
    category = "ContainerAppSystemLogs"
  }

  metric {
    category = "AllMetrics"
    enabled  = true

    retention_policy {
      enabled = var.diagnostic_retention_enabled
      days    = var.diagnostic_retention_days
    }
  }
}
