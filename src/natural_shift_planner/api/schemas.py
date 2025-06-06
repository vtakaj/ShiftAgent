"""
API request/response schemas using Pydantic
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


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
    unavailable_dates: List[datetime] = Field(
        default_factory=list, description="Specific dates when employee is unavailable"
    )


class ShiftRequest(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    required_skills: List[str]
    location: Optional[str] = None
    priority: int = 5


class ShiftScheduleRequest(BaseModel):
    employees: List[EmployeeRequest]
    shifts: List[ShiftRequest]


class SolveResponse(BaseModel):
    job_id: str
    status: str


class SolutionResponse(BaseModel):
    job_id: str
    status: str
    solution: Optional[Dict[str, Any]] = None
    score: Optional[str] = None
    assigned_shifts: Optional[int] = None
    unassigned_shifts: Optional[int] = None
    message: Optional[str] = None


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
    excluded_employee_ids: List[str] = Field(
        default_factory=list, description="Additional employees to exclude"
    )


class ShiftPinRequest(BaseModel):
    """Request to pin/unpin shifts for continuous planning"""

    shift_ids: List[str] = Field(..., min_items=1, description="Shift IDs to pin/unpin")
    action: Literal["pin", "unpin"] = Field(..., description="Pin or unpin action")


class ShiftReassignRequest(BaseModel):
    """Request to reassign a shift to a specific employee"""

    shift_id: str = Field(..., description="ID of the shift to reassign")
    new_employee_id: Optional[str] = Field(
        None, description="ID of new employee (None to unassign)"
    )


class ContinuousPlanningResponse(BaseModel):
    """Response from continuous planning operations"""

    success: bool
    message: str
    operation: str
    affected_shifts: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
