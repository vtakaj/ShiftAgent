# Output values for Shift Scheduler infrastructure

# Resource Group outputs
output "resource_group_name" {
  description = "Name of the resource group"
  value       = module.resource_group.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = module.resource_group.id
}

output "location" {
  description = "Azure region where resources are deployed"
  value       = module.resource_group.location
}

# Storage Account outputs
output "storage_account_name" {
  description = "Name of the storage account"
  value       = module.storage.storage_account_name
}

output "storage_primary_endpoint" {
  description = "Primary blob endpoint of the storage account"
  value       = module.storage.primary_blob_endpoint
}

output "storage_connection_string" {
  description = "Connection string for the storage account"
  value       = module.storage.connection_string
  sensitive   = true
}

output "storage_job_data_container" {
  description = "Name of the job data container"
  value       = module.storage.job_data_container_name
}

output "storage_logs_container" {
  description = "Name of the logs container"
  value       = module.storage.logs_container_name
}

# Container Registry outputs
output "container_registry_name" {
  description = "Name of the container registry"
  value       = module.container_registry.registry_name
}

output "container_registry_login_server" {
  description = "Login server URL of the container registry"
  value       = module.container_registry.login_server
}

output "container_registry_id" {
  description = "ID of the container registry"
  value       = module.container_registry.registry_id
}

output "container_registry_sku" {
  description = "SKU of the container registry"
  value       = module.container_registry.sku
}

output "container_registry_admin_username" {
  description = "Admin username for the container registry"
  value       = module.container_registry.admin_username
  sensitive   = true
}

output "container_registry_admin_password" {
  description = "Admin password for the container registry"
  value       = module.container_registry.admin_password
  sensitive   = true
}

# Container Apps Environment outputs
output "container_apps_environment_name" {
  description = "Name of the Container Apps environment"
  value       = module.container_apps.environment_name
}

output "container_apps_environment_id" {
  description = "ID of the Container Apps environment"
  value       = module.container_apps.environment_id
}

output "container_apps_default_domain" {
  description = "Default domain of the Container Apps environment"
  value       = module.container_apps.default_domain
}

# Log Analytics outputs
output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  value       = module.log_analytics.workspace_name
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = module.log_analytics.workspace_id
}

output "log_analytics_customer_id" {
  description = "Customer ID of the Log Analytics workspace"
  value       = module.log_analytics.customer_id
}

output "container_registry_registry_name" {
  description = "Legacy: Name of the container registry"
  value       = module.container_registry.registry_name
}

output "container_registry_environment" {
  description = "Environment of the container registry"
  value       = var.environment
}

# Networking outputs
output "virtual_network_id" {
  description = "ID of the Virtual Network (if VNet integration enabled)"
  value       = var.enable_vnet_integration ? module.networking.vnet_id : null
}

output "virtual_network_name" {
  description = "Name of the Virtual Network (if VNet integration enabled)"
  value       = var.enable_vnet_integration ? module.networking.vnet_name : null
}

output "container_apps_subnet_id" {
  description = "ID of the Container Apps subnet (if VNet integration enabled)"
  value       = var.enable_vnet_integration ? module.networking.container_apps_subnet_id : null
}

output "container_apps_static_ip" {
  description = "Static IP address of the Container Apps environment (if VNet integrated)"
  value       = module.container_apps.static_ip_address
}

output "is_vnet_integrated" {
  description = "Whether the Container Apps environment is VNet integrated"
  value       = module.container_apps.is_vnet_integrated
}

# Application Insights outputs
output "application_insights_id" {
  description = "ID of the Application Insights component"
  value       = module.application_insights.application_insights_id
}

output "application_insights_name" {
  description = "Name of the Application Insights component"
  value       = module.application_insights.application_insights_name
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = module.application_insights.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = module.application_insights.connection_string
  sensitive   = true
}

output "application_insights_app_id" {
  description = "Application ID of the Application Insights component"
  value       = module.application_insights.app_id
}

# Enhanced Container Apps outputs
output "container_apps_docker_bridge_cidr" {
  description = "Docker bridge CIDR of the Container Apps environment"
  value       = module.container_apps.docker_bridge_cidr
}

output "container_apps_platform_reserved_cidr" {
  description = "Platform reserved CIDR of the Container Apps environment"
  value       = module.container_apps.platform_reserved_cidr
}

output "container_apps_platform_reserved_dns_ip" {
  description = "Platform reserved DNS IP address of the Container Apps environment"
  value       = module.container_apps.platform_reserved_dns_ip_address
}
