# Production environment configuration

environment = "prod"
location    = "Japan East"
instance    = "001"

# Container Registry settings
registry_sku                  = "Standard"
enable_registry_admin_user    = false # Disabled for production security
enable_vulnerability_scanning = true  # Enabled for Standard SKU
image_retention_days          = 30

# Log Analytics settings
log_retention_days = 90

# Container Apps settings
zone_redundant = true # Enable for production high availability

# VNet Integration (recommended for production)
enable_vnet_integration = true
vnet_address_space = ["10.1.0.0/16"]
container_apps_subnet_address_prefixes = ["10.1.1.0/24"]
enable_private_dns = true
internal_load_balancer_enabled = true

# Application Insights settings
application_insights_type = "web"
application_insights_retention_days = 180
application_insights_sampling_percentage = 75  # Reduce sampling for cost optimization
enable_smart_detection = true
create_monitoring_workbook = true

# Enhanced diagnostics
enable_container_apps_diagnostics = true
diagnostic_retention_enabled = true
diagnostic_retention_days = 90

# Workload profiles for production scaling
container_apps_workload_profiles = [
  {
    name                  = "general-purpose"
    workload_profile_type = "D4"
    minimum_count         = 1
    maximum_count         = 10
  }
]
