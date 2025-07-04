# ShiftAgent

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Timefold](https://img.shields.io/badge/Timefold-1.14%2B-orange.svg)](https://timefold.ai)
[![FastMCP](https://img.shields.io/badge/FastMCP-0.1%2B-purple.svg)](https://github.com/pydantic/fastmcp)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checker](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy.readthedocs.io)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://docker.com)
[![Azure](https://img.shields.io/badge/Azure-supported-0078d4.svg)](https://azure.microsoft.com)
[![AI Optimization](https://img.shields.io/badge/AI-optimization-ff6b35.svg)](https://timefold.ai)
[![MCP Protocol](https://img.shields.io/badge/MCP-protocol-8b5cf6.svg)](https://modelcontextprotocol.io)

An AI-powered employee shift scheduling agent using Timefold Solver with FastMCP integration for AI assistant support.

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
code /projects/shared/shiftagent

# Command Palette (Cmd+Shift+P) → "Dev Containers: Reopen in Container"
```

**Method 2: Setup Script**
```bash
cd /projects/shared/shiftagent

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

# Start with extended solver timeout and verbose logging
SOLVER_TIMEOUT_SECONDS=300 SOLVER_LOG_LEVEL=DEBUG make run

# Run tests
make test

# Check API specification
# → http://localhost:8081/docs (Swagger UI)
```

## 🐳 Docker Deployment

The project includes Docker Compose configurations for both development and production environments.

### Development with Docker Compose

```bash
# Copy environment variables template
cp .env.example .env

# Start development environment (API + PostgreSQL)
docker-compose up

# Start with MCP server included
docker-compose --profile mcp up

# Start in background
docker-compose up -d
```

**Features:**
- Hot reload with source code volume mounts
- PostgreSQL database for future use
- Persistent job storage
- Development-optimized settings

### Production Deployment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Full production stack with reverse proxy and cache
docker-compose -f docker-compose.prod.yml --profile nginx --profile cache up -d
```

**Features:**
- Optimized container settings
- Nginx reverse proxy
- Resource limits and health checks
- Redis cache (optional)
- Production-grade logging

### Environment Variables

All configuration is managed through environment variables. See `.env.example` for a complete list.

**Key Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Application logging level |
| `SOLVER_TIMEOUT_SECONDS` | `120` | Solver optimization timeout |
| `SHIFT_AGENT_PORT` | `8081` | API server port |
| `POSTGRES_PASSWORD` | - | Database password (required in production) |
| `JAVA_OPTS` | `-Xmx1g` | JVM memory and optimization settings |

**Development Example:**
```bash
# .env file for development
LOG_LEVEL=DEBUG
SOLVER_TIMEOUT_SECONDS=60
JAVA_OPTS=-Xmx512m
```

**Production Example:**
```bash
# .env file for production
LOG_LEVEL=WARN
SOLVER_TIMEOUT_SECONDS=300
JAVA_OPTS=-Xmx2g -XX:+UseG1GC
POSTGRES_PASSWORD=secure_password_here
```

### Service Profiles

Use Docker Compose profiles to control which services are started:

```bash
# Default: API + Database
docker-compose up

# Include MCP server
docker-compose --profile mcp up

# Production with reverse proxy
docker-compose -f docker-compose.prod.yml --profile nginx up

# Full stack with cache
docker-compose -f docker-compose.prod.yml --profile nginx --profile cache up
```

### Health Checks and Monitoring

All services include health checks:
- **API**: `GET /health` endpoint
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping` command
- **Nginx**: Process and port monitoring

Access points:
- **API**: http://localhost:8081
- **API Documentation**: http://localhost:8081/docs
- **MCP Server**: http://localhost:8082 (if enabled)
- **Web Interface**: http://localhost (if nginx profile enabled)

## 📁 Project Structure

```
shiftagent/
├── .devcontainer/          # Dev Container configuration
│   ├── devcontainer.json   # VS Code Dev Container settings
│   ├── docker-compose.yml  # Dev Container Docker Compose
│   └── Dockerfile          # Dev Container Dockerfile
├── .vscode/                # VS Code settings
│   ├── settings.json       # Editor settings
│   ├── launch.json         # Debug settings
│   └── extensions.json     # Recommended extensions
├── src/                    # Source code directory
│   ├── shiftagent/         # Main application package
│   │   ├── api/            # FastAPI application
│   │   │   ├── app.py      # FastAPI instance
│   │   │   ├── routes.py   # API endpoints
│   │   │   ├── schemas.py  # Pydantic models
│   │   │   ├── jobs.py     # Async job management
│   │   │   ├── converters.py # Schema converters
│   │   │   ├── solver.py   # Timefold solver configuration
│   │   │   ├── analysis.py # Weekly hours analysis
│   │   │   ├── server.py   # Server configuration
│   │   │   ├── job_store.py # Job storage implementation
│   │   │   ├── azure_job_store.py # Azure storage backend
│   │   │   ├── problem_fact_changes.py # Dynamic problem updates
│   │   │   └── shift-schedule-template.html # HTML template
│   │   ├── core/           # Domain logic
│   │   │   ├── models/     # Domain models
│   │   │   │   ├── employee.py
│   │   │   │   ├── shift.py
│   │   │   │   └── schedule.py
│   │   │   └── constraints/# Optimization constraints
│   │   │       └── shift_constraints.py
│   │   ├── config/         # Configuration management
│   │   │   └── storage_config.py
│   │   ├── templates/      # HTML templates and rendering
│   │   │   ├── renderer.py
│   │   │   └── schedule_report.html
│   │   ├── utils/          # Utilities
│   │   │   └── demo_data.py
│   │   └── streamlit_app.py # Streamlit web interface
│   └── shiftagent_mcp/     # MCP server implementation
│       ├── server.py       # FastMCP server
│       └── tools.py        # MCP tool functions
├── tests/                  # Test files
│   ├── test_models.py
│   ├── test_mcp.py
│   ├── test_preferences.py
│   ├── test_emergency_staff.py
│   ├── test_continuous_planning.py
│   └── test_azure_storage.py
├── scripts/                # Utility scripts
│   ├── run_mcp_http.py     # MCP HTTP server runner
│   ├── run_mcp_sse.py      # MCP SSE server runner
│   ├── docker_mcp.sh       # Docker MCP setup
│   └── test_mcp_connection.sh
├── docker/                 # Docker configurations
│   ├── dockerfiles/        # Dockerfile variants
│   └── compose/            # Docker Compose files
│       ├── docker-compose.yml
│       ├── docker-compose.prod.yml
│       ├── docker-compose.mcp.yml
│       └── docker-compose.n8n.yml
├── docs/                   # Documentation
│   ├── SYSTEM_SPECIFICATION.md
│   ├── CONTAINER_REGISTRY.md
│   ├── SOLVER_CONFIGURATION.md
│   └── mcp-employee-management-sequence.md
├── infrastructure/         # Terraform infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── environments/       # Environment configurations
│   ├── modules/            # Terraform modules
│   └── scripts/            # Infrastructure scripts
├── job_storage/            # Local job storage directory
├── api-test.http           # REST Client API tests
├── MCP_SERVER.md           # MCP server documentation
├── DOCKER_MCP.md           # Docker MCP setup guide
├── CLAUDE.md               # Claude Code guidance
├── CONTRIBUTING.md         # Contribution guidelines
├── Dockerfile              # Production Dockerfile
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

### 👥 **Employee Management**
- **Add Employees to Completed Jobs**: Add new employees to already solved schedules
- **Skill Updates**: Update employee skills and re-optimize affected assignments
- **Minimal Re-optimization**: Uses intelligent pinning to preserve valid assignments
- **Constraint Resolution**: Automatically resolves violations while minimizing changes

### 📄 **Report Generation**
- **HTML Reports**: Formatted web-based schedule reports with statistics and styling
- **Visual Display**: Clear visual representation of shift schedules
- **Downloadable Files**: Automatic filename generation with timestamps

### 🤖 **MCP Server Integration**
- **AI Assistant Support**: Built-in MCP (Model Context Protocol) server for Claude Desktop and other AI assistants
- **Python-based Implementation**: Uses FastMCP for seamless integration
- **Full API Access**: All shift scheduling and continuous planning features available through MCP tools

### ⚙️ **Configurable Solver**
- **Extended Timeout**: Configure solver runtime via `SOLVER_TIMEOUT_SECONDS` (default: 120s)
- **Verbose Logging**: Real-time optimization progress with `SOLVER_LOG_LEVEL=DEBUG`
- **Progress Tracking**: Monitor score improvements and constraint violations
- **Better Solutions**: Longer solving time for more optimal shift assignments

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

### Employee Management Endpoints

```http
POST /api/shifts/{job_id}/add-employee        # Add employee to completed job
PATCH /api/shifts/{job_id}/employee/{employee_id}/skills  # Update employee skills
```

### Job Management Endpoints

```http
GET  /api/jobs                               # List all jobs
DELETE /api/jobs/{job_id}                    # Delete specific job
POST /api/jobs/cleanup                       # Clean up old jobs
```

### Report Generation Endpoints

```http
# HTML Reports
GET  /api/shifts/demo/html                   # Demo schedule as HTML report
GET  /api/shifts/solve/{job_id}/html         # Optimization result as HTML report
POST /api/shifts/solve-sync/html             # Synchronous solve with HTML report
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

This project includes a built-in MCP (Model Context Protocol) server that allows AI assistants like Claude Desktop to interact with the Shift Agent API.

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

#### Schedule Management
- `get_schedule_shifts` - Inspect completed schedules in detail

#### Report Generation
- `get_demo_schedule_html` - Get demo schedule as HTML report
- `get_schedule_html_report` - Get completed schedule as HTML report
- `solve_schedule_sync_html` - Solve and return HTML report in one step

### Claude Desktop Configuration

Add to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### **Code Quality & Git Hooks**
- Auto-format on save (ruff)
- Linting (ruff, mypy)
- Type hints recommended
- **pre-commit hooks** automatically ensure code quality

#### Git Hooks (pre-commit)
This project uses pre-commit to automatically run quality checks before commits:

```bash
# Pre-commit hooks run automatically:
# ✅ Code formatting (ruff format)
# ✅ Linting (ruff check --fix)
# ✅ Type checking (mypy - warnings only)
# ✅ Auto-stage formatted files

# Pre-push hooks run automatically:
# ✅ Full test suite execution

# Commit message validation:
# ✅ Conventional commit format required
```

#### Manual Code Quality Checks
```bash
# Using make commands
make lint             # Run linting (ruff + mypy)
make format           # Run formatting (ruff)
make test             # Run pytest test suite

# Or using uv directly
uv run ruff check .   # Run ruff linting
uv run ruff format .  # Run ruff formatting
uv run mypy .         # Run mypy type checking
uv run pytest -v      # Run pytest test suite
```

#### Bypassing Hooks (Emergency Use)
```bash
# Skip pre-commit hooks
git commit --no-verify -m "emergency fix"

# Skip pre-push hooks
git push --no-verify

# Skip tests during push
SKIP_TESTS=true git push
```

#### Conventional Commit Format
```bash
# Required format: type: description
feat: add new feature
fix: fix a bug
docs: update documentation
style: code style changes
refactor: code refactoring
test: add or update tests
chore: maintenance tasks
```

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

**🎉 Happy Coding with Shift Agent!**

## Development Environment

All development for this project must be done inside the VS Code Dev Container. Direct local development is not supported.

### Setup Instructions
1. Install Visual Studio Code
2. Install the Remote - Containers extension
3. Open this repository in VS Code and select "Remote-Containers: Open Folder in Container..."

## Shift Creation Flow

The following diagram explains the flow of shift creation.

```mermaid
sequenceDiagram
    participant Human as Human
    participant LLM as Claude Desktop (LLM)
    participant Tool as Tool
    participant Solver as Solver

    Human->>LLM: Shift Creation Request
    Note over Human: "Please create a one-month work schedule."

    LLM->>LLM: 1. Employee Preference Collection
    Note over LLM: - Collect employee preferences<br>- Preferred days off<br>- Preferred work days<br>- Unavailable dates<br>- Skill information

    LLM->>LLM: 2. Shift Data Creation
    Note over LLM: - Create empty shifts for one month<br>- Set time slots<br>- Set required skills<br>- Set priorities<br>- Set locations<br>- Incorporate employee preferences

    LLM->>Tool: 3. Shift Data Analysis
    Note over Tool: Process employee data<br>- Skill information<br>- Preferred days off<br>- Unavailable dates

    Tool->>Solver: 4. Shift Optimization Problem Construction
    Note over Solver: - Set constraints<br>- Set objective function<br>- Set optimization parameters

    Solver->>Solver: 5. Optimization Calculation
    Note over Solver: - Constraint satisfaction<br>- Objective function optimization<br>- Solution generation

    Solver->>Tool: 6. Optimization Result Reception
    Note over Tool: - Solution validation<br>- Result formatting

    Tool->>LLM: 7. Result Display
    Note over LLM: - Display shift table<br>- Display optimization score

    LLM->>Human: 8. Result Presentation
    Note over Human: - Review shift table<br>- Review optimization results
```

### Step-by-Step Explanation

1. **Employee Preference Collection (LLM)**
   - Gather employee information
     - Preferred days off
     - Preferred work days
     - Unavailable dates
     - Skill information
     - Employment type preferences

2. **Shift Data Creation (LLM)**
   - Create empty shifts for one month
     - Weekday shifts (Mon-Fri)
     - Weekend shifts
   - Configure each shift
     - Time slots (Morning, Afternoon)
     - Required skills
     - Priority levels
     - Locations
   - Special shift settings
     - Saturday special shifts, etc.
   - Incorporate employee preferences
     - Match skills with required positions
     - Consider preferred work days
     - Avoid unavailable dates

3. **Shift Data Analysis (Tool)**
   - Create employee data
     - Skill information
     - Preferred days off
     - Unavailable dates
     - Employment type

4. **Shift Optimization Problem Construction (Solver)**
   - Set hard constraints
     - Skill requirements
     - Unavailable dates
   - Set soft constraints
     - Preferred days off
     - Preferred work days

5. **Optimization Calculation (Solver)**
   - Solve constraint satisfaction problem
   - Optimize objective function
   - Generate and evaluate solutions

6. **Optimization Result Reception (Tool)**
   - Validate generated solutions
   - Format and structure results

7. **Result Display (LLM)**
   - Display shift table in tabular format
   - Display optimization score
   - Display constraint satisfaction status

8. **Result Presentation (Human)**
   - Review shift table in tabular format
   - Review optimization results explanation

## 🏗️ Infrastructure

This project includes Infrastructure as Code (IaC) using Terraform for Azure deployment with comprehensive CI/CD automation.

### Infrastructure Documentation

- **包括のインフラドキュメント**: [infrastructure/README.md](infrastructure/README.md)

### Quick Infrastructure Setup

```bash
# Navigate to infrastructure directory
cd infrastructure

# Initialize Terraform
terraform init

# Deploy development environment
terraform apply -var-file=environments/dev.tfvars

# Deploy production environment
terraform apply -var-file=environments/prod.tfvars
```

### 🚀 CI/CD Features

This project includes comprehensive CI/CD automation:
- **Automated Testing**: Python tests with coverage reporting
- **Security Scanning**: Vulnerability detection and dependency review
- **Quality Gates**: Code formatting, linting, and type checking
- **Infrastructure Validation**: Terraform plan and validation
- **Multi-Environment Deployment**: Automated dev, manual production

### Infrastructure Features

- **Azure Container Apps**: Application hosting
- **Azure Container Registry**: Docker image storage
- **Azure Storage**: Job data persistence
- **Azure Key Vault**: Secrets management (production)
- **Azure Monitor**: Application monitoring
- **CI/CD Integration**: GitHub Actions workflows

For detailed infrastructure documentation, see [infrastructure/README.md](infrastructure/README.md).
