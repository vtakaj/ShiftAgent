# Application Insights module variables

variable "name" {
  description = "Name of the Application Insights component"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the Application Insights component"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  type        = string
}

variable "application_type" {
  description = "Type of application being monitored"
  type        = string
  default     = "web"
  validation {
    condition     = contains(["web", "other", "java", "MobileCenter", "Node.JS", "store"], var.application_type)
    error_message = "Application type must be one of: web, other, java, MobileCenter, Node.JS, store."
  }
}

variable "retention_in_days" {
  description = "Number of days to retain Application Insights data"
  type        = number
  default     = 90
  validation {
    condition     = contains([30, 60, 90, 120, 180, 270, 365, 550, 730], var.retention_in_days)
    error_message = "Retention must be one of: 30, 60, 90, 120, 180, 270, 365, 550, 730 days."
  }
}

variable "sampling_percentage" {
  description = "Percentage of telemetry to sample (0-100)"
  type        = number
  default     = 100
  validation {
    condition     = var.sampling_percentage >= 0 && var.sampling_percentage <= 100
    error_message = "Sampling percentage must be between 0 and 100."
  }
}

variable "enable_smart_detection" {
  description = "Enable smart detection for anomaly detection"
  type        = bool
  default     = true
}

variable "action_group_ids" {
  description = "List of action group IDs for smart detection alerts"
  type        = list(string)
  default     = []
}

variable "create_workbook" {
  description = "Create a monitoring workbook for Container Apps"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to the Application Insights component"
  type        = map(string)
  default     = {}
}