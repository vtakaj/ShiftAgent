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
