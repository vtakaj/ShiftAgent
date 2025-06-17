"""
Tests for emergency staff addition using Problem Fact Changes
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.natural_shift_planner.api.problem_fact_changes import (
    AddEmployeeProblemFactChange,
    RemoveEmployeeProblemFactChange,
)
from src.natural_shift_planner.core.models import Employee, Shift, ShiftSchedule


@pytest.fixture
def sample_schedule():
    """Create a sample schedule with some assigned and unassigned shifts"""
    base_date = datetime(2025, 6, 23, 9, 0)  # Next Monday

    employees = [
        Employee("emp1", "田中太郎", {"フォークリフト", "検品", "正社員"}),
        Employee("emp2", "佐藤花子", {"ピッキング", "梱包", "正社員"}),
    ]

    shifts = [
        # Assigned shifts
        Shift(
            id="shift1",
            start_time=base_date,
            end_time=base_date.replace(hour=17),
            required_skills={"フォークリフト"},
            location="入庫エリア",
        ),
        Shift(
            id="shift2",
            start_time=base_date.replace(hour=14),
            end_time=base_date.replace(hour=22),
            required_skills={"ピッキング"},
            location="ピッキングエリア",
        ),
        # Unassigned shifts
        Shift(
            id="shift3",
            start_time=base_date + timedelta(days=1),
            end_time=base_date + timedelta(days=1, hours=8),
            required_skills={"フォークリフト"},
            location="入庫エリア",
        ),
        Shift(
            id="shift4",
            start_time=base_date + timedelta(days=1, hours=14),
            end_time=base_date + timedelta(days=1, hours=22),
            required_skills={"梱包"},
            location="梱包エリア",
        ),
    ]

    # Assign some shifts
    shifts[0].employee = employees[0]  # 田中さん to shift1
    shifts[1].employee = employees[1]  # 佐藤さん to shift2

    return ShiftSchedule(employees=employees, shifts=shifts)


@pytest.fixture
def mock_score_director():
    """Create a mock ScoreDirector for testing"""
    mock = MagicMock()
    # Add expected methods
    mock.get_working_solution = MagicMock()
    mock.before_problem_fact_added = MagicMock()
    mock.after_problem_fact_added = MagicMock()
    mock.before_problem_fact_removed = MagicMock()
    mock.after_problem_fact_removed = MagicMock()
    mock.before_variable_changed = MagicMock()
    mock.after_variable_changed = MagicMock()
    mock.trigger_variable_listeners = MagicMock()
    return mock


def test_add_employee_problem_fact_change_creation():
    """Test creating an AddEmployeeProblemFactChange"""
    new_employee = Employee(
        "emp_emergency_001",
        "緊急対応 太郎",
        {"フォークリフト", "入庫管理"},
    )

    change = AddEmployeeProblemFactChange(
        new_employee,
        auto_assign_shift_ids=["shift3"],
    )

    assert change.new_employee == new_employee
    assert change.auto_assign_shift_ids == ["shift3"]


def test_add_employee_to_solution(sample_schedule, mock_score_director):
    """Test adding an emergency employee to the solution"""
    # Setup
    mock_score_director.get_working_solution.return_value = sample_schedule

    new_employee = Employee(
        "emp_emergency_001",
        "緊急対応 太郎",
        {"フォークリフト", "入庫管理"},
    )

    change = AddEmployeeProblemFactChange(new_employee)

    # Execute
    change.do_change(mock_score_director)

    # Verify
    assert len(sample_schedule.employees) == 3
    assert new_employee in sample_schedule.employees

    # Verify score director calls
    mock_score_director.before_problem_fact_added.assert_called_once_with(new_employee)
    mock_score_director.after_problem_fact_added.assert_called_once_with(new_employee)
    mock_score_director.trigger_variable_listeners.assert_called_once()


def test_auto_assign_to_compatible_shift(sample_schedule, mock_score_director):
    """Test automatic assignment to compatible unassigned shift"""
    # Setup
    mock_score_director.get_working_solution.return_value = sample_schedule

    new_employee = Employee(
        "emp_emergency_001",
        "緊急対応 太郎",
        {"フォークリフト", "入庫管理"},
    )

    change = AddEmployeeProblemFactChange(new_employee)

    # Execute
    change.do_change(mock_score_director)

    # Verify auto-assignment to shift3 (unassigned forklift shift)
    shift3 = next(s for s in sample_schedule.shifts if s.id == "shift3")
    assert shift3.employee == new_employee

    # Verify score director was notified of the assignment
    mock_score_director.before_variable_changed.assert_called()
    mock_score_director.after_variable_changed.assert_called()


def test_specific_shift_assignment(sample_schedule, mock_score_director):
    """Test assigning to specific requested shifts"""
    # Setup
    mock_score_director.get_working_solution.return_value = sample_schedule

    new_employee = Employee(
        "emp_emergency_001",
        "緊急対応 太郎",
        {"梱包"},  # Only has packing skill
    )

    change = AddEmployeeProblemFactChange(
        new_employee,
        auto_assign_shift_ids=["shift4"],  # Request specific shift
    )

    # Execute
    change.do_change(mock_score_director)

    # Verify specific assignment
    shift4 = next(s for s in sample_schedule.shifts if s.id == "shift4")
    assert shift4.employee == new_employee


def test_employee_emergency_marking():
    """Test marking employee as emergency addition"""
    employee = Employee("emp1", "Test Employee", {"skill1"})

    assert employee.is_emergency_addition is False
    assert employee.emergency_added_at is None

    # Mark as emergency
    employee.mark_as_emergency_addition()

    assert employee.is_emergency_addition is True
    assert employee.emergency_added_at is not None
    assert isinstance(employee.emergency_added_at, datetime)


def test_employee_has_required_skills():
    """Test employee skill checking"""
    employee = Employee("emp1", "Test", {"フォークリフト", "検品"})

    # Has all required skills
    assert employee.has_required_skills({"フォークリフト"}) is True
    assert employee.has_required_skills({"フォークリフト", "検品"}) is True

    # Missing required skill
    assert employee.has_required_skills({"フォークリフト", "梱包"}) is False
    assert employee.has_required_skills({"入庫管理"}) is False

    # Empty required skills
    assert employee.has_required_skills(set()) is True


def test_remove_employee_problem_fact_change(sample_schedule, mock_score_director):
    """Test removing an employee and unassigning their shifts"""
    # Setup
    mock_score_director.get_working_solution.return_value = sample_schedule

    change = RemoveEmployeeProblemFactChange("emp1")  # Remove 田中太郎

    # Execute
    change.do_change(mock_score_director)

    # Verify employee removed
    assert len(sample_schedule.employees) == 1
    assert not any(e.id == "emp1" for e in sample_schedule.employees)

    # Verify shift1 was unassigned (was assigned to emp1)
    shift1 = next(s for s in sample_schedule.shifts if s.id == "shift1")
    assert shift1.employee is None

    # Verify score director calls
    mock_score_director.before_problem_fact_removed.assert_called_once()
    mock_score_director.after_problem_fact_removed.assert_called_once()


def test_remove_nonexistent_employee(sample_schedule, mock_score_director):
    """Test removing an employee that doesn't exist"""
    # Setup
    mock_score_director.get_working_solution.return_value = sample_schedule
    initial_employee_count = len(sample_schedule.employees)

    change = RemoveEmployeeProblemFactChange("emp_nonexistent")

    # Execute
    change.do_change(mock_score_director)

    # Verify nothing changed
    assert len(sample_schedule.employees) == initial_employee_count
    mock_score_director.before_problem_fact_removed.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
