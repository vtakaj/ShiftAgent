import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)

from constraints import shift_scheduling_constraints
from models import (
    Employee,
    EmployeeRequest,
    Shift,
    ShiftRequest,
    ShiftSchedule,
    ShiftScheduleRequest,
    SolutionResponse,
    SolveResponse,
)

# Create FastAPI application
app = FastAPI(
    title="Shift Scheduler API",
    description="Shift creation API using Timefold Solver",
    version="1.0.0",
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Solver settings
solver_config = SolverConfig(
    solution_class=ShiftSchedule,
    entity_class_list=[Shift],
    score_director_factory_config=ScoreDirectorFactoryConfig(
        constraint_provider_function=shift_scheduling_constraints
    ),
    termination_config=TerminationConfig(spent_limit=Duration(seconds=30)),
)

solver_factory = SolverFactory.create(solver_config)

# Job management dictionary
jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def convert_request_to_domain(request: ShiftScheduleRequest) -> ShiftSchedule:
    """Convert API request to domain objects"""
    # Convert employees
    employees = [
        Employee(id=emp.id, name=emp.name, skills=set(emp.skills))
        for emp in request.employees
    ]

    # Convert shifts
    shifts = [
        Shift(
            id=shift.id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            required_skills=set(shift.required_skills),
            location=shift.location,
            priority=shift.priority,
        )
        for shift in request.shifts
    ]

    return ShiftSchedule(employees=employees, shifts=shifts)


def convert_domain_to_response(schedule: ShiftSchedule) -> Dict[str, Any]:
    """Convert domain objects to API response"""
    return {
        "employees": [
            {"id": emp.id, "name": emp.name, "skills": list(emp.skills)}
            for emp in schedule.employees
        ],
        "shifts": [
            {
                "id": shift.id,
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat(),
                "required_skills": list(shift.required_skills),
                "location": shift.location,
                "priority": shift.priority,
                "employee": (
                    {"id": shift.employee.id, "name": shift.employee.name}
                    if shift.employee
                    else None
                ),
            }
            for shift in schedule.shifts
        ],
        "statistics": {
            "total_employees": schedule.get_employee_count(),
            "total_shifts": schedule.get_shift_count(),
            "assigned_shifts": schedule.get_assigned_shift_count(),
            "unassigned_shifts": schedule.get_unassigned_shift_count(),
        },
    }


def solve_problem_async(job_id: str, problem: ShiftSchedule):
    """Execute shift optimization asynchronously"""
    try:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_ACTIVE"

        solver = solver_factory.build_solver()
        solution = solver.solve(problem)

        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()

    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Shift Scheduler API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "UP",
        "service": "shift-scheduler",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/shifts/demo")
async def get_demo_data():
    """Get demo data"""
    schedule = create_demo_schedule()
    return convert_domain_to_response(schedule)


@app.post("/api/shifts/solve", response_model=SolveResponse)
async def solve_shifts(request: ShiftScheduleRequest):
    """Shift optimization (asynchronous)"""
    job_id = str(uuid.uuid4())
    problem = convert_request_to_domain(request)

    # Register job
    with job_lock:
        jobs[job_id] = {
            "status": "SOLVING_SCHEDULED",
            "created_at": datetime.now(),
            "problem": problem,
        }

    # Start optimization asynchronously
    thread = threading.Thread(
        target=solve_problem_async,
        args=(job_id, problem)
    )
    thread.daemon = True
    thread.start()

    return SolveResponse(job_id=job_id, status="SOLVING_SCHEDULED")


@app.get("/api/shifts/solve/{job_id}", response_model=SolutionResponse)
async def get_solution(job_id: str):
    """Get optimization result"""
    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]

        response = SolutionResponse(job_id=job_id, status=job["status"])

        if job["status"] == "SOLVING_COMPLETED":
            solution = job["solution"]
            response.solution = convert_domain_to_response(solution)
            response.score = str(solution.score)
            response.assigned_shifts = solution.get_assigned_shift_count()
            response.unassigned_shifts = solution.get_unassigned_shift_count()
        elif job["status"] == "SOLVING_FAILED":
            response.message = job.get("error", "Unknown error occurred")

        return response


@app.post("/api/shifts/solve-sync")
async def solve_shifts_sync(request: ShiftScheduleRequest):
    """Shift optimization (synchronous)"""
    try:
        problem = convert_request_to_domain(request)
        solver = solver_factory.build_solver()
        solution = solver.solve(problem)

        return convert_domain_to_response(solution)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_demo_schedule() -> ShiftSchedule:
    """Create demo shift schedule"""
    # Create employees (with employment type)
    employees = [
        Employee("emp1", "John Smith", {"Nurse", "CPR", "Full-time"}),
        Employee("emp2", "Sarah Johnson", {"Nurse", "Full-time"}),
        Employee("emp3", "Michael Brown", {"Security", "Full-time"}),
        Employee("emp4", "Emily Davis", {"Reception", "Admin", "Part-time"}),
        Employee("emp5", "David Wilson", {"Nurse", "Part-time"}),
    ]

    # Create shifts for one week (considering weekly working hours)
    base_date = datetime.now().replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0
    )
    # Start from Monday
    monday = base_date - timedelta(days=base_date.weekday())

    shifts = []

    for day in range(7):  # One week
        day_start = monday + timedelta(days=day)
        day_name = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ][day]

        # Morning shift (8:00-16:00) - 8 hours
        shifts.append(
            Shift(
                id=f"morning_{day_name}",
                start_time=day_start.replace(hour=8),
                end_time=day_start.replace(hour=16),
                required_skills={"Nurse"},
                location="Hospital",
            )
        )

        # Evening shift (16:00-24:00) - 8 hours
        shifts.append(
            Shift(
                id=f"evening_{day_name}",
                start_time=day_start.replace(hour=16),
                end_time=day_start.replace(hour=23, minute=59),
                required_skills={"Nurse"},
                location="Hospital",
            )
        )

        # Night security (22:00-06:00) - 8 hours
        if day < 6:  # Except Sunday
            shifts.append(
                Shift(
                    id=f"security_{day_name}",
                    start_time=day_start.replace(hour=22),
                    end_time=(day_start + timedelta(days=1)).replace(hour=6),
                    required_skills={"Security"},
                    location="Hospital",
                )
            )

        # Reception shift (9:00-13:00) - 4 hours (for part-time)
        if day < 5:  # Weekdays only
            shifts.append(
                Shift(
                    id=f"reception_morning_{day_name}",
                    start_time=day_start.replace(hour=9),
                    end_time=day_start.replace(hour=13),
                    required_skills={"Reception"},
                    location="Reception",
                )
            )

            shifts.append(
                Shift(
                    id=f"reception_afternoon_{day_name}",
                    start_time=day_start.replace(hour=13),
                    end_time=day_start.replace(hour=17),
                    required_skills={"Reception"},
                    location="Reception",
                )
            )

    return ShiftSchedule(employees=employees, shifts=shifts)


# Weekly working hours analysis helper functions
def get_week_key(date: datetime) -> str:
    """Generate week key (year-week number) from date"""
    year, week_num, _ = date.isocalendar()
    return f"{year}-W{week_num:02d}"


def is_full_time_employee(employee: Employee) -> bool:
    """Check if employee is full-time"""
    return "Full-time" in employee.skills or "Full-time" in employee.skills


def get_target_hours(employee: Employee) -> int:
    """Get employee's target working hours"""
    if "Part-time" in employee.skills:
        return 20  # Part-time: 20 hours/week
    elif "Full-time" in employee.skills or "Full-time" in employee.skills:
        return 40  # Full-time: 40 hours/week
    else:
        return 32  # Default: 32 hours/week


@app.get("/api/shifts/weekly-analysis/{job_id}")
async def get_weekly_analysis(job_id: str):
    """Detailed analysis of weekly working hours"""
    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]
        if job["status"] != "SOLVING_COMPLETED":
            raise HTTPException(status_code=400, detail="Job not completed")

        solution = job["solution"]
        analysis = analyze_weekly_hours(solution)

        return analysis


@app.post("/api/shifts/analyze-weekly")
async def analyze_weekly_hours_sync(request: ShiftScheduleRequest):
    """Immediate analysis of weekly working hours (without optimization)"""
    try:
        schedule = convert_request_to_domain(request)
        analysis = analyze_weekly_hours(schedule)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def analyze_weekly_hours(schedule: ShiftSchedule) -> Dict[str, Any]:
    """Detailed analysis of weekly working hours"""

    # Aggregate weekly working hours
    weekly_hours_by_employee = {}
    week_summary = {}

    for shift in schedule.shifts:
        if shift.employee is None:
            continue

        emp_id = shift.employee.id
        week_key = get_week_key(shift.start_time)
        duration_minutes = shift.get_duration_minutes()

        # Aggregate by employee
        if emp_id not in weekly_hours_by_employee:
            weekly_hours_by_employee[emp_id] = {}

        if week_key not in weekly_hours_by_employee[emp_id]:
            weekly_hours_by_employee[emp_id][week_key] = {
                "total_minutes": 0,
                "shift_count": 0,
                "shifts": [],
            }

        weekly_hours_by_employee[emp_id][week_key][
            "total_minutes"
        ] += duration_minutes
        weekly_hours_by_employee[emp_id][week_key][
            "shift_count"
        ] += 1
        weekly_hours_by_employee[emp_id][week_key][
            "shifts"
        ].append(
            {
                "id": shift.id,
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat(),
                "duration_hours": duration_minutes / 60,
                "location": shift.location,
            }
        )

        # Weekly summary
        if week_key not in week_summary:
            week_summary[week_key] = {
                "total_shifts": 0,
                "assigned_shifts": 0,
                "total_hours": 0,
                "employees": set(),
            }

        week_summary[week_key]["total_shifts"] += 1
        week_summary[week_key]["assigned_shifts"] += 1
        week_summary[week_key]["total_hours"] += duration_minutes / 60
        week_summary[week_key]["employees"].add(emp_id)

    # Count unassigned shifts
    for shift in schedule.shifts:
        if shift.employee is None:
            week_key = get_week_key(shift.start_time)
            if week_key in week_summary:
                week_summary[week_key]["total_shifts"] += 1

    # Generate analysis results
    analysis = {
        "by_employee": {},
        "by_week": {},
        "violations": {
            "overtime": [],  # Over 45 hours (hard constraint violation)
            "excessive_hours": [],  # Over 40 hours (overtime)
            "undertime": [],  # Insufficient working hours
            "target_deviation": [],  # Significant deviation from target
        },
        "statistics": {
            "total_employees": len(schedule.employees),
            "weeks_analyzed": len(week_summary),
            "average_weekly_hours": 0,
            "max_weekly_hours": 0,
            "min_weekly_hours": float("inf"),
            "compliance_rate": 0,
        },
    }

    total_hours = 0
    total_employee_weeks = 0
    compliant_weeks = 0

    # Detailed analysis by employee
    for employee in schedule.employees:
        emp_id = employee.id
        employee_analysis = {
            "name": employee.name,
            "employment_type": (
                "Full-time" if is_full_time_employee(employee) else "Part-time"
            ),
            "target_hours": get_target_hours(employee),
            "weeks": {},
        }

        if emp_id in weekly_hours_by_employee:
            for week_key, week_data in weekly_hours_by_employee[emp_id].items():
                hours = week_data["total_minutes"] / 60
                target = get_target_hours(employee)

                week_analysis = {
                    "hours": round(hours, 1),
                    "target": target,
                    "deviation": round(hours - target, 1),
                    "shift_count": week_data["shift_count"],
                    "shifts": week_data["shifts"],
                    "status": "compliant",
                }

                # Constraint violation checks
                if hours > 45:  # Hard constraint violation
                    analysis["violations"]["overtime"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "overtime": round(hours - 45, 1),
                            "severity": "critical",
                        }
                    )
                    week_analysis["status"] = "overtime_violation"

                elif hours > 40:  # Overtime
                    analysis["violations"]["excessive_hours"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "overtime": round(hours - 40, 1),
                            "severity": "warning",
                        }
                    )
                    week_analysis["status"] = "overtime"

                if is_full_time_employee(employee) and hours < 32:  # Insufficient hours
                    analysis["violations"]["undertime"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "shortage": round(32 - hours, 1),
                            "severity": "warning",
                        }
                    )
                    if week_analysis["status"] == "compliant":
                        week_analysis["status"] = "undertime"

                if abs(hours - target) > 5:  # More than 5 hours deviation from target
                    analysis["violations"]["target_deviation"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "target": target,
                            "deviation": round(hours - target, 1),
                            "severity": "info",
                        }
                    )

                # Update statistics
                total_hours += hours
                total_employee_weeks += 1
                if week_analysis["status"] == "compliant":
                    compliant_weeks += 1

                analysis["statistics"]["max_weekly_hours"] = max(
                    analysis["statistics"]["max_weekly_hours"], hours
                )
                analysis["statistics"]["min_weekly_hours"] = min(
                    analysis["statistics"]["min_weekly_hours"], hours
                )

                employee_analysis["weeks"][week_key] = week_analysis

        analysis["by_employee"][emp_id] = employee_analysis

    # Weekly summary
    for week_key, summary in week_summary.items():
        analysis["by_week"][week_key] = {
            "total_shifts": summary["total_shifts"],
            "assigned_shifts": summary["assigned_shifts"],
            "unassigned_shifts": (
                summary["total_shifts"] - summary["assigned_shifts"]
            ),
            "total_hours": round(summary["total_hours"], 1),
            "active_employees": len(summary["employees"]),
            "average_hours_per_employee": round(
                (
                    summary["total_hours"] / len(summary["employees"])
                    if summary["employees"]
                    else 0
                ),
                1,
            ),
        }

    # Complete statistics
    if total_employee_weeks > 0:
        analysis["statistics"]["average_weekly_hours"] = round(
            total_hours / total_employee_weeks, 1
        )
        analysis["statistics"]["compliance_rate"] = round(
            compliant_weeks / total_employee_weeks * 100, 1
        )

    if analysis["statistics"]["min_weekly_hours"] == float("inf"):
        analysis["statistics"]["min_weekly_hours"] = 0
    else:
        analysis["statistics"]["min_weekly_hours"] = round(
            analysis["statistics"]["min_weekly_hours"], 1
        )

    analysis["statistics"]["max_weekly_hours"] = round(
        analysis["statistics"]["max_weekly_hours"], 1
    )

    return analysis


@app.get("/api/shifts/test-weekly")
async def test_weekly_constraints():
    """Test weekly working hours constraints"""
    schedule = create_demo_schedule()
    analysis = analyze_weekly_hours(schedule)

    return {
        "demo_schedule": convert_domain_to_response(schedule),
        "weekly_analysis": analysis,
        "summary": {
            "total_violations": (
                len(analysis["violations"]["overtime"])
                + len(analysis["violations"]["excessive_hours"])
                + len(analysis["violations"]["undertime"])
                + len(analysis["violations"]["target_deviation"])
            ),
            "compliance_rate": analysis["statistics"]["compliance_rate"],
            "recommendations": generate_recommendations(analysis),
        },
    }


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate improvement recommendations based on analysis"""
    recommendations = []

    if analysis["violations"]["overtime"]:
        recommendations.append(
            f"⚠️ {len(analysis['violations']['overtime'])} "
            "critical working hours violations. "
            "Consider hiring additional staff."
        )

    if analysis["violations"]["excessive_hours"]:
        recommendations.append(
            f"🔶 {len(analysis['violations']['excessive_hours'])} "
            "overtime cases. "
            "Consider redistributing shifts."
        )

    if analysis["violations"]["undertime"]:
        recommendations.append(
            f"📉 {len(analysis['violations']['undertime'])} "
            "cases of insufficient hours. "
            "Increase shifts for full-time employees or "
            "assign additional tasks."
        )

    if analysis["statistics"]["compliance_rate"] < 80:
        recommendations.append(
            f"📊 Compliance rate is low at "
            f"{analysis['statistics']['compliance_rate']}%. "
            "Review constraint settings and optimize staff allocation."
        )

    if not recommendations:
        recommendations.append("✅ Weekly working hours constraints are well managed.")

    return recommendations


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
