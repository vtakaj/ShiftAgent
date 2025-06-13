"""
Container Registry module for Azure infrastructure
"""

from typing import Any

import pulumi
import pulumi_azure_native as azure_native

from ..config.naming import get_naming_convention


class ContainerRegistryModule:
    """Module for managing Azure Container Registry"""

    def __init__(
        self,
        resource_group_name: pulumi.Input[str],
        location: pulumi.Input[str],
        sku: str = "Basic",
        additional_tags: dict[str, Any] = None,
    ):
        """
        Initialize Container Registry module

        Args:
            resource_group_name: Resource group name
            location: Azure location
            sku: Registry SKU (Basic, Standard, Premium)
            additional_tags: Additional resource tags
        """
        self.naming = get_naming_convention()
        self.name = self.naming.container_registry()
        self.resource_group_name = resource_group_name
        self.location = location
        self.sku = sku
        self.tags = self.naming.get_resource_tags(additional_tags)

        # Create container registry
        self.registry = azure_native.containerregistry.Registry(
            resource_name=self.name,
            registry_name=self.name,
            resource_group_name=resource_group_name,
            location=location,
            sku=azure_native.containerregistry.SkuArgs(name=sku),
            admin_user_enabled=True,  # Enable for simplicity, use managed identity in production
            public_network_access=azure_native.containerregistry.PublicNetworkAccess.ENABLED,
            zone_redundancy=azure_native.containerregistry.ZoneRedundancy.DISABLED
            if sku == "Basic"
            else azure_native.containerregistry.ZoneRedundancy.ENABLED,
            tags=self.tags,
        )

    def get_admin_credentials(self) -> pulumi.Output[dict]:
        """Get admin credentials for the registry"""
        return pulumi.Output.all(self.resource_group_name, self.registry.name).apply(
            lambda args: azure_native.containerregistry.list_registry_credentials(
                resource_group_name=args[0], registry_name=args[1]
            )
        )

    def get_login_server(self) -> pulumi.Output[str]:
        """Get registry login server URL"""
        return self.registry.login_server
