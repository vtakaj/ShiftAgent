#!/usr/bin/env python3
"""
Test script for Azure Storage functionality
"""

import os
import sys
from datetime import datetime

from shiftagent.api.azure_job_store import create_azure_job_store
from shiftagent.config.storage_config import (
    StorageConfigManager,
    get_current_storage_config,
)
from shiftagent.core.models.employee import Employee
from shiftagent.core.models.schedule import ShiftSchedule
from shiftagent.core.models.shift import Shift


def create_test_data():
    """Create test job data for upload/download testing"""
    # Create test employee
    employee = Employee(
        id="test-emp-1",
        name="Test Employee",
        skills={"programming", "testing"},
        preferred_days_off={6, 0},  # Saturday, Sunday
        preferred_work_days={1, 2, 3, 4, 5},  # Monday-Friday
        unavailable_dates=set(),
    )

    # Create test shift
    shift = Shift(
        id="test-shift-1",
        start_time=datetime(2024, 6, 13, 9, 0),
        end_time=datetime(2024, 6, 13, 17, 0),
        required_skills={"programming"},
        location="Remote",
        priority=1,
        pinned=False,
    )
    shift.employee = employee

    # Create test schedule
    schedule = ShiftSchedule(employees=[employee], shifts=[shift])

    # Create job data
    job_data = {
        "job_id": "test-job-azure-storage",
        "status": "completed",
        "created_at": datetime.now(),
        "completed_at": datetime.now(),
        "error": None,
        "problem": schedule,
        "solution": schedule,
    }

    return job_data


def test_configuration():
    """Test storage configuration"""
    print("=== Testing Storage Configuration ===")

    config = get_current_storage_config()
    StorageConfigManager.print_config_info(config)

    is_valid = StorageConfigManager.validate_config(config)
    if not is_valid:
        print("❌ Configuration is invalid")
        return False

    print("✅ Configuration is valid")
    return True


def test_azure_connection():
    """Test Azure storage connection"""
    print("\n=== Testing Azure Storage Connection ===")

    try:
        job_store = create_azure_job_store()
        if job_store is None:
            print("❌ Failed to create Azure job store")
            return False

        print("✅ Azure job store created successfully")
        print(f"   Container: {job_store.container_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to connect to Azure Storage: {e}")
        return False


def test_upload_download():
    """Test upload and download functionality"""
    print("\n=== Testing Upload/Download Functionality ===")

    try:
        # Create job store
        job_store = create_azure_job_store()
        if job_store is None:
            print("❌ Failed to create Azure job store")
            return False

        # Create test data
        test_data = create_test_data()
        job_id = test_data["job_id"]

        print(f"📤 Uploading test job: {job_id}")

        # Upload test job
        job_store.save_job(job_id, test_data)
        print("✅ Job uploaded successfully")

        # Download and verify
        print(f"📥 Downloading test job: {job_id}")
        retrieved_data = job_store.get_job(job_id)

        if retrieved_data is None:
            print("❌ Failed to retrieve uploaded job")
            return False

        # Verify data
        if retrieved_data["job_id"] != job_id:
            print("❌ Retrieved job ID doesn't match")
            return False

        if retrieved_data["status"] != "completed":
            print("❌ Retrieved job status doesn't match")
            return False

        if retrieved_data["solution"] is None:
            print("❌ Retrieved job solution is missing")
            return False

        print("✅ Job downloaded and verified successfully")

        # Test listing jobs
        print("📋 Testing job listing...")
        job_ids = job_store.list_jobs()
        if job_id not in job_ids:
            print("❌ Uploaded job not found in job list")
            return False

        print(f"✅ Job found in list ({len(job_ids)} total jobs)")

        # Clean up - delete test job
        print("🗑️  Cleaning up test job...")
        job_store.delete_job(job_id)

        # Verify deletion
        retrieved_after_delete = job_store.get_job(job_id)
        if retrieved_after_delete is not None:
            print("❌ Job still exists after deletion")
            return False

        print("✅ Test job deleted successfully")
        return True

    except Exception as e:
        print(f"❌ Upload/download test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🧪 Azure Storage Integration Test")
    print("=" * 50)

    # Check environment
    if not os.getenv("AZURE_STORAGE_CONNECTION_STRING") and not os.getenv(
        "AZURE_STORAGE_ACCOUNT_NAME"
    ):
        print("❌ No Azure Storage configuration found")
        print("   Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_NAME")
        print("   Example:")
        print(
            "   export AZURE_STORAGE_CONNECTION_STRING='DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net'"
        )
        print("   or")
        print("   export AZURE_STORAGE_ACCOUNT_NAME='mystorageaccount'")
        return 1

    success = True

    # Run tests
    success &= test_configuration()
    success &= test_azure_connection()
    success &= test_upload_download()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Azure Storage integration is working.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
