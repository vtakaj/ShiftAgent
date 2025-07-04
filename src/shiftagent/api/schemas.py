"""
API request/response schemas using Pydantic
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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
    unavailable_dates: list[datetime] = Field(
        default_factory=list,
        description="Specific dates when employee is unavailable. Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Examples: '2024-01-15T00:00:00', '2024-01-15'. Time component is optional and will be normalized to date-only for comparison.",
    )
    max_hours_per_week: int | None = Field(
        default=None,
        description="Maximum hours per week for the employee",
    )
    min_hours_per_week: int | None = Field(
        default=None,
        description="Minimum hours per week for the employee",
    )


class BatchEmployeeRequest(BaseModel):
    employees: list[EmployeeRequest] = Field(
        description="List of employees to add to the job"
    )
    auto_assign: bool = Field(
        default=False,
        description="Whether to automatically assign new employees to unassigned shifts",
    )


class EmployeeAdditionResult(BaseModel):
    employee_id: str
    employee_name: str
    status: str  # SUCCESS, FAILED, SKIPPED
    message: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assigned_shifts: int = 0


class BatchEmployeeResponse(BaseModel):
    job_id: str
    total_employees: int
    successful_additions: int
    failed_additions: int
    skipped_additions: int
    overall_status: str  # SUCCESS, PARTIAL_SUCCESS, FAILED
    message: str
    results: list[EmployeeAdditionResult]
    final_score: str | None = None
    html_report_url: str | None = None


class ShiftRequest(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    required_skills: list[str]
    location: str | None = None
    priority: int = 5


class ShiftScheduleRequest(BaseModel):
    employees: list[EmployeeRequest]
    shifts: list[ShiftRequest]


class SolveResponse(BaseModel):
    job_id: str
    status: str


class SwapShiftsRequest(BaseModel):
    shift1_id: str = Field(description="ID of the first shift to swap")
    shift2_id: str = Field(description="ID of the second shift to swap")


class SwapShiftsResponse(BaseModel):
    job_id: str
    shift1_id: str
    shift2_id: str
    status: str
    message: str
    final_score: str | None = None
    html_report_url: str | None = None


class ReassignShiftRequest(BaseModel):
    shift_id: str = Field(description="ID of the shift to reassign")
    employee_id: str | None = Field(
        description="ID of the employee to assign (null to unassign)"
    )
    force: bool = Field(
        default=False, description="Override soft constraint violations"
    )


class ReassignShiftResponse(BaseModel):
    job_id: str
    shift_id: str
    employee_id: str | None
    employee_name: str | None
    status: str
    message: str
    warnings: list[str] = Field(default_factory=list)
    final_score: str | None = None
    html_report_url: str | None = None


class SolutionResponse(BaseModel):
    job_id: str
    status: str
    solution: dict[str, Any] | None = None
    score: str | None = None
    assigned_shifts: int | None = None
    unassigned_shifts: int | None = None
    message: str | None = None
    html_report_url: str | None = Field(
        None, description="URL to view the schedule as a formatted HTML report"
    )
