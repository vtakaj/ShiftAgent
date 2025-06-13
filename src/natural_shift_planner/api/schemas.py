"""
API request/response schemas using Pydantic
"""

from datetime import datetime
from typing import Any, Literal

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


class SolutionResponse(BaseModel):
    job_id: str
    status: str
    solution: dict[str, Any] | None = None
    score: str | None = None
    assigned_shifts: int | None = None
    unassigned_shifts: int | None = None
    message: str | None = None


# Continuous Planning Schemas
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
    excluded_employee_ids: list[str] = Field(
        default_factory=list, description="Additional employees to exclude"
    )


class ShiftPinRequest(BaseModel):
    """Request to pin/unpin shifts for continuous planning"""

    shift_ids: list[str] = Field(min_length=1, description="Shift IDs to pin/unpin")
    action: Literal["pin", "unpin"] = Field(..., description="Pin or unpin action")


class ShiftReassignRequest(BaseModel):
    """Request to reassign a shift to a specific employee"""

    shift_id: str = Field(..., description="ID of the shift to reassign")
    new_employee_id: str | None = Field(
        None, description="ID of new employee (None to unassign)"
    )


class ContinuousPlanningResponse(BaseModel):
    """Response from continuous planning operations"""

    success: bool
    message: str
    operation: str
    affected_shifts: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# Employee Management Schemas
class AddEmployeeRequest(BaseModel):
    """Request to add a single employee"""

    id: str = Field(..., description="Unique employee ID")
    name: str = Field(..., description="Employee name")
    skills: list[str] = Field(min_length=1, description="Employee skills")
    preferred_days_off: list[str] = Field(
        default_factory=list, description="Days employee prefers not to work"
    )
    preferred_work_days: list[str] = Field(
        default_factory=list, description="Days employee prefers to work"
    )
    unavailable_dates: list[datetime] = Field(
        default_factory=list,
        description="Specific dates when employee is unavailable. Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Examples: '2024-01-15T00:00:00', '2024-01-15'. Time component is optional and will be normalized to date-only for comparison.",
    )


class AddEmployeesBatchRequest(BaseModel):
    """Request to add multiple employees"""

    employees: list[AddEmployeeRequest] = Field(
        min_length=1, description="List of employees to add"
    )


class AddEmployeeAndAssignRequest(BaseModel):
    """Request to add employee and assign to shift"""

    employee: AddEmployeeRequest = Field(..., description="Employee to add")
    shift_id: str = Field(..., description="ID of shift to assign employee to")


class EmployeeManagementResponse(BaseModel):
    """Response from employee management operations"""

    success: bool
    message: str
    operation: Literal["add", "add_batch", "remove", "add_and_assign"]
    employee_ids: list[str] = Field(default_factory=list)
    affected_shifts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
