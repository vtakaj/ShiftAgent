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
    """シフトクラス"""

    id: str
    start_time: datetime
    end_time: datetime
    required_skills: set[str] = field(default_factory=set)
    location: str | None = None
    priority: int = 5  # 1が最高優先度、10が最低優先度

    # Timefold Solverによって最適化される変数
    employee: Annotated[Employee | None, PlanningVariable] = field(default=None)

    # Pinning field for continuous planning
    # When pinned is True, Timefold will not change the employee assignment
    pinned: Annotated[bool, PlanningPin] = field(default=False)

    def get_duration_minutes(self) -> int:
        """シフトの時間（分）を取得"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def overlaps_with(self, other: "Shift") -> bool:
        """他のシフトと時間が重複するかチェック"""
        if other is None:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time

    def is_assigned(self) -> bool:
        """従業員が割り当てられているかチェック"""
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
        employee_name = self.employee.name if self.employee else "未割り当て"
        return (
            f"Shift(id='{self.id}', "
            f"start={self.start_time.strftime('%Y-%m-%d %H:%M')}, "
            f"end={self.end_time.strftime('%Y-%m-%d %H:%M')}, "
            f"skills={self.required_skills}, employee='{employee_name}')"
        )
