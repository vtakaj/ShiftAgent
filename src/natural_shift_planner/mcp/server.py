"""
FastMCP server for Shift Scheduler
"""
from fastmcp import FastMCP

from .tools import (
    analyze_weekly_hours,
    get_demo_schedule,
    get_solve_status,
    health_check,
    solve_schedule_async,
    solve_schedule_sync,
    test_weekly_constraints,
)

# Create FastMCP server
mcp = FastMCP("shift-scheduler-mcp", dependencies=["httpx"])

# Register tools
mcp.tool()(health_check)
mcp.tool()(get_demo_schedule)
mcp.tool()(solve_schedule_sync)
mcp.tool()(solve_schedule_async)
mcp.tool()(get_solve_status)
mcp.tool()(analyze_weekly_hours)
mcp.tool()(test_weekly_constraints)

# Add prompts
@mcp.prompt()
async def shift_scheduling_prompt() -> str:
    """Prompt for shift scheduling assistance"""
    return """You are a shift scheduling assistant. You can help with:

1. Creating and optimizing employee shift schedules
2. Ensuring employees have the required skills for shifts
3. Preventing scheduling conflicts (no double-booking)
4. Managing weekly working hours constraints
5. Analyzing schedule fairness and compliance

Available tools:
- health_check: Check API availability
- get_demo_schedule: Get sample schedule data
- solve_schedule_sync: Optimize shifts (blocking)
- solve_schedule_async: Start optimization job
- get_solve_status: Check job status
- analyze_weekly_hours: Analyze hours and violations
- test_weekly_constraints: Test with demo data

When creating schedules, consider:
- Employee skills must match shift requirements
- Full-time employees: 32-40 hours/week target
- Part-time employees: ~20 hours/week target
- Maximum 45 hours/week (hard limit)
- Minimum 8 hours rest between shifts
- Fair distribution of shifts
"""


if __name__ == "__main__":
    mcp.run()