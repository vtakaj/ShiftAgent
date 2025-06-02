# Shift Scheduler API

A Shift Scheduler API using Timefold Solver.

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
├── main.py                 # FastAPI main application
├── models.py               # Timefold Solver data models
├── constraints.py          # Shift optimization constraints
├── api-test.http           # REST Client API tests
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

## 📊 API Specification

### Basic Endpoints

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

#### 3. **Browser Access Issues**
```bash
# Check VS Code PORTS tab
# Click 🌐 icon for localhost:8081
# Or right-click → "Open in Browser"
```

#### 4. **bash history Error**
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
