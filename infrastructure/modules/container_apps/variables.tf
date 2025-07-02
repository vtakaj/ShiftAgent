# Container Apps module variables

variable "name" {
  description = "Name of the Container Apps environment"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the Container Apps environment"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace for logging"
  type        = string
}

variable "log_analytics_workspace_key" {
  description = "Primary shared key of the Log Analytics workspace"
  type        = string
  sensitive   = true
}

variable "zone_redundant" {
  description = "Enable zone redundancy for the Container Apps environment"
  type        = bool
  default     = false
}

variable "infrastructure_subnet_id" {
  description = "ID of the subnet for VNet integration (optional)"
  type        = string
  default     = null
}

variable "internal_load_balancer_enabled" {
  description = "Enable internal load balancer for VNet integration"
  type        = bool
  default     = false
}

variable "workload_profiles" {
  description = "List of workload profiles for different compute requirements"
  type = list(object({
    name                  = string
    workload_profile_type = string
    maximum_count         = number
    minimum_count         = number
  }))
  default = []
}

variable "enable_diagnostic_settings" {
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

variable "tags" {
  description = "Tags to apply to the Container Apps environment"
  type        = map(string)
  default     = {}
}
