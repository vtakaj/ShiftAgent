# Application Insights module outputs

output "application_insights_id" {
  description = "ID of the Application Insights component"
  value       = azurerm_application_insights.main.id
}

output "application_insights_name" {
  description = "Name of the Application Insights component"
  value       = azurerm_application_insights.main.name
}

output "instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "app_id" {
  description = "Application ID of the Application Insights component"
  value       = azurerm_application_insights.main.app_id
}

output "application_type" {
  description = "Application type of the Application Insights component"
  value       = azurerm_application_insights.main.application_type
}

output "workbook_id" {
  description = "ID of the monitoring workbook"
  value       = var.create_workbook ? azurerm_application_insights_workbook.container_apps[0].id : null
}