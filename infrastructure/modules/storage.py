"""
Storage module for Azure infrastructure
"""
import pulumi
import pulumi_azure_native as azure_native
from typing import Dict, Any


class StorageModule:
    """Module for managing Azure Storage Account"""
    
    def __init__(self, name: str, resource_group_name: pulumi.Input[str], 
                 location: pulumi.Input[str], tags: Dict[str, Any] = None):
        """
        Initialize Storage module
        
        Args:
            name: Storage account name (must be globally unique, lowercase, alphanumeric)
            resource_group_name: Resource group name
            location: Azure location
            tags: Resource tags
        """
        self.name = name.lower()[:24]  # Storage account names must be <= 24 chars
        self.resource_group_name = resource_group_name
        self.location = location
        self.tags = tags or {}
        
        # Create storage account
        self.storage_account = azure_native.storage.StorageAccount(
            resource_name=self.name,
            account_name=self.name,
            resource_group_name=resource_group_name,
            location=location,
            sku=azure_native.storage.SkuArgs(
                name=azure_native.storage.SkuName.STANDARD_LRS
            ),
            kind=azure_native.storage.Kind.STORAGE_V2,
            access_tier=azure_native.storage.AccessTier.HOT,
            allow_blob_public_access=False,
            enable_https_traffic_only=True,
            minimum_tls_version=azure_native.storage.MinimumTlsVersion.TLS1_2,
            tags=self.tags
        )
        
        # Create blob container for job data
        self.job_data_container = azure_native.storage.BlobContainer(
            resource_name=f"{self.name}-job-data",
            container_name="job-data",
            account_name=self.storage_account.name,
            resource_group_name=resource_group_name,
            public_access=azure_native.storage.PublicAccess.NONE
        )
        
        # Create blob container for application logs
        self.logs_container = azure_native.storage.BlobContainer(
            resource_name=f"{self.name}-logs",
            container_name="logs",
            account_name=self.storage_account.name,
            resource_group_name=resource_group_name,
            public_access=azure_native.storage.PublicAccess.NONE
        )
    
    def get_connection_string(self) -> pulumi.Output[str]:
        """Get storage account connection string"""
        return pulumi.Output.all(
            self.resource_group_name,
            self.storage_account.name
        ).apply(lambda args: azure_native.storage.list_storage_account_keys(
            resource_group_name=args[0],
            account_name=args[1]
        ).keys[0].value.apply(lambda key: f"DefaultEndpointsProtocol=https;AccountName={args[1]};AccountKey={key};EndpointSuffix=core.windows.net"))
    
    def get_primary_access_key(self) -> pulumi.Output[str]:
        """Get storage account primary access key"""
        return pulumi.Output.all(
            self.resource_group_name,
            self.storage_account.name
        ).apply(lambda args: azure_native.storage.list_storage_account_keys(
            resource_group_name=args[0],
            account_name=args[1]
        ).keys[0].value)