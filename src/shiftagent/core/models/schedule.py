"""
Shift Schedule domain model
"""

from dataclasses import dataclass, field
from typing import Annotated

from timefold.solver.domain import (
    PlanningEntityCollectionProperty,
    PlanningScore,
    ProblemFactCollectionProperty,
    ValueRangeProvider,
    planning_solution,
)
from timefold.solver.score import HardMediumSoftScore

from .employee import Employee
from .shift import Shift


@planning_solution
@dataclass
class ShiftSchedule:
    """Class representing the entire shift schedule"""

    # Problem facts (information that doesn't change)
    employees: Annotated[
        list[Employee], ProblemFactCollectionProperty, ValueRangeProvider
    ] = field(default_factory=list)

    # Planning entities (optimization targets)
    shifts: Annotated[list[Shift], PlanningEntityCollectionProperty] = field(
        default_factory=list
    )

    # Score (optimization result)
    score: Annotated[HardMediumSoftScore, PlanningScore] = field(
        default=HardMediumSoftScore.ZERO
    )

    def get_employee_count(self) -> int:
        """Get the number of employees"""
        return len(self.employees)

    def get_shift_count(self) -> int:
        """Get the number of shifts"""
        return len(self.shifts)

    def get_assigned_shift_count(self) -> int:
        """Get the number of assigned shifts"""
        return sum(1 for shift in self.shifts if shift.is_assigned())

    def get_unassigned_shift_count(self) -> int:
        """Get the number of unassigned shifts"""
        return self.get_shift_count() - self.get_assigned_shift_count()

    def add_employee(self, employee: Employee):
        """Add an employee"""
        self.employees.append(employee)

    def add_shift(self, shift: Shift):
        """Add a shift"""
        self.shifts.append(shift)

    def __str__(self):
        return (
            f"ShiftSchedule("
            f"employees={len(self.employees)}, "
            f"shifts={len(self.shifts)}, "
            f"assigned={self.get_assigned_shift_count()}, "
            f"score={self.score})"
        )
