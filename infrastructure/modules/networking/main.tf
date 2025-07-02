# Virtual Network module for optional VNet integration

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  count = var.enable_vnet ? 1 : 0

  name                = var.vnet_name
  address_space       = var.vnet_address_space
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.tags
}

# Container Apps subnet
resource "azurerm_subnet" "container_apps" {
  count = var.enable_vnet ? 1 : 0

  name                 = var.container_apps_subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = var.container_apps_subnet_address_prefixes

  # Delegate subnet to Container Apps
  delegation {
    name = "Microsoft.App.environments"

    service_delegation {
      name    = "Microsoft.App/environments"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

# Network Security Group for Container Apps subnet
resource "azurerm_network_security_group" "container_apps" {
  count = var.enable_vnet ? 1 : 0

  name                = "${var.container_apps_subnet_name}-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name

  # Allow HTTPS inbound
  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow HTTP inbound (if needed for dev)
  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

# Associate NSG with Container Apps subnet
resource "azurerm_subnet_network_security_group_association" "container_apps" {
  count = var.enable_vnet ? 1 : 0

  subnet_id                 = azurerm_subnet.container_apps[0].id
  network_security_group_id = azurerm_network_security_group.container_apps[0].id
}

# Optional: Private DNS zone for Container Apps (if custom domain needed)
resource "azurerm_private_dns_zone" "container_apps" {
  count = var.enable_vnet && var.enable_private_dns ? 1 : 0

  name                = var.private_dns_zone_name
  resource_group_name = var.resource_group_name

  tags = var.tags
}

# Link Private DNS zone to VNet
resource "azurerm_private_dns_zone_virtual_network_link" "container_apps" {
  count = var.enable_vnet && var.enable_private_dns ? 1 : 0

  name                  = "${var.vnet_name}-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.container_apps[0].name
  virtual_network_id    = azurerm_virtual_network.main[0].id
  registration_enabled  = false

  tags = var.tags
}