"""
Tests for partial shift modification functionality
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from natural_shift_planner.api.partial_modifications import (
    apply_shift_modification,
    calculate_weekly_impact,
    check_shift_modification_constraints,
)
from natural_shift_planner.core.models import Employee, Shift, ShiftSchedule


def create_test_employees():
    """Create test employees"""
    return [
        Employee("emp1", "John Doe", {"Nurse", "CPR", "Full-time"}),
        Employee("emp2", "Jane Smith", {"Nurse", "Full-time"}),
        Employee("emp3", "Bob Johnson", {"Security", "Full-time"}),
        Employee("emp4", "Alice Brown", {"Reception", "Part-time"}),
    ]


def create_test_shifts():
    """Create test shifts"""
    base_date = datetime(2025, 6, 10, 0, 0)  # Monday
    shifts = []

    # Morning shifts
    for day in range(5):  # Monday to Friday
        shift_date = base_date + timedelta(days=day)
        shifts.append(
            Shift(
                id=f"morning_{day}",
                start_time=shift_date.replace(hour=8),
                end_time=shift_date.replace(hour=16),
                required_skills={"Nurse"},
                location="Hospital",
            )
        )

    # Evening shifts
    for day in range(5):  # Monday to Friday
        shift_date = base_date + timedelta(days=day)
        shifts.append(
            Shift(
                id=f"evening_{day}",
                start_time=shift_date.replace(hour=16),
                end_time=shift_date.replace(hour=23, minute=59),
                required_skills={"Nurse"},
                location="Hospital",
            )
        )

    # Security shift
    shifts.append(
        Shift(
            id="security_0",
            start_time=base_date.replace(hour=22),
            end_time=(base_date + timedelta(days=1)).replace(hour=6),
            required_skills={"Security"},
            location="Hospital",
        )
    )

    return shifts


class TestShiftLocking:
    """Test shift locking functionality"""

    def test_lock_shift(self):
        """Test locking a shift"""
        shift = Shift(
            id="test_shift",
            start_time=datetime(2025, 6, 10, 8, 0),
            end_time=datetime(2025, 6, 10, 16, 0),
            required_skills={"Nurse"},
        )

        assert not shift.is_locked
        assert shift.can_modify()

        # Lock the shift
        shift.lock("user123", "Manager approval")

        assert shift.is_locked
        assert not shift.can_modify()
        assert shift.locked_by == "user123"
        assert shift.lock_reason == "Manager approval"
        assert shift.locked_at is not None

    def test_unlock_shift(self):
        """Test unlocking a shift"""
        shift = Shift(
            id="test_shift",
            start_time=datetime(2025, 6, 10, 8, 0),
            end_time=datetime(2025, 6, 10, 16, 0),
            required_skills={"Nurse"},
        )

        # Lock then unlock
        shift.lock("user123", "Test")
        shift.unlock()

        assert not shift.is_locked
        assert shift.can_modify()
        assert shift.locked_by is None
        assert shift.lock_reason is None
        assert shift.locked_at is None


class TestConstraintChecking:
    """Test constraint checking for modifications"""

    def test_check_locked_shift_constraint(self):
        """Test that locked shifts cannot be modified"""
        employees = create_test_employees()
        shifts = create_test_shifts()

        # Assign and lock a shift
        shifts[0].employee = employees[0]
        shifts[0].lock("manager", "Confirmed")

        schedule = ShiftSchedule(employees=employees, shifts=shifts)

        # Try to modify locked shift
        violations, warnings = check_shift_modification_constraints(
            shifts[0], employees[1], schedule
        )

        # Should have a hard constraint violation
        assert len(violations) > 0
        assert any(v.constraint_name == "shift_locked" for v in violations)
        assert any(v.type == "hard" for v in violations)

    def test_check_skill_constraint(self):
        """Test skill requirement constraints"""
        employees = create_test_employees()
        shifts = create_test_shifts()
        schedule = ShiftSchedule(employees=employees, shifts=shifts)

        # Try to assign nurse shift to security guard
        violations, warnings = check_shift_modification_constraints(
            shifts[0], employees[2], schedule  # Nurse shift  # Security guard
        )

        # Should have skill violation
        assert len(violations) > 0
        assert any(v.constraint_name == "skill_requirement" for v in violations)

    def test_check_overlap_constraint(self):
        """Test overlapping shift constraints"""
        employees = create_test_employees()
        shifts = create_test_shifts()

        # Create an overlapping shift
        overlapping_shift = Shift(
            id="overlap_test",
            start_time=datetime(2025, 6, 10, 15, 0),  # 3 PM
            end_time=datetime(2025, 6, 10, 20, 0),  # 8 PM
            required_skills={"Nurse"},
            location="Hospital",
        )

        # Assign employee to a shift that overlaps with the test shift
        shifts[0].employee = employees[0]  # 8 AM - 4 PM
        shifts.append(overlapping_shift)

        schedule = ShiftSchedule(employees=employees, shifts=shifts)

        # Try to assign same employee to overlapping shift
        violations, warnings = check_shift_modification_constraints(
            overlapping_shift, employees[0], schedule
        )

        # Should have overlap violation
        assert len(violations) > 0
        assert any(v.constraint_name == "shift_overlap" for v in violations)

    def test_check_weekly_hours_constraint(self):
        """Test weekly hours constraints"""
        employees = create_test_employees()
        shifts = create_test_shifts()

        # Assign employee to multiple shifts (5 days * 8 hours = 40 hours)
        for i in range(5):
            shifts[i].employee = employees[0]

        schedule = ShiftSchedule(employees=employees, shifts=shifts)

        # Try to assign one more 8-hour shift (would be 48 hours)
        violations, warnings = check_shift_modification_constraints(
            shifts[5], employees[0], schedule  # Another 8-hour shift
        )

        # Should have hard violation (>45 hours)
        assert len(violations) > 0
        assert any(v.constraint_name == "max_weekly_hours" for v in violations)
        assert any(v.type == "hard" for v in violations)


class TestWeeklyImpact:
    """Test weekly impact calculations"""

    def test_calculate_weekly_impact_add_shift(self):
        """Test impact when adding a shift to an employee"""
        employees = create_test_employees()
        shifts = create_test_shifts()

        # Employee has one shift (8 hours)
        shifts[0].employee = employees[0]

        schedule = ShiftSchedule(employees=employees, shifts=shifts)

        # Calculate impact of adding another shift
        impacts = calculate_weekly_impact(
            shifts[1],  # Unassigned shift
            None,  # No previous employee
            employees[0],  # Assign to emp1
            schedule,
        )

        assert employees[0].id in impacts
        impact = impacts[employees[0].id]
        assert impact.old_hours == 8.0
        assert impact.new_hours == 16.0
        assert impact.change == 8.0
        # 16 hours is still undertime for full-time employee (min 32 hours)
        assert impact.status == "undertime"

    def test_calculate_weekly_impact_reassign(self):
        """Test impact when reassigning a shift"""
        employees = create_test_employees()
        shifts = create_test_shifts()

        # Initial assignment
        shifts[0].employee = employees[0]
        shifts[1].employee = employees[0]  # 16 hours total

        schedule = ShiftSchedule(employees=employees, shifts=shifts)

        # Calculate impact of reassigning
        impacts = calculate_weekly_impact(
            shifts[1],
            employees[0],  # Remove from emp1
            employees[1],  # Assign to emp2
            schedule,
        )

        # Check impact on both employees
        assert len(impacts) == 2

        # Employee losing the shift
        assert employees[0].id in impacts
        assert impacts[employees[0].id].old_hours == 16.0
        assert impacts[employees[0].id].new_hours == 8.0
        assert impacts[employees[0].id].change == -8.0

        # Employee gaining the shift
        assert employees[1].id in impacts
        assert impacts[employees[1].id].old_hours == 0.0
        assert impacts[employees[1].id].new_hours == 8.0
        assert impacts[employees[1].id].change == 8.0


class TestApplyModification:
    """Test applying modifications"""

    def test_apply_modification_success(self):
        """Test successful modification"""
        employees = create_test_employees()
        shift = Shift(
            id="test_shift",
            start_time=datetime(2025, 6, 10, 8, 0),
            end_time=datetime(2025, 6, 10, 16, 0),
            required_skills={"Nurse"},
        )

        # Apply modification
        success = apply_shift_modification(shift, employees[0], dry_run=False)

        assert success
        assert shift.employee == employees[0]

    def test_apply_modification_locked_fails(self):
        """Test that locked shift modification fails"""
        employees = create_test_employees()
        shift = Shift(
            id="test_shift",
            start_time=datetime(2025, 6, 10, 8, 0),
            end_time=datetime(2025, 6, 10, 16, 0),
            required_skills={"Nurse"},
        )

        # Lock the shift
        shift.lock("manager", "Confirmed")

        # Try to modify
        success = apply_shift_modification(shift, employees[0], dry_run=False)

        assert not success
        assert shift.employee is None  # Should remain unchanged

    def test_apply_modification_dry_run(self):
        """Test dry run doesn't change shift"""
        employees = create_test_employees()
        shift = Shift(
            id="test_shift",
            start_time=datetime(2025, 6, 10, 8, 0),
            end_time=datetime(2025, 6, 10, 16, 0),
            required_skills={"Nurse"},
        )

        # Apply in dry run mode
        success = apply_shift_modification(shift, employees[0], dry_run=True)

        assert success
        assert shift.employee is None  # Should not be changed
