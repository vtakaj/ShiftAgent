"""
FastMCP server for Shift Scheduler
"""

import logging
import os
import sys

from fastmcp import FastMCP

from .tools import (
    add_employee_to_job,
    analyze_weekly_hours,
    get_demo_schedule,
    get_schedule_html_report,
    get_schedule_shifts,
    get_solve_status,
    health_check,
    reassign_shift,
    solve_schedule_async,
    solve_schedule_sync,
    swap_shifts,
    test_weekly_constraints,
    update_employee_skills,
)

# Ensure all logging goes to stderr, as stdout is used for MCP communication.
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), stream=sys.stderr)

# Create FastMCP server with logging
logger = logging.getLogger(__name__)
mcp: FastMCP = FastMCP("shift-scheduler-mcp", dependencies=["httpx"])

# Configure logging for fastmcp specifically if needed
mcp_log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
logging.getLogger("fastmcp").setLevel(mcp_log_level)

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

# Register employee management tools
mcp.tool()(add_employee_to_job)
mcp.tool()(update_employee_skills)

# Register report generation tools
mcp.tool()(get_schedule_html_report)

# Register continuous planning tools
mcp.tool()(swap_shifts)
mcp.tool()(reassign_shift)

# TODO: Register remaining continuous planning tools when implemented
# mcp.tool()(find_shift_replacement)
# mcp.tool()(pin_shifts)

# TODO: Register additional employee management tools when implemented
# mcp.tool()(add_employees_batch_to_job)
# mcp.tool()(remove_employee_from_job)
# mcp.tool()(add_employee_and_assign_to_shift)


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

### Employee Management (Available Now)
- add_employee_to_job: Add new employee to completed job with minimal re-optimization
- update_employee_skills: Update employee skills and re-optimize affected assignments

### Report Generation (Available Now)
- get_schedule_html_report: Generate beautiful HTML schedule report for viewing in browser

### Continuous Planning (Available Now)
- swap_shifts: Swap employees between two shifts during optimization
- reassign_shift: Reassign shift to specific employee or unassign (with validation and force override)

### Continuous Planning (Coming Soon)
The following real-time modification features are planned but not yet implemented:
- find_shift_replacement: Find replacement when employee becomes unavailable
- pin_shifts: Pin/unpin shifts to prevent changes during optimization

### Additional Employee Management (Coming Soon)
The following additional employee management features are planned but not yet implemented:
- add_employees_batch_to_job: Add multiple employees at once
- remove_employee_from_job: Remove employee (unassigns their shifts)
- add_employee_and_assign_to_shift: Add employee and assign to specific shift


## Constraint Guidelines
- Employee skills must match shift requirements
- Full-time employees: 32-40 hours/week target
- Part-time employees: ~20 hours/week target
- Maximum 45 hours/week (hard limit)
- Minimum 8 hours rest between shifts
- Fair distribution of shifts

## Future Features
- Continuous planning for real-time schedule modifications
- Dynamic employee management during optimization
- Emergency shift coverage and swapping
- Shift pinning to lock specific assignments
"""


def main():
    """Entry point for MCP server"""
    # Check if we should run as HTTP server (SSE) or stdio
    server_mode = os.getenv("MCP_SERVER_MODE", "stdio").lower()
    port = int(os.getenv("MCP_SERVER_PORT", "8082"))
    
    if server_mode == "sse" or server_mode == "http":
        logger.info(f"Starting MCP server in SSE mode on port {port}")
        mcp.run_sse(host="0.0.0.0", port=port)
    else:
        logger.info("Starting MCP server in stdio mode")
        mcp.run()


if __name__ == "__main__":
    main()
