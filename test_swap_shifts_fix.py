"""
Test the swap_shifts fix for issue #50
"""

import asyncio
import json

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
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response


async def test_swap_shifts_with_invalid_shift_ids():
    """Test that swap_shifts returns proper error for invalid shift IDs"""

    # Create a simple schedule
    schedule_request = {
        "employees": [{"id": "emp1", "name": "田中太郎", "skills": ["正社員"]}],
        "shifts": [
            {
                "id": "valid_shift",
                "start_time": "2025-06-09T09:00:00",
                "end_time": "2025-06-09T18:00:00",
                "required_skills": ["正社員"],
                "location": "事務所",
                "priority": 1,
            }
        ],
    }

    # Start async optimization
    solve_response = await call_api("POST", "/api/shifts/solve", schedule_request)
    assert solve_response.status_code == 200

    job_data = solve_response.json()
    job_id = job_data["job_id"]

    # Wait for job to complete
    max_wait = 30
    for _ in range(max_wait):
        status_response = await call_api("GET", f"/api/shifts/solve/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "SOLVING_COMPLETED":
            break
        elif status_data["status"] == "SOLVING_FAILED":
            pytest.fail(f"Job failed: {status_data.get('message', 'Unknown error')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Job did not complete within timeout")

    # Restart the job for continuous planning
    restart_response = await call_api("POST", f"/api/shifts/{job_id}/restart")
    assert restart_response.status_code == 200

    # Wait for restart to take effect
    await asyncio.sleep(2)

    # Test 1: Both shift IDs invalid
    swap_request = {
        "shift1_id": "nonexistent_shift1",
        "shift2_id": "nonexistent_shift2",
    }

    response = await call_api("POST", f"/api/shifts/{job_id}/swap", swap_request)
    assert response.status_code == 400
    error_text = response.text
    assert "not found in solution" in error_text
    assert "nonexistent_shift1" in error_text

    # Test 2: First shift ID invalid
    swap_request = {"shift1_id": "nonexistent_shift", "shift2_id": "valid_shift"}

    response = await call_api("POST", f"/api/shifts/{job_id}/swap", swap_request)
    assert response.status_code == 400
    error_text = response.text
    assert "not found in solution" in error_text
    assert "nonexistent_shift" in error_text

    # Test 3: Second shift ID invalid
    swap_request = {"shift1_id": "valid_shift", "shift2_id": "nonexistent_shift"}

    response = await call_api("POST", f"/api/shifts/{job_id}/swap", swap_request)
    assert response.status_code == 400
    error_text = response.text
    assert "not found in solution" in error_text
    assert "nonexistent_shift" in error_text


async def test_swap_shifts_with_valid_shift_ids():
    """Test that swap_shifts works correctly with valid shift IDs"""

    # Create a schedule with two shifts
    schedule_request = {
        "employees": [
            {"id": "emp1", "name": "田中太郎", "skills": ["正社員", "フォークリフト"]},
            {"id": "emp2", "name": "佐藤花子", "skills": ["正社員", "ピッキング"]},
        ],
        "shifts": [
            {
                "id": "事務作業_monday",
                "start_time": "2025-06-09T09:00:00",
                "end_time": "2025-06-09T18:00:00",
                "required_skills": ["正社員"],
                "location": "事務所",
                "priority": 1,
            },
            {
                "id": "入庫_monday",
                "start_time": "2025-06-09T06:00:00",
                "end_time": "2025-06-09T14:00:00",
                "required_skills": ["フォークリフト"],
                "location": "入庫エリア",
                "priority": 1,
            },
        ],
    }

    # Start async optimization
    solve_response = await call_api("POST", "/api/shifts/solve", schedule_request)
    assert solve_response.status_code == 200

    job_data = solve_response.json()
    job_id = job_data["job_id"]

    # Wait for job to complete
    max_wait = 30
    for _ in range(max_wait):
        status_response = await call_api("GET", f"/api/shifts/solve/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "SOLVING_COMPLETED":
            break
        elif status_data["status"] == "SOLVING_FAILED":
            pytest.fail(f"Job failed: {status_data.get('message', 'Unknown error')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Job did not complete within timeout")

    # Restart the job for continuous planning
    restart_response = await call_api("POST", f"/api/shifts/{job_id}/restart")
    assert restart_response.status_code == 200

    # Wait for restart to take effect
    await asyncio.sleep(2)

    # Test valid swap
    swap_request = {"shift1_id": "事務作業_monday", "shift2_id": "入庫_monday"}

    response = await call_api("POST", f"/api/shifts/{job_id}/swap", swap_request)
    assert response.status_code == 200

    result = response.json()
    assert result["success"] is True
    assert "Successfully swapped" in result["message"]
    assert result["operation"] == "swap"


async def test_find_replacement_with_invalid_shift():
    """Test that find_replacement returns proper error for invalid shift ID"""

    # Create a simple schedule
    schedule_request = {
        "employees": [{"id": "emp1", "name": "田中太郎", "skills": ["正社員"]}],
        "shifts": [
            {
                "id": "valid_shift",
                "start_time": "2025-06-09T09:00:00",
                "end_time": "2025-06-09T18:00:00",
                "required_skills": ["正社員"],
                "location": "事務所",
                "priority": 1,
            }
        ],
    }

    # Start and complete job
    solve_response = await call_api("POST", "/api/shifts/solve", schedule_request)
    assert solve_response.status_code == 200

    job_data = solve_response.json()
    job_id = job_data["job_id"]

    # Wait for completion and restart
    max_wait = 30
    for _ in range(max_wait):
        status_response = await call_api("GET", f"/api/shifts/solve/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "SOLVING_COMPLETED":
            break
        elif status_data["status"] == "SOLVING_FAILED":
            pytest.fail(f"Job failed: {status_data.get('message', 'Unknown error')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Job did not complete within timeout")

    restart_response = await call_api("POST", f"/api/shifts/{job_id}/restart")
    assert restart_response.status_code == 200
    await asyncio.sleep(2)

    # Test with invalid shift ID
    replace_request = {
        "shift_id": "nonexistent_shift",
        "unavailable_employee_id": "emp1",
    }

    response = await call_api("POST", f"/api/shifts/{job_id}/replace", replace_request)
    assert response.status_code == 400
    error_text = response.text
    assert "not found in solution" in error_text
    assert "nonexistent_shift" in error_text


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

        print("Running swap_shifts fix tests...")

        try:
            await test_swap_shifts_with_invalid_shift_ids()
            print("✓ Invalid shift IDs test passed")

            await test_swap_shifts_with_valid_shift_ids()
            print("✓ Valid shift IDs test passed")

            await test_find_replacement_with_invalid_shift()
            print("✓ Find replacement invalid shift test passed")

            print("\nAll tests passed! ✓")

        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(run_tests())
