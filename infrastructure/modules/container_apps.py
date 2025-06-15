"""
Container Apps module for Azure infrastructure
"""

from typing import Any

import pulumi
import pulumi_azure_native as azure_native

from config.naming import get_naming_convention


class ContainerAppsModule:
    """Module for managing Azure Container Apps Environment"""

    def __init__(
        self,
        resource_group_name: pulumi.Input[str],
        location: pulumi.Input[str],
        additional_tags: dict[str, Any] = None,
    ):
        """
        Initialize Container Apps module

        Args:
            resource_group_name: Resource group name
            location: Azure location
            additional_tags: Additional resource tags
        """
        self.naming = get_naming_convention()
        self.name = self.naming.container_apps_environment()
        self.log_workspace_name = self.naming.log_analytics_workspace()
        self.resource_group_name = resource_group_name
        self.location = location
        self.tags = self.naming.get_resource_tags(additional_tags)

        # Create Log Analytics Workspace for Container Apps
        self.log_analytics_workspace = azure_native.operationalinsights.Workspace(
            resource_name=self.log_workspace_name,
            workspace_name=self.log_workspace_name,
            resource_group_name=resource_group_name,
            location=location,
            sku=azure_native.operationalinsights.WorkspaceSkuArgs(
                name=azure_native.operationalinsights.WorkspaceSkuNameEnum.PER_GB2018
            ),
            retention_in_days=30,
            tags=self.tags,
        )

        # Get Log Analytics workspace keys
        self.workspace_keys = pulumi.Output.all(
            self.resource_group_name, self.log_analytics_workspace.name
        ).apply(
            lambda args: azure_native.operationalinsights.get_shared_keys(
                resource_group_name=args[0], workspace_name=args[1]
            )
        )

        # Create Container Apps Environment
        self.environment = azure_native.app.ManagedEnvironment(
            resource_name=self.name,
            environment_name=self.name,
            resource_group_name=resource_group_name,
            location=location,
            app_logs_configuration=azure_native.app.AppLogsConfigurationArgs(
                destination="log-analytics",
                log_analytics_configuration=azure_native.app.LogAnalyticsConfigurationArgs(
                    customer_id=self.log_analytics_workspace.customer_id,
                    shared_key=self.workspace_keys.primary_shared_key,
                ),
            ),
            zone_redundant=False,  # Set to True for production
            tags=self.tags,
        )

    def get_environment_id(self) -> pulumi.Output[str]:
        """Get Container Apps Environment ID"""
        return self.environment.id

    def get_default_domain(self) -> pulumi.Output[str]:
        """Get Container Apps Environment default domain"""
        return self.environment.default_domain
