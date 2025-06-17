"""
Tests for employee preference functionality
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from natural_shift_planner.api.converters import (
    convert_domain_to_response,
    convert_request_to_domain,
)
from natural_shift_planner.api.schemas import (
    EmployeeRequest,
    ShiftRequest,
    ShiftScheduleRequest,
)
from natural_shift_planner.core.models import Employee


def test_api_converter_with_preferences():
    """Test API converter with employee preferences"""
    test_date = datetime(2025, 6, 5, 10, 0, 0)

    # Create API request with preferences
    employee_request = EmployeeRequest(
        id="emp1",
        name="John Smith",
        skills=["Nurse", "CPR"],
        preferred_days_off=["friday", "saturday"],
        preferred_work_days=["monday", "tuesday"],
        unavailable_dates=[test_date],
    )

    shift_request = ShiftRequest(
        id="shift1",
        start_time=datetime(2025, 6, 2, 9, 0),
        end_time=datetime(2025, 6, 2, 17, 0),
        required_skills=["Nurse"],
    )

    schedule_request = ShiftScheduleRequest(
        employees=[employee_request], shifts=[shift_request]
    )

    # Convert to domain
    domain_schedule = convert_request_to_domain(schedule_request)

    # Verify conversion
    employee = domain_schedule.employees[0]
    assert employee.id == "emp1"
    assert employee.name == "John Smith"
    assert employee.skills == {"Nurse", "CPR"}
    assert employee.preferred_days_off == {"friday", "saturday"}
    assert employee.preferred_work_days == {"monday", "tuesday"}
    assert test_date in employee.unavailable_dates

    # Test preference methods
    assert employee.prefers_day_off("friday")
    assert employee.prefers_work_day("monday")
    assert employee.is_unavailable_on_date(test_date)

    # Convert back to response
    response = convert_domain_to_response(domain_schedule)

    # Verify round-trip conversion
    response_employee = response["employees"][0]
    assert response_employee["id"] == "emp1"
    assert response_employee["name"] == "John Smith"
    assert set(response_employee["skills"]) == {"Nurse", "CPR"}
    assert set(response_employee["preferred_days_off"]) == {"friday", "saturday"}
    assert set(response_employee["preferred_work_days"]) == {"monday", "tuesday"}
    assert len(response_employee["unavailable_dates"]) == 1


def test_demo_data_with_preferences():
    """Test demo data includes preferences"""
    from natural_shift_planner.utils.demo_data import create_demo_schedule

    schedule = create_demo_schedule()

    # Verify we have employees with preferences
    employees_with_prefs = [
        emp
        for emp in schedule.employees
        if emp.preferred_days_off or emp.preferred_work_days
    ]
    assert len(employees_with_prefs) > 0

    # Check specific employee preferences (田中太郎)
    tanaka = next((emp for emp in schedule.employees if emp.name == "田中太郎"), None)
    assert tanaka is not None
    assert "friday" in tanaka.preferred_days_off
    assert "saturday" in tanaka.preferred_days_off
    assert "monday" in tanaka.preferred_work_days

    # Check 佐藤花子 has unavailable dates
    sato = next((emp for emp in schedule.employees if emp.name == "佐藤花子"), None)
    assert sato is not None
    assert len(sato.unavailable_dates) > 0


def test_constraint_helper_functions():
    """Test constraint helper functions"""
    from natural_shift_planner.core.constraints.shift_constraints import get_day_name

    # Test get_day_name function
    monday = datetime(2025, 6, 2)  # This is a Monday
    tuesday = datetime(2025, 6, 3)  # This is a Tuesday

    assert get_day_name(monday) == "monday"
    assert get_day_name(tuesday) == "tuesday"

    # Test with different times on same day
    monday_evening = monday.replace(hour=20)
    assert get_day_name(monday_evening) == "monday"


def test_employee_preference_edge_cases():
    """Test edge cases for employee preferences"""
    employee = Employee(
        "emp1",
        "Test Employee",
        {"Nurse"},
        preferred_days_off={"Friday", "SATURDAY"},  # Mixed case
        preferred_work_days={"monday"},
        unavailable_dates=set(),
    )

    # Test case insensitive matching
    assert employee.prefers_day_off("friday")
    assert employee.prefers_day_off("saturday")
    assert employee.prefers_day_off("FRIDAY")
    assert employee.prefers_work_day("MONDAY")
    assert employee.prefers_work_day("Monday")

    # Test no conflicts
    assert not employee.prefers_day_off("monday")
    assert not employee.prefers_work_day("friday")


def test_get_next_monday():
    """Test get_next_monday() function returns correct dates"""
    from natural_shift_planner.utils.demo_data import get_next_monday
    
    # Mock different scenarios by testing the logic
    # Test case 1: If today is Tuesday, should return next Monday (6 days later)
    tuesday = datetime(2025, 6, 17, 10, 0)  # June 17, 2025 is a Tuesday
    
    # Calculate expected next Monday manually
    days_until_monday = (7 - tuesday.weekday()) % 7  # Tuesday is weekday 1, so (7-1)%7 = 6
    expected_monday = tuesday + timedelta(days=6)
    
    # Test the function works correctly by checking the weekday
    result = get_next_monday()
    # The result should always be a Monday (weekday 0)
    assert result.weekday() == 0, f"get_next_monday() returned {result.strftime('%A')}, expected Monday"
    
    # The result should be in the future or today (if today is Monday before 6PM)
    today = datetime.now()
    if today.weekday() == 0 and today.hour < 18:  # If it's Monday before 6PM
        assert result.date() == today.date()
    else:
        assert result.date() > today.date()


def test_demo_data_uses_future_dates():
    """Test that demo data now uses future dates starting from next Monday"""
    from natural_shift_planner.utils.demo_data import create_demo_schedule
    
    schedule = create_demo_schedule()
    today = datetime.now()
    
    # Find the earliest shift date
    earliest_shift = min(schedule.shifts, key=lambda s: s.start_time)
    
    # The earliest shift should be on or after today
    assert earliest_shift.start_time.date() >= today.date(), \
        f"Demo data should start from future dates, but earliest shift is {earliest_shift.start_time.date()}"
    
    # The earliest shift should be on a Monday
    assert earliest_shift.start_time.weekday() == 0, \
        f"Demo data should start on Monday, but starts on {earliest_shift.start_time.strftime('%A')}"
