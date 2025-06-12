"""
Container Apps module for Azure infrastructure
"""
import pulumi
import pulumi_azure_native as azure_native
from typing import Dict, Any


class ContainerAppsModule:
    """Module for managing Azure Container Apps Environment"""
    
    def __init__(self, name: str, resource_group_name: pulumi.Input[str],
                 location: pulumi.Input[str], tags: Dict[str, Any] = None):
        """
        Initialize Container Apps module
        
        Args:
            name: Container Apps Environment name
            resource_group_name: Resource group name
            location: Azure location
            tags: Resource tags
        """
        self.name = name
        self.resource_group_name = resource_group_name
        self.location = location
        self.tags = tags or {}
        
        # Create Log Analytics Workspace for Container Apps
        self.log_analytics_workspace = azure_native.operationalinsights.Workspace(
            resource_name=f"{name}-logs",
            workspace_name=f"{name}-logs",
            resource_group_name=resource_group_name,
            location=location,
            sku=azure_native.operationalinsights.WorkspaceSkuArgs(
                name=azure_native.operationalinsights.WorkspaceSkuNameEnum.PER_GB2018
            ),
            retention_in_days=30,
            tags=self.tags
        )
        
        # Get Log Analytics workspace keys
        self.workspace_keys = pulumi.Output.all(
            self.resource_group_name,
            self.log_analytics_workspace.name
        ).apply(lambda args: azure_native.operationalinsights.get_shared_keys(
            resource_group_name=args[0],
            workspace_name=args[1]
        ))
        
        # Create Container Apps Environment
        self.environment = azure_native.app.ManagedEnvironment(
            resource_name=name,
            environment_name=name,
            resource_group_name=resource_group_name,
            location=location,
            app_logs_configuration=azure_native.app.AppLogsConfigurationArgs(
                destination="log-analytics",
                log_analytics_configuration=azure_native.app.LogAnalyticsConfigurationArgs(
                    customer_id=self.log_analytics_workspace.customer_id,
                    shared_key=self.workspace_keys.primary_shared_key
                )
            ),
            zone_redundant=False,  # Set to True for production
            tags=self.tags
        )
    
    def get_environment_id(self) -> pulumi.Output[str]:
        """Get Container Apps Environment ID"""
        return self.environment.id
    
    def get_default_domain(self) -> pulumi.Output[str]:
        """Get Container Apps Environment default domain"""
        return self.environment.default_domain