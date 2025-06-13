"""
Main Pulumi program for Shift Scheduler infrastructure
"""

import pulumi
from config.naming import get_naming_convention
from modules.container_apps import ContainerAppsModule
from modules.container_registry import ContainerRegistryModule
from modules.resource_group import ResourceGroupModule
from modules.storage import StorageModule


def main():
    """Main infrastructure deployment function"""

    # Get configuration and naming convention
    config = pulumi.Config()
    naming = get_naming_convention()

    # Create resource group using Microsoft CAF naming convention
    rg_module = ResourceGroupModule(
        workload="core",
        additional_tags={
            "Workload": "core-infrastructure",
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

    # Create container registry (for Docker images)
    registry_module = ContainerRegistryModule(
        resource_group_name=rg_module.resource_group.name,
        location=rg_module.resource_group.location,
        sku="Basic",
        additional_tags={"Purpose": "Container image registry"},
    )

    # Export registry information
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
