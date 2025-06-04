"""
API request/response schemas using Pydantic
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class EmployeeRequest(BaseModel):
    id: str
    name: str
    skills: List[str]


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


# Partial modification schemas
class ShiftModificationRequest(BaseModel):
    """Request to modify an individual shift assignment"""
    employee_id: Optional[str] = Field(None, description="New employee ID, null to unassign")
    check_constraints: bool = Field(True, description="Check constraints before applying")
    dry_run: bool = Field(False, description="Simulate change without applying")


class ShiftLockRequest(BaseModel):
    """Request to lock or unlock shifts"""
    shift_ids: List[str] = Field(..., min_items=1)
    action: Literal["lock", "unlock"]
    reason: Optional[str] = Field(None, description="Reason for locking")
    locked_by: Optional[str] = Field(None, description="User who is locking")


class DateRange(BaseModel):
    """Date range for partial optimization"""
    start_date: datetime
    end_date: datetime


class OptimizationScope(BaseModel):
    """Scope definition for partial optimization"""
    date_range: Optional[DateRange] = None
    employees: Optional[List[str]] = Field(None, description="Employee IDs to include")
    locations: Optional[List[str]] = Field(None, description="Locations to include")
    shift_types: Optional[List[str]] = Field(None, description="Shift types to include")


class PartialOptimizationRequest(BaseModel):
    """Request for partial schedule optimization"""
    base_schedule_id: str = Field(..., description="ID of existing schedule to modify")
    optimization_scope: OptimizationScope
    preserve_locked: bool = Field(True, description="Keep locked shifts unchanged")
    minimize_changes: bool = Field(False, description="Minimize changes from current state")
    max_reassignments: Optional[int] = Field(None, description="Maximum number of reassignments")


class WeeklyImpact(BaseModel):
    """Weekly hours impact for an employee"""
    employee_id: str
    employee_name: str
    old_hours: float
    new_hours: float
    change: float
    status: Literal["normal", "overtime_warning", "overtime_violation", "undertime"]


class ConstraintViolation(BaseModel):
    """Details of a constraint violation"""
    type: Literal["hard", "medium", "soft"]
    constraint_name: str
    description: str
    severity: Literal["error", "warning", "info"]


class ShiftModificationResponse(BaseModel):
    """Response from shift modification"""
    shift: Dict[str, Any]
    success: bool
    warnings: List[str] = Field(default_factory=list)
    constraint_violations: List[ConstraintViolation] = Field(default_factory=list)
    weekly_impact: Optional[WeeklyImpact] = None


class ShiftLockResponse(BaseModel):
    """Response from shift lock/unlock operation"""
    success: bool
    locked_count: int = 0
    unlocked_count: int = 0
    failed_locks: List[Dict[str, str]] = Field(default_factory=list)
    message: str


class ImpactSummary(BaseModel):
    """Summary of change impact analysis"""
    constraint_violations: List[ConstraintViolation]
    warnings: List[str]
    affected_employees: List[str]
    weekly_hours_impact: Dict[str, Dict[str, float]]
    recommendations: List[str] = Field(default_factory=list)


class ChangeImpactResponse(BaseModel):
    """Response from change impact analysis"""
    impact_summary: ImpactSummary
    is_valid: bool


class PartialOptimizationResponse(BaseModel):
    """Response from partial optimization request"""
    job_id: str
    status: str
    scope_summary: Dict[str, int]
    message: Optional[str] = None