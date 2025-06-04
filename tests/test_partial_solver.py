"""
Tests for partial solver functionality
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from natural_shift_planner.api.partial_solver import (
    count_modified_shifts,
    create_partial_schedule,
    filter_shifts_by_scope,
    merge_partial_solution,
)
from natural_shift_planner.api.schemas import DateRange, OptimizationScope
from natural_shift_planner.core.models import Employee, Shift, ShiftSchedule


def create_test_schedule():
    """Create a test schedule with multiple shifts"""
    employees = [
        Employee("emp1", "John Doe", {"Nurse", "Full-time"}),
        Employee("emp2", "Jane Smith", {"Nurse", "Full-time"}),
        Employee("emp3", "Bob Johnson", {"Security", "Full-time"}),
    ]
    
    base_date = datetime(2025, 6, 10, 0, 0)  # Monday
    shifts = []
    
    # Create 2 weeks of shifts
    for week in range(2):
        for day in range(7):
            shift_date = base_date + timedelta(weeks=week, days=day)
            
            # Morning nurse shift
            shifts.append(
                Shift(
                    id=f"morning_w{week}_d{day}",
                    start_time=shift_date.replace(hour=8),
                    end_time=shift_date.replace(hour=16),
                    required_skills={"Nurse"},
                    location="Hospital",
                )
            )
            
            # Evening nurse shift
            shifts.append(
                Shift(
                    id=f"evening_w{week}_d{day}",
                    start_time=shift_date.replace(hour=16),
                    end_time=shift_date.replace(hour=23, minute=59),
                    required_skills={"Nurse"},
                    location="Hospital",
                )
            )
            
            # Night security shift
            if day < 6:  # Not on Sunday
                shifts.append(
                    Shift(
                        id=f"security_w{week}_d{day}",
                        start_time=shift_date.replace(hour=22),
                        end_time=(shift_date + timedelta(days=1)).replace(hour=6),
                        required_skills={"Security"},
                        location="Entrance",
                    )
                )
    
    # Assign some shifts
    shifts[0].employee = employees[0]  # Morning week 0 day 0
    shifts[1].employee = employees[1]  # Evening week 0 day 0
    shifts[2].employee = employees[2]  # Security week 0 day 0
    
    return ShiftSchedule(employees=employees, shifts=shifts)


class TestFilterShiftsByScope:
    """Test filtering shifts by optimization scope"""
    
    def test_filter_by_date_range(self):
        """Test filtering shifts by date range"""
        schedule = create_test_schedule()
        
        # Filter first week only
        scope = OptimizationScope(
            date_range=DateRange(
                start_date=datetime(2025, 6, 10),
                end_date=datetime(2025, 6, 16, 23, 59)
            )
        )
        
        in_scope = filter_shifts_by_scope(schedule.shifts, scope)
        
        # Should include all shifts from first week
        expected_count = 7 * 2 + 6  # 7 days * 2 nurse shifts + 6 security shifts
        assert len(in_scope) == expected_count
        
        # All in-scope shifts should be from week 0
        for shift_id in in_scope:
            assert "_w0_" in shift_id
    
    def test_filter_by_location(self):
        """Test filtering shifts by location"""
        schedule = create_test_schedule()
        
        scope = OptimizationScope(
            locations=["Hospital"]
        )
        
        in_scope = filter_shifts_by_scope(schedule.shifts, scope)
        
        # Should only include hospital shifts (morning and evening)
        for shift_id in in_scope:
            assert "morning" in shift_id or "evening" in shift_id
            assert "security" not in shift_id
    
    def test_filter_by_employees(self):
        """Test filtering shifts by employees"""
        schedule = create_test_schedule()
        
        scope = OptimizationScope(
            employees=["emp1", "emp2"]
        )
        
        in_scope = filter_shifts_by_scope(schedule.shifts, scope)
        
        # Should include assigned shifts for emp1 and emp2, plus unassigned shifts
        # that could potentially be assigned to them
        assert len(in_scope) > 0
    
    def test_filter_combined_criteria(self):
        """Test filtering with multiple criteria"""
        schedule = create_test_schedule()
        
        scope = OptimizationScope(
            date_range=DateRange(
                start_date=datetime(2025, 6, 10),
                end_date=datetime(2025, 6, 12, 23, 59)
            ),
            locations=["Hospital"]
        )
        
        in_scope = filter_shifts_by_scope(schedule.shifts, scope)
        
        # Should only include hospital shifts from first 3 days
        expected_count = 3 * 2  # 3 days * 2 nurse shifts
        assert len(in_scope) == expected_count


class TestCreatePartialSchedule:
    """Test creating partial schedules"""
    
    def test_create_partial_schedule_basic(self):
        """Test basic partial schedule creation"""
        schedule = create_test_schedule()
        
        # Lock one shift
        schedule.shifts[0].lock("manager", "Confirmed")
        
        scope = OptimizationScope(
            date_range=DateRange(
                start_date=datetime(2025, 6, 10),
                end_date=datetime(2025, 6, 12, 23, 59)
            )
        )
        
        partial = create_partial_schedule(schedule, scope, preserve_locked=True)
        
        # Should have same number of employees and shifts
        assert len(partial.employees) == len(schedule.employees)
        assert len(partial.shifts) == len(schedule.shifts)
        
        # Locked shift should keep assignment
        locked_shift = next(s for s in partial.shifts if s.id == schedule.shifts[0].id)
        assert locked_shift.is_locked
        assert locked_shift.employee is not None
        assert locked_shift.employee.id == schedule.shifts[0].employee.id
    
    def test_create_partial_schedule_employee_filter(self):
        """Test partial schedule with employee filtering"""
        schedule = create_test_schedule()
        
        scope = OptimizationScope(
            employees=["emp1", "emp2"]
        )
        
        partial = create_partial_schedule(schedule, scope, preserve_locked=False)
        
        # Should only have specified employees
        assert len(partial.employees) == 2
        assert all(e.id in ["emp1", "emp2"] for e in partial.employees)
        
        # Shifts assigned to emp3 should be unassigned
        for shift in partial.shifts:
            if shift.employee:
                assert shift.employee.id in ["emp1", "emp2"]


class TestMergePartialSolution:
    """Test merging partial solutions back"""
    
    def test_merge_partial_solution(self):
        """Test merging a partial solution back to base schedule"""
        base_schedule = create_test_schedule()
        
        # Create a modified version as partial solution
        partial_solution = create_test_schedule()
        
        # Change some assignments in partial solution
        partial_solution.shifts[3].employee = partial_solution.employees[0]
        partial_solution.shifts[4].employee = partial_solution.employees[1]
        
        scope = OptimizationScope(
            date_range=DateRange(
                start_date=datetime(2025, 6, 10),
                end_date=datetime(2025, 6, 16, 23, 59)
            )
        )
        
        # Merge changes back
        merged = merge_partial_solution(base_schedule, partial_solution, scope)
        
        # In-scope changes should be applied
        assert merged.shifts[3].employee == partial_solution.shifts[3].employee
        assert merged.shifts[4].employee == partial_solution.shifts[4].employee
        
        # Out-of-scope shifts should remain unchanged
        # (shifts from week 2 should keep original assignments)
        week2_shifts = [s for s in merged.shifts if "_w1_" in s.id]
        base_week2_shifts = [s for s in base_schedule.shifts if "_w1_" in s.id]
        
        for merged_shift, base_shift in zip(week2_shifts, base_week2_shifts):
            if base_shift.employee:
                assert merged_shift.employee == base_shift.employee
            else:
                assert merged_shift.employee is None


class TestCountModifiedShifts:
    """Test counting modified shifts"""
    
    def test_count_no_changes(self):
        """Test counting when no shifts are modified"""
        schedule = create_test_schedule()
        
        count = count_modified_shifts(schedule, schedule)
        assert count == 0
    
    def test_count_with_changes(self):
        """Test counting modified shifts"""
        original = create_test_schedule()
        modified = create_test_schedule()
        
        # Change two assignments
        modified.shifts[3].employee = modified.employees[0]
        modified.shifts[4].employee = modified.employees[1]
        
        # Unassign one
        modified.shifts[0].employee = None
        
        count = count_modified_shifts(original, modified)
        assert count == 3  # 2 new assignments + 1 unassignment