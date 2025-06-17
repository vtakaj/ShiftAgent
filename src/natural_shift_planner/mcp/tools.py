"""
MCP tools for shift scheduler operations
"""

import json
import os
from datetime import datetime
from typing import Any

import httpx
from fastmcp import Context
from pydantic import BaseModel, Field

# Configuration
API_BASE_URL = os.getenv("SHIFT_SCHEDULER_API_URL", "http://localhost:8081")


# Helper functions
def parse_list_param(param: None | str | list[str]) -> list[str]:
    """Parse a parameter that could be a list or JSON string"""
    if param is None:
        return []
    if isinstance(param, str):
        try:
            parsed = json.loads(param)
            # Ensure the parsed value is a list
            if isinstance(parsed, list):
                return parsed
            else:
                # If it's not a list after parsing, treat original as single item
                return [param]
        except json.JSONDecodeError:
            # If it's not valid JSON, treat as single item list
            return [param]
    return param


# Pydantic models for API requests
class EmployeeRequest(BaseModel):
    id: str
    name: str
    skills: list[str]
    preferred_days_off: list[str] = Field(
        default_factory=list,
        description="Days employee prefers not to work (e.g., ['friday', 'saturday'])",
    )
    preferred_work_days: list[str] = Field(
        default_factory=list,
        description="Days employee prefers to work (e.g., ['sunday', 'monday'])",
    )
    unavailable_dates: list[str] = Field(
        default_factory=list,
        description="Specific dates when employee is unavailable. Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Examples: '2024-01-15T00:00:00', '2024-01-15'. Time component is optional and will be normalized to date-only for comparison.",
    )


class ShiftRequest(BaseModel):
    id: str
    start_time: str
    end_time: str
    required_skills: list[str]
    location: str | None = None
    priority: int = Field(default=5, ge=1, le=10)


class ScheduleRequest(BaseModel):
    employees: list[EmployeeRequest]
    shifts: list[ShiftRequest]


# Helper function to make API calls
async def call_api(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Make an API call to the shift scheduler"""
    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "PATCH":
            response = await client.patch(url, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


# Tool functions
async def health_check(ctx: Context) -> dict[str, Any]:
    """Check if the Shift Scheduler API is healthy"""
    return await call_api("GET", "/health")


async def get_demo_schedule(ctx: Context) -> dict[str, Any]:
    """Get a demo shift schedule with sample data"""
    return await call_api("GET", "/api/shifts/demo")


async def solve_schedule_sync(
    ctx: Context, employees: list[EmployeeRequest], shifts: list[ShiftRequest]
) -> dict[str, Any]:
    """
    Solve shift scheduling synchronously (blocks until complete)

    Args:
        employees: List of employees with their skills
        shifts: List of shifts to be assigned

    Returns:
        Optimized schedule with assignments
    """
    request_data = {
        "employees": [emp.model_dump() for emp in employees],
        "shifts": [shift.model_dump() for shift in shifts],
    }

    # Parse datetime strings to ensure they're in ISO format
    for shift in request_data["shifts"]:
        shift["start_time"] = datetime.fromisoformat(shift["start_time"]).isoformat()
        shift["end_time"] = datetime.fromisoformat(shift["end_time"]).isoformat()

    return await call_api("POST", "/api/shifts/solve-sync", request_data)


async def solve_schedule_async(
    ctx: Context, employees: list[EmployeeRequest], shifts: list[ShiftRequest]
) -> dict[str, Any]:
    """
    Start async shift scheduling (returns job ID immediately)

    Args:
        employees: List of employees with their skills
        shifts: List of shifts to be assigned

    Returns:
        Job ID and status for tracking the optimization
    """
    request_data = {
        "employees": [emp.model_dump() for emp in employees],
        "shifts": [shift.model_dump() for shift in shifts],
    }

    # Parse datetime strings to ensure they're in ISO format
    for shift in request_data["shifts"]:
        shift["start_time"] = datetime.fromisoformat(shift["start_time"]).isoformat()
        shift["end_time"] = datetime.fromisoformat(shift["end_time"]).isoformat()

    return await call_api("POST", "/api/shifts/solve", request_data)


async def get_solve_status(ctx: Context, job_id: str) -> dict[str, Any]:
    """
    Get the status and result of an async solve job

    Args:
        job_id: The job ID returned by solve_schedule_async

    Returns:
        Job status and solution (if completed)
    """
    return await call_api("GET", f"/api/shifts/solve/{job_id}")


async def analyze_weekly_hours(
    ctx: Context, employees: list[EmployeeRequest], shifts: list[ShiftRequest]
) -> dict[str, Any]:
    """
    Analyze weekly working hours for constraint violations

    Args:
        employees: List of employees with their skills
        shifts: List of shifts (can be already assigned or not)

    Returns:
        Detailed analysis of weekly hours, violations, and recommendations
    """
    request_data = {
        "employees": [emp.model_dump() for emp in employees],
        "shifts": [shift.model_dump() for shift in shifts],
    }

    # Parse datetime strings to ensure they're in ISO format
    for shift in request_data["shifts"]:
        shift["start_time"] = datetime.fromisoformat(shift["start_time"]).isoformat()
        shift["end_time"] = datetime.fromisoformat(shift["end_time"]).isoformat()

    return await call_api("POST", "/api/shifts/analyze-weekly", request_data)


async def test_weekly_constraints(ctx: Context) -> dict[str, Any]:
    """Test weekly constraints with demo data"""
    return await call_api("GET", "/api/shifts/test-weekly")


async def get_schedule_shifts(ctx: Context, job_id: str) -> dict[str, Any]:
    """
    Get all shifts from a completed schedule for inspection

    Args:
        job_id: ID of the completed optimization job

    Returns:
        Schedule data with detailed shift information
    """
    return await call_api("GET", f"/api/shifts/solve/{job_id}")


# Employee Management Tools
async def add_employee_to_job(
    ctx: Context, job_id: str, employee: EmployeeRequest
) -> dict[str, Any]:
    """
    Add a new employee to a completed job and re-optimize with minimal changes

    This feature adds an employee to an already solved schedule and re-optimizes
    only the necessary parts, preserving existing valid assignments.

    Args:
        job_id: ID of the completed optimization job
        employee: Employee details including skills and preferences

    Returns:
        Success message with updated job status and statistics
    """
    employee_data = employee.model_dump()

    # Ensure dates are in ISO format
    if employee_data.get("unavailable_dates"):
        employee_data["unavailable_dates"] = [
            datetime.fromisoformat(date).isoformat()
            if isinstance(date, str)
            else date.isoformat()
            for date in employee_data["unavailable_dates"]
        ]

    return await call_api("POST", f"/api/shifts/{job_id}/add-employee", employee_data)


async def update_employee_skills(
    ctx: Context, job_id: str, employee_id: str, skills: None | str | list[str]
) -> dict[str, Any]:
    """
    Update an employee's skills and re-optimize affected assignments

    This feature updates the skills of an employee in a completed job and
    re-optimizes only the shifts that might be affected by the skill change.

    Args:
        job_id: ID of the completed optimization job
        employee_id: ID of the employee to update
        skills: New skills for the employee (can be a list or JSON string)

    Returns:
        Success message with skill update details and statistics
    """
    # Parse skills parameter to ensure it's a list
    parsed_skills = parse_list_param(skills)

    return await call_api(
        "PATCH", f"/api/shifts/{job_id}/employee/{employee_id}/skills", parsed_skills
    )
