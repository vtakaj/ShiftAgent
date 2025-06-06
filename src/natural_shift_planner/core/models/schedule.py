"""
Shift Schedule domain model
"""

from dataclasses import dataclass, field
from typing import Annotated, List

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
    """シフトスケジュール全体を表すクラス"""

    # 問題のファクト（変更されない情報）
    employees: Annotated[
        List[Employee], ProblemFactCollectionProperty, ValueRangeProvider
    ] = field(default_factory=list)

    # 最適化対象のエンティティ
    shifts: Annotated[List[Shift], PlanningEntityCollectionProperty] = field(
        default_factory=list
    )

    # スコア（最適化の結果）
    score: Annotated[HardMediumSoftScore, PlanningScore] = field(default=None)

    def get_employee_count(self) -> int:
        """従業員数を取得"""
        return len(self.employees)

    def get_shift_count(self) -> int:
        """シフト数を取得"""
        return len(self.shifts)

    def get_assigned_shift_count(self) -> int:
        """割り当て済みシフト数を取得"""
        return sum(1 for shift in self.shifts if shift.is_assigned())

    def get_unassigned_shift_count(self) -> int:
        """未割り当てシフト数を取得"""
        return self.get_shift_count() - self.get_assigned_shift_count()

    def add_employee(self, employee: Employee):
        """従業員を追加"""
        self.employees.append(employee)

    def add_shift(self, shift: Shift):
        """シフトを追加"""
        self.shifts.append(shift)

    def __str__(self):
        return (
            f"ShiftSchedule("
            f"employees={len(self.employees)}, "
            f"shifts={len(self.shifts)}, "
            f"assigned={self.get_assigned_shift_count()}, "
            f"score={self.score})"
        )
