# Production environment configuration

environment = "production"
location    = "Japan East"
instance    = "001"

# Container Registry settings
registry_sku                     = "Standard"
enable_registry_admin_user       = false  # Disabled for production security
enable_vulnerability_scanning    = true   # Enabled for Standard SKU
image_retention_days            = 30

# Log Analytics settings
log_retention_days = 90

# Container Apps settings
zone_redundant = true  # Enable for production high availability