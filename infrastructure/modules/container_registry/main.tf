# Container Registry module

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

locals {
  # Security settings based on environment
  is_production = var.environment == "production"
  
  # Configure security settings based on environment
  public_network_access = local.is_production ? false : true
  anonymous_pull_enabled = false
  data_endpoint_enabled = local.is_production ? true : false
  
  # Vulnerability scanning only for Standard/Premium SKUs
  vulnerability_scanning_enabled = var.enable_vulnerability_scanning && var.sku != "Basic"
  
  # Zone redundancy only for Standard/Premium SKUs
  zone_redundancy_enabled = var.sku != "Basic"
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  
  # Admin user configuration
  admin_enabled = var.enable_admin_user
  
  # Security configuration
  public_network_access_enabled = local.public_network_access
  anonymous_pull_enabled        = local.anonymous_pull_enabled
  data_endpoint_enabled         = local.data_endpoint_enabled
  
  # Zone redundancy (only for Standard/Premium)
  zone_redundancy_enabled = local.zone_redundancy_enabled
  
  # Network rule bypass
  network_rule_bypass_option = "AzureServices"
  
  # Encryption (only for Premium)
  dynamic "encryption" {
    for_each = var.sku == "Premium" ? [1] : []
    content {
      enabled = true
    }
  }

  tags = var.tags
}

# Retention Policy (only for Standard/Premium SKUs)
resource "azurerm_container_registry_task" "retention_policy" {
  count                 = var.retention_days > 0 && var.sku != "Basic" ? 1 : 0
  name                  = "retention-policy"
  container_registry_id = azurerm_container_registry.main.id
  
  platform {
    os = "Linux"
  }
  
  docker_step {
    dockerfile_path      = "Dockerfile"
    context_path        = "https://github.com/Azure/acr.git#main:docs/scenarios/retention"
    context_access_token = ""
    
    arguments = {
      PURGE_AFTER = "${var.retention_days}d"
    }
  }
  
  timer_trigger {
    name     = "daily"
    schedule = "0 2 * * *" # Run daily at 2 AM
  }

  tags = var.tags
}

# Scope map for fine-grained access control (Premium only)
resource "azurerm_container_registry_scope_map" "main" {
  count                   = var.sku == "Premium" ? 1 : 0
  name                    = "${var.name}-scope-map"
  container_registry_name = azurerm_container_registry.main.name
  resource_group_name     = var.resource_group_name
  
  actions = [
    "repositories/*/content/read",
    "repositories/*/content/write",
    "repositories/*/content/delete"
  ]
}

# Token for repository-scoped authentication (Premium only)
resource "azurerm_container_registry_token" "main" {
  count                   = var.sku == "Premium" ? 1 : 0
  name                    = "${var.name}-token"
  container_registry_name = azurerm_container_registry.main.name
  resource_group_name     = var.resource_group_name
  scope_map_id           = azurerm_container_registry_scope_map.main[0].id
  enabled                = true
}