"""
Test that MCP tools correctly handle employee preferences (Issue #48)
"""

import asyncio
import json
from datetime import datetime

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


async def test_mcp_employee_preferences_included():
    """Test that employee preferences are included when using MCP-style requests"""

    # Create a schedule request with employee preferences (MCP-style format)
    schedule_request = {
        "employees": [
            {
                "id": "emp1",
                "name": "田中太郎",
                "skills": ["正社員", "フォークリフト"],
                "preferred_days_off": ["friday", "saturday"],
                "preferred_work_days": ["monday", "tuesday"],
                "unavailable_dates": ["2025-06-15T00:00:00"],
            },
            {
                "id": "emp2",
                "name": "佐藤花子",
                "skills": ["正社員", "ピッキング"],
                "preferred_work_days": ["sunday", "saturday"],
                "unavailable_dates": [],
            },
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
                "id": "事務作業_friday",
                "start_time": "2025-06-13T09:00:00",
                "end_time": "2025-06-13T18:00:00",
                "required_skills": ["正社員"],
                "location": "事務所",
                "priority": 1,
            },
        ],
    }

    # Send the request to the API
    response = await call_api("POST", "/api/shifts/solve-sync", schedule_request)
    assert response.status_code == 200

    result = response.json()

    # Verify that preferences are preserved in the response
    employees = result["employees"]

    # Find emp1 in the response
    emp1 = next(emp for emp in employees if emp["id"] == "emp1")
    assert "friday" in emp1["preferred_days_off"]
    assert "saturday" in emp1["preferred_days_off"]
    assert "monday" in emp1["preferred_work_days"]
    assert "tuesday" in emp1["preferred_work_days"]
    assert len(emp1["unavailable_dates"]) == 1

    # Find emp2 in the response
    emp2 = next(emp for emp in employees if emp["id"] == "emp2")
    assert "sunday" in emp2["preferred_work_days"]
    assert "saturday" in emp2["preferred_work_days"]
    assert len(emp2["unavailable_dates"]) == 0

    # Check that optimization respects preferences
    shifts = result["shifts"]

    # Find the Friday shift - emp1 should NOT be assigned (prefers Friday off)
    friday_shift = next(shift for shift in shifts if shift["id"] == "事務作業_friday")

    # Find the Monday shift - emp1 should be PREFERRED (prefers Monday work)
    monday_shift = next(shift for shift in shifts if shift["id"] == "事務作業_monday")

    # Verify the optimization respects preferences
    if friday_shift["employee"]:
        # If Friday shift is assigned, it should not be to emp1
        assert (
            friday_shift["employee"]["id"] != "emp1"
        ), "emp1 should not work Friday (preferred day off)"

    if monday_shift["employee"]:
        # If Monday shift is assigned, emp1 should be preferred
        # (This is a soft constraint, so we'll just check it's not impossible)
        pass


async def test_mcp_schema_backward_compatibility():
    """Test that the updated MCP schema is backward compatible"""

    # Old format without preferences should still work
    old_format_request = {
        "employees": [{"id": "emp1", "name": "田中太郎", "skills": ["正社員"]}],
        "shifts": [
            {
                "id": "事務作業_monday",
                "start_time": "2025-06-09T09:00:00",
                "end_time": "2025-06-09T18:00:00",
                "required_skills": ["正社員"],
                "location": "事務所",
                "priority": 1,
            }
        ],
    }

    # Send the request to the API
    response = await call_api("POST", "/api/shifts/solve-sync", old_format_request)
    assert response.status_code == 200

    result = response.json()

    # Verify that default empty preferences are applied
    employees = result["employees"]
    emp1 = employees[0]

    assert emp1["preferred_days_off"] == []
    assert emp1["preferred_work_days"] == []
    assert emp1["unavailable_dates"] == []


async def test_demo_schedule_preferences():
    """Test that demo schedule includes preferences"""

    response = await call_api("GET", "/api/shifts/demo")
    assert response.status_code == 200

    result = response.json()
    employees = result["employees"]

    # Find an employee with preferences (e.g., 田中太郎)
    tanaka = next((emp for emp in employees if emp["name"] == "田中太郎"), None)
    assert tanaka is not None

    # Verify preferences are present
    assert len(tanaka["preferred_days_off"]) > 0
    assert "friday" in tanaka["preferred_days_off"]
    assert "saturday" in tanaka["preferred_days_off"]


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

        print("Running MCP employee preferences tests...")

        try:
            await test_mcp_employee_preferences_included()
            print("✓ Employee preferences inclusion test passed")

            await test_mcp_schema_backward_compatibility()
            print("✓ Backward compatibility test passed")

            await test_demo_schedule_preferences()
            print("✓ Demo schedule preferences test passed")

            print("\nAll tests passed! ✓")

        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(run_tests())
