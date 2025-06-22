"""
Container Registry module for Azure infrastructure
"""

from typing import Any, Optional

import pulumi
import pulumi_azure_native as azure_native
from config.naming import get_naming_convention


class ContainerRegistryModule:
    """Module for managing Azure Container Registry with enhanced security and policies"""

    def __init__(
        self,
        resource_group_name: pulumi.Input[str],
        location: pulumi.Input[str],
        sku: str = "Basic",
        environment: str = "development",
        enable_admin_user: bool = True,
        enable_vulnerability_scanning: bool = True,
        retention_days: int = 30,
        additional_tags: dict[str, Any] = None,
    ):
        """
        Initialize Container Registry module

        Args:
            resource_group_name: Resource group name
            location: Azure location
            sku: Registry SKU (Basic, Standard, Premium)
            environment: Environment name (development, production)
            enable_admin_user: Whether to enable admin user (use False for production)
            enable_vulnerability_scanning: Enable vulnerability scanning (requires Standard/Premium)
            retention_days: Number of days to retain images (0 = unlimited)
            additional_tags: Additional resource tags
        """
        self.naming = get_naming_convention()
        self.name = self.naming.container_registry()
        self.resource_group_name = resource_group_name
        self.location = location
        self.sku = sku
        self.environment = environment
        self.enable_admin_user = enable_admin_user
        self.enable_vulnerability_scanning = enable_vulnerability_scanning and sku != "Basic"
        self.retention_days = retention_days
        self.tags = self.naming.get_resource_tags(additional_tags)

        # Determine security settings based on environment
        self._configure_security_settings()

        # Create container registry
        self.registry = self._create_registry()

        # Configure retention policies
        if self.retention_days > 0 and self.sku != "Basic":
            self._create_retention_policy()

        # Configure vulnerability scanning
        if self.enable_vulnerability_scanning:
            self._configure_vulnerability_scanning()

    def _configure_security_settings(self):
        """Configure security settings based on environment"""
        if self.environment == "production":
            # Production security settings
            self.public_network_access = azure_native.containerregistry.PublicNetworkAccess.DISABLED
            self.anonymous_pull_enabled = False
            self.data_endpoint_enabled = True
            self.network_rule_bypass_options = azure_native.containerregistry.NetworkRuleBypassOptions.AZURE_SERVICES
        else:
            # Development security settings
            self.public_network_access = azure_native.containerregistry.PublicNetworkAccess.ENABLED
            self.anonymous_pull_enabled = False
            self.data_endpoint_enabled = False
            self.network_rule_bypass_options = azure_native.containerregistry.NetworkRuleBypassOptions.AZURE_SERVICES

    def _create_registry(self) -> azure_native.containerregistry.Registry:
        """Create the container registry with enhanced configuration"""
        registry_args = {
            "resource_name": self.name,
            "registry_name": self.name,
            "resource_group_name": self.resource_group_name,
            "location": self.location,
            "sku": azure_native.containerregistry.SkuArgs(name=self.sku),
            "admin_user_enabled": self.enable_admin_user,
            "public_network_access": self.public_network_access,
            "anonymous_pull_enabled": self.anonymous_pull_enabled,
            "data_endpoint_enabled": self.data_endpoint_enabled,
            "network_rule_bypass_options": self.network_rule_bypass_options,
            "zone_redundancy": azure_native.containerregistry.ZoneRedundancy.DISABLED
            if self.sku == "Basic"
            else azure_native.containerregistry.ZoneRedundancy.ENABLED,
            "tags": self.tags,
        }

        # Add encryption configuration for Premium SKU
        if self.sku == "Premium":
            registry_args["encryption"] = azure_native.containerregistry.EncryptionPropertyArgs(
                status=azure_native.containerregistry.EncryptionStatus.ENABLED
            )

        return azure_native.containerregistry.Registry(**registry_args)

    def _create_retention_policy(self):
        """Create image retention policy for Standard/Premium SKUs"""
        self.retention_policy = azure_native.containerregistry.RetentionPolicy(
            resource_name=f"{self.name}-retention",
            registry_name=self.registry.name,
            resource_group_name=self.resource_group_name,
            policy_name="retentionPolicy",
            status=azure_native.containerregistry.PolicyStatus.ENABLED,
            days=self.retention_days,
        )

    def _configure_vulnerability_scanning(self):
        """Configure vulnerability scanning for Standard/Premium SKUs"""
        # Note: Microsoft Defender for container registries requires additional setup
        # This enables the basic scanning capabilities available in ACR
        pass  # Vulnerability scanning is enabled by default on Standard/Premium SKUs

    def create_scope_map(self, name: str, actions: list[str]) -> azure_native.containerregistry.ScopeMap:
        """
        Create a scope map for fine-grained access control

        Args:
            name: Scope map name
            actions: List of allowed actions (e.g., ['repositories/*/content/read'])

        Returns:
            ScopeMap resource
        """
        return azure_native.containerregistry.ScopeMap(
            resource_name=f"{self.name}-{name}",
            registry_name=self.registry.name,
            resource_group_name=self.resource_group_name,
            scope_map_name=name,
            actions=actions,
        )

    def create_token(self, name: str, scope_map_id: pulumi.Input[str]) -> azure_native.containerregistry.Token:
        """
        Create a repository-scoped token for authentication

        Args:
            name: Token name
            scope_map_id: Associated scope map ID

        Returns:
            Token resource
        """
        return azure_native.containerregistry.Token(
            resource_name=f"{self.name}-{name}",
            registry_name=self.registry.name,
            resource_group_name=self.resource_group_name,
            token_name=name,
            scope_map_id=scope_map_id,
            status=azure_native.containerregistry.TokenStatus.ENABLED,
        )

    def get_admin_credentials(self) -> pulumi.Output[dict]:
        """Get admin credentials for the registry"""
        if not self.enable_admin_user:
            return pulumi.Output.from_input({})
        
        return pulumi.Output.all(self.resource_group_name, self.registry.name).apply(
            lambda args: azure_native.containerregistry.list_registry_credentials(
                resource_group_name=args[0], registry_name=args[1]
            )
        )

    def get_login_server(self) -> pulumi.Output[str]:
        """Get registry login server URL"""
        return self.registry.login_server

    def get_registry_name(self) -> pulumi.Output[str]:
        """Get registry name"""
        return self.registry.name

    def get_registry_id(self) -> pulumi.Output[str]:
        """Get registry resource ID"""
        return self.registry.id

    def get_outputs(self) -> dict[str, pulumi.Output]:
        """Get all important outputs from the registry module"""
        outputs = {
            "registry_name": self.get_registry_name(),
            "login_server": self.get_login_server(),
            "registry_id": self.get_registry_id(),
            "sku": pulumi.Output.from_input(self.sku),
            "environment": pulumi.Output.from_input(self.environment),
        }
        
        if self.enable_admin_user:
            outputs["admin_credentials"] = self.get_admin_credentials()
            
        return outputs
