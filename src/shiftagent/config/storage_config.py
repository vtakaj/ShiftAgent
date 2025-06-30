"""
Storage configuration management for Azure integration
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class StorageType(Enum):
    """Supported storage types"""

    FILESYSTEM = "filesystem"
    AZURE = "azure"


@dataclass
class StorageConfig:
    """Storage configuration container"""

    storage_type: StorageType
    filesystem_dir: str | None = None
    azure_connection_string: str | None = None
    azure_account_name: str | None = None
    azure_container_name: str = "job-data"


class StorageConfigManager:
    """Manager for storage configuration"""

    @staticmethod
    def from_environment() -> StorageConfig:
        """Create storage config from environment variables"""
        storage_type_str = os.getenv("JOB_STORAGE_TYPE", "filesystem").lower()

        try:
            storage_type = StorageType(storage_type_str)
        except ValueError:
            print(
                f"Warning: Unknown storage type '{storage_type_str}', defaulting to filesystem"
            )
            storage_type = StorageType.FILESYSTEM

        config = StorageConfig(
            storage_type=storage_type,
            filesystem_dir=os.getenv("JOB_STORAGE_DIR", "./job_storage"),
            azure_connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
            azure_account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
            azure_container_name=os.getenv("AZURE_STORAGE_CONTAINER_NAME", "job-data"),
        )

        return config

    @staticmethod
    def from_terraform_outputs(terraform_outputs: dict[str, Any]) -> StorageConfig:
        """Create storage config from Terraform outputs"""
        return StorageConfig(
            storage_type=StorageType.AZURE,
            azure_connection_string=terraform_outputs.get("storage_connection_string"),
            azure_account_name=terraform_outputs.get("storage_account_name"),
            azure_container_name=terraform_outputs.get(
                "storage_job_data_container", "job-data"
            ),
        )

    @staticmethod
    def validate_config(config: StorageConfig) -> bool:
        """Validate storage configuration"""
        if config.storage_type == StorageType.FILESYSTEM:
            return config.filesystem_dir is not None

        elif config.storage_type == StorageType.AZURE:
            # Either connection string or account name is required
            return (
                config.azure_connection_string is not None
                or config.azure_account_name is not None
            )

        return False

    @staticmethod
    def get_environment_variables(config: StorageConfig) -> dict[str, str]:
        """Get environment variables dict from config"""
        env_vars = {"JOB_STORAGE_TYPE": config.storage_type.value}

        if config.storage_type == StorageType.FILESYSTEM:
            if config.filesystem_dir:
                env_vars["JOB_STORAGE_DIR"] = config.filesystem_dir

        elif config.storage_type == StorageType.AZURE:
            if config.azure_connection_string:
                env_vars["AZURE_STORAGE_CONNECTION_STRING"] = (
                    config.azure_connection_string
                )
            if config.azure_account_name:
                env_vars["AZURE_STORAGE_ACCOUNT_NAME"] = config.azure_account_name
            if config.azure_container_name:
                env_vars["AZURE_STORAGE_CONTAINER_NAME"] = config.azure_container_name

        return env_vars

    @staticmethod
    def apply_to_environment(config: StorageConfig) -> None:
        """Apply configuration to current environment"""
        env_vars = StorageConfigManager.get_environment_variables(config)
        os.environ.update(env_vars)

    @staticmethod
    def create_env_file(config: StorageConfig, file_path: str = ".env") -> None:
        """Create .env file with storage configuration"""
        env_vars = StorageConfigManager.get_environment_variables(config)

        with open(file_path, "w") as f:
            f.write("# Storage Configuration\n")
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

    @staticmethod
    def print_config_info(config: StorageConfig) -> None:
        """Print configuration information"""
        print(f"Storage Type: {config.storage_type.value}")

        if config.storage_type == StorageType.FILESYSTEM:
            print(f"Storage Directory: {config.filesystem_dir}")

        elif config.storage_type == StorageType.AZURE:
            print(f"Container Name: {config.azure_container_name}")
            if config.azure_account_name:
                print(f"Account Name: {config.azure_account_name}")
            if config.azure_connection_string:
                print("Connection String: [CONFIGURED]")
            else:
                print("Connection String: [NOT SET]")

        is_valid = StorageConfigManager.validate_config(config)
        print(f"Configuration Valid: {is_valid}")


def get_current_storage_config() -> StorageConfig:
    """Get current storage configuration from environment"""
    return StorageConfigManager.from_environment()


def setup_azure_storage_from_terraform(terraform_outputs: dict[str, Any]) -> None:
    """Setup Azure storage configuration from Terraform outputs"""
    config = StorageConfigManager.from_terraform_outputs(terraform_outputs)

    if StorageConfigManager.validate_config(config):
        StorageConfigManager.apply_to_environment(config)
        print("Azure storage configuration applied to environment")
        StorageConfigManager.print_config_info(config)
    else:
        print("Warning: Invalid Azure storage configuration from Terraform outputs")
