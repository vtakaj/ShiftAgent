from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, List, Optional, Set

from timefold.solver.domain import (
    PlanningEntityCollectionProperty,
    PlanningScore,
    PlanningVariable,
    ProblemFactCollectionProperty,
    ValueRangeProvider,
    planning_entity,
    planning_solution,
)
from timefold.solver.score import HardMediumSoftScore


@dataclass
class Employee:
    """従業員クラス"""

    id: str
    name: str
    skills: Set[str] = field(default_factory=set)

    def has_skill(self, skill: str) -> bool:
        """指定されたスキルを持っているかチェック"""
        return skill in self.skills

    def has_all_skills(self, required_skills: Set[str]) -> bool:
        """必要なスキルをすべて持っているかチェック"""
        return required_skills.issubset(self.skills)

    def __str__(self):
        return f"Employee(id='{self.id}', name='{self.name}', skills={self.skills})"


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


from typing import Any, Dict

# APIリクエスト/レスポンス用のPydanticモデル
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
