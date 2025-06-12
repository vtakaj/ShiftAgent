"""
Resource Group module for Azure infrastructure
"""
import pulumi
import pulumi_azure_native as azure_native
from typing import Dict, Any


class ResourceGroupModule:
    """Module for managing Azure Resource Group"""
    
    def __init__(self, name: str, location: str, tags: Dict[str, Any] = None):
        """
        Initialize Resource Group module
        
        Args:
            name: Resource group name
            location: Azure location
            tags: Resource tags
        """
        self.name = name
        self.location = location
        self.tags = tags or {}
        
        # Create the resource group
        self.resource_group = azure_native.resources.ResourceGroup(
            resource_name=name,
            location=location,
            tags=self.tags,
            opts=pulumi.ResourceOptions(
                protect=False  # Set to True in production
            )
        )
    
    def get_resource_group_name(self) -> pulumi.Output[str]:
        """Get the resource group name as Output"""
        return self.resource_group.name
    
    def get_resource_group_id(self) -> pulumi.Output[str]:
        """Get the resource group ID as Output"""
        return self.resource_group.id