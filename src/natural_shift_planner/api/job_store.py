"""
Job persistence layer for storing optimization jobs
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from ..core.models.employee import Employee
from ..core.models.schedule import ShiftSchedule
from ..core.models.shift import Shift


class JobStore(Protocol):
    """Interface for job storage implementations"""

    def save_job(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Save job data to storage"""
        ...

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve job data from storage"""
        ...

    def list_jobs(self) -> list[str]:
        """List all job IDs"""
        ...

    def delete_job(self, job_id: str) -> None:
        """Delete a job from storage"""
        ...


class FileSystemJobStore:
    """File-based job storage implementation"""

    def __init__(self, storage_dir: str = "./job_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_job_path(self, job_id: str) -> Path:
        """Get file path for a job"""
        return self.storage_dir / f"{job_id}.json"

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

    def save_job(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Save job data to file"""
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

        # Write to file
        job_path = self._get_job_path(job_id)
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

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

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve job data from file"""
        job_path = self._get_job_path(job_id)
        if not job_path.exists():
            return None

        try:
            with open(job_path, encoding="utf-8") as f:
                data = json.load(f)

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
        except Exception as e:
            print(f"Error loading job {job_id}: {e}")
            return None

    def list_jobs(self) -> list[str]:
        """List all job IDs"""
        job_files = self.storage_dir.glob("*.json")
        return [f.stem for f in job_files]

    def delete_job(self, job_id: str) -> None:
        """Delete a job file"""
        job_path = self._get_job_path(job_id)
        if job_path.exists():
            job_path.unlink()

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove jobs older than specified hours"""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        deleted_count = 0

        for job_file in self.storage_dir.glob("*.json"):
            # Check file modification time
            if job_file.stat().st_mtime < cutoff:
                try:
                    job_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting old job file {job_file}: {e}")

        return deleted_count


# Initialize job store based on environment
STORAGE_TYPE = os.getenv("JOB_STORAGE_TYPE", "filesystem")
STORAGE_DIR = os.getenv("JOB_STORAGE_DIR", "./job_storage")

if STORAGE_TYPE == "filesystem":
    job_store: JobStore | None = FileSystemJobStore(STORAGE_DIR)
elif STORAGE_TYPE == "azure":
    try:
        from .azure_job_store import create_azure_job_store
        job_store = create_azure_job_store()
        if job_store is None:
            print("Failed to create Azure job store, falling back to filesystem")
            job_store = FileSystemJobStore(STORAGE_DIR)
    except ImportError as e:
        print(f"Azure storage dependencies not available: {e}")
        print("Falling back to filesystem storage")
        job_store = FileSystemJobStore(STORAGE_DIR)
else:
    job_store = None  # Memory only
