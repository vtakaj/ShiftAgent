# MCP Server for Natural Shift Planner

This document provides detailed setup and usage instructions for the Model Context Protocol (MCP) server that exposes the Shift Scheduler API functionality to AI assistants like Claude Desktop.

## 🚀 Quick Start

### Prerequisites
- Natural Shift Planner API running on `http://localhost:8081`
- Claude Desktop or another MCP-compatible AI assistant
- Python 3.11+ with FastMCP installed

### 1. Start the MCP Server

```bash
# Run both API and MCP servers together (recommended)
make run-mcp

# Or run them separately:
make run      # Terminal 1: API server (port 8081)
make mcp      # Terminal 2: MCP server (stdio)
```

### 2. Claude Desktop Configuration

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "shift-scheduler": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/natural-shift-planner", "python", "/path/to/natural-shift-planner/mcp_server.py"],
      "env": {
        "SHIFT_SCHEDULER_API_URL": "http://localhost:8081"
      }
    }
  }
}
```

**Important**: Replace `/path/to/natural-shift-planner` with the actual absolute path to your project directory.

### 3. Restart Claude Desktop

After updating the configuration, restart Claude Desktop for the changes to take effect. You should see the shift scheduler tools available in Claude Desktop.

## 🛠 Available MCP Tools

The MCP server exposes 15 tools organized into 4 categories:

### Basic Operations (7 tools)
1. **`health_check`** - Check API health status
2. **`get_demo_schedule`** - Retrieve demo shift schedule with sample data
3. **`solve_schedule_sync`** - Solve shift scheduling synchronously (blocks until complete)
4. **`solve_schedule_async`** - Start async optimization (returns job ID immediately)
5. **`get_solve_status`** - Check async job status and get results
6. **`analyze_weekly_hours`** - Analyze weekly work hours for constraint violations
7. **`test_weekly_constraints`** - Test weekly hour constraints with demo data

### Schedule Management (1 tool)
8. **`get_schedule_shifts`** - Inspect completed schedules in detail

### Continuous Planning (4 tools)
9. **`swap_shifts`** - Swap employees between two shifts during optimization
10. **`find_shift_replacement`** - Find replacement when employee becomes unavailable
11. **`pin_shifts`** - Pin/unpin shifts to prevent changes during optimization
12. **`reassign_shift`** - Reassign shift to specific employee or unassign


## 📋 Usage Examples

### Basic Schedule Optimization

```markdown
@claude I need to create a shift schedule for my team. Can you help me optimize it?

Here are my employees:
- John: Nurse, CPR certified
- Sarah: Nurse, full-time
- Mike: Security guard
- Emily: Receptionist, admin skills

And I need coverage for:
- Morning shift (8AM-4PM): Nurse required
- Night shift (10PM-6AM): Security required
- Reception (9AM-5PM): Admin skills required
```

### Continuous Planning Workflow

```markdown
@claude I have an active optimization job (ID: abc123) and need to make some changes:

1. Pin the morning shift on Monday to keep John assigned
2. Swap the employees between Tuesday morning and evening shifts  
3. Find a replacement for Sarah on Wednesday (she called in sick)
```

### Report Generation

```markdown
@claude Can you generate an HTML report for the completed schedule from job ID xyz789? I need it for the manager meeting.
```

## 🔧 Tool Details

### Employee and Shift Data Structure

**Employee Format:**
```json
{
  "id": "emp1",
  "name": "John Doe", 
  "skills": ["Nurse", "CPR", "Full-time"]
}
```

**Shift Format:**
```json
{
  "id": "morning_shift_mon",
  "start_time": "2025-06-01T08:00:00",
  "end_time": "2025-06-01T16:00:00", 
  "required_skills": ["Nurse"],
  "location": "Hospital Ward A",
  "priority": 1
}
```

### Continuous Planning Requirements

All continuous planning tools require:
- **Active job ID**: From an async solve operation (`solve_schedule_async`)
- **Job in solving state**: The job must be actively optimizing (status: `SOLVING_SCHEDULED`)
- **Valid shift/employee IDs**: Must reference existing entities in the problem

### Report Generation Features

**PDF Reports:**
- Professional layout optimized for printing
- Automatic filename generation with timestamps
- Binary content returned as downloadable file
- Includes all schedule data and optimization scores

## 🔍 Troubleshooting

### Common Issues

#### 1. MCP Server Not Connecting
- **Check API Status**: Ensure the API server is running on port 8081
- **Verify Configuration**: Double-check the Claude Desktop config file path and syntax
- **Restart Claude**: Always restart Claude Desktop after config changes

#### 2. Tool Execution Errors
- **API Timeout**: Large datasets may require longer processing (default: 120 seconds)
- **Invalid Job ID**: Ensure job IDs are from active async solve operations

#### 3. Continuous Planning Failures
- **Job State**: Job must be in active solving state (not completed)
- **Invalid References**: Shift/employee IDs must exist in the original problem
- **Constraint Violations**: Some operations may fail if they violate hard constraints

### Debug Mode

Set environment variable for detailed logging:
```bash
export SHIFT_SCHEDULER_API_URL="http://localhost:8081"
export PYTHONPATH="/path/to/natural-shift-planner/src"
```

### Checking API Health

Use the health check tool to verify connectivity:
```markdown
@claude Can you check if the shift scheduler API is healthy?
```

## 📊 Performance Considerations

- **Synchronous Operations**: Block until complete, suitable for small datasets (< 100 shifts)
- **Asynchronous Operations**: Return immediately, better for large datasets (> 100 shifts)
- **Continuous Planning**: Minimal overhead, changes applied in real-time during optimization
- **Report Generation**: HTML reports provide a visual representation of the schedule

## 🔒 Security Notes

- MCP server runs locally and communicates with local API only
- No external network access required
- All data remains on your local machine
- Use in trusted environments only

## 🆘 Getting Help

If you encounter issues:

1. **Check API Status**: `curl http://localhost:8081/health`
2. **Verify MCP Config**: Ensure JSON syntax is valid
3. **Review Logs**: Check Claude Desktop logs for MCP connection errors
4. **Test Basic Tools**: Start with `health_check` before complex operations

For additional support, refer to the main README.md and API documentation.