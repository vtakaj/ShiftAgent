# Container Apps module outputs

output "environment_name" {
  description = "Name of the Container Apps environment"
  value       = azurerm_container_app_environment.main.name
}

output "environment_id" {
  description = "ID of the Container Apps environment"
  value       = azurerm_container_app_environment.main.id
}

output "default_domain" {
  description = "Default domain of the Container Apps environment"
  value       = azurerm_container_app_environment.main.default_domain
}

output "static_ip_address" {
  description = "Static IP address of the Container Apps environment (if VNet integrated)"
  value       = azurerm_container_app_environment.main.static_ip_address
}

output "docker_bridge_cidr" {
  description = "Docker bridge CIDR of the Container Apps environment"
  value       = azurerm_container_app_environment.main.docker_bridge_cidr
}

output "platform_reserved_cidr" {
  description = "Platform reserved CIDR of the Container Apps environment"
  value       = azurerm_container_app_environment.main.platform_reserved_cidr
}

output "platform_reserved_dns_ip_address" {
  description = "Platform reserved DNS IP address of the Container Apps environment"
  value       = azurerm_container_app_environment.main.platform_reserved_dns_ip_address
}

output "is_vnet_integrated" {
  description = "Whether the Container Apps environment is VNet integrated"
  value       = var.infrastructure_subnet_id != null
}
