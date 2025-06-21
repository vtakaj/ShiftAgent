"""
Azure Blob Storage implementation of JobStore
"""

import json
import os
from datetime import datetime
from typing import Any

from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential

from .job_store import JobStore
from ..core.models.employee import Employee
from ..core.models.schedule import ShiftSchedule
from ..core.models.shift import Shift


class AzureBlobJobStore(JobStore):
    """Azure Blob Storage job store implementation"""

    def __init__(
        self,
        connection_string: str | None = None,
        account_name: str | None = None,
        container_name: str = "job-data",
    ):
        """
        Initialize Azure Blob Storage job store
        
        Args:
            connection_string: Azure Storage connection string
            account_name: Storage account name (uses DefaultAzureCredential if no connection_string)
            container_name: Blob container name for job data
        """
        self.container_name = container_name
        
        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        elif account_name:
            # Use managed identity / default credential
            credential = DefaultAzureCredential()
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url, credential=credential
            )
        else:
            raise ValueError("Either connection_string or account_name must be provided")
        
        # Ensure container exists
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            container_client.get_container_properties()
        except ResourceNotFoundError:
            self.blob_service_client.create_container(container_name)

    def _get_blob_name(self, job_id: str) -> str:
        """Get blob name for a job"""
        return f"jobs/{job_id}.json"

    def _serialize_datetime(self, dt: datetime | None) -> str | None:
        """Convert datetime to ISO string"""
        return dt.isoformat() if dt else None

    def _deserialize_datetime(self, dt_str: str | None) -> datetime | None:
        """Convert ISO string to datetime"""
        return datetime.fromisoformat(dt_str) if dt_str else None

    def _serialize_employee(self, employee: Employee | None) -> dict[str, Any] | None:
        """Convert Employee to dict"""
        if not employee:
            return None
        return {
            "id": employee.id,
            "name": employee.name,
            "skills": list(employee.skills),
            "preferred_days_off": list(employee.preferred_days_off),
            "preferred_work_days": list(employee.preferred_work_days),
            "unavailable_dates": [
                self._serialize_datetime(d) for d in employee.unavailable_dates
            ],
        }

    def _serialize_shift(self, shift: Shift | None) -> dict[str, Any] | None:
        """Convert Shift to dict"""
        if not shift:
            return None
        return {
            "id": shift.id,
            "start_time": self._serialize_datetime(shift.start_time),
            "end_time": self._serialize_datetime(shift.end_time),
            "required_skills": list(shift.required_skills),
            "location": shift.location,
            "priority": shift.priority,
            "employee": self._serialize_employee(shift.employee),
            "pinned": shift.pinned,
        }

    def _serialize_schedule(
        self, schedule: ShiftSchedule | None
    ) -> dict[str, Any] | None:
        """Convert ShiftSchedule to dict"""
        if not schedule:
            return None
        return {
            "employees": [self._serialize_employee(emp) for emp in schedule.employees],
            "shifts": [self._serialize_shift(shift) for shift in schedule.shifts],
            "score": str(schedule.score) if schedule.score else None,
        }

    def _deserialize_employee(self, emp_data: dict[str, Any] | None) -> Employee | None:
        """Convert dict to Employee"""
        if not emp_data:
            return None
        return Employee(
            id=emp_data["id"],
            name=emp_data["name"],
            skills=set(emp_data["skills"]),
            preferred_days_off=set(emp_data.get("preferred_days_off", [])),
            preferred_work_days=set(emp_data.get("preferred_work_days", [])),
            unavailable_dates={
                self._deserialize_datetime(d)
                for d in emp_data.get("unavailable_dates", [])
                if d is not None
            },
        )

    def _deserialize_shift(self, shift_data: dict[str, Any] | None) -> Shift | None:
        """Convert dict to Shift"""
        if not shift_data:
            return None
        shift = Shift(
            id=shift_data["id"],
            start_time=self._deserialize_datetime(shift_data["start_time"]),
            end_time=self._deserialize_datetime(shift_data["end_time"]),
            required_skills=set(shift_data["required_skills"]),
            location=shift_data["location"],
            priority=shift_data["priority"],
            pinned=shift_data.get("pinned", False),
        )
        # Set employee if present
        if shift_data.get("employee"):
            shift.employee = self._deserialize_employee(shift_data["employee"])
        return shift

    def _deserialize_schedule(
        self, schedule_data: dict[str, Any] | None
    ) -> ShiftSchedule | None:
        """Convert dict to ShiftSchedule"""
        if not schedule_data:
            return None
        employees = [
            self._deserialize_employee(emp) for emp in schedule_data["employees"]
        ]
        shifts = [self._deserialize_shift(shift) for shift in schedule_data["shifts"]]
        schedule = ShiftSchedule(employees=employees, shifts=shifts)
        if schedule_data.get("score"):
            # Note: Score reconstruction from string is complex, skip for now
            pass
        return schedule

    def save_job(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Save job data to Azure Blob Storage"""
        # Create serializable version of job data
        serializable_data = {
            "job_id": job_id,
            "status": job_data["status"],
            "created_at": self._serialize_datetime(job_data.get("created_at")),
            "completed_at": self._serialize_datetime(job_data.get("completed_at")),
            "error": job_data.get("error"),
            # Don't serialize solver reference or other non-serializable objects
        }

        # Serialize problem and solution if they exist
        if "problem" in job_data and job_data["problem"]:
            serializable_data["problem"] = self._serialize_schedule(job_data["problem"])

        if "solution" in job_data and job_data["solution"]:
            serializable_data["solution"] = self._serialize_schedule(
                job_data["solution"]
            )

        # Upload to blob storage
        blob_name = self._get_blob_name(job_id)
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        
        json_data = json.dumps(serializable_data, indent=2, ensure_ascii=False)
        blob_client.upload_blob(
            json_data, 
            overwrite=True,
            metadata={
                "job_id": job_id,
                "status": job_data["status"],
                "created_at": str(job_data.get("created_at", "")),
            }
        )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve job data from Azure Blob Storage"""
        blob_name = self._get_blob_name(job_id)
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )

        try:
            blob_data = blob_client.download_blob()
            data = json.loads(blob_data.readall().decode("utf-8"))

            # Convert datetime strings back to datetime objects
            if data.get("created_at"):
                data["created_at"] = self._deserialize_datetime(data["created_at"])
            if data.get("completed_at"):
                data["completed_at"] = self._deserialize_datetime(data["completed_at"])

            # Convert problem and solution back to domain objects
            if data.get("problem"):
                data["problem"] = self._deserialize_schedule(data["problem"])
            if data.get("solution"):
                data["solution"] = self._deserialize_schedule(data["solution"])

            return data
        except ResourceNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading job {job_id} from Azure Storage: {e}")
            return None

    def list_jobs(self) -> list[str]:
        """List all job IDs"""
        container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
        
        try:
            blobs = container_client.list_blobs(name_starts_with="jobs/")
            job_ids = []
            for blob in blobs:
                if blob.name.endswith(".json"):
                    # Extract job ID from blob name (jobs/{job_id}.json)
                    job_id = blob.name[5:-5]  # Remove "jobs/" prefix and ".json" suffix
                    job_ids.append(job_id)
            return job_ids
        except Exception as e:
            print(f"Error listing jobs from Azure Storage: {e}")
            return []

    def delete_job(self, job_id: str) -> None:
        """Delete a job from Azure Blob Storage"""
        blob_name = self._get_blob_name(job_id)
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        
        try:
            blob_client.delete_blob()
        except ResourceNotFoundError:
            # Job doesn't exist, which is fine
            pass
        except Exception as e:
            print(f"Error deleting job {job_id} from Azure Storage: {e}")

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove jobs older than specified hours"""
        from datetime import timezone, timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        deleted_count = 0

        container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
        
        try:
            blobs = container_client.list_blobs(name_starts_with="jobs/")
            for blob in blobs:
                if blob.name.endswith(".json") and blob.last_modified:
                    if blob.last_modified < cutoff:
                        try:
                            blob_client = self.blob_service_client.get_blob_client(
                                container=self.container_name, blob=blob.name
                            )
                            blob_client.delete_blob()
                            deleted_count += 1
                        except Exception as e:
                            print(f"Error deleting old job blob {blob.name}: {e}")
        except Exception as e:
            print(f"Error cleaning up old jobs from Azure Storage: {e}")

        return deleted_count


def create_azure_job_store() -> AzureBlobJobStore | None:
    """
    Factory function to create Azure job store based on environment variables
    """
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "job-data")
    
    if connection_string:
        return AzureBlobJobStore(
            connection_string=connection_string,
            container_name=container_name
        )
    elif account_name:
        return AzureBlobJobStore(
            account_name=account_name,
            container_name=container_name
        )
    else:
        print("Warning: No Azure Storage configuration found")
        return None