"""
Partial shift modification functionality
"""

from typing import Dict, List, Optional, Tuple

from ..core.models import Employee, Shift, ShiftSchedule
from .analysis import analyze_weekly_hours, get_week_key
from .schemas import ConstraintViolation, WeeklyImpact


def check_shift_modification_constraints(
    shift: Shift, new_employee: Optional[Employee], schedule: ShiftSchedule
) -> Tuple[List[ConstraintViolation], List[str]]:
    """
    Check if a shift modification would violate any constraints

    Returns:
        Tuple of (constraint_violations, warnings)
    """
    violations = []
    warnings = []

    # Check if shift is locked
    if shift.is_locked:
        violations.append(
            ConstraintViolation(
                type="hard",
                constraint_name="shift_locked",
                description=f"Shift {shift.id} is locked and cannot be modified",
                severity="error",
            )
        )
        return violations, warnings

    if new_employee is None:
        # Unassigning is always allowed if not locked
        return violations, warnings

    # Check skill requirements
    if not new_employee.has_all_skills(shift.required_skills):
        missing_skills = shift.required_skills - new_employee.skills
        violations.append(
            ConstraintViolation(
                type="hard",
                constraint_name="skill_requirement",
                description=f"Employee {new_employee.name} lacks required skills: {missing_skills}",
                severity="error",
            )
        )

    # Check for overlapping shifts
    for other_shift in schedule.shifts:
        if (
            other_shift.id != shift.id
            and other_shift.employee == new_employee
            and shift.overlaps_with(other_shift)
        ):
            violations.append(
                ConstraintViolation(
                    type="hard",
                    constraint_name="shift_overlap",
                    description=f"Employee {new_employee.name} already has overlapping shift {other_shift.id}",
                    severity="error",
                )
            )

    # Check weekly hours constraints
    week_key = get_week_key(shift.start_time)
    weekly_minutes = 0

    # Calculate current weekly hours for the new employee
    for s in schedule.shifts:
        if s.employee == new_employee and get_week_key(s.start_time) == week_key:
            if s.id != shift.id:  # Don't count the shift being modified
                weekly_minutes += s.get_duration_minutes()

    # Add the shift being assigned
    weekly_minutes += shift.get_duration_minutes()
    weekly_hours = weekly_minutes / 60

    # Check hard constraint: max 45 hours
    if weekly_hours > 45:
        violations.append(
            ConstraintViolation(
                type="hard",
                constraint_name="max_weekly_hours",
                description=f"Employee {new_employee.name} would have {weekly_hours:.1f} hours (max 45)",
                severity="error",
            )
        )

    # Check medium constraint: full-time minimum hours
    if "Full-time" in new_employee.skills and weekly_hours < 32:
        violations.append(
            ConstraintViolation(
                type="medium",
                constraint_name="min_weekly_hours",
                description=f"Full-time employee {new_employee.name} would have only {weekly_hours:.1f} hours (min 32)",
                severity="warning",
            )
        )

    # Warnings for soft constraints
    if weekly_hours > 40:
        warnings.append(
            f"Employee {new_employee.name} will have {weekly_hours:.1f} hours this week (overtime)"
        )

    # Check minimum rest time if there are adjacent shifts
    min_rest_minutes = 8 * 60  # 8 hours
    for other_shift in schedule.shifts:
        if other_shift.employee == new_employee and other_shift.id != shift.id:
            # Check if shifts are adjacent
            if other_shift.end_time <= shift.start_time:
                rest_time = (
                    shift.start_time - other_shift.end_time
                ).total_seconds() / 60
                if rest_time < min_rest_minutes:
                    violations.append(
                        ConstraintViolation(
                            type="medium",
                            constraint_name="min_rest_time",
                            description=f"Only {rest_time/60:.1f} hours rest before shift (min 8 hours)",
                            severity="warning",
                        )
                    )
            elif shift.end_time <= other_shift.start_time:
                rest_time = (
                    other_shift.start_time - shift.end_time
                ).total_seconds() / 60
                if rest_time < min_rest_minutes:
                    violations.append(
                        ConstraintViolation(
                            type="medium",
                            constraint_name="min_rest_time",
                            description=f"Only {rest_time/60:.1f} hours rest after shift (min 8 hours)",
                            severity="warning",
                        )
                    )

    return violations, warnings


def calculate_weekly_impact(
    shift: Shift,
    old_employee: Optional[Employee],
    new_employee: Optional[Employee],
    schedule: ShiftSchedule,
) -> Dict[str, WeeklyImpact]:
    """
    Calculate the weekly hours impact of a shift modification
    """
    impacts = {}
    week_key = get_week_key(shift.start_time)
    shift_hours = shift.get_duration_minutes() / 60

    # Impact on old employee (if any)
    if old_employee:
        old_weekly_minutes = 0
        for s in schedule.shifts:
            if s.employee == old_employee and get_week_key(s.start_time) == week_key:
                old_weekly_minutes += s.get_duration_minutes()

        old_hours = old_weekly_minutes / 60
        new_hours = old_hours - shift_hours

        status = "normal"
        if new_hours > 45:
            status = "overtime_violation"
        elif new_hours > 40:
            status = "overtime_warning"
        elif "Full-time" in old_employee.skills and new_hours < 32:
            status = "undertime"

        impacts[old_employee.id] = WeeklyImpact(
            employee_id=old_employee.id,
            employee_name=old_employee.name,
            old_hours=old_hours,
            new_hours=new_hours,
            change=-shift_hours,
            status=status,
        )

    # Impact on new employee (if any)
    if new_employee:
        new_weekly_minutes = 0
        for s in schedule.shifts:
            if s.employee == new_employee and get_week_key(s.start_time) == week_key:
                if s.id != shift.id:  # Don't count the shift being modified
                    new_weekly_minutes += s.get_duration_minutes()

        old_hours = new_weekly_minutes / 60
        new_hours = old_hours + shift_hours

        status = "normal"
        if new_hours > 45:
            status = "overtime_violation"
        elif new_hours > 40:
            status = "overtime_warning"
        elif "Full-time" in new_employee.skills and new_hours < 32:
            status = "undertime"

        impacts[new_employee.id] = WeeklyImpact(
            employee_id=new_employee.id,
            employee_name=new_employee.name,
            old_hours=old_hours,
            new_hours=new_hours,
            change=shift_hours,
            status=status,
        )

    return impacts


def apply_shift_modification(
    shift: Shift, new_employee: Optional[Employee], dry_run: bool = False
) -> bool:
    """
    Apply a shift modification

    Returns:
        True if modification was applied (or would be in dry_run mode)
    """
    if shift.is_locked:
        return False

    if not dry_run:
        shift.employee = new_employee

    return True
