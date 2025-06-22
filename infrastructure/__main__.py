"""
Main Pulumi program for Shift Scheduler infrastructure
"""

import pulumi
from modules.container_apps import ContainerAppsModule
from modules.container_registry import ContainerRegistryModule
from modules.resource_group import ResourceGroupModule
from modules.storage import StorageModule


def main():
    """Main infrastructure deployment function"""

    # Get configuration and naming convention
    # config = pulumi.Config()  # Reserved for future use
    # naming = get_naming_convention()  # Reserved for future use

    # Create resource group using Microsoft CAF naming convention
    rg_module = ResourceGroupModule(
        additional_tags={
            "Purpose": "Main infrastructure components",
        },
    )

    # Export resource group information
    pulumi.export("resource_group_name", rg_module.resource_group.name)
    pulumi.export("resource_group_id", rg_module.resource_group.id)
    pulumi.export("location", rg_module.resource_group.location)

    # Create storage account (for job data and future use)
    storage_module = StorageModule(
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        purpose="data",
        additional_tags={"Purpose": "Job data and application storage"},
    )

    # Export storage information
    pulumi.export("storage_account_name", storage_module.storage_account.name)
    pulumi.export(
        "storage_primary_endpoint",
        storage_module.storage_account.primary_endpoints.blob,
    )
    pulumi.export("storage_connection_string", storage_module.get_connection_string())
    pulumi.export("storage_job_data_container", storage_module.job_data_container.name)
    pulumi.export("storage_logs_container", storage_module.logs_container.name)

    # Get configuration for container registry
    config = pulumi.Config()
    environment = config.get("environment") or "development"
    sku_size = config.get("sku_size") or "Basic"
    
    # Map sku_size to registry SKU (Basic -> Basic, Standard -> Standard, Premium -> Premium)
    registry_sku = sku_size if sku_size in ["Basic", "Standard", "Premium"] else "Basic"
    
    # Create container registry (for Docker images)
    registry_module = ContainerRegistryModule(
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        sku=registry_sku,
        environment=environment,
        enable_admin_user=environment != "production",  # Disable admin user in production
        enable_vulnerability_scanning=registry_sku != "Basic",  # Enable for Standard/Premium
        retention_days=30 if environment == "production" else 7,  # Longer retention in production
        additional_tags={"Purpose": "Container image registry"},
    )

    # Export registry information
    registry_outputs = registry_module.get_outputs()
    for key, value in registry_outputs.items():
        pulumi.export(f"container_registry_{key}", value)
    
    # Export legacy outputs for backward compatibility
    pulumi.export("container_registry_name", registry_module.registry.name)
    pulumi.export(
        "container_registry_login_server", registry_module.registry.login_server
    )

    # Create Container Apps environment (for application hosting)
    container_apps_module = ContainerAppsModule(
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        additional_tags={"Purpose": "Container Apps hosting environment"},
    )

    # Export Container Apps information
    pulumi.export(
        "container_apps_environment_name", container_apps_module.environment.name
    )
    pulumi.export("container_apps_environment_id", container_apps_module.environment.id)


if __name__ == "__main__":
    main()
