"""
MCP tools for shift scheduler operations
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from fastmcp import Context
from pydantic import BaseModel, Field

# Configuration
API_BASE_URL = os.getenv("SHIFT_SCHEDULER_API_URL", "http://localhost:8081")


# Helper functions
def parse_list_param(param: Union[None, str, List[str]]) -> List[str]:
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
    skills: List[str]
    preferred_days_off: List[str] = Field(
        default_factory=list,
        description="Days employee prefers not to work (e.g., ['friday', 'saturday'])",
    )
    preferred_work_days: List[str] = Field(
        default_factory=list,
        description="Days employee prefers to work (e.g., ['sunday', 'monday'])",
    )
    unavailable_dates: List[str] = Field(
        default_factory=list,
        description="Specific dates when employee is unavailable (ISO format)",
    )


class ShiftRequest(BaseModel):
    id: str
    start_time: str
    end_time: str
    required_skills: List[str]
    location: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)


class ScheduleRequest(BaseModel):
    employees: List[EmployeeRequest]
    shifts: List[ShiftRequest]


# Helper function to make API calls
async def call_api(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
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
        return response.json()


async def call_continuous_planning_api(
    endpoint: str,
    data: Dict[str, Any],
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """
    Make a continuous planning API call with automatic job restart if needed
    """
    try:
        return await call_api("POST", endpoint, data, timeout)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400 and "has already completed" in e.response.text:
            # Extract job_id from endpoint
            job_id = endpoint.split("/")[3]  # /api/shifts/{job_id}/operation

            # Try to restart the job
            try:
                await call_api("POST", f"/api/shifts/{job_id}/restart")
                # Wait a moment for the job to restart
                import asyncio

                await asyncio.sleep(1)

                # Retry the original operation
                return await call_api("POST", endpoint, data, timeout)
            except Exception as restart_error:
                raise Exception(
                    f"Failed to restart job {job_id}: {restart_error}"
                ) from e
        else:
            raise


# Tool functions
async def health_check(ctx: Context) -> Dict[str, Any]:
    """Check if the Shift Scheduler API is healthy"""
    return await call_api("GET", "/health")


async def get_demo_schedule(ctx: Context) -> Dict[str, Any]:
    """Get a demo shift schedule with sample data"""
    return await call_api("GET", "/api/shifts/demo")


async def solve_schedule_sync(
    ctx: Context, employees: List[EmployeeRequest], shifts: List[ShiftRequest]
) -> Dict[str, Any]:
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
    ctx: Context, employees: List[EmployeeRequest], shifts: List[ShiftRequest]
) -> Dict[str, Any]:
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


async def get_solve_status(ctx: Context, job_id: str) -> Dict[str, Any]:
    """
    Get the status and result of an async solve job

    Args:
        job_id: The job ID returned by solve_schedule_async

    Returns:
        Job status and solution (if completed)
    """
    return await call_api("GET", f"/api/shifts/solve/{job_id}")


async def analyze_weekly_hours(
    ctx: Context, employees: List[EmployeeRequest], shifts: List[ShiftRequest]
) -> Dict[str, Any]:
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


async def test_weekly_constraints(ctx: Context) -> Dict[str, Any]:
    """Test weekly constraints with demo data"""
    return await call_api("GET", "/api/shifts/test-weekly")


async def get_schedule_shifts(ctx: Context, job_id: str) -> Dict[str, Any]:
    """
    Get all shifts from a completed schedule for inspection

    Args:
        job_id: ID of the completed optimization job

    Returns:
        Schedule data with detailed shift information
    """
    return await call_api("GET", f"/api/shifts/solve/{job_id}")


# Continuous Planning tools
class ShiftSwapRequest(BaseModel):
    """Request to swap employees between two shifts"""

    shift1_id: str = Field(..., description="ID of the first shift")
    shift2_id: str = Field(..., description="ID of the second shift")


class ShiftReplacementRequest(BaseModel):
    """Request to find replacement for a shift"""

    shift_id: str = Field(..., description="ID of the shift needing replacement")
    unavailable_employee_id: str = Field(
        ..., description="ID of the employee who cannot work"
    )
    excluded_employee_ids: List[str] = Field(
        default_factory=list, description="Additional employees to exclude"
    )


class ShiftPinRequest(BaseModel):
    """Request to pin/unpin shifts for continuous planning"""

    shift_ids: List[str] = Field(..., min_items=1, description="Shift IDs to pin/unpin")
    action: str = Field(..., description="Pin or unpin action", pattern="^(pin|unpin)$")


class ShiftReassignRequest(BaseModel):
    """Request to reassign a shift to a specific employee"""

    shift_id: str = Field(..., description="ID of the shift to reassign")
    new_employee_id: Optional[str] = Field(
        None, description="ID of new employee (None to unassign)"
    )


async def swap_shifts(
    ctx: Context, job_id: str, shift1_id: str, shift2_id: str
) -> Dict[str, Any]:
    """
    Swap employees between two shifts during continuous planning

    Args:
        job_id: ID of the active optimization job
        shift1_id: ID of the first shift
        shift2_id: ID of the second shift

    Returns:
        Success status and details of the swap operation
    """
    request_data = {"shift1_id": shift1_id, "shift2_id": shift2_id}
    return await call_continuous_planning_api(
        f"/api/shifts/{job_id}/swap", request_data
    )


async def find_shift_replacement(
    ctx: Context,
    job_id: str,
    shift_id: str,
    unavailable_employee_id: str,
    excluded_employee_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Find replacement for a shift when an employee becomes unavailable

    Args:
        job_id: ID of the active optimization job
        shift_id: ID of the shift needing replacement
        unavailable_employee_id: ID of the employee who cannot work
        excluded_employee_ids: Additional employees to exclude from consideration

    Returns:
        Success status and replacement details
    """
    request_data = {
        "shift_id": shift_id,
        "unavailable_employee_id": unavailable_employee_id,
        "excluded_employee_ids": excluded_employee_ids or [],
    }
    return await call_continuous_planning_api(
        f"/api/shifts/{job_id}/replace", request_data
    )


async def pin_shifts(
    ctx: Context, job_id: str, shift_ids: List[str], action: str = "pin"
) -> Dict[str, Any]:
    """
    Pin or unpin shifts to prevent changes during optimization

    Args:
        job_id: ID of the active optimization job
        shift_ids: List of shift IDs to pin/unpin
        action: Either "pin" or "unpin"

    Returns:
        Success status and details of the pin operation
    """
    if action not in ["pin", "unpin"]:
        raise ValueError("Action must be 'pin' or 'unpin'")

    request_data = {"shift_ids": shift_ids, "action": action}
    return await call_continuous_planning_api(f"/api/shifts/{job_id}/pin", request_data)


async def reassign_shift(
    ctx: Context, job_id: str, shift_id: str, new_employee_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reassign a shift to a specific employee or unassign it

    Args:
        job_id: ID of the active optimization job
        shift_id: ID of the shift to reassign
        new_employee_id: ID of new employee (None to unassign)

    Returns:
        Success status and reassignment details
    """
    request_data = {"shift_id": shift_id, "new_employee_id": new_employee_id}
    return await call_continuous_planning_api(
        f"/api/shifts/{job_id}/reassign", request_data
    )


async def restart_job(ctx: Context, job_id: str) -> Dict[str, Any]:
    """
    Restart a completed job to enable continuous planning modifications

    Args:
        job_id: ID of the completed optimization job

    Returns:
        Success status and new job status
    """
    return await call_api("POST", f"/api/shifts/{job_id}/restart")


# Employee Management tools
class AddEmployeeRequest(BaseModel):
    """Request to add a single employee"""

    id: str = Field(..., description="Unique employee ID")
    name: str = Field(..., description="Employee name")
    skills: List[str] = Field(..., min_items=1, description="Employee skills")
    preferred_days_off: List[str] = Field(
        default_factory=list, description="Days employee prefers not to work"
    )
    preferred_work_days: List[str] = Field(
        default_factory=list, description="Days employee prefers to work"
    )
    unavailable_dates: List[str] = Field(
        default_factory=list,
        description="Specific dates when employee is unavailable (ISO format)",
    )


class AddEmployeesBatchRequest(BaseModel):
    """Request to add multiple employees"""

    employees: List[AddEmployeeRequest] = Field(
        ..., min_items=1, description="List of employees to add"
    )


class AddEmployeeAndAssignRequest(BaseModel):
    """Request to add employee and assign to shift"""

    employee: AddEmployeeRequest = Field(..., description="Employee to add")
    shift_id: str = Field(..., description="ID of shift to assign employee to")


async def add_employee_to_job(
    ctx: Context,
    job_id: str,
    employee_id: str,
    name: str,
    skills: List[str],
    preferred_days_off: Optional[List[str]] = None,
    preferred_work_days: Optional[List[str]] = None,
    unavailable_dates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Add a new employee to an active solving job

    Args:
        job_id: ID of the active optimization job
        employee_id: Unique employee ID
        name: Employee name
        skills: List of employee skills
        preferred_days_off: Days employee prefers not to work
        preferred_work_days: Days employee prefers to work
        unavailable_dates: Specific dates when employee is unavailable (ISO format)

    Returns:
        Success status and employee addition details
    """
    request_data = {
        "id": employee_id,
        "name": name,
        "skills": skills,
        "preferred_days_off": parse_list_param(preferred_days_off),
        "preferred_work_days": parse_list_param(preferred_work_days),
        "unavailable_dates": parse_list_param(unavailable_dates),
    }
    return await call_continuous_planning_api(
        f"/api/shifts/{job_id}/add-employee", request_data
    )


async def add_employees_batch_to_job(
    ctx: Context, job_id: str, employees: List[AddEmployeeRequest]
) -> Dict[str, Any]:
    """
    Add multiple employees to an active solving job

    Args:
        job_id: ID of the active optimization job
        employees: List of employees to add

    Returns:
        Success status and batch addition details
    """
    request_data = {"employees": [emp.model_dump() for emp in employees]}
    return await call_continuous_planning_api(
        f"/api/shifts/{job_id}/add-employees", request_data
    )


async def remove_employee_from_job(
    ctx: Context, job_id: str, employee_id: str
) -> Dict[str, Any]:
    """
    Remove an employee from an active solving job

    Args:
        job_id: ID of the active optimization job
        employee_id: ID of the employee to remove

    Returns:
        Success status and removal details (any assigned shifts will be unassigned)
    """
    return await call_api(
        "DELETE", f"/api/shifts/{job_id}/remove-employee/{employee_id}"
    )


async def add_employee_and_assign_to_shift(
    ctx: Context,
    job_id: str,
    employee_id: str,
    name: str,
    skills: List[str],
    shift_id: str,
    preferred_days_off: Optional[List[str]] = None,
    preferred_work_days: Optional[List[str]] = None,
    unavailable_dates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Add a new employee and immediately assign them to a specific shift

    Args:
        job_id: ID of the active optimization job
        employee_id: Unique employee ID
        name: Employee name
        skills: List of employee skills
        shift_id: ID of shift to assign the new employee to
        preferred_days_off: Days employee prefers not to work
        preferred_work_days: Days employee prefers to work
        unavailable_dates: Specific dates when employee is unavailable (ISO format)

    Returns:
        Success status and assignment details
    """
    employee_data = {
        "id": employee_id,
        "name": name,
        "skills": skills,
        "preferred_days_off": parse_list_param(preferred_days_off),
        "preferred_work_days": parse_list_param(preferred_work_days),
        "unavailable_dates": parse_list_param(unavailable_dates),
    }
    request_data = {"employee": employee_data, "shift_id": shift_id}
    return await call_continuous_planning_api(
        f"/api/shifts/{job_id}/add-employee-assign", request_data
    )
