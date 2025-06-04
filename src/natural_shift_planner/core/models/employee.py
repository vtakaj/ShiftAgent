"""
Employee domain model
"""
from dataclasses import dataclass, field
from typing import Set


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