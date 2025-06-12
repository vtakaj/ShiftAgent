"""
Main Pulumi program for Shift Scheduler infrastructure
"""
import pulumi
from modules.resource_group import ResourceGroupModule
from modules.storage import StorageModule
from modules.container_registry import ContainerRegistryModule
from modules.container_apps import ContainerAppsModule


def main():
    """Main infrastructure deployment function"""
    
    # Get configuration
    config = pulumi.Config()
    stack = pulumi.get_stack()
    project = pulumi.get_project()
    
    # Common tags
    common_tags = {
        "Project": project,
        "Stack": stack,
        "ManagedBy": "Pulumi",
        "Application": "shift-scheduler"
    }
    
    # Create resource group
    rg_module = ResourceGroupModule(
        name=f"rg-{project}-{stack}",
        location=config.get("azure-native:location") or "East US",
        tags=common_tags
    )
    
    # Export resource group information
    pulumi.export("resource_group_name", rg_module.resource_group.name)
    pulumi.export("resource_group_id", rg_module.resource_group.id)
    pulumi.export("location", rg_module.resource_group.location)
    
    # Create storage account (for job data and future use)
    storage_module = StorageModule(
        name=f"st{project.replace('-', '')}{stack}",
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        tags=common_tags
    )
    
    # Export storage information
    pulumi.export("storage_account_name", storage_module.storage_account.name)
    pulumi.export("storage_primary_endpoint", storage_module.storage_account.primary_endpoints.blob)
    
    # Create container registry (for Docker images)
    registry_module = ContainerRegistryModule(
        name=f"cr{project.replace('-', '')}{stack}",
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        sku="Basic",
        tags=common_tags
    )
    
    # Export registry information
    pulumi.export("container_registry_name", registry_module.registry.name)
    pulumi.export("container_registry_login_server", registry_module.registry.login_server)
    
    # Create Container Apps environment (for application hosting)
    container_apps_module = ContainerAppsModule(
        name=f"cae-{project}-{stack}",
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        tags=common_tags
    )
    
    # Export Container Apps information
    pulumi.export("container_apps_environment_name", container_apps_module.environment.name)
    pulumi.export("container_apps_environment_id", container_apps_module.environment.id)


if __name__ == "__main__":
    main()