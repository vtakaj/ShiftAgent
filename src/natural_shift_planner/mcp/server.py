"""
FastMCP server for Shift Scheduler
"""

from fastmcp import FastMCP

from .tools import (
    analyze_weekly_hours,
    find_shift_replacement,
    get_demo_schedule,
    get_demo_schedule_pdf,
    get_schedule_pdf_report,
    get_schedule_shifts,
    get_solve_status,
    health_check,
    pin_shifts,
    reassign_shift,
    solve_schedule_async,
    solve_schedule_sync,
    solve_schedule_sync_pdf,
    swap_shifts,
    test_weekly_constraints,
)

# Create FastMCP server
mcp = FastMCP("shift-scheduler-mcp", dependencies=["httpx"])

# Register original tools
mcp.tool()(health_check)
mcp.tool()(get_demo_schedule)
mcp.tool()(solve_schedule_sync)
mcp.tool()(solve_schedule_async)
mcp.tool()(get_solve_status)
mcp.tool()(analyze_weekly_hours)
mcp.tool()(test_weekly_constraints)

# Register remaining tools
mcp.tool()(get_schedule_shifts)

# Register PDF report tools
mcp.tool()(get_demo_schedule_pdf)
mcp.tool()(get_schedule_pdf_report)
mcp.tool()(solve_schedule_sync_pdf)

# Register continuous planning tools
mcp.tool()(swap_shifts)
mcp.tool()(find_shift_replacement)
mcp.tool()(pin_shifts)
mcp.tool()(reassign_shift)


# Add prompts
@mcp.prompt()
async def shift_scheduling_prompt() -> str:
    """Prompt for shift scheduling assistance"""
    return """You are an advanced shift scheduling assistant with full schedule management capabilities. You can help with:

## Core Scheduling
1. Creating and optimizing employee shift schedules
2. Ensuring employees have the required skills for shifts
3. Preventing scheduling conflicts (no double-booking)
4. Managing weekly working hours constraints
5. Analyzing schedule fairness and compliance
6. Real-time schedule modifications and continuous planning

## Available Tools

### Basic Operations
- health_check: Check API availability
- get_demo_schedule: Get sample schedule data
- solve_schedule_sync: Full schedule optimization (blocking)
- solve_schedule_async: Start full optimization job
- get_solve_status: Check job status and get results
- analyze_weekly_hours: Analyze hours and violations
- test_weekly_constraints: Test with demo data

### Schedule Inspection
- get_schedule_shifts: Inspect completed schedules

### Continuous Planning (Real-time Modifications)
- swap_shifts: Swap employees between two shifts during optimization
- find_shift_replacement: Find replacement when employee becomes unavailable
- pin_shifts: Pin/unpin shifts to prevent changes during optimization
- reassign_shift: Reassign shift to specific employee or unassign

### PDF Reports
- get_demo_schedule_pdf: Get demo schedule as PDF report
- get_schedule_pdf_report: Get completed schedule as PDF report
- solve_schedule_sync_pdf: Solve and return PDF report in one step

## Constraint Guidelines
- Employee skills must match shift requirements
- Full-time employees: 32-40 hours/week target
- Part-time employees: ~20 hours/week target
- Maximum 45 hours/week (hard limit)
- Minimum 8 hours rest between shifts
- Fair distribution of shifts

## Continuous Planning Usage
- Continuous planning tools require an active solving session
- Start with solve_schedule_async, then use continuous planning tools
- Pin shifts to lock them before making changes
- Use find_shift_replacement for emergency coverage
- Swap shifts for quick employee exchanges
"""


if __name__ == "__main__":
    mcp.run()
