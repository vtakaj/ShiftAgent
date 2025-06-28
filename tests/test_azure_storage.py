"""
Tests for Azure Storage integration
"""

import os
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from src.shift_agent.api.azure_job_store import AzureBlobJobStore
from src.shift_agent.core.models.employee import Employee
from src.shift_agent.core.models.schedule import ShiftSchedule
from src.shift_agent.core.models.shift import Shift


class TestAzureBlobJobStore:
    """Test Azure Blob Storage job store"""

    @pytest.fixture
    def mock_blob_service_client(self):
        """Mock Azure Blob Service Client"""
        with patch(
            "src.shift_agent.api.azure_job_store.BlobServiceClient"
        ) as mock_client:
            mock_instance = Mock()
            mock_client.from_connection_string.return_value = mock_instance
            mock_client.return_value = mock_instance

            # Mock container operations
            mock_container_client = Mock()
            mock_instance.get_container_client.return_value = mock_container_client
            mock_instance.create_container.return_value = None
            mock_container_client.get_container_properties.return_value = None

            yield mock_instance

    @pytest.fixture
    def job_store(self, mock_blob_service_client):
        """Create Azure job store with mocked dependencies"""
        return AzureBlobJobStore(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test==;EndpointSuffix=core.windows.net",
            container_name="test-jobs",
        )

    def test_initialization_with_connection_string(self, mock_blob_service_client):
        """Test job store initialization with connection string"""
        store = AzureBlobJobStore(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test==;EndpointSuffix=core.windows.net"
        )
        assert store.container_name == "job-data"

    def test_initialization_with_account_name(self, mock_blob_service_client):
        """Test job store initialization with account name"""
        with patch("src.shift_agent.api.azure_job_store.DefaultAzureCredential"):
            store = AzureBlobJobStore(account_name="testaccount")
            assert store.container_name == "job-data"

    def test_initialization_without_credentials(self):
        """Test job store initialization fails without credentials"""
        with pytest.raises(
            ValueError,
            match="Either connection_string or account_name must be provided",
        ):
            AzureBlobJobStore()

    def test_save_and_get_job(self, job_store, mock_blob_service_client):
        """Test saving and retrieving a job"""
        # Setup mock blob client
        mock_blob_client = Mock()
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        # Test data
        job_id = "test-job-1"
        job_data = {
            "status": "completed",
            "created_at": datetime.now(),
            "completed_at": datetime.now(),
            "error": None,
        }

        # Save job
        job_store.save_job(job_id, job_data)

        # Verify blob upload was called
        mock_blob_client.upload_blob.assert_called_once()

        # Mock blob download for retrieval
        mock_blob_data = Mock()
        mock_blob_data.readall.return_value = (
            b'{"job_id": "test-job-1", "status": "completed"}'
        )
        mock_blob_client.download_blob.return_value = mock_blob_data

        # Get job
        retrieved_job = job_store.get_job(job_id)

        assert retrieved_job is not None
        assert retrieved_job["job_id"] == job_id
        assert retrieved_job["status"] == "completed"

    def test_list_jobs(self, job_store, mock_blob_service_client):
        """Test listing jobs"""
        # Mock container client
        mock_container_client = Mock()
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        # Mock blob list
        mock_blob1 = Mock()
        mock_blob1.name = "jobs/job1.json"
        mock_blob2 = Mock()
        mock_blob2.name = "jobs/job2.json"
        mock_container_client.list_blobs.return_value = [mock_blob1, mock_blob2]

        job_ids = job_store.list_jobs()

        assert len(job_ids) == 2
        assert "job1" in job_ids
        assert "job2" in job_ids

    def test_delete_job(self, job_store, mock_blob_service_client):
        """Test deleting a job"""
        mock_blob_client = Mock()
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        job_store.delete_job("test-job-1")

        mock_blob_client.delete_blob.assert_called_once()

    def test_cleanup_old_jobs(self, job_store, mock_blob_service_client):
        """Test cleaning up old jobs"""
        # Mock container client
        mock_container_client = Mock()
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        # Mock old blob
        mock_old_blob = Mock()
        mock_old_blob.name = "jobs/old-job.json"
        mock_old_blob.last_modified = datetime(2023, 1, 1, tzinfo=UTC)  # Very old
        mock_container_client.list_blobs.return_value = [mock_old_blob]

        # Mock blob client for deletion
        mock_blob_client = Mock()
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        deleted_count = job_store.cleanup_old_jobs(max_age_hours=1)

        assert deleted_count == 1
        mock_blob_client.delete_blob.assert_called_once()

    def test_serialization_deserialization(self, job_store):
        """Test serialization and deserialization of domain objects"""
        # Create test employee
        employee = Employee(
            id="emp1",
            name="Test Employee",
            skills={"skill1", "skill2"},
            preferred_days_off={1, 2},
            preferred_work_days={3, 4, 5},
            unavailable_dates={datetime(2024, 1, 1)},
        )

        # Create test shift
        shift = Shift(
            id="shift1",
            start_time=datetime(2024, 1, 1, 9, 0),
            end_time=datetime(2024, 1, 1, 17, 0),
            required_skills={"skill1"},
            location="Office",
            priority=1,
            pinned=False,
        )
        shift.employee = employee

        # Create test schedule
        schedule = ShiftSchedule(employees=[employee], shifts=[shift])

        # Test serialization
        serialized_emp = job_store._serialize_employee(employee)
        serialized_shift = job_store._serialize_shift(shift)
        serialized_schedule = job_store._serialize_schedule(schedule)

        assert serialized_emp["id"] == "emp1"
        assert serialized_emp["name"] == "Test Employee"
        assert set(serialized_emp["skills"]) == {"skill1", "skill2"}

        assert serialized_shift["id"] == "shift1"
        assert serialized_shift["location"] == "Office"
        assert serialized_shift["employee"]["id"] == "emp1"

        assert len(serialized_schedule["employees"]) == 1
        assert len(serialized_schedule["shifts"]) == 1

        # Test deserialization
        deserialized_emp = job_store._deserialize_employee(serialized_emp)
        deserialized_shift = job_store._deserialize_shift(serialized_shift)
        deserialized_schedule = job_store._deserialize_schedule(serialized_schedule)

        assert deserialized_emp.id == "emp1"
        assert deserialized_emp.name == "Test Employee"
        assert deserialized_emp.skills == {"skill1", "skill2"}

        assert deserialized_shift.id == "shift1"
        assert deserialized_shift.location == "Office"
        assert deserialized_shift.employee.id == "emp1"

        assert len(deserialized_schedule.employees) == 1
        assert len(deserialized_schedule.shifts) == 1


def test_create_azure_job_store():
    """Test factory function for creating Azure job store"""
    from src.shift_agent.api.azure_job_store import create_azure_job_store

    # Test with no environment variables
    with patch.dict(os.environ, {}, clear=True):
        store = create_azure_job_store()
        assert store is None

    # Test with connection string
    with patch.dict(
        os.environ,
        {
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test==;EndpointSuffix=core.windows.net"
        },
        clear=True,
    ):
        with patch("src.shift_agent.api.azure_job_store.BlobServiceClient"):
            store = create_azure_job_store()
            assert store is not None
            assert store.container_name == "job-data"

    # Test with account name
    with patch.dict(
        os.environ, {"AZURE_STORAGE_ACCOUNT_NAME": "testaccount"}, clear=True
    ):
        with (
            patch("src.shift_agent.api.azure_job_store.BlobServiceClient"),
            patch("src.shift_agent.api.azure_job_store.DefaultAzureCredential"),
        ):
            store = create_azure_job_store()
            assert store is not None
            assert store.container_name == "job-data"
