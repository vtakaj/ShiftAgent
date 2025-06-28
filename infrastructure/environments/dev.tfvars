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
