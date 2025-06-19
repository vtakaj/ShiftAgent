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
