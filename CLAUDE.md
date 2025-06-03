# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Shift Scheduler API built with FastAPI and Timefold Solver (AI optimization engine). The application optimizes employee shift assignments based on skills, work hours constraints, and fairness.

## Key Commands

### Development Setup
```bash
# Initial setup (clears uv.lock and installs dependencies)
make setup

# Install dependencies only
make install

# Install with dev dependencies
make dev
```

### Running the Application
```bash
# Start FastAPI server on port 8081
make run

# Start in debug mode with verbose logging
make debug
```

### Testing
```bash
# Run all tests
make test

# Test API endpoints (server must be running)
make test-api
```

### Code Quality
```bash
# Format code with Black and isort
make format

# Run linters (flake8, mypy)
make lint
```

### Troubleshooting
```bash
# Check environment
make check

# Full troubleshooting info
make troubleshoot

# Clean cache and Python artifacts
make clean
```

## Architecture

### Core Components

1. **main.py**: FastAPI application entry point
   - Defines API endpoints for shift optimization
   - Manages async job processing
   - Configures Timefold Solver

2. **models.py**: Domain models using Timefold annotations
   - `Employee`: Has skills, assigned to shifts
   - `Shift`: Planning entity with time, location, required skills
   - `ShiftSchedule`: Planning solution containing employees and shifts

3. **constraints.py**: Optimization rules
   - Hard constraints: skill matching, no overlapping shifts, max weekly hours
   - Medium constraints: minimum rest time, minimum weekly hours
   - Soft constraints: minimize unassigned shifts, fair workload distribution

### Constraint System

The solver optimizes using HardMediumSoftScore:
- Hard constraints must be satisfied (skill requirements, no double-booking)
- Medium constraints are important but can be violated (8-hour rest periods)
- Soft constraints are optimization goals (fairness, target hours)

### API Endpoints

- `GET /health`: Health check
- `GET /api/shifts/demo`: Demo data with sample schedule
- `POST /api/shifts/solve-sync`: Synchronous optimization (blocks until complete)
- `POST /api/shifts/solve`: Async optimization (returns job ID)
- `GET /api/shifts/solve/{job_id}`: Get optimization results
- `POST /api/shifts/analyze-weekly`: Analyze weekly work hours
- `GET /api/shifts/test-weekly`: Test weekly constraint calculations

## Development Notes

### Dependencies
- Python 3.11+ required
- Java 17 required (for Timefold Solver)
- Uses `uv` for dependency management
- FastAPI for web framework
- Timefold Solver for constraint optimization

### Testing
Tests use pytest and are located in `test_models.py`. Run a single test with:
```bash
uv run pytest test_models.py::test_name -v
```

### Common Issues
1. If `uv sync` fails, delete `uv.lock` and run `make setup`
2. Java environment must be properly configured (JAVA_HOME)
3. Port 8081 must be available for the server

### API Testing
The `api-test.http` file contains REST Client requests for testing endpoints. Use with VS Code REST Client extension or similar tools.