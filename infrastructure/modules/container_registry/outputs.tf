# Container Registry module outputs

output "registry_name" {
  description = "Name of the container registry"
  value       = azurerm_container_registry.main.name
}

output "registry_id" {
  description = "ID of the container registry"
  value       = azurerm_container_registry.main.id
}

output "login_server" {
  description = "Login server URL of the container registry"
  value       = azurerm_container_registry.main.login_server
}

output "sku" {
  description = "SKU of the container registry"
  value       = azurerm_container_registry.main.sku
}

output "admin_username" {
  description = "Admin username for the container registry"
  value       = var.enable_admin_user ? azurerm_container_registry.main.admin_username : null
  sensitive   = true
}

output "admin_password" {
  description = "Admin password for the container registry"
  value       = var.enable_admin_user ? azurerm_container_registry.main.admin_password : null
  sensitive   = true
}

output "admin_enabled" {
  description = "Whether admin user is enabled"
  value       = azurerm_container_registry.main.admin_enabled
}

# Scope map and token outputs (Premium only)
output "scope_map_id" {
  description = "ID of the scope map (Premium SKU only)"
  value       = var.sku == "Premium" ? azurerm_container_registry_scope_map.main[0].id : null
}

output "token_id" {
  description = "ID of the authentication token (Premium SKU only)"
  value       = var.sku == "Premium" ? azurerm_container_registry_token.main[0].id : null
}