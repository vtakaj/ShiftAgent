# Networking module variables

variable "enable_vnet" {
  description = "Enable Virtual Network integration"
  type        = bool
  default     = false
}

variable "vnet_name" {
  description = "Name of the Virtual Network"
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for the Virtual Network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "location" {
  description = "Azure region for networking resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
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

variable "tags" {
  description = "Tags to apply to networking resources"
  type        = map(string)
  default     = {}
}