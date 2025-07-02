# Input variables for Shift Scheduler infrastructure

variable "environment" {
  description = "Environment name (development, production)"
  type        = string
  validation {
    condition     = contains(["development", "production", "dev", "prod"], var.environment)
    error_message = "Environment must be one of: development, production, dev, prod."
  }
}

variable "location" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "Japan East"
}

variable "instance" {
  description = "Instance identifier for resource naming"
  type        = string
  default     = "001"
}

variable "registry_sku" {
  description = "Container Registry SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Basic"
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.registry_sku)
    error_message = "Registry SKU must be one of: Basic, Standard, Premium."
  }
}

variable "enable_registry_admin_user" {
  description = "Enable admin user for Container Registry (disable for production)"
  type        = bool
  default     = true
}

variable "enable_vulnerability_scanning" {
  description = "Enable vulnerability scanning for Container Registry (requires Standard/Premium)"
  type        = bool
  default     = true
}

variable "image_retention_days" {
  description = "Number of days to retain container images (0 = unlimited)"
  type        = number
  default     = 7
}

variable "log_retention_days" {
  description = "Log Analytics workspace data retention in days"
  type        = number
  default     = 30
}

variable "zone_redundant" {
  description = "Enable zone redundancy for Container Apps Environment"
  type        = bool
  default     = false
}

# VNet Integration Variables
variable "enable_vnet_integration" {
  description = "Enable VNet integration for Container Apps"
  type        = bool
  default     = false
}

variable "vnet_address_space" {
  description = "Address space for the Virtual Network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "container_apps_subnet_name" {
  description = "Name of the Container Apps subnet"
  type        = string
  default     = "container-apps-subnet"
}

variable "container_apps_subnet_address_prefixes" {
  description = "Address prefixes for the Container Apps subnet"
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

variable "enable_private_dns" {
  description = "Enable private DNS zone for Container Apps"
  type        = bool
  default     = false
}

variable "private_dns_zone_name" {
  description = "Name of the private DNS zone"
  type        = string
  default     = "privatelink.azurecontainerapps.io"
}

variable "internal_load_balancer_enabled" {
  description = "Enable internal load balancer for VNet integration"
  type        = bool
  default     = false
}

# Application Insights Variables
variable "application_insights_type" {
  description = "Type of application being monitored"
  type        = string
  default     = "web"
}

variable "application_insights_retention_days" {
  description = "Number of days to retain Application Insights data"
  type        = number
  default     = 90
}

variable "application_insights_sampling_percentage" {
  description = "Percentage of telemetry to sample (0-100)"
  type        = number
  default     = 100
}

variable "enable_smart_detection" {
  description = "Enable smart detection for anomaly detection"
  type        = bool
  default     = true
}

variable "create_monitoring_workbook" {
  description = "Create a monitoring workbook for Container Apps"
  type        = bool
  default     = true
}

# Container Apps Advanced Configuration
variable "container_apps_workload_profiles" {
  description = "List of workload profiles for different compute requirements"
  type = list(object({
    name                  = string
    workload_profile_type = string
    maximum_count         = number
    minimum_count         = number
  }))
  default = []
}

variable "enable_container_apps_diagnostics" {
  description = "Enable diagnostic settings for Container Apps environment"
  type        = bool
  default     = true
}

variable "diagnostic_retention_enabled" {
  description = "Enable retention policy for diagnostic settings"
  type        = bool
  default     = true
}

variable "diagnostic_retention_days" {
  description = "Number of days to retain diagnostic data"
  type        = number
  default     = 30
}
