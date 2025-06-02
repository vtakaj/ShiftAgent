"""
Shift Scheduler - Employee shift scheduling using Timefold Solver

A FastAPI-based application for optimizing employee shift schedules
with constraint satisfaction using Timefold Solver.
"""

__version__ = "1.0.0"
__author__ = "Shift Scheduler Team"

# パッケージレベルのインポート
from .models import Employee, Shift, ShiftSchedule
from .constraints import shift_scheduling_constraints

__all__ = [
    "Employee",
    "Shift", 
    "ShiftSchedule",
    "shift_scheduling_constraints",
]