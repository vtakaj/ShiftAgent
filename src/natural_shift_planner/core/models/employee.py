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
        if self.preferred_days_off is None or len(self.preferred_days_off) == 0:
            return False
        day_lower = day_name.lower()
        for pref_day in self.preferred_days_off:
            if pref_day is not None and pref_day.lower() == day_lower:
                return True
        return False

    def prefers_work_day(self, day_name: str) -> bool:
        """Check if employee prefers to work on this day"""
        if self.preferred_work_days is None or len(self.preferred_work_days) == 0:
            return False
        day_lower = day_name.lower()
        for pref_day in self.preferred_work_days:
            if pref_day is not None and pref_day.lower() == day_lower:
                return True
        return False

    def is_unavailable_on_date(self, date: datetime) -> bool:
        """Check if employee is unavailable on a specific date"""
        # Handle None or empty unavailable_dates safely
        if self.unavailable_dates is None or len(self.unavailable_dates) == 0:
            return False
        
        # Normalize the input date to date-only (remove time components)
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check each unavailable date explicitly to avoid generator expression issues
        for unavailable_date in self.unavailable_dates:
            if unavailable_date is None:
                continue
            unavailable_only = unavailable_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            if unavailable_only == date_only:
                return True
        
        return False

    def __str__(self):
        return f"Employee(id='{self.id}', name='{self.name}', skills={self.skills})"
