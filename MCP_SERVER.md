# Shift Scheduler MCP Server (Python/FastMCP)

A Python-based MCP (Model Context Protocol) server using FastMCP that provides access to the Shift Scheduler API for AI assistants and other MCP clients.

## Installation

The MCP server is automatically installed when you run:
```bash
make setup
```

This installs FastMCP and httpx along with other dependencies.

## Usage

### Running the MCP Server

**Option 1: Run both API and MCP servers together**
```bash
make run-mcp
```

**Option 2: Run servers separately**
```bash
# Terminal 1: Start API server
make run

# Terminal 2: Start MCP server
make mcp
```

### Environment Variables

- `SHIFT_SCHEDULER_API_URL`: Base URL for the Shift Scheduler API (default: `http://localhost:8081`)

## Available Tools

The MCP server exposes the following tools:

### 1. `health_check`
Check if the Shift Scheduler API is healthy.

### 2. `get_demo_schedule`
Get a demo shift schedule with sample data.

### 3. `solve_schedule_sync`
Solve shift scheduling synchronously (blocks until complete).

**Parameters:**
- `employees`: List of employees with their skills
- `shifts`: List of shifts to be scheduled

### 4. `solve_schedule_async`
Start asynchronous shift scheduling (returns job ID).

**Parameters:**
- `employees`: List of employees with their skills
- `shifts`: List of shifts to be scheduled

### 5. `get_solve_status`
Get the status and results of an async solve job.

**Parameters:**
- `job_id`: The job ID returned from solve_schedule_async

### 6. `analyze_weekly_hours`
Analyze weekly work hours for a given schedule.

**Parameters:**
- `employees`: List of employees
- `shifts`: List of shifts with assignments

### 7. `test_weekly_constraints`
Test weekly hour constraints with demo data.

## Integration with Claude Desktop

To use this MCP server with Claude Desktop, add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "shift-scheduler": {
      "command": "uv",
      "args": ["run", "python", "/path/to/shift-scheduler/mcp_server.py"],
      "env": {
        "SHIFT_SCHEDULER_API_URL": "http://localhost:8081"
      }
    }
  }
}
```

Replace `/path/to/shift-scheduler` with the actual path to your project directory.

## Testing the MCP Server

You can test the MCP server using:
```bash
make test-mcp
```

Or manually send JSON-RPC requests:
```bash
echo '{"jsonrpc":"2.0","method":"list_tools","id":1}' | uv run python mcp_server.py
```

## Development

The MCP server is implemented in `mcp_server.py` using FastMCP, which provides:
- Automatic tool discovery and documentation
- Type validation using Pydantic
- Async support for API calls
- Standard MCP protocol compliance

## Requirements

- Python 3.11+
- Shift Scheduler API running (default: http://localhost:8081)
- FastMCP and httpx (installed via `make setup`)