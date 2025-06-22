#!/usr/bin/env python3
"""
Validation script for Pulumi infrastructure configuration
"""

import sys

try:
    import pulumi
    from config.naming import get_naming_convention

    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

try:
    # Test configuration access
    config = pulumi.Config()
    project_config = pulumi.Config("shift-scheduler-infra")

    print(f"📋 Current stack: {pulumi.get_stack()}")
    print(f"📍 Azure location: {config.get('azure-native:location')}")
    print(f"🏗️  Environment: {project_config.get('environment')}")

    # Test naming convention
    naming = get_naming_convention()
    print(f"🏷️  Resource group name: {naming.resource_group()}")
    print(f"💾 Storage account name: {naming.storage_account('data')}")

    print("✅ Configuration validation successful")

except Exception as e:
    print(f"❌ Configuration error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("🎉 All validations passed!")
