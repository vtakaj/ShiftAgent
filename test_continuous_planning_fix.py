"""
Test the continuous planning fix for completed jobs (Issue #45)
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


async def test_continuous_planning_completed_job_error():
    """Test that completed jobs return helpful error messages"""

    # Create a demo schedule request
    demo_request = {
        "employees": [
            {"id": "emp1", "name": "John", "skills": ["cooking"]},
            {"id": "emp2", "name": "Jane", "skills": ["serving"]},
        ],
        "shifts": [
            {
                "id": "morning_cook",
                "start_time": "2024-01-15T08:00:00",
                "end_time": "2024-01-15T16:00:00",
                "required_skills": ["cooking"],
            }
        ],
    }

    # Start async optimization
    solve_response = await call_api("POST", "/api/shifts/solve", demo_request)
    assert solve_response.status_code == 200

    job_data = solve_response.json()
    job_id = job_data["job_id"]

    # Wait for job to complete
    max_wait = 30  # seconds
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

    # Try continuous planning operation on completed job
    replacement_request = {
        "shift_id": "morning_cook",
        "unavailable_employee_id": "emp1",
    }

    replace_response = await call_api(
        "POST", f"/api/shifts/{job_id}/replace", replacement_request
    )

    # Should return 400 with helpful error message
    assert replace_response.status_code == 400
    error_text = replace_response.text
    assert "has already completed" in error_text
    assert "Use POST /api/shifts/" in error_text
    assert "/restart" in error_text


async def test_job_restart_functionality():
    """Test that jobs can be restarted for continuous planning"""

    # Create a demo schedule request
    demo_request = {
        "employees": [
            {"id": "emp1", "name": "John", "skills": ["cooking"]},
            {"id": "emp2", "name": "Jane", "skills": ["cooking"]},
        ],
        "shifts": [
            {
                "id": "morning_cook",
                "start_time": "2024-01-15T08:00:00",
                "end_time": "2024-01-15T16:00:00",
                "required_skills": ["cooking"],
            }
        ],
    }

    # Start async optimization
    solve_response = await call_api("POST", "/api/shifts/solve", demo_request)
    assert solve_response.status_code == 200

    job_data = solve_response.json()
    job_id = job_data["job_id"]

    # Wait for job to complete
    max_wait = 30  # seconds
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

    # Restart the completed job
    restart_response = await call_api("POST", f"/api/shifts/{job_id}/restart")
    assert restart_response.status_code == 200

    restart_data = restart_response.json()
    assert restart_data["status"] == "SOLVING_SCHEDULED"

    # Wait a moment for restart to take effect
    await asyncio.sleep(2)

    # Now continuous planning operations should work
    replacement_request = {
        "shift_id": "morning_cook",
        "unavailable_employee_id": "emp1",
    }

    replace_response = await call_api(
        "POST", f"/api/shifts/{job_id}/replace", replacement_request
    )
    assert replace_response.status_code == 200

    replace_data = replace_response.json()
    assert replace_data["success"] is True


async def test_restart_non_completed_job():
    """Test that non-completed jobs cannot be restarted"""

    # Create a demo schedule request
    demo_request = {
        "employees": [{"id": "emp1", "name": "John", "skills": ["cooking"]}],
        "shifts": [
            {
                "id": "morning_cook",
                "start_time": "2024-01-15T08:00:00",
                "end_time": "2024-01-15T16:00:00",
                "required_skills": ["cooking"],
            }
        ],
    }

    # Start async optimization
    solve_response = await call_api("POST", "/api/shifts/solve", demo_request)
    assert solve_response.status_code == 200

    job_data = solve_response.json()
    job_id = job_data["job_id"]

    # Try to restart immediately (while still solving)
    restart_response = await call_api("POST", f"/api/shifts/{job_id}/restart")

    # Should return 400 for non-completed job
    assert restart_response.status_code == 400
    error_text = restart_response.text
    assert "is not completed" in error_text


async def test_restart_nonexistent_job():
    """Test restarting a job that doesn't exist"""

    fake_job_id = "00000000-0000-0000-0000-000000000000"

    restart_response = await call_api("POST", f"/api/shifts/{fake_job_id}/restart")

    # Should return 404
    assert restart_response.status_code == 404
    assert "Job not found" in restart_response.text


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

        print("Running continuous planning fix tests...")

        try:
            await test_continuous_planning_completed_job_error()
            print("✓ Error message test passed")

            await test_job_restart_functionality()
            print("✓ Job restart test passed")

            await test_restart_non_completed_job()
            print("✓ Non-completed job restart test passed")

            await test_restart_nonexistent_job()
            print("✓ Nonexistent job restart test passed")

            print("\nAll tests passed! ✓")

        except Exception as e:
            print(f"✗ Test failed: {e}")

    asyncio.run(run_tests())
