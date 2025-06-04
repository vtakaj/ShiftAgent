"""
API route handlers
"""
import threading
import uuid
from datetime import datetime

from fastapi import HTTPException

from ..utils import create_demo_schedule
from .analysis import analyze_weekly_hours, generate_recommendations
from .app import app
from .converters import convert_domain_to_response, convert_request_to_domain
from .jobs import job_lock, jobs, solve_problem_async
from .schemas import ShiftScheduleRequest, SolutionResponse, SolveResponse
from .solver import solver_factory


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