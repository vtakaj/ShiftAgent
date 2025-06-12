# Shift Scheduler MCP Server

Employee shift scheduling optimization using Timefold Solver with MCP (Model Context Protocol) support for AI assistants.

## 🚀 Quick Start with uvx

### Prerequisites
- Python 3.11+
- Java 17+ (for Timefold Solver)
- `uvx` installed (`pip install uvx` or `uv tool install uvx`)

### 1. Start the API Server
```bash
# Option 1: Using uvx
uvx shift-scheduler-mcp@shift-scheduler-api

# Option 2: From source
git clone https://github.com/vtakaj/natural-shift-planner.git
cd natural-shift-planner
uvx --from . shift-scheduler-api
```

### 2. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shift-scheduler": {
      "command": "uvx",
      "args": ["shift-scheduler-mcp@shift-scheduler-mcp"],
      "env": {
        "SHIFT_SCHEDULER_API_URL": "http://localhost:8081"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

The shift scheduler tools will be available in Claude Desktop.

## 🛠️ Available Commands

- `shift-scheduler-api`: Start the FastAPI server
- `shift-scheduler-mcp`: Start the MCP server

## 🎯 Example Usage

```
I need to create a shift schedule:

Employees:
- John: Nurse, CPR certified
- Sarah: Security guard  
- Mike: Receptionist, admin skills

Shifts:
- Morning (8AM-4PM): Nurse required
- Evening (4PM-12AM): Security required
- Night (12AM-8AM): Receptionist required

Can you optimize this schedule?
```

## 📊 Available MCP Tools

- Health check and demo data
- Synchronous and asynchronous shift optimization
- Weekly hours analysis
- Continuous planning (swap, replace, pin shifts)
- HTML report generation

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHIFT_SCHEDULER_API_URL` | `http://localhost:8081` | API server URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SOLVER_TIMEOUT_SECONDS` | `120` | Optimization timeout |

## 📝 License

Apache-2.0