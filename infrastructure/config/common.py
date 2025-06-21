"""
Common configuration for all environments
"""

import pulumi


def get_common_config():
    """Get common configuration values"""
    config = pulumi.Config()

    return {
        "project_name": "nss",
        "environment": config.get("environment") or "dev",
        "location": config.get("azure-native:location") or "Japan East",
        "instance_count": config.get_int("instance_count") or 1,
        "sku_size": config.get("sku_size") or "Basic",
    }


def get_common_tags(environment: str):
    """Get common resource tags"""
    return {
        "project": "nss",
        "environment": environment,
        "managed_by": "pulumi",
        "application": "nss",
        "owner": "nss-team",
    }
