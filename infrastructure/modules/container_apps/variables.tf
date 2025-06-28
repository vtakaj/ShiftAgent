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

variable "tags" {
  description = "Tags to apply to the Container Apps environment"
  type        = map(string)
  default     = {}
}
