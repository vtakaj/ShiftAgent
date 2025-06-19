"""
Common configuration for all environments
"""

import pulumi


def get_common_config():
    """Get common configuration values"""
    config = pulumi.Config()

    return {
        "project_name": "shift-scheduler",
        "environment": config.get("environment") or "dev",
        "location": config.get("azure-native:location") or "Japan East",
        "instance_count": config.get_int("instance_count") or 1,
        "sku_size": config.get("sku_size") or "Basic",
    }


def get_common_tags(environment: str):
    """Get common resource tags"""
    return {
        "Project": "shift-scheduler",
        "Environment": environment,
        "ManagedBy": "Pulumi",
        "Application": "shift-scheduler",
        "Owner": "shift-scheduler-team",
    }
