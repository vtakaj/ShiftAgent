import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shiftagent_api.api.analysis import (
    get_target_hours,
    get_week_key,
    is_full_time_employee,
)
from shiftagent_api.core.models import Employee, Shift, ShiftSchedule


def test_employee_creation():
    """Test for employee creation"""
    employee = Employee("emp1", "John Smith", {"Nurse"})
    assert employee.id == "emp1"
    assert employee.name == "John Smith"
    assert employee.skills == {"Nurse"}


def test_employee_skill_check():
    """Test for employee skill check"""
    employee = Employee("emp1", "John Smith", {"Nurse", "CPR"})
    assert employee.has_all_skills({"Nurse"})
    assert employee.has_all_skills({"Nurse", "CPR"})
    assert not employee.has_all_skills({"Doctor"})


def test_shift_creation():
    """Test for shift creation"""
    start_time = datetime(2025, 6, 1, 9, 0)
    end_time = start_time + timedelta(hours=8)
    shift = Shift(
        "shift1",
        start_time,
        end_time,
        {"Nurse"},
        "Hospital",
    )
    assert shift.id == "shift1"
    assert shift.start_time == start_time
    assert shift.end_time == end_time
    assert shift.required_skills == {"Nurse"}
    assert shift.location == "Hospital"
    assert shift.employee is None


def test_shift_pinning_functionality():
    """Test basic pinning functionality for shifts"""
    # Create a shift
    shift = Shift(
        id="test_shift",
        start_time=datetime(2025, 6, 1, 8, 0),
        end_time=datetime(2025, 6, 1, 16, 0),
        required_skills={"Nurse"},
    )

    # Test initial state
    assert shift.pinned is False
    assert not shift.is_pinned()

    # Test pinning
    shift.pin()
    assert shift.pinned is True
    assert shift.is_pinned()

    # Test unpinning
    shift.unpin()
    assert shift.pinned is False
    assert not shift.is_pinned()


def test_shift_model_with_pinning():
    """Test that Shift model works with new pinning field"""
    employee = Employee(id="emp1", name="John Smith", skills={"Nurse"})

    shift = Shift(
        id="shift1",
        start_time=datetime(2025, 6, 1, 8, 0),
        end_time=datetime(2025, 6, 1, 16, 0),
        required_skills={"Nurse"},
        employee=employee,
        pinned=True,  # Test creating with pinned=True
    )

    assert shift.pinned is True
    assert shift.employee == employee


def test_shift_assignment():
    """Test for shift assignment"""
    employee = Employee("emp1", "John Smith", {"Nurse"})
    start_time = datetime(2025, 6, 1, 9, 0)
    end_time = start_time + timedelta(hours=8)
    shift = Shift(
        "shift1",
        start_time,
        end_time,
        {"Nurse"},
        "Hospital",
    )
    shift.employee = employee
    assert shift.employee == employee


def test_shift_overlap():
    """Test for shift overlap detection"""
    start_time = datetime(2025, 6, 1, 9, 0)
    end_time = start_time + timedelta(hours=8)
    shift1 = Shift(
        "shift1",
        start_time,
        end_time,
        {"Nurse"},
        "Hospital",
    )
    shift2 = Shift(
        "shift2",
        start_time + timedelta(hours=4),
        end_time + timedelta(hours=4),
        {"Nurse"},
        "Hospital",
    )
    assert shift1.overlaps_with(shift2)
    assert shift2.overlaps_with(shift1)


def test_shift_no_overlap():
    """Test for non-overlapping shifts"""
    start_time = datetime(2025, 6, 1, 9, 0)
    end_time = start_time + timedelta(hours=8)
    shift1 = Shift(
        "shift1",
        start_time,
        end_time,
        {"Nurse"},
        "Hospital",
    )
    shift2 = Shift(
        "shift2",
        end_time,
        end_time + timedelta(hours=8),
        {"Nurse"},
        "Hospital",
    )
    assert not shift1.overlaps_with(shift2)
    assert not shift2.overlaps_with(shift1)


def test_schedule_creation():
    """Test for schedule creation"""
    employees = [
        Employee("emp1", "John Smith", {"Nurse"}),
        Employee("emp2", "Sarah Johnson", {"Security"}),
    ]
    start_time = datetime(2025, 6, 1, 9, 0)
    end_time = start_time + timedelta(hours=8)
    shifts = [
        Shift(
            "shift1",
            start_time,
            end_time,
            {"Nurse"},
            "Hospital",
        ),
        Shift(
            "shift2",
            start_time,
            end_time,
            {"Security"},
            "Hospital",
        ),
    ]
    schedule = ShiftSchedule(employees=employees, shifts=shifts)
    assert schedule.employees == employees
    assert schedule.shifts == shifts
    assert schedule.get_employee_count() == 2
    assert schedule.get_shift_count() == 2
    assert schedule.get_assigned_shift_count() == 0  # No assignments yet


def test_week_key_generation():
    """Test for week key generation"""
    date1 = datetime(2025, 6, 1)  # Sunday
    date2 = datetime(2025, 6, 2)  # Monday
    date3 = datetime(2025, 6, 8)  # Next Sunday
    assert get_week_key(date1) == "2025-W22"
    assert get_week_key(date2) == "2025-W23"
    assert get_week_key(date3) == "2025-W23"


def test_employee_type_detection():
    """Test for employee type detection"""
    full_time_emp = Employee("emp1", "John Smith", {"Nurse", "Full-time"})
    part_time_emp = Employee("emp2", "Sarah Johnson", {"Reception", "Part-time"})
    regular_emp = Employee("emp3", "Michael Brown", {"Security"})
    assert is_full_time_employee(full_time_emp)
    assert not is_full_time_employee(part_time_emp)
    assert not is_full_time_employee(regular_emp)


def test_target_hours():
    """Test for target hours calculation"""
    full_time_emp = Employee("emp1", "John Smith", {"Nurse", "Full-time"})
    part_time_emp = Employee("emp2", "Sarah Johnson", {"Reception", "Part-time"})
    regular_emp = Employee("emp3", "Michael Brown", {"Security"})
    assert get_target_hours(full_time_emp) == 40
    assert get_target_hours(part_time_emp) == 20
    assert get_target_hours(regular_emp) == 32


@pytest.fixture
def sample_schedule():
    """Sample schedule for testing"""
    employees = [
        Employee("emp1", "John Smith", {"Nurse", "Full-time"}),
        Employee("emp2", "Sarah Johnson", {"Security"}),
    ]

    shifts = [
        Shift(
            "shift1",
            datetime(2025, 6, 1, 9, 0),
            datetime(2025, 6, 1, 17, 0),
            {"Nurse"},
        ),
        Shift(
            "shift2",
            datetime(2025, 6, 1, 22, 0),
            datetime(2025, 6, 2, 6, 0),
            {"Security"},
        ),
    ]

    return ShiftSchedule(employees, shifts)


def test_schedule_statistics(sample_schedule):
    """Test for schedule statistics"""
    schedule = sample_schedule

    assert schedule.get_employee_count() == 2
    assert schedule.get_shift_count() == 2
    assert schedule.get_unassigned_shift_count() == 2

    # Assign one shift
    schedule.shifts[0].employee = schedule.employees[0]

    assert schedule.get_assigned_shift_count() == 1
    assert schedule.get_unassigned_shift_count() == 1


def test_employee_preferences():
    """Test employee preference functionality"""
    test_date = datetime(2025, 6, 5)  # This is a Thursday

    employee = Employee(
        "emp1",
        "John Smith",
        {"Nurse"},
        preferred_days_off={"friday", "saturday"},
        preferred_work_days={"monday", "tuesday"},
        unavailable_dates={test_date},
    )

    # Test preferred days off
    assert employee.prefers_day_off("friday")
    assert employee.prefers_day_off("Saturday")  # Case insensitive
    assert not employee.prefers_day_off("monday")

    # Test preferred work days
    assert employee.prefers_work_day("monday")
    assert employee.prefers_work_day("Tuesday")  # Case insensitive
    assert not employee.prefers_work_day("friday")

    # Test unavailable dates
    assert employee.is_unavailable_on_date(test_date)
    assert not employee.is_unavailable_on_date(test_date + timedelta(days=1))

    # Test with different time on same date
    same_day_different_time = test_date.replace(hour=15, minute=30)
    assert employee.is_unavailable_on_date(same_day_different_time)


def test_employee_preferences_empty():
    """Test employee with no preferences"""
    employee = Employee("emp1", "John Smith", {"Nurse"})

    # No preferences should return False
    assert not employee.prefers_day_off("friday")
    assert not employee.prefers_work_day("monday")
    assert not employee.is_unavailable_on_date(datetime.now())


def test_day_name_helper():
    """Test day name helper function"""
    from shiftagent_api.core.constraints.shift_constraints import get_day_name

    # Test specific dates
    monday = datetime(2025, 6, 2)  # This is a Monday
    friday = datetime(2025, 6, 6)  # This is a Friday

    assert get_day_name(monday) == "monday"
    assert get_day_name(friday) == "friday"
