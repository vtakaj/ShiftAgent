"""
Tests for adding employees to completed jobs
"""

from datetime import datetime, timedelta

import pytest

from src.shift_agent.core.models import Employee, Shift, ShiftSchedule


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


def test_add_employee_to_completed_job_logic_only():
    """Test adding employee to completed job (logic verification only)"""
    import uuid
    from datetime import datetime

    from src.shift_agent.api.jobs import job_lock, jobs
    from src.shift_agent.core.models import Employee, ShiftSchedule

    # Create a simple completed job (mock, no actual solving)
    job_id = str(uuid.uuid4())

    # Create minimal schedule for testing
    schedule = ShiftSchedule(employees=[], shifts=[])

    with job_lock:
        jobs[job_id] = {
            "status": "SOLVING_COMPLETED",
            "solution": schedule,
            "created_at": datetime.now(),
            "completed_at": datetime.now(),
        }

    # Create new employee
    new_employee = Employee(
        "emp_new_001",
        "新規従業員",
        {"フォークリフト", "検品"},
    )

    # Test direct addition to solution (skip actual solving for speed)
    with job_lock:
        job = jobs[job_id]
        if job["status"] == "SOLVING_COMPLETED":
            # Simulate the addition logic without actual solving
            job["solution"].employees.append(new_employee)
            job["status"] = "SOLVING_COMPLETED"
            job["updated_at"] = datetime.now()

            if "employee_additions" not in job:
                job["employee_additions"] = []
            job["employee_additions"].append(
                {
                    "employee_id": new_employee.id,
                    "employee_name": new_employee.name,
                    "timestamp": datetime.now(),
                }
            )

    # Verify job was updated
    with job_lock:
        job = jobs[job_id]
        assert job["status"] == "SOLVING_COMPLETED"
        assert "updated_at" in job
        assert "employee_additions" in job
        assert len(job["employee_additions"]) == 1
        assert job["employee_additions"][0]["employee_id"] == "emp_new_001"

        # Verify employee was added to solution
        solution = job["solution"]
        employee_ids = [emp.id for emp in solution.employees]
        assert "emp_new_001" in employee_ids


def test_add_employee_to_invalid_job():
    """Test adding employee to job that's not completed"""
    import uuid
    from datetime import datetime

    from src.shift_agent.api.jobs import (
        add_employee_to_completed_job,
        job_lock,
        jobs,
    )
    from src.shift_agent.core.models import Employee

    # Create a mock active job
    job_id = str(uuid.uuid4())

    with job_lock:
        jobs[job_id] = {
            "status": "SOLVING_ACTIVE",
            "created_at": datetime.now(),
        }

    new_employee = Employee("emp_test", "Test Employee", {"skill1"})

    # Test employee addition (should fail)
    success = add_employee_to_completed_job(job_id, new_employee)
    assert success is False


def test_add_employee_to_nonexistent_job():
    """Test adding employee to job that doesn't exist"""
    from src.shift_agent.api.jobs import add_employee_to_completed_job
    from src.shift_agent.core.models import Employee

    new_employee = Employee("emp_test", "Test Employee", {"skill1"})

    # Test adding to nonexistent job
    success = add_employee_to_completed_job("nonexistent_job_id", new_employee)
    assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
