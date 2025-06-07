# Shift Scheduler System Specification
# For Claude Code Implementation

## 📋 Project Overview

### System Name
Employee Shift Scheduler API

### Overview
Employee shift optimization system using Timefold Solver. Solves complex shift requirements as a constraint satisfaction problem, balancing labor law compliance with operational efficiency.

### Technology Stack
- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **Optimization Engine**: Timefold Solver (Java 17)
- **Package Manager**: uv
- **Development Environment**: Dev Container (Apple Silicon Support)
- **Database**: In-memory (Future PostgreSQL support)

---

## 🎯 Functional Requirements

### 1. Shift Optimization Features

#### 1.1 Basic Optimization
- **Feature ID**: F001
- **Description**: Employee and shift matching optimization
- **Input**: Employee list, shift list, constraints
- **Output**: Optimized shift assignments
- **Endpoint**: `POST /api/shifts/solve-sync`

#### 1.2 Asynchronous Optimization
- **Feature ID**: F002
- **Description**: Asynchronous processing for large datasets
- **Input**: Employee list, shift list
- **Output**: Job ID, processing status
- **Endpoints**: 
  - `POST /api/shifts/solve` (Job submission)
  - `GET /api/shifts/solve/{job_id}` (Result retrieval)

#### 1.3 Shift Pinning Feature
- **Feature ID**: F003
- **Description**: Pin existing shifts and optimize remaining ones
- **Input**: Shift ID, employee ID, pin flag
- **Output**: Pin status, re-optimization results
- **Endpoints**:
  - `POST /api/shifts/pin` (Pin shift)
  - `POST /api/shifts/unpin` (Unpin shift)
  - `POST /api/shifts/re-optimize/{job_id}` (Re-optimize)

### 2. Weekly Work Hours Analysis Features

#### 2.1 Work Hours Analysis
- **Feature ID**: F004
- **Description**: Per-employee weekly work hours analysis and constraint violation detection
- **Input**: Shift schedule
- **Output**: Weekly work hours, constraint violations, improvement suggestions
- **Endpoint**: `POST /api/shifts/analyze-weekly`

#### 2.2 Compliance Check
- **Feature ID**: F005
- **Description**: Verify compliance with labor laws
- **Output**: Violation items, importance, recommended actions
- **Endpoint**: `GET /api/shifts/test-weekly`

### 3. Data Management Features

#### 3.1 Demo Data Provision
- **Feature ID**: F006
- **Description**: Generate sample data for testing
- **Output**: One week of realistic shift data
- **Endpoint**: `GET /api/shifts/demo`

---

## 🔒 Constraint Specifications

### Hard Constraints (Must Follow)

#### HC001: Skill Matching Constraint
```python
Constraint Name: required_skill_constraint
Description: Only assign employees with required skills to shifts
Condition: shift.employee.skills ⊇ shift.required_skills
Violation: HardMediumSoftScore.ONE_HARD penalty
```

#### HC002: Shift Overlap Prevention Constraint
```python
Constraint Name: no_overlapping_shifts_constraint
Description: Prevent same employee from being assigned to overlapping shifts
Condition: ∀(shift1, shift2) where shift1.employee = shift2.employee
      → ¬overlaps(shift1.time, shift2.time)
Violation: HardMediumSoftScore.ONE_HARD penalty
```

#### HC003: Weekly Maximum Hours Constraint
```python
Constraint Name: weekly_maximum_hours_constraint
Description: Employee weekly work hours limit (45 hours)
Condition: sum(employee.weekly_hours) ≤ 45 * 60 (minutes)
Violation: HardMediumSoftScore.ONE_HARD * excess_hours
```

### Medium Constraints (Important but Exceptions Allowed)

#### MC001: Minimum Rest Time Constraint
```python
Constraint Name: minimum_rest_time_constraint
Description: Minimum rest time between consecutive shifts (8 hours)
Condition: next_shift.start_time - current_shift.end_time ≥ 8 hours
Violation: HardMediumSoftScore.ONE_MEDIUM penalty
```

#### MC002: Weekly Minimum Hours Constraint
```python
Constraint Name: weekly_minimum_hours_constraint
Description: Minimum work hours for full-time employees (32 hours)
Condition: full_time_employee → weekly_hours ≥ 32 * 60 (minutes)
Violation: HardMediumSoftScore.ONE_MEDIUM * deficit_hours
```

### Soft Constraints (Optimization Goals)

#### SC001: Minimize Unassigned Shifts
```python
Constraint Name: minimize_unassigned_shifts_constraint
Description: Minimize unassigned shifts (considering priority)
Goal: Assign employees to all shifts
Penalty: HardMediumSoftScore.of_soft(shift.priority * 10)
```

#### SC002: Fair Workload Distribution
```python
Constraint Name: fair_workload_distribution_constraint
Description: Minimize work hours gap between employees
Goal: Keep each employee's work hours close to 8 hours/day
Penalty: HardMediumSoftScore.ONE_SOFT * |actual_hours - 480 minutes|
```

#### SC003: Weekly Hours Target Achievement
```python
Constraint Name: weekly_hours_target_constraint
Description: Achieve target work hours for each employee
Goal: Full-time 40 hours/week, Part-time 20 hours/week
Penalty: HardMediumSoftScore.ONE_SOFT * |actual - target|
```

---

## 📊 Data Model Specifications

### Employee
```python
@dataclass
class Employee:
    id: str                    # Unique identifier
    name: str                  # Employee name
    skills: Set[str]           # List of skills
    
    # Method specifications
    has_skill(skill: str) -> bool
    has_all_skills(required_skills: Set[str]) -> bool
```

### Shift
```python
@planning_entity
@dataclass  
class Shift:
    id: str                           # Unique identifier
    start_time: datetime              # Start date/time
    end_time: datetime                # End date/time
    required_skills: Set[str]         # Required skills
    location: Optional[str]           # Work location
    priority: int                     # Priority (1-10, 1 is highest)
    is_pinned: bool                   # Pin flag
    
    # Planning Variable (Timefold optimization target)
    employee: Optional[Employee]      # Assigned employee
    
    # Method specifications
    get_duration_minutes() -> int
    overlaps_with(other: Shift) -> bool
    is_assigned() -> bool
    pin_assignment(employee: Employee) -> None
    unpin_assignment() -> None
```

### ShiftSchedule
```python
@planning_solution
@dataclass
class ShiftSchedule:
    # Problem Facts (unchanged during optimization)
    employees: List[Employee]
    
    # Planning Entities (optimization targets)
    shifts: List[Shift]
```

---

## 🌐 API Specifications

### Base URL
```
http://localhost:8081
```

### Authentication
Currently no authentication (planned for future implementation)

### Content-Type
```
application/json
```

### Common Response Format
```json
{
  "success": boolean,
  "data": object,
  "message": string,
  "error": string,
  "timestamp": string
}
```

### Endpoint List

#### 1. Health Check
```http
GET /health
Response: {"status": "UP", "service": "shift-scheduler"}
```

#### 2. Demo Data Retrieval
```http
GET /api/shifts/demo
Response: ShiftScheduleResponse
```

#### 3. Synchronous Shift Optimization
```http
POST /api/shifts/solve-sync
Request: ShiftScheduleRequest
Response: ShiftScheduleResponse
```

#### 4. Asynchronous Shift Optimization
```http
POST /api/shifts/solve
Request: ShiftScheduleRequest  
Response: {"job_id": string, "status": "SOLVING_SCHEDULED"}

GET /api/shifts/solve/{job_id}
Response: SolutionResponse
```

#### 5. Continuous Planning Features
```http
POST /api/shifts/{job_id}/swap
Request: {"shift1_id": string, "shift2_id": string}
Response: ContinuousPlanningResponse

POST /api/shifts/{job_id}/replace
Request: {"shift_id": string, "unavailable_employee_id": string}
Response: ContinuousPlanningResponse

POST /api/shifts/{job_id}/pin
Request: {"shift_ids": array, "action": "pin" | "unpin"}
Response: ContinuousPlanningResponse

POST /api/shifts/{job_id}/reassign
Request: {"shift_id": string, "new_employee_id": string}
Response: ContinuousPlanningResponse
```

#### 6. Weekly Work Hours Analysis
```http
POST /api/shifts/analyze-weekly
Request: ShiftScheduleRequest
Response: WeeklyAnalysisResponse

GET /api/shifts/test-weekly
Response: WeeklyTestResponse
```

---

## 🏗️ System Architecture Specifications

### System Configuration
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Timefold      │    │   Data Models   │
│   (Web Layer)   │────│   Solver        │────│   (Domain)      │
│                 │    │   (Optimization)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Constraints   │──────────────┘
                        │   (Business     │
                        │    Logic)       │
                        └─────────────────┘
```

### Directory Structure
```
shift-scheduler/
├── main.py                  # FastAPI application entry point
├── models.py                # Data models and Pydantic schemas  
├── constraints.py           # Timefold constraint definitions
├── pyproject.toml          # uv configuration and dependencies
├── .devcontainer/          # Dev Container configuration
├── .vscode/                # VS Code settings and debug config
├── api-test.http           # REST client test cases
└── test_models.py          # Unit tests
```

### Dependencies
```toml
[dependencies]
fastapi = ">=0.104.1"           # Web framework
uvicorn = ">=0.24.0"            # ASGI server  
timefold = ">=1.14.0"           # Optimization solver
pydantic = ">=2.5.0"            # Data validation
python-multipart = ">=0.0.6"   # Form data support
```

---

## 🧪 Test Specifications

### Test Strategy
- **Unit Tests**: Individual class/method unit tests
- **Integration Tests**: API endpoint tests
- **Constraint Tests**: Constraint logic verification
- **Performance Tests**: Optimization process performance tests

### Test Data
```python
# Standard test data set
employees = [
    Employee("emp1", "John Smith", {"Nurse", "CPR", "Full-time"}),
    Employee("emp2", "Sarah Johnson", {"Nurse", "Full-time"}), 
    Employee("emp3", "Michael Brown", {"Security", "Full-time"}),
    Employee("emp4", "Emily Davis", {"Reception", "Admin", "Part-time"})
]

shifts = [
    # 1 week of realistic shift pattern
    # Morning shift, Night shift, Guard shift, Reception shift
]
```

### Test Execution
```bash
# Run all tests
make test

# Test coverage
uv run pytest --cov=.

# Specific test execution  
uv run pytest test_models.py::test_employee_creation
```

---

## 🚀 Deployment Specifications

### Development Environment
- **Dev Container**: Apple Silicon Mac support
- **Hot Reload**: uvicorn --reload
- **Debugging**: VS Code integrated debugger

### Production Environment
- **Container**: Docker (Multi-platform support)
- **Process Management**: uvicorn (Multiple workers)
- **Reverse Proxy**: Nginx (Future plan)
- **Database**: PostgreSQL (Future plan)

### Environment Variables
```bash
# Production environment
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=postgresql://user:pass@host:port/db
JWT_SECRET_KEY=secret
TIMEFOLD_SOLVER_TIMEOUT=60s
```

---

## 📈 Performance Requirements

### Response Time
- **Synchronous Optimization**: Within 30 seconds (Medium-sized data)
- **API Response**: Within 200ms (Data retrieval)
- **Weekly Work Hours Analysis**: Within 5 seconds

### Scalability
- **Employee Count**: Up to 1000
- **Shift Count**: Up to 10000 shifts/month
- **Simultaneous Requests**: 100req/sec

### Memory Usage
- **Baseline**: 512MB
- **Optimization Execution**: Within 2GB
- **Java Heap**: 1GB (Timefold Solver use)

---

## 🔒 Security Specifications

### Authentication/Authorization (Future implementation)
- **Authentication Method**: JWT Bearer Token
- **Role**: Admin, Manager, Employee
- **Permissions**: Read, Write, Execute

### Data Protection
- **Input Validation**: Strict type checking with Pydantic
- **SQL Injection**: Already mitigated with ORM usage
- **XSS**: FastAPI automatic escape

### Logging/Auditing
- **Access Log**: uvicorn standard log
- **Operation Log**: Shift pinning/unpinning history
- **Error Log**: Structured log output

---

## 🔄 Future Extension Plan

### Phase 2: Database Integration
- PostgreSQL introduction
- Data persistence
- History management

### Phase 3: Authentication/Authorization Management
- JWT authentication
- Role-based access control
- Organizational hierarchy support

### Phase 4: Advanced Features
- Multiple site support
- Automatic notification function
- Report generation
- CSV/Excel input/output

### Phase 5: Machine Learning Integration
- Demand prediction
- Pattern learning
- Automatic adjustment proposal

---

## 📞 Development/Operation Information

### Development Team Contact
- **Lead Developer**: [Contact]
- **System Architecture**: [Contact]  
- **QA Engineer**: [Contact]

### Repository Information
- **Git Repository**: [URL]
- **CI/CD Pipeline**: [URL]
- **Documentation**: [URL]

### Support/Troubleshooting
- **Issue Tracker**: [URL]
- **Knowledge Base**: [URL]
- **Emergency Contact**: [Contact]

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-06-02  
**Next Review**: 2025-07-02