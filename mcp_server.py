#!/usr/bin/env python3
"""
MCP Server for Shift Scheduler API using FastMCP
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import asyncio

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field


# Configuration
API_BASE_URL = os.getenv("SHIFT_SCHEDULER_API_URL", "http://localhost:8081")

# Create FastMCP server
mcp = FastMCP("shift-scheduler-mcp", dependencies=["httpx"])


# Pydantic models for API requests
class EmployeeRequest(BaseModel):
    id: str
    name: str
    skills: List[str]


class ShiftRequest(BaseModel):
    id: str
    start_time: str
    end_time: str
    required_skills: List[str]
    location: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)


class ScheduleRequest(BaseModel):
    employees: List[EmployeeRequest]
    shifts: List[ShiftRequest]


# Helper function to make API calls
async def call_api(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 120.0
) -> Dict[str, Any]:
    """Make an API call to the Shift Scheduler API."""
    url = f"{API_BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Request timed out after {timeout} seconds")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")


@mcp.tool()
async def health_check(ctx: Context) -> str:
    """Check if the Shift Scheduler API is healthy."""
    try:
        result = await call_api("GET", "/health")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Health check failed: {str(e)}"


@mcp.tool()
async def get_demo_schedule(ctx: Context) -> str:
    """Get a demo shift schedule with sample data."""
    try:
        result = await call_api("GET", "/api/shifts/demo")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Failed to get demo schedule: {str(e)}"


@mcp.tool()
async def solve_schedule_sync(
    ctx: Context,
    employees: List[Dict[str, Any]],
    shifts: List[Dict[str, Any]]
) -> str:
    """
    Solve shift scheduling synchronously (blocks until complete).
    
    Args:
        employees: List of employees with their skills
        shifts: List of shifts to be scheduled
    """
    try:
        # Validate request
        request = ScheduleRequest(
            employees=[EmployeeRequest(**emp) for emp in employees],
            shifts=[ShiftRequest(**shift) for shift in shifts]
        )
        
        result = await call_api(
            "POST", 
            "/api/shifts/solve-sync",
            data=request.model_dump()
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Failed to solve schedule: {str(e)}"


@mcp.tool()
async def solve_schedule_async(
    ctx: Context,
    employees: List[Dict[str, Any]],
    shifts: List[Dict[str, Any]]
) -> str:
    """
    Start asynchronous shift scheduling (returns job ID).
    
    Args:
        employees: List of employees with their skills
        shifts: List of shifts to be scheduled
    """
    try:
        # Validate request
        request = ScheduleRequest(
            employees=[EmployeeRequest(**emp) for emp in employees],
            shifts=[ShiftRequest(**shift) for shift in shifts]
        )
        
        result = await call_api(
            "POST",
            "/api/shifts/solve",
            data=request.model_dump()
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Failed to start async solve: {str(e)}"


@mcp.tool()
async def get_solve_status(ctx: Context, job_id: str) -> str:
    """
    Get the status and results of an async solve job.
    
    Args:
        job_id: The job ID returned from solve_schedule_async
    """
    try:
        result = await call_api("GET", f"/api/shifts/solve/{job_id}")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Failed to get solve status: {str(e)}"


@mcp.tool()
async def analyze_weekly_hours(
    ctx: Context,
    employees: List[Dict[str, Any]],
    shifts: List[Dict[str, Any]]
) -> str:
    """
    Analyze weekly work hours for a given schedule.
    
    Args:
        employees: List of employees
        shifts: List of shifts with assignments
    """
    try:
        data = {
            "employees": employees,
            "shifts": shifts
        }
        
        result = await call_api(
            "POST",
            "/api/shifts/analyze-weekly",
            data=data
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Failed to analyze weekly hours: {str(e)}"


@mcp.tool()
async def test_weekly_constraints(ctx: Context) -> str:
    """Test weekly hour constraints with demo data."""
    try:
        result = await call_api("GET", "/api/shifts/test-weekly")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Failed to test weekly constraints: {str(e)}"


# Additional tool for server info
@mcp.tool()
async def get_server_info(ctx: Context) -> str:
    """Get information about the MCP server and API connection."""
    info = {
        "server_name": "shift-scheduler-mcp",
        "version": "0.1.0",
        "api_url": API_BASE_URL,
        "description": "MCP server for Shift Scheduler API",
        "available_tools": [
            "health_check",
            "get_demo_schedule",
            "solve_schedule_sync",
            "solve_schedule_async",
            "get_solve_status",
            "analyze_weekly_hours",
            "test_weekly_constraints",
            "get_server_info"
        ]
    }
    return json.dumps(info, indent=2)


if __name__ == "__main__":
    import sys
    
    # Debug logging
    print(f"Starting MCP server with API URL: {API_BASE_URL}", file=sys.stderr)
    
    # Check if API is accessible
    async def check_api():
        try:
            print(f"Checking API connection to {API_BASE_URL}/health...", file=sys.stderr)
            result = await call_api("GET", "/health", timeout=5.0)
            print(f"API health check successful: {result}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"API connection failed: {type(e).__name__}: {e}", file=sys.stderr)
            return False
    
    # Run check
    if not asyncio.run(check_api()):
        print(f"Warning: Cannot connect to API at {API_BASE_URL}", file=sys.stderr)
        print("Make sure the API server is running with 'make run'", file=sys.stderr)
        print("Continuing anyway - connection will be attempted when tools are called", file=sys.stderr)
    
    # Run the MCP server
    mcp.run()