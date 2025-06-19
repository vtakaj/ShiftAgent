"""
Resource Group module for Azure infrastructure
"""

from typing import Any

import pulumi
import pulumi_azure_native as azure_native
from config.naming import get_naming_convention


class ResourceGroupModule:
    """Module for managing Azure Resource Group"""

    def __init__(
        self,
        workload: str = "core",
        location: str = None,
        additional_tags: dict[str, Any] = None,
    ):
        """
        Initialize Resource Group module

        Args:
            workload: Workload name (e.g., 'core', 'data', 'web')
            location: Azure location
            additional_tags: Additional resource tags
        """
        self.naming = get_naming_convention()
        self.name = self.naming.resource_group(workload)
        self.location = location or self.naming.location
        self.tags = self.naming.get_resource_tags(additional_tags)

        # Create the resource group
        self.resource_group = azure_native.resources.ResourceGroup(
            resource_name=self.name,
            resource_group_name=self.name,
            location=self.location,
            tags=self.tags,
            opts=pulumi.ResourceOptions(
                protect=False  # Set to True in production
            ),
        )

    def get_resource_group_name(self) -> pulumi.Output[str]:
        """Get the resource group name as Output"""
        return self.resource_group.name

    def get_resource_group_id(self) -> pulumi.Output[str]:
        """Get the resource group ID as Output"""
        return self.resource_group.id
