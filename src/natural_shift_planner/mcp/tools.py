"""
MCP tools for shift scheduler operations
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import Context
from pydantic import BaseModel, Field

# Configuration
API_BASE_URL = os.getenv("SHIFT_SCHEDULER_API_URL", "http://localhost:8081")


# Pydantic models for API requests
class EmployeeRequest(BaseModel):
    id: str
    name: str
    skills: List[str]


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


async def quick_fix_schedule(
    ctx: Context, base_schedule_id: str, issues: List[str], date_range_days: int = 7
) -> Dict[str, Any]:
    """
    Quick fix common scheduling issues using partial optimization

    Args:
        base_schedule_id: ID of the existing schedule
        issues: List of issues to fix ("overtime", "unassigned", "skills")
        date_range_days: Number of days to optimize (from today)

    Returns:
        Optimization result focusing on fixing specified issues
    """
    from datetime import datetime, timedelta

    today = datetime.now().date()
    end_date = today + timedelta(days=date_range_days)

    # Use partial optimization with focused scope
    return await partial_optimize_schedule(
        ctx,
        base_schedule_id=base_schedule_id,
        start_date=today.isoformat(),
        end_date=end_date.isoformat(),
        preserve_locked=True,
        minimize_changes=True,
    )


# HTML Report tools
async def call_api_html(endpoint: str, timeout: float = 120.0) -> str:
    """Make an API call that returns HTML content"""
    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def get_demo_schedule_html(ctx: Context) -> str:
    """Get a demo shift schedule as HTML report"""
    return await call_api_html("/api/shifts/demo/html")


async def get_schedule_html_report(ctx: Context, job_id: str) -> str:
    """
    Get an optimized schedule as HTML report

    Args:
        job_id: The job ID returned by solve_schedule_async

    Returns:
        HTML report of the completed schedule
    """
    return await call_api_html(f"/api/shifts/solve/{job_id}/html")


async def solve_schedule_sync_html(
    ctx: Context, employees: List[EmployeeRequest], shifts: List[ShiftRequest]
) -> str:
    """
    Solve shift scheduling synchronously and return HTML report

    Args:
        employees: List of employees with their skills
        shifts: List of shifts to be assigned

    Returns:
        HTML report of the optimized schedule
    """
    request_data = {
        "employees": [emp.model_dump() for emp in employees],
        "shifts": [shift.model_dump() for shift in shifts],
    }

    # Parse datetime strings to ensure they're in ISO format
    for shift in request_data["shifts"]:
        shift["start_time"] = datetime.fromisoformat(shift["start_time"]).isoformat()
        shift["end_time"] = datetime.fromisoformat(shift["end_time"]).isoformat()

    url = f"{API_BASE_URL}/api/shifts/solve-sync/html"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=request_data)
        response.raise_for_status()
        return response.text


# PDF Report tools
async def call_api_pdf(
    endpoint: str, data: Optional[Dict[str, Any]] = None, timeout: float = 120.0
) -> bytes:
    """Make an API call that returns PDF content"""
    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        if data:
            response = await client.post(url, json=data)
        else:
            response = await client.get(url)
        response.raise_for_status()
        return response.content


async def get_demo_schedule_pdf(ctx: Context) -> bytes:
    """Get a demo shift schedule as PDF report"""
    return await call_api_pdf("/api/shifts/demo/pdf")


async def get_schedule_pdf_report(ctx: Context, job_id: str) -> bytes:
    """
    Get an optimized schedule as PDF report

    Args:
        job_id: The job ID returned by solve_schedule_async

    Returns:
        PDF report of the completed schedule as bytes
    """
    return await call_api_pdf(f"/api/shifts/solve/{job_id}/pdf")


async def solve_schedule_sync_pdf(
    ctx: Context, employees: List[EmployeeRequest], shifts: List[ShiftRequest]
) -> bytes:
    """
    Solve shift scheduling synchronously and return PDF report

    Args:
        employees: List of employees with their skills
        shifts: List of shifts to be assigned

    Returns:
        PDF report of the optimized schedule as bytes
    """
    request_data = {
        "employees": [emp.model_dump() for emp in employees],
        "shifts": [shift.model_dump() for shift in shifts],
    }

    # Parse datetime strings to ensure they're in ISO format
    for shift in request_data["shifts"]:
        shift["start_time"] = datetime.fromisoformat(shift["start_time"]).isoformat()
        shift["end_time"] = datetime.fromisoformat(shift["end_time"]).isoformat()

    return await call_api_pdf("/api/shifts/solve-sync/pdf", request_data)
