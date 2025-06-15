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

# Azure regions abbreviations
REGION_ABBREVIATIONS = {
    "East US": "eus",
    "East US 2": "eus2",
    "West US": "wus",
    "West US 2": "wus2",
    "West US 3": "wus3",
    "Central US": "cus",
    "North Central US": "ncus",
    "South Central US": "scus",
    "West Central US": "wcus",
    "Canada Central": "cac",
    "Canada East": "cae",
    "Brazil South": "brs",
    "North Europe": "ne",
    "West Europe": "we",
    "UK South": "uks",
    "UK West": "ukw",
    "France Central": "fc",
    "France South": "fs",
    "Germany West Central": "gwc",
    "Germany North": "gn",
    "Norway East": "noe",
    "Norway West": "now",
    "Switzerland North": "sn",
    "Switzerland West": "sw",
    "Southeast Asia": "sea",
    "East Asia": "ea",
    "Australia East": "ae",
    "Australia Southeast": "ase",
    "Australia Central": "ac",
    "Australia Central 2": "ac2",
    "Japan East": "je",
    "Japan West": "jw",
    "Korea Central": "kc",
    "Korea South": "ks",
    "India Central": "ic",
    "India South": "is",
    "India West": "iw",
}


class AzureNamingConvention:
    """Azure resource naming convention helper"""

    def __init__(
        self,
        organization: str = "vtakaj",
        project: str = "shift-scheduler",
        environment: str | None = None,
        location: str | None = None,
        instance: str = "001",
    ):
        """
        Initialize naming convention

        Args:
            organization: Organization/company name (3-4 chars recommended)
            project: Project name
            environment: Environment (dev, stg, prod)
            location: Azure region
            instance: Instance number (001, 002, etc.)
        """
        self.organization = organization.lower()
        self.project = (
            project.lower().replace("-", "").replace("_", "")[:8]
        )  # Max 8 chars for project
        self.environment = self._get_environment_abbr(environment)
        self.location = self._get_location_abbr(location)
        self.instance = instance

    def _get_environment_abbr(self, environment: str | None) -> str:
        """Get environment abbreviation"""
        if not environment:
            config = pulumi.Config()
            environment = config.get("environment") or pulumi.get_stack()

        return ENVIRONMENT_ABBREVIATIONS.get(
            environment.lower(), environment.lower()[:3]
        )

    def _get_location_abbr(self, location: str | None) -> str:
        """Get location abbreviation"""
        if not location:
            config = pulumi.Config()
            location = config.get("azure-native:location") or "Japan East"

        return REGION_ABBREVIATIONS.get(location, location.lower().replace(" ", "")[:4])

    def resource_group(self, workload: str = "core") -> str:
        """
        Generate resource group name
        Format: rg-{org}-{project}-{workload}-{env}-{location}-{instance}
        Example: rg-vtakaj-shiftsch-core-dev-eus-001
        """
        workload_abbr = workload.lower()[:8]
        return f"rg-{self.organization}-{self.project}-{workload_abbr}-{self.environment}-{self.location}-{self.instance}"

    def storage_account(self, purpose: str = "data") -> str:
        """
        Generate storage account name
        Format: st{org}{project}{purpose}{env}{location}{instance}
        Example: stvtakajshiftschdatadeveus001
        Note: Storage account names must be 3-24 chars, lowercase alphanumeric only
        """
        purpose_abbr = purpose.lower()[:4]
        name = f"st{self.organization}{self.project}{purpose_abbr}{self.environment}{self.location}{self.instance}"
        return name[:24]  # Max 24 characters for storage account

    def container_registry(self) -> str:
        """
        Generate container registry name
        Format: cr{org}{project}{env}{location}{instance}
        Example: crvtakajshiftschdeveus001
        Note: Registry names must be 5-50 chars, alphanumeric only
        """
        name = f"cr{self.organization}{self.project}{self.environment}{self.location}{self.instance}"
        return name[:50]  # Max 50 characters for container registry

    def container_apps_environment(self) -> str:
        """
        Generate Container Apps Environment name
        Format: cae-{org}-{project}-{env}-{location}-{instance}
        Example: cae-vtakaj-shiftsch-dev-eus-001
        """
        return f"cae-{self.organization}-{self.project}-{self.environment}-{self.location}-{self.instance}"

    def container_app(self, app_name: str) -> str:
        """
        Generate Container App name
        Format: ca-{org}-{project}-{app}-{env}-{location}-{instance}
        Example: ca-vtakaj-shiftsch-api-dev-eus-001
        """
        app_abbr = app_name.lower().replace("-", "")[:8]
        return f"ca-{self.organization}-{self.project}-{app_abbr}-{self.environment}-{self.location}-{self.instance}"

    def log_analytics_workspace(self) -> str:
        """
        Generate Log Analytics Workspace name
        Format: log-{org}-{project}-{env}-{location}-{instance}
        Example: log-vtakaj-shiftsch-dev-eus-001
        """
        return f"log-{self.organization}-{self.project}-{self.environment}-{self.location}-{self.instance}"

    def key_vault(self) -> str:
        """
        Generate Key Vault name
        Format: kv-{org}-{project}-{env}-{location}-{instance}
        Example: kv-vtakaj-shiftsch-dev-eus-001
        Note: Key Vault names must be 3-24 chars
        """
        name = f"kv-{self.organization}-{self.project}-{self.environment}-{self.location}-{self.instance}"
        return name[:24]  # Max 24 characters for Key Vault

    def application_insights(self) -> str:
        """
        Generate Application Insights name
        Format: appi-{org}-{project}-{env}-{location}-{instance}
        Example: appi-vtakaj-shiftsch-dev-eus-001
        """
        return f"appi-{self.organization}-{self.project}-{self.environment}-{self.location}-{self.instance}"

    def postgresql_server(self) -> str:
        """
        Generate PostgreSQL server name
        Format: psql-{org}-{project}-{env}-{location}-{instance}
        Example: psql-vtakaj-shiftsch-dev-eus-001
        """
        return f"psql-{self.organization}-{self.project}-{self.environment}-{self.location}-{self.instance}"

    def postgresql_database(self, db_name: str = "main") -> str:
        """
        Generate PostgreSQL database name
        Format: psqldb-{org}-{project}-{db}-{env}-{instance}
        Example: psqldb-vtakaj-shiftsch-main-dev-001
        """
        db_abbr = db_name.lower()[:8]
        return f"psqldb-{self.organization}-{self.project}-{db_abbr}-{self.environment}-{self.instance}"

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
            "Organization": self.organization,
            "Project": "shift-scheduler",
            "Environment": self.environment,
            "Location": self.location,
            "ManagedBy": "Pulumi",
            "Owner": "shift-scheduler-team",
            "Application": "shift-scheduler",
            "CostCenter": f"shift-scheduler-{self.environment}",
            "CreatedBy": "infrastructure-as-code",
        }

        if additional_tags:
            tags.update(additional_tags)

        return tags


def get_naming_convention() -> AzureNamingConvention:
    """Get naming convention instance with current Pulumi configuration"""
    config = pulumi.Config()

    return AzureNamingConvention(
        organization="vtakaj",
        project="shift-scheduler",
        environment=config.get("environment") or pulumi.get_stack(),
        location=config.get("azure-native:location"),
        instance="001",
    )
