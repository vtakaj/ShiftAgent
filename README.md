# Natural Shift Planner

A Shift Scheduler API using Timefold Solver with FastMCP integration for AI assistant support.

## 🚀 Quick Start

### Prerequisites

```bash
# Docker Desktop
brew install --cask docker

# VS Code + Dev Containers extension
brew install --cask visual-studio-code
code --install-extension ms-vscode-remote.remote-containers
```

### Starting Development Environment

**Method 1: VS Code Dev Container (Recommended)**
```bash
# Open project
code /projects/shared/shift-scheduler

# Command Palette (Cmd+Shift+P) → "Dev Containers: Reopen in Container"
```

**Method 2: Setup Script**
```bash
cd /projects/shared/shift-scheduler

# Docker environment setup
chmod +x setup-docker.sh
./setup-docker.sh

# Start Dev Container
make dev-setup
```

### Development Start

Inside Dev Container:
```bash
# Install dependencies
make setup

# Start application
make run  # → http://localhost:8081

# Run tests
make test

# Check API specification
# → http://localhost:8081/docs (Swagger UI)
```

## 📁 Project Structure

```
shift-scheduler/
├── .devcontainer/          # Dev Container configuration
│   ├── devcontainer.json   # VS Code Dev Container settings
│   ├── docker-compose.yml  # Dev Container Docker Compose
│   └── Dockerfile          # Dev Container Dockerfile
├── .vscode/                # VS Code settings
│   ├── settings.json       # Editor settings
│   ├── launch.json         # Debug settings
│   └── extensions.json     # Recommended extensions
├── src/                    # Source code directory
│   └── natural_shift_planner/
│       ├── api/            # FastAPI application
│       │   ├── app.py      # FastAPI instance
│       │   ├── routes.py   # API endpoints
│       │   ├── schemas.py  # Pydantic models
│       │   ├── solver.py   # Timefold solver config
│       │   ├── jobs.py     # Async job management
│       │   ├── converters.py # Schema converters
│       │   └── analysis.py # Weekly hours analysis
│       ├── core/           # Domain logic
│       │   ├── models/     # Domain models
│       │   │   ├── employee.py
│       │   │   ├── shift.py
│       │   │   └── schedule.py
│       │   └── constraints/# Optimization constraints
│       │       └── shift_constraints.py
│       ├── mcp/            # MCP server implementation
│       │   ├── server.py   # FastMCP server
│       │   └── tools.py    # MCP tool functions
│       └── utils/          # Utilities
│           └── demo_data.py
├── tests/                  # Test files
│   ├── test_models.py
│   └── test_mcp.py
├── main.py                 # API entry point
├── mcp_server.py           # MCP server entry point
├── api-test.http           # REST Client API tests
├── MCP_SERVER.md           # MCP server documentation
├── CLAUDE.md               # Claude Code guidance
├── Dockerfile              # Production Dockerfile (multi-platform)
├── docker-compose.yml      # Production Docker Compose
├── pyproject.toml          # uv configuration
├── Makefile                # Development efficiency commands
└── README.md               # This file
```

## 🎯 Key Features

### ✅ **Shift Optimization**
- **Skill-based Assignment**: Matching required skills with employee skills
- **Time Constraint Management**: Shift overlap prevention, minimum break time
- **Weekly Work Hours Constraints**: 40-hour limit, minimum work hours, target time adjustment
- **Fairness Optimization**: Equal distribution of work hours

### 🔧 **Partial Modifications** (NEW!)
- **Individual Shift Changes**: Modify single shift assignments with constraint validation
- **Shift Locking**: Lock confirmed shifts to prevent unwanted modifications
- **Impact Analysis**: Preview weekly hours and constraint effects before applying changes
- **Partial Optimization**: Re-optimize only specific date ranges, employees, or locations
- **Quick Fixes**: Rapidly address common scheduling issues in focused scopes

### 📄 **Report Generation** (NEW!)
- **HTML Reports**: Formatted web-based schedule reports with statistics and styling
- **PDF Reports**: Professional PDF reports optimized for printing and sharing
- **Downloadable Files**: Automatic filename generation with timestamps
- **Multiple Formats**: Same schedule data available in both HTML and PDF formats

### 🤖 **MCP Server Integration**
- **AI Assistant Support**: Built-in MCP (Model Context Protocol) server for Claude Desktop and other AI assistants
- **Python-based Implementation**: Uses FastMCP for seamless integration
- **Full API Access**: All shift scheduling and partial modification features available through MCP tools

## 📊 API Specification

### Core Endpoints

```http
GET  /health                          # Health check
GET  /api/shifts/demo                 # Demo data
POST /api/shifts/solve-sync           # Synchronous shift optimization
POST /api/shifts/solve                # Asynchronous shift optimization
GET  /api/shifts/solve/{job_id}       # Get optimization results
POST /api/shifts/analyze-weekly       # Weekly work hours analysis (immediate)
GET  /api/shifts/weekly-analysis/{job_id} # Weekly work hours analysis (after solve)
GET  /api/shifts/test-weekly          # Weekly work hours constraint test (demo)
```

### Partial Modification Endpoints (NEW!)

```http
PATCH /api/shifts/{shift_id}                 # Modify individual shift assignment
POST  /api/shifts/lock                       # Lock/unlock multiple shifts
GET   /api/shifts/change-impact/{shift_id}   # Analyze change impact
POST  /api/shifts/partial-solve              # Partial schedule optimization
```

### Report Generation Endpoints (NEW!)

```http
# HTML Reports
GET  /api/shifts/demo/html                   # Demo schedule as HTML report
GET  /api/shifts/solve/{job_id}/html         # Optimization result as HTML report
POST /api/shifts/solve-sync/html             # Synchronous solve with HTML report

# PDF Reports  
GET  /api/shifts/demo/pdf                    # Demo schedule as PDF report
GET  /api/shifts/solve/{job_id}/pdf          # Optimization result as PDF report
POST /api/shifts/solve-sync/pdf              # Synchronous solve with PDF report
```

### Request Example

```json
{
  "employees": [
    {
      "id": "emp1",
      "name": "John Doe",
      "skills": ["Nurse", "CPR", "Full-time"]
    }
  ],
  "shifts": [
    {
      "id": "morning_shift",
      "start_time": "2025-06-01T08:00:00",
      "end_time": "2025-06-01T16:00:00",
      "required_skills": ["Nurse"],
      "location": "Hospital",
      "priority": 1
    }
  ]
}
```

## 🔧 Constraint System

| Level | Constraint | Description |
|--------|--------|------|
| **HARD** | Skill Matching | Only assign employees with required skills |
| **HARD** | Shift Overlap Prevention | Prevent same employee in overlapping shifts |
| **HARD** | Weekly Max Hours | Violation if over 45 hours |
| **MEDIUM** | Minimum Break Time | 8 hours break between consecutive shifts |
| **MEDIUM** | Weekly Min Hours | Full-time minimum 32 hours |
| **SOFT** | Work Hours Fair Distribution | Minimize work hours gap between employees |
| **SOFT** | Weekly Target Hours | Approximate to personal target hours |

## 🤖 MCP Server for AI Assistants

This project includes a built-in MCP (Model Context Protocol) server that allows AI assistants like Claude Desktop to interact with the Shift Scheduler API.

### Quick Start with MCP

```bash
# Run both API and MCP servers together
make run-mcp

# Or run them separately:
make run      # Terminal 1: API server
make mcp      # Terminal 2: MCP server
```

### Available MCP Tools

#### Core Operations
- `health_check` - Check API health status
- `get_demo_schedule` - Retrieve demo shift schedule with sample data
- `solve_schedule_sync` - Solve shift scheduling synchronously
- `solve_schedule_async` - Start async optimization (returns job ID)
- `get_solve_status` - Check async job status
- `analyze_weekly_hours` - Analyze weekly work hours for schedules
- `test_weekly_constraints` - Test weekly hour constraints with demo data

#### Partial Modifications (NEW!)
- `modify_shift_assignment` - Change individual shift assignments safely
- `lock_shifts` - Lock/unlock shifts to prevent modifications
- `analyze_change_impact` - Preview effects of changes before applying
- `partial_optimize_schedule` - Re-optimize specific date ranges or employees
- `get_schedule_shifts` - Inspect completed schedules in detail
- `quick_fix_schedule` - Rapidly fix common issues in focused scopes

#### Report Generation (NEW!)
- `get_demo_schedule_html` - Get demo schedule as HTML report
- `get_schedule_html_report` - Get completed schedule as HTML report  
- `solve_schedule_sync_html` - Solve and return HTML report in one step
- `get_demo_schedule_pdf` - Get demo schedule as PDF report
- `get_schedule_pdf_report` - Get completed schedule as PDF report
- `solve_schedule_sync_pdf` - Solve and return PDF report in one step

### Claude Desktop Configuration

Add to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "shift-scheduler": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/shift-scheduler", "python", "/path/to/shift-scheduler/mcp_server.py"],
      "env": {
        "SHIFT_SCHEDULER_API_URL": "http://localhost:8081"
      }
    }
  }
}
```

See [MCP_SERVER.md](MCP_SERVER.md) for detailed setup and usage instructions.

## 🧪 Testing & Debugging

### VS Code Integrated Testing
```bash
# Run in Test Explorer
# Command Palette → "Test: Run All Tests"

# Debug Execution
# F5 key → Start debugging with "FastAPI Server" configuration
```

### REST Client Testing
```bash
# Open api-test.http file and
# Click "Send Request" above API requests
```

### Command Line Testing
```bash
make test-api      # Verify API functionality
make test-solve    # Test shift optimization
make test          # Full test suite
```

## 🛠 Troubleshooting

### Common Issues and Solutions

#### 1. **uv sync Error**
```bash
# Issue: Corrupted uv.lock file
# Solution:
rm -f uv.lock
uv sync --no-install-project
```

#### 2. **Java Environment Error**
```bash
# Check Java environment
java -version
echo $JAVA_HOME

# Expected values: 
# OpenJDK 17
# JAVA_HOME=/usr/lib/jvm/java-17-openjdk
```

#### 3. **Python Version Error (Timefold)**
```bash
# Issue: Timefold doesn't support Python 3.13+
# Solution: Use Python 3.11 or 3.12
rm -rf .venv
uv venv --python 3.11
make setup
```

#### 4. **Browser Access Issues**
```bash
# Check VS Code PORTS tab
# Click 🌐 icon for localhost:8081
# Or right-click → "Open in Browser"
```

#### 5. **bash history Error**
```bash
# Solution:
mkdir -p /home/vscode/commandhistory
touch /home/vscode/commandhistory/.bash_history

# Or rebuild Dev Container completely
# Command Palette → "Dev Containers: Rebuild Container"
```

### Environment Check Commands

```bash
# Overall check
make check

# Individual checks
python --version    # Python 3.11.x
uv --version       # uv 0.7.x
java -version      # OpenJDK 17
echo $JAVA_HOME    # Java environment variable

# Application verification
curl http://localhost:8081/health
curl http://localhost:8081/api/shifts/demo
```

### Complete Reset Procedure

Last resort if issues persist:

```bash
# 1. Clean up Docker environment
docker system prune -a

# 2. Rebuild Dev Container completely
# VS Code Command Palette:
# "Dev Containers: Rebuild Container"

# 3. Manual verification
cd /workspace
make setup
make run
```

## 💡 Best Practices

### **Code Quality**
- Auto-format on save (Black, isort)
- Linting (flake8, mypy)
- Type hints recommended

### **Testing**
```bash
# Unit tests
make test

# Check coverage
uv run pytest --cov=.
```

### **Performance**
- Docker Desktop recommended settings: CPU 4+ cores, Memory 8GB+
- File sync optimized

## 📚 References

- [Timefold Solver Documentation](https://docs.timefold.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)

## ✅ Success Checklist

- [ ] Dev Container started successfully
- [ ] Server started with `make run`
- [ ] Browser access to http://localhost:8081
- [ ] `/health` endpoint verified
- [ ] `/api/shifts/demo` data retrieved
- [ ] Debug and test execution in VS Code working

## 🤝 Support

If issues persist, please provide:
- OS version
- Docker Desktop version
- VS Code version
- Specific error messages
- `make check` results

---

**🎉 Happy Coding with Shift Scheduler!**

## Development Environment

All development for this project must be done inside the VS Code Dev Container. Direct local development is not supported.

### Setup Instructions
1. Install Visual Studio Code
2. Install the Remote - Containers extension
3. Open this repository in VS Code and select "Remote-Containers: Open Folder in Container..."
