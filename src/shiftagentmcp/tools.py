"""
MCP tools for ShiftAgent operations
"""

import json
import os
from datetime import datetime
from typing import Any

import httpx
from fastmcp import Context
from pydantic import BaseModel, Field

# Configuration
API_BASE_URL = os.getenv("SHIFTAGENT_API_URL", "http://localhost:8081")


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
    """Make an API call to the ShiftAgent"""
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
    """Check if the ShiftAgent API is healthy"""
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

    result = await call_api("POST", "/api/shifts/solve-sync", request_data)

    # Add user-friendly message about HTML report
    if result.get("html_report_url"):
        result["html_report_message"] = (
            f"✨ Schedule optimized! View the formatted HTML report at: "
            f"http://localhost:8081{result['html_report_url']}"
        )

    return result


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
    result = await call_api("GET", f"/api/shifts/solve/{job_id}")

    # Add a user-friendly message about the HTML report if job is completed
    if result.get("status") == "SOLVING_COMPLETED" and result.get("html_report_url"):
        result["html_report_message"] = (
            f"✨ Schedule completed! View the formatted HTML report at: "
            f"http://localhost:8081{result['html_report_url']}"
        )

    return result


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

    # Make direct PATCH request with list body
    url = f"{API_BASE_URL}/api/shifts/{job_id}/employee/{employee_id}/skills"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.patch(url, json=parsed_skills)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


async def get_schedule_html_report(ctx: Context, job_id: str) -> dict[str, Any]:
    """
    Get completed schedule as HTML report

    This tool generates a beautiful HTML schedule report that can be viewed in a browser
    or saved as a file. The report includes visual calendar layout, constraint violations,
    and employee preferences.

    Args:
        job_id: ID of the completed optimization job

    Returns:
        HTML content and metadata for the schedule report
    """
    try:
        # Get HTML content from API
        url = f"{API_BASE_URL}/api/shifts/solve/{job_id}/html"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

            return {
                "html_content": html_content,
                "content_type": "text/html",
                "job_id": job_id,
                "generated_at": datetime.now().isoformat(),
                "message": "HTML report generated successfully. You can save this to a file and open in a browser.",
            }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": "Job not found", "job_id": job_id}
        elif e.response.status_code == 400:
            return {"error": "Job not completed yet", "job_id": job_id}
        else:
            return {"error": f"API error: {e.response.status_code}", "job_id": job_id}
    except Exception as e:
        return {"error": f"Failed to generate HTML report: {str(e)}", "job_id": job_id}


# Continuous Planning Tools
async def swap_shifts(
    ctx: Context, job_id: str, shift1_id: str, shift2_id: str
) -> dict[str, Any]:
    """
    Swap employees between two shifts during optimization

    This tool swaps the employee assignments between two shifts in a completed schedule.
    It performs a targeted re-optimization to find the best possible assignment after the swap.

    Args:
        job_id: ID of the completed optimization job
        shift1_id: ID of the first shift to swap
        shift2_id: ID of the second shift to swap

    Returns:
        Success message with swap details and updated schedule statistics
    """
    request_data = {"shift1_id": shift1_id, "shift2_id": shift2_id}
    return await call_api("POST", f"/api/shifts/{job_id}/swap", request_data)


async def reassign_shift(
    ctx: Context,
    job_id: str,
    shift_id: str,
    employee_id: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Reassign a shift to a specific employee or unassign it

    This tool allows managers to manually override the optimizer's decisions by reassigning
    a shift to a specific employee or unassigning it entirely. It validates skill requirements
    and constraints but can be forced to override soft constraint violations.

    Args:
        job_id: ID of the completed optimization job
        shift_id: ID of the shift to reassign
        employee_id: ID of the employee to assign (null/None to unassign)
        force: Whether to override soft constraint violations (default: False)

    Returns:
        Success message with reassignment details, warnings, and updated schedule statistics
    """
    request_data = {
        "shift_id": shift_id,
        "employee_id": employee_id,
        "force": force,
    }
    return await call_api("POST", f"/api/shifts/{job_id}/reassign", request_data)
