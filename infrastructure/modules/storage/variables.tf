# Storage module variables

variable "name" {
  description = "Name of the storage account"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the storage account"
  type        = string
}

variable "purpose" {
  description = "Purpose of the storage account (e.g., 'data', 'logs', 'backup')"
  type        = string
  default     = "data"
}

variable "tags" {
  description = "Tags to apply to the storage account"
  type        = map(string)
  default     = {}
}
