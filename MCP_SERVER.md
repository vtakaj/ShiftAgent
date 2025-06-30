# MCP Server for ShiftAgent

This document provides detailed setup and usage instructions for the Model Context Protocol (MCP) server that exposes the Shift Agent API functionality to AI assistants like Claude Desktop.

For Docker deployment with HTTP/SSE transport, see [`DOCKER_MCP.md`](DOCKER_MCP.md).

## 🚀 Quick Start

### Prerequisites
- ShiftAgent API running on `http://localhost:8081`
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
    "shiftagent": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/shiftagent", "python", "/path/to/shiftagent/mcp_server.py"],
      "env": {
        "SHIFT_AGENT_API_URL": "http://localhost:8081"
      }
    }
  }
}
```

**Important**: Replace `/path/to/shiftagent` with the actual absolute path to your project directory.

### 3. Restart Claude Desktop

After updating the configuration, restart Claude Desktop for the changes to take effect. You should see the shift agent tools available in Claude Desktop.

## 🌐 HTTP Transport (Alternative)

The MCP server also supports Streamable HTTP transport for web-based deployments and multiple concurrent clients.

### Starting with HTTP Transport

```bash
# Run MCP server with HTTP transport
make mcp-http

# Or with custom configuration
MCP_HTTP_HOST=0.0.0.0 MCP_HTTP_PORT=8082 make mcp-http
```

### Environment Variables

- `MCP_TRANSPORT`: Transport type (`stdio` or `http`, default: `stdio`)
- `MCP_HTTP_HOST`: HTTP server host (default: `127.0.0.1`)
- `MCP_HTTP_PORT`: HTTP server port (default: `8083`)
- `MCP_HTTP_PATH`: HTTP endpoint path (default: `/mcp`)

### Connecting to HTTP Transport

```python
from fastmcp import Client

async def connect():
    async with Client("http://localhost:8083/mcp") as client:
        # List available tools
        tools = await client.list_tools()

        # Call a tool
        result = await client.call_tool("solve_schedule_sync", {
            "schedule_input": {...}
        })
```

### Use Cases for HTTP Transport

- **Web Applications**: Deploy MCP server as a web service
- **Multiple Clients**: Support concurrent connections from multiple AI agents
- **Cloud Deployment**: Compatible with AWS Lambda, Google Cloud Functions, etc.
- **API Integration**: Integrate with existing web applications

Note: Claude Desktop currently works best with stdio transport. Use HTTP transport for web-based or programmatic access.

## 📡 SSE Transport (Deprecated)

The MCP server also supports SSE (Server-Sent Events) transport for backward compatibility with legacy clients.

### ⚠️ Deprecation Warning

SSE transport is deprecated and may be removed in future versions. New deployments should use HTTP transport instead.

### Starting with SSE Transport

```bash
# Run MCP server with SSE transport
make mcp-sse

# Or with custom configuration
MCP_SSE_HOST=0.0.0.0 MCP_SSE_PORT=8085 make mcp-sse
```

### Environment Variables

- `MCP_TRANSPORT`: Set to `sse` for SSE transport
- `MCP_SSE_HOST`: SSE server host (default: `127.0.0.1`)
- `MCP_SSE_PORT`: SSE server port (default: `8084`)

### Connecting to SSE Transport

```python
from fastmcp import Client
from fastmcp.client.transports import SSETransport

# Automatic detection for URLs with /sse/
async with Client("http://localhost:8084/sse/") as client:
    result = await client.call_tool("solve_schedule_sync", {...})

# Or explicit transport
transport = SSETransport(
    url="http://localhost:8084/sse/",
    headers={"Authorization": "Bearer token"}
)
async with Client(transport) as client:
    result = await client.call_tool("solve_schedule_sync", {...})
```

### Why SSE is Deprecated

- Less efficient than HTTP transport
- Limited bidirectional communication
- More complex client-server architecture
- HTTP transport provides all SSE features plus more

## 🛠 Available MCP Tools

The MCP server exposes 11 tools organized into 4 categories:

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

### Employee Management (3 tools - NEW!)
9. **`add_employee_to_job`** - Add new employee to completed job with minimal re-optimization
10. **`update_employee_skills`** - Update employee skills and re-optimize affected assignments
11. **`reassign_shift`** - Reassign shift to specific employee or unassign it

### Continuous Planning (Coming Soon)
The following tools are planned but not yet implemented:
- **`swap_shifts`** - Swap employees between two shifts during optimization
- **`find_shift_replacement`** - Find replacement when employee becomes unavailable
- **`pin_shifts`** - Pin/unpin shifts to prevent changes during optimization


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

### Employee Management Workflow

```markdown
@claude I have a completed schedule (job ID: abc123) and need to make adjustments:

1. Add a new employee "Mike Johnson" with skills ["Nurse", "CPR"] to handle unassigned shifts
2. Update Sarah's skills to add "ICU" certification since she just completed training
```

The system will preserve existing valid assignments and only re-optimize where necessary.

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
  "skills": ["Nurse", "CPR", "Full-time"],
  "preferred_days_off": ["friday", "saturday"],
  "preferred_work_days": ["monday", "tuesday"],
  "unavailable_dates": ["2025-06-15", "2025-06-16T00:00:00"]
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

### Employee Management Requirements

Employee management tools work on completed jobs:
- **Completed job ID**: From a completed optimization (`solve_schedule_sync` or `solve_schedule_async`)
- **Job status**: Must be `SOLVING_COMPLETED`
- **Valid employee data**: Must include ID, name, and skills
- **Intelligent re-optimization**: System preserves valid assignments and only changes what's necessary

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

#### 3. Employee Management Failures
- **Job State**: Job must be completed (status: `SOLVING_COMPLETED`)
- **Invalid Employee ID**: For skill updates, employee must exist in the job
- **Constraint Violations**: System will attempt to resolve violations automatically

### Debug Mode

Set environment variable for detailed logging:
```bash
export SHIFT_AGENT_API_URL="http://localhost:8081"
export PYTHONPATH="/path/to/shiftagent/src"
```

### Checking API Health

Use the health check tool to verify connectivity:
```markdown
@claude Can you check if the shift agent API is healthy?
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
