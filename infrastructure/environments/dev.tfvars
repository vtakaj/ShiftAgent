# Development environment configuration

environment = "dev"
location    = "Japan East"
instance    = "001"

# Container Registry settings
registry_sku                  = "Basic"
enable_registry_admin_user    = true
enable_vulnerability_scanning = false # Not available for Basic SKU
image_retention_days          = 7

# Log Analytics settings
log_retention_days = 30

# Container Apps settings
zone_redundant = false

# VNet Integration (optional - disabled for basic dev setup)
enable_vnet_integration = false
# Uncomment and configure if VNet integration is needed:
# vnet_address_space = ["10.0.0.0/16"]
# container_apps_subnet_address_prefixes = ["10.0.1.0/24"]
# enable_private_dns = false
# internal_load_balancer_enabled = false

# Application Insights settings
application_insights_type = "web"
application_insights_retention_days = 90
application_insights_sampling_percentage = 100
enable_smart_detection = true
create_monitoring_workbook = true

# Enhanced diagnostics
enable_container_apps_diagnostics = true
diagnostic_retention_enabled = true
diagnostic_retention_days = 30

# Workload profiles (empty for dev - uses consumption plan)
container_apps_workload_profiles = []
