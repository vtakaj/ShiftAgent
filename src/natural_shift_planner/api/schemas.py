"""
API request/response schemas using Pydantic
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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