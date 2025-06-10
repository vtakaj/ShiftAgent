"""
Test employee management during continuous planning (Issue #52)
"""

import asyncio
import json
from datetime import datetime, timedelta

import httpx
import pytest

API_BASE_URL = "http://localhost:8081"


async def call_api(method: str, endpoint: str, data=None):
    """Helper function to make API calls"""
    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response


async def create_test_job():
    """Create a test solving job with minimal data"""
    tomorrow = datetime.now() + timedelta(days=1)

    schedule_request = {
        "employees": [
            {
                "id": "emp1",
                "name": "田中太郎",
                "skills": ["正社員", "フォークリフト"],
                "preferred_days_off": ["friday"],
                "preferred_work_days": ["monday"],
            },
            {
                "id": "emp2",
                "name": "佐藤花子",
                "skills": ["正社員", "ピッキング"],
                "preferred_work_days": ["sunday"],
            },
        ],
        "shifts": [
            {
                "id": "shift1",
                "start_time": tomorrow.replace(hour=9, minute=0).isoformat(),
                "end_time": tomorrow.replace(hour=17, minute=0).isoformat(),
                "required_skills": ["正社員"],
                "location": "倉庫A",
                "priority": 1,
            },
            {
                "id": "shift2",
                "start_time": tomorrow.replace(hour=18, minute=0).isoformat(),
                "end_time": tomorrow.replace(hour=22, minute=0).isoformat(),
                "required_skills": ["正社員", "ピッキング"],
                "location": "倉庫B",
                "priority": 2,
            },
        ],
    }

    # Start async optimization
    response = await call_api("POST", "/api/shifts/solve", schedule_request)
    assert response.status_code == 200

    result = response.json()
    job_id = result["job_id"]

    # Wait a moment for the job to start solving
    await asyncio.sleep(2)

    return job_id


async def test_add_single_employee():
    """Test adding a single employee to an active job"""
    job_id = await create_test_job()

    # Add a new employee
    new_employee = {
        "id": "emp_new",
        "name": "新入社員太郎",
        "skills": ["正社員", "梱包"],
        "preferred_days_off": ["saturday", "sunday"],
        "preferred_work_days": ["monday", "tuesday"],
        "unavailable_dates": [],
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee", new_employee
    )
    assert response.status_code == 200

    result = response.json()
    assert result["success"] is True
    assert result["operation"] == "add"
    assert "emp_new" in result["employee_ids"]
    assert "新入社員太郎" in result["message"]


async def test_add_multiple_employees():
    """Test adding multiple employees in batch"""
    job_id = await create_test_job()

    # Add multiple employees
    employees_batch = {
        "employees": [
            {
                "id": "emp_batch1",
                "name": "パート花子",
                "skills": ["パート", "検品"],
                "preferred_days_off": ["monday"],
            },
            {
                "id": "emp_batch2",
                "name": "アルバイト次郎",
                "skills": ["パート", "ピッキング"],
                "preferred_work_days": ["weekend"],
            },
        ]
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employees", employees_batch
    )
    assert response.status_code == 200

    result = response.json()
    assert result["success"] is True
    assert result["operation"] == "add_batch"
    assert "emp_batch1" in result["employee_ids"]
    assert "emp_batch2" in result["employee_ids"]
    assert len(result["employee_ids"]) == 2


async def test_remove_employee():
    """Test removing an employee from an active job"""
    job_id = await create_test_job()

    # First add an employee
    new_employee = {
        "id": "emp_to_remove",
        "name": "削除予定者",
        "skills": ["正社員", "フォークリフト"],
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee", new_employee
    )
    assert response.status_code == 200

    # Wait a moment
    await asyncio.sleep(1)

    # Now remove the employee
    response = await call_api(
        "DELETE", f"/api/shifts/{job_id}/remove-employee/emp_to_remove"
    )
    assert response.status_code == 200

    result = response.json()
    assert result["success"] is True
    assert result["operation"] == "remove"
    assert "emp_to_remove" in result["employee_ids"]
    assert "削除予定者" in result["message"] or "emp_to_remove" in result["message"]


async def test_add_employee_and_assign_to_shift():
    """Test adding an employee and immediately assigning to a shift"""
    job_id = await create_test_job()

    # Add employee and assign to specific shift
    request_data = {
        "employee": {
            "id": "emp_assign",
            "name": "即戦力三郎",
            "skills": ["正社員", "フォークリフト", "ピッキング"],
            "preferred_work_days": ["monday", "tuesday"],
        },
        "shift_id": "shift1",
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee-assign", request_data
    )
    assert response.status_code == 200

    result = response.json()
    assert result["success"] is True
    assert result["operation"] == "add_and_assign"
    assert "emp_assign" in result["employee_ids"]
    assert "shift1" in result["affected_shifts"]


async def test_employee_validation_errors():
    """Test validation errors for employee management"""
    job_id = await create_test_job()

    # Test adding employee with duplicate ID
    duplicate_employee = {
        "id": "emp1",  # This ID already exists
        "name": "重複ID",
        "skills": ["正社員"],
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee", duplicate_employee
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

    # Test removing non-existent employee
    response = await call_api(
        "DELETE", f"/api/shifts/{job_id}/remove-employee/nonexistent"
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

    # Test assigning to non-existent shift
    request_data = {
        "employee": {
            "id": "emp_bad_shift",
            "name": "悪いシフト割当",
            "skills": ["正社員"],
        },
        "shift_id": "nonexistent_shift",
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee-assign", request_data
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


async def test_employee_preferences_preserved():
    """Test that employee preferences are correctly preserved"""
    job_id = await create_test_job()

    # Add employee with comprehensive preferences
    new_employee = {
        "id": "emp_prefs",
        "name": "希望持ち従業員",
        "skills": ["正社員", "ピッキング"],
        "preferred_days_off": ["friday", "saturday"],
        "preferred_work_days": ["monday", "tuesday"],
        "unavailable_dates": ["2025-06-15T00:00:00"],
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee", new_employee
    )
    assert response.status_code == 200

    # Get the job status to verify the employee was added with preferences
    response = await call_api("GET", f"/api/shifts/solve/{job_id}")
    assert response.status_code == 200

    result = response.json()
    if result["status"] == "SOLVING_COMPLETED" and "solution" in result:
        employees = result["solution"]["employees"]
        added_emp = next((emp for emp in employees if emp["id"] == "emp_prefs"), None)

        if added_emp:
            assert "friday" in added_emp["preferred_days_off"]
            assert "saturday" in added_emp["preferred_days_off"]
            assert "monday" in added_emp["preferred_work_days"]
            assert "tuesday" in added_emp["preferred_work_days"]
            assert len(added_emp["unavailable_dates"]) == 1


async def test_job_not_found_error():
    """Test error handling for non-existent job IDs"""
    fake_job_id = "nonexistent-job-id"

    new_employee = {
        "id": "emp_fake",
        "name": "偽ジョブ従業員",
        "skills": ["正社員"],
    }

    response = await call_api(
        "POST", f"/api/shifts/{fake_job_id}/add-employee", new_employee
    )
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


async def test_completed_job_error():
    """Test that operations fail on completed jobs with helpful error message"""
    job_id = await create_test_job()

    # Wait for the job to complete
    max_wait = 30  # Maximum 30 seconds
    for _ in range(max_wait):
        response = await call_api("GET", f"/api/shifts/solve/{job_id}")
        result = response.json()
        if result["status"] == "SOLVING_COMPLETED":
            break
        await asyncio.sleep(1)

    # Try to add employee to completed job
    new_employee = {
        "id": "emp_completed",
        "name": "完了済みジョブ従業員",
        "skills": ["正社員"],
    }

    response = await call_api(
        "POST", f"/api/shifts/{job_id}/add-employee", new_employee
    )
    assert response.status_code == 400
    assert "has already completed" in response.json()["detail"]
    assert "restart" in response.json()["detail"]


if __name__ == "__main__":
    # Check if server is running
    async def check_server():
        try:
            health_response = await call_api("GET", "/health")
            return health_response.status_code == 200
        except:
            return False

    async def run_tests():
        if not await check_server():
            print(
                "Error: Server is not running. Please start the server with 'make run' first."
            )
            return

        print("Running employee management tests...")

        try:
            await test_add_single_employee()
            print("✓ Add single employee test passed")

            await test_add_multiple_employees()
            print("✓ Add multiple employees test passed")

            await test_remove_employee()
            print("✓ Remove employee test passed")

            await test_add_employee_and_assign_to_shift()
            print("✓ Add employee and assign to shift test passed")

            await test_employee_validation_errors()
            print("✓ Employee validation errors test passed")

            await test_employee_preferences_preserved()
            print("✓ Employee preferences preservation test passed")

            await test_job_not_found_error()
            print("✓ Job not found error test passed")

            await test_completed_job_error()
            print("✓ Completed job error test passed")

            print("\nAll employee management tests passed! ✓")

        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(run_tests())
