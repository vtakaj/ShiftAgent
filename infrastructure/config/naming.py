"""
Azure resource naming conventions following Microsoft CAF (Cloud Adoption Framework)
Reference: https://docs.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming
"""

import pulumi

# Azure resource type abbreviations according to Microsoft CAF
RESOURCE_ABBREVIATIONS = {
    "resource_group": "rg",
    "storage_account": "st",
    "container_registry": "cr",
    "container_apps_environment": "cae",
    "container_app": "ca",
    "log_analytics_workspace": "log",
    "key_vault": "kv",
    "application_insights": "appi",
    "app_service_plan": "asp",
    "virtual_network": "vnet",
    "subnet": "snet",
    "network_security_group": "nsg",
    "public_ip": "pip",
    "load_balancer": "lb",
    "postgresql_server": "psql",
    "postgresql_database": "psqldb",
}

# Environment abbreviations
ENVIRONMENT_ABBREVIATIONS = {
    "development": "dev",
    "staging": "stg",
    "production": "prod",
    "test": "test",
    "dev": "dev",
    "prod": "prod",
}


class AzureNamingConvention:
    """Azure resource naming convention helper"""

    def __init__(
        self,
        organization: str = "",
        project: str = "nss",
        environment: str | None = None,
        location: str | None = None,
        instance: str = "001",
    ):
        """
        Initialize naming convention

        Args:
            organization: Organization/company name (empty by default)
            project: Project name (default: nss)
            environment: Environment (dev, stg, prod)
            location: Azure region
            instance: Instance number (001, 002, etc.)
        """
        self.organization = organization.lower()
        self.project = (
            project.lower().replace("-", "").replace("_", "")[:8]
        )  # Max 8 chars for project
        self.environment = self._get_environment_abbr(environment)
        self.location = location
        self.instance = instance

    def _get_environment_abbr(self, environment: str | None) -> str:
        """Get environment abbreviation"""
        if not environment:
            config = pulumi.Config()
            environment = config.get("environment") or pulumi.get_stack()

        return ENVIRONMENT_ABBREVIATIONS.get(
            environment.lower(), environment.lower()[:3]
        )

    def resource_group(self, workload: str = "core") -> str:
        """
        Generate resource group name
        Format: rg-{project}-{workload}-{env}-{instance}
        Example: rg-nss-core-dev-001
        """
        workload_abbr = workload.lower()[:8]
        return f"rg-{self.project}-{workload_abbr}-{self.environment}-{self.instance}"

    def storage_account(self, purpose: str = "data") -> str:
        """
        Generate storage account name
        Format: st{project}{purpose}{env}{instance}
        Example: stnssdata dev001
        Note: Storage account names must be 3-24 chars, lowercase alphanumeric only
        """
        purpose_abbr = purpose.lower()[:4]
        name = f"st{self.project}{purpose_abbr}{self.environment}{self.instance}"
        return name[:24]  # Max 24 characters for storage account

    def container_registry(self) -> str:
        """
        Generate container registry name
        Format: cr{project}{env}{instance}
        Example: crnssdev001
        Note: Registry names must be 5-50 chars, alphanumeric only
        """
        name = f"cr{self.project}{self.environment}{self.instance}"
        return name[:50]  # Max 50 characters for container registry

    def container_apps_environment(self) -> str:
        """
        Generate Container Apps Environment name
        Format: cae-{project}-{env}-{instance}
        Example: cae-nss-dev-001
        """
        return (
            f"cae-{self.project}-{self.environment}-{self.instance}"
        )

    def container_app(self, app_name: str) -> str:
        """
        Generate Container App name
        Format: ca-{project}-{app}-{env}-{instance}
        Example: ca-nss-api-dev-001
        """
        app_abbr = app_name.lower().replace("-", "")[:8]
        return f"ca-{self.project}-{app_abbr}-{self.environment}-{self.instance}"

    def log_analytics_workspace(self) -> str:
        """
        Generate Log Analytics Workspace name
        Format: log-{project}-{env}-{instance}
        Example: log-nss-dev-001
        """
        return (
            f"log-{self.project}-{self.environment}-{self.instance}"
        )

    def key_vault(self) -> str:
        """
        Generate Key Vault name
        Format: kv-{project}-{env}-{instance}
        Example: kv-nss-dev-001
        Note: Key Vault names must be 3-24 chars
        """
        name = (
            f"kv-{self.project}-{self.environment}-{self.instance}"
        )
        return name[:24]  # Max 24 characters for Key Vault

    def application_insights(self) -> str:
        """
        Generate Application Insights name
        Format: appi-{project}-{env}-{instance}
        Example: appi-nss-dev-001
        """
        return f"appi-{self.project}-{self.environment}-{self.instance}"

    def postgresql_server(self) -> str:
        """
        Generate PostgreSQL server name
        Format: psql-{project}-{env}-{instance}
        Example: psql-nss-dev-001
        """
        return f"psql-{self.project}-{self.environment}-{self.instance}"

    def postgresql_database(self, db_name: str = "main") -> str:
        """
        Generate PostgreSQL database name
        Format: psqldb-{project}-{db}-{env}-{instance}
        Example: psqldb-nss-main-dev-001
        """
        db_abbr = db_name.lower()[:8]
        return f"psqldb-{self.project}-{db_abbr}-{self.environment}-{self.instance}"

    def get_resource_tags(
        self, additional_tags: dict[str, str] | None = None
    ) -> dict[str, str]:
        """
        Generate standard resource tags

        Args:
            additional_tags: Additional tags to merge with standard tags

        Returns:
            Dictionary of resource tags
        """
        tags = {
            "project": "nss",
            "environment": self.environment,
            "location": self.location,
            "managed_by": "pulumi",
            "owner": "nss-team",
            "application": "nss",
            "cost_center": f"nss-{self.environment}",
            "created_by": "infrastructure-as-code",
        }

        if additional_tags:
            tags.update(additional_tags)

        return tags


def get_naming_convention() -> AzureNamingConvention:
    """Get naming convention instance with current Pulumi configuration"""
    config = pulumi.Config()

    return AzureNamingConvention(
        organization="",  # Organization removed as requested
        project="nss",
        environment=config.get("environment") or pulumi.get_stack(),
        location=config.get("azure-native:location"),
        instance="001",
    )
