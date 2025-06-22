"""
Storage module for Azure infrastructure
"""

from datetime import datetime, timedelta
from typing import Any

import pulumi
import pulumi_azure_native as azure_native
from config.naming import get_naming_convention


class StorageModule:
    """Module for managing Azure Storage Account"""

    def __init__(
        self,
        resource_group_name: pulumi.Input[str],
        location: pulumi.Input[str],
        purpose: str = "data",
        additional_tags: dict[str, Any] = None,
    ):
        """
        Initialize Storage module

        Args:
            resource_group_name: Resource group name
            location: Azure location
            purpose: Storage purpose (e.g., 'data', 'logs', 'backup')
            additional_tags: Additional resource tags
        """
        self.naming = get_naming_convention()
        self.name = self.naming.storage_account(purpose)
        self.resource_group_name = resource_group_name
        self.location = location
        self.tags = self.naming.get_resource_tags(additional_tags)

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
            tags=self.tags,
        )

        # Create blob container for job data
        self.job_data_container = azure_native.storage.BlobContainer(
            resource_name=f"{self.name}-job-data",
            container_name="job-data",
            account_name=self.storage_account.name,
            resource_group_name=resource_group_name,
            public_access=azure_native.storage.PublicAccess.NONE,
        )

        # Create blob container for application logs
        self.logs_container = azure_native.storage.BlobContainer(
            resource_name=f"{self.name}-logs",
            container_name="logs",
            account_name=self.storage_account.name,
            resource_group_name=resource_group_name,
            public_access=azure_native.storage.PublicAccess.NONE,
        )

    def create_sas_token(
        self,
        container_name: str = "job-data",
        permissions: str = "rwd",
        hours: int = 24,
    ) -> pulumi.Output[str]:
        """
        Generate SAS token for container access

        Args:
            container_name: Name of the container
            permissions: Permissions string (r=read, w=write, d=delete, l=list)
            hours: Token validity in hours
        """

        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(hours=hours)

        return pulumi.Output.all(
            self.resource_group_name, self.storage_account.name, container_name
        ).apply(
            lambda args: azure_native.storage.list_storage_account_service_sas(
                resource_group_name=args[0],
                account_name=args[1],
                parameters=azure_native.storage.ServiceSasParametersArgs(
                    canonicalized_resource=f"/blob/{args[1]}/{args[2]}",
                    resource=azure_native.storage.SignedResource.C,  # Container
                    permissions=azure_native.storage.Permissions(permissions),
                    shared_access_start_time=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    shared_access_expiry_time=expiry_time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    protocols=azure_native.storage.HttpProtocol.HTTPS,
                ),
            ).service_sas_token
        )

    def get_connection_string(self) -> pulumi.Output[str]:
        """Get storage account connection string"""
        keys = pulumi.Output.all(
            self.resource_group_name, self.storage_account.name
        ).apply(
            lambda args: azure_native.storage.list_storage_account_keys(
                resource_group_name=args[0], account_name=args[1]
            )
        )

        return pulumi.Output.all(self.storage_account.name, keys).apply(
            lambda args: f"DefaultEndpointsProtocol=https;AccountName={args[0]};AccountKey={args[1].keys[0].value};EndpointSuffix=core.windows.net"
        )

    def get_primary_access_key(self) -> pulumi.Output[str]:
        """Get storage account primary access key"""
        return pulumi.Output.all(
            self.resource_group_name, self.storage_account.name
        ).apply(
            lambda args: azure_native.storage.list_storage_account_keys(
                resource_group_name=args[0], account_name=args[1]
            )
            .keys[0]
            .value
        )
