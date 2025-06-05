"""
FastMCP server for Shift Scheduler
"""
from fastmcp import FastMCP

from .tools import (
    analyze_change_impact,
    analyze_weekly_hours,
    get_demo_schedule,
    get_demo_schedule_html,
    get_schedule_html_report,
    get_schedule_shifts,
    get_solve_status,
    health_check,
    lock_shifts,
    modify_shift_assignment,
    partial_optimize_schedule,
    quick_fix_schedule,
    solve_schedule_async,
    solve_schedule_sync,
    solve_schedule_sync_html,
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

# Register partial modification tools
mcp.tool()(modify_shift_assignment)
mcp.tool()(lock_shifts)
mcp.tool()(analyze_change_impact)
mcp.tool()(partial_optimize_schedule)
mcp.tool()(get_schedule_shifts)
mcp.tool()(quick_fix_schedule)

# Register HTML report tools
mcp.tool()(get_demo_schedule_html)
mcp.tool()(get_schedule_html_report)
mcp.tool()(solve_schedule_sync_html)

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

## Advanced Partial Modifications
6. Modifying individual shift assignments with constraint checking
7. Locking/unlocking shifts to prevent unwanted changes
8. Analyzing impact of proposed changes before applying
9. Partial schedule optimization for specific date ranges or employees
10. Quick fixes for common scheduling issues

## Available Tools

### Basic Operations
- health_check: Check API availability
- get_demo_schedule: Get sample schedule data
- solve_schedule_sync: Full schedule optimization (blocking)
- solve_schedule_async: Start full optimization job
- get_solve_status: Check job status and get results
- analyze_weekly_hours: Analyze hours and violations
- test_weekly_constraints: Test with demo data

### Partial Modifications (NEW!)
- modify_shift_assignment: Change individual shift assignments safely
- lock_shifts: Lock confirmed shifts to prevent changes
- analyze_change_impact: Preview effects of changes before applying
- partial_optimize_schedule: Re-optimize only specific parts of schedule
- get_schedule_shifts: Inspect completed schedules
- quick_fix_schedule: Rapidly fix common issues in focused date ranges

### HTML Reports (NEW!)
- get_demo_schedule_html: Get demo schedule as formatted HTML report
- get_schedule_html_report: Get completed schedule as HTML report
- solve_schedule_sync_html: Solve and return HTML report in one step

## Constraint Guidelines
- Employee skills must match shift requirements
- Full-time employees: 32-40 hours/week target
- Part-time employees: ~20 hours/week target
- Maximum 45 hours/week (hard limit)
- Minimum 8 hours rest between shifts
- Fair distribution of shifts

## Best Practices for Partial Modifications
1. Always use analyze_change_impact before making changes
2. Lock confirmed shifts before partial optimization
3. Use partial_optimize_schedule for targeted fixes
4. Check constraint violations and weekly hour impacts
5. Use dry_run mode to test changes safely

## Common Workflows
- **Emergency reassignment**: analyze_change_impact → modify_shift_assignment
- **Weekly optimization**: lock_shifts → partial_optimize_schedule
- **Quick fixes**: quick_fix_schedule for common issues
- **Schedule confirmation**: lock_shifts for approved assignments
"""


if __name__ == "__main__":
    mcp.run()