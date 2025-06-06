"""
Employee domain model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Set


@dataclass
class Employee:
    """従業員クラス"""

    id: str
    name: str
    skills: Set[str] = field(default_factory=set)
    # Employee preference fields
    preferred_days_off: Set[str] = field(
        default_factory=set
    )  # e.g., {"friday", "saturday"}
    preferred_work_days: Set[str] = field(
        default_factory=set
    )  # e.g., {"sunday", "monday"}
    unavailable_dates: Set[datetime] = field(
        default_factory=set
    )  # Specific dates (hard constraint)

    def has_skill(self, skill: str) -> bool:
        """指定されたスキルを持っているかチェック"""
        return skill in self.skills

    def has_all_skills(self, required_skills: Set[str]) -> bool:
        """必要なスキルをすべて持っているかチェック"""
        return required_skills.issubset(self.skills)

    def prefers_day_off(self, day_name: str) -> bool:
        """Check if employee prefers this day off"""
        return day_name.lower() in {day.lower() for day in self.preferred_days_off}

    def prefers_work_day(self, day_name: str) -> bool:
        """Check if employee prefers to work on this day"""
        return day_name.lower() in {day.lower() for day in self.preferred_work_days}

    def is_unavailable_on_date(self, date: datetime) -> bool:
        """Check if employee is unavailable on a specific date"""
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return any(
            unavailable.replace(hour=0, minute=0, second=0, microsecond=0) == date_only
            for unavailable in self.unavailable_dates
        )

    def __str__(self):
        return f"Employee(id='{self.id}', name='{self.name}', skills={self.skills})"
