# Networking module outputs

output "vnet_id" {
  description = "ID of the Virtual Network"
  value       = var.enable_vnet ? azurerm_virtual_network.main[0].id : null
}

output "vnet_name" {
  description = "Name of the Virtual Network"
  value       = var.enable_vnet ? azurerm_virtual_network.main[0].name : null
}

output "container_apps_subnet_id" {
  description = "ID of the Container Apps subnet"
  value       = var.enable_vnet ? azurerm_subnet.container_apps[0].id : null
}

output "container_apps_subnet_name" {
  description = "Name of the Container Apps subnet"
  value       = var.enable_vnet ? azurerm_subnet.container_apps[0].name : null
}

output "network_security_group_id" {
  description = "ID of the Container Apps Network Security Group"
  value       = var.enable_vnet ? azurerm_network_security_group.container_apps[0].id : null
}

output "private_dns_zone_id" {
  description = "ID of the private DNS zone"
  value       = var.enable_vnet && var.enable_private_dns ? azurerm_private_dns_zone.container_apps[0].id : null
}

output "private_dns_zone_name" {
  description = "Name of the private DNS zone"
  value       = var.enable_vnet && var.enable_private_dns ? azurerm_private_dns_zone.container_apps[0].name : null
}