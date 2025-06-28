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