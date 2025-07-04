"""
Shift domain model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated

from timefold.solver.domain import PlanningPin, PlanningVariable, planning_entity

from .employee import Employee


@planning_entity
@dataclass
class Shift:
    """Shift class"""

    id: str
    start_time: datetime
    end_time: datetime
    required_skills: set[str] = field(default_factory=set)
    location: str | None = None
    priority: int = 5  # 1 is highest priority, 10 is lowest priority

    # Variable optimized by Timefold Solver
    employee: Annotated[Employee | None, PlanningVariable] = field(default=None)

    # Pinning field for continuous planning
    # When pinned is True, Timefold will not change the employee assignment
    pinned: Annotated[bool, PlanningPin] = field(default=False)

    def get_duration_minutes(self) -> int:
        """Get the duration of the shift in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def overlaps_with(self, other: "Shift") -> bool:
        """Check if this shift overlaps with another shift"""
        if other is None:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time

    def is_assigned(self) -> bool:
        """Check if an employee is assigned to this shift"""
        return self.employee is not None

    def pin(self) -> None:
        """Pin this shift to prevent employee reassignment during solving"""
        self.pinned = True

    def unpin(self) -> None:
        """Unpin this shift to allow employee reassignment during solving"""
        self.pinned = False

    def is_pinned(self) -> bool:
        """Check if this shift is pinned"""
        return self.pinned

    def __str__(self):
        employee_name = (
            self.employee.name
            if self.employee is not None and hasattr(self.employee, "name")
            else "Unassigned"
        )
        return (
            f"Shift(id='{self.id}', "
            f"start={self.start_time.strftime('%Y-%m-%d %H:%M')}, "
            f"end={self.end_time.strftime('%Y-%m-%d %H:%M')}, "
            f"skills={self.required_skills}, employee='{employee_name}')"
        )
