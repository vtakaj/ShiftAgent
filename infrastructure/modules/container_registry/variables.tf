# Container Registry module variables

variable "name" {
  description = "Name of the container registry"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the container registry"
  type        = string
}

variable "sku" {
  description = "Container Registry SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Basic"
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku)
    error_message = "SKU must be one of: Basic, Standard, Premium."
  }
}

variable "environment" {
  description = "Environment name (development, production)"
  type        = string
}

variable "enable_admin_user" {
  description = "Enable admin user for the container registry (disable for production)"
  type        = bool
  default     = true
}

variable "enable_vulnerability_scanning" {
  description = "Enable vulnerability scanning (requires Standard/Premium SKU)"
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Number of days to retain images (0 = unlimited)"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to the container registry"
  type        = map(string)
  default     = {}
}