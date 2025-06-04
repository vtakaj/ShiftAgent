"""
Shift domain model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Optional, Set

from timefold.solver.domain import PlanningVariable, planning_entity

from .employee import Employee


@planning_entity
@dataclass
class Shift:
    """シフトクラス"""

    id: str
    start_time: datetime
    end_time: datetime
    required_skills: Set[str] = field(default_factory=set)
    location: Optional[str] = None
    priority: int = 5  # 1が最高優先度、10が最低優先度

    # Timefold Solverによって最適化される変数
    employee: Annotated[Optional[Employee], PlanningVariable] = field(default=None)

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

    def __str__(self):
        employee_name = self.employee.name if self.employee else "未割り当て"
        return (
            f"Shift(id='{self.id}', "
            f"start={self.start_time.strftime('%Y-%m-%d %H:%M')}, "
            f"end={self.end_time.strftime('%Y-%m-%d %H:%M')}, "
            f"skills={self.required_skills}, employee='{employee_name}')"
        )