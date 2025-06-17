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
from .job_store import job_store
from .jobs import (
    _sync_job_to_store,
    create_emergency_job,
    job_lock,
    jobs,
    solve_problem_async,
)
from .problem_fact_changes import AddEmployeeProblemFactChange
from .schemas import (
    EmployeeRequest,
    ShiftScheduleRequest,
    SolutionResponse,
    SolveResponse,
)
from .solver import solver_factory


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Shift Scheduler API", "version": "1.0.0", "docs": "/docs"}


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
        _sync_job_to_store(job_id)

    # Start optimization asynchronously
    thread = threading.Thread(target=solve_problem_async, args=(job_id, problem))
    thread.daemon = True
    thread.start()

    return SolveResponse(job_id=job_id, status="SOLVING_SCHEDULED")


@app.get("/api/shifts/solve/{job_id}", response_model=SolutionResponse)
async def get_solution(job_id: str):
    """Get optimization result"""
    with job_lock:
        # First check in-memory jobs
        if job_id not in jobs and job_store:
            # Try to load from persistent storage
            stored_job = job_store.get_job(job_id)
            if stored_job:
                jobs[job_id] = stored_job

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
    import logging
    from datetime import datetime

    from .solver import SOLVER_LOG_LEVEL, SOLVER_TIMEOUT_SECONDS

    logger = logging.getLogger(__name__)

    try:
        problem = convert_request_to_domain(request)
        solver = solver_factory.build_solver()

        start_time = datetime.now()
        logger.info(
            f"[Sync] Starting optimization with {len(problem.shifts)} shifts "
            f"and {len(problem.employees)} employees (timeout: {SOLVER_TIMEOUT_SECONDS}s)"
        )

        solution = solver.solve(problem)

        elapsed = (datetime.now() - start_time).total_seconds()
        assigned_count = sum(
            1 for shift in solution.shifts if shift.employee is not None
        )

        logger.info(
            f"[Sync] Optimization completed in {elapsed:.1f}s. "
            f"Final score: {solution.score}, "
            f"Assigned shifts: {assigned_count}/{len(solution.shifts)}"
        )

        # Log score breakdown in debug mode
        if SOLVER_LOG_LEVEL == "DEBUG" and solution.score:
            logger.debug(
                f"[Sync] Score breakdown - "
                f"Hard: {solution.score.hard_score}, "
                f"Medium: {solution.score.medium_score}, "
                f"Soft: {solution.score.soft_score}"
            )

        return convert_domain_to_response(solution)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
        raise HTTPException(status_code=500, detail=str(e)) from e


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


# Job Management endpoints
@app.get("/api/jobs")
async def list_jobs():
    """List all jobs (both in-memory and persistent)"""
    all_job_ids = set(jobs.keys())

    # Add persistent job IDs if available
    if job_store:
        all_job_ids.update(job_store.list_jobs())

    job_summaries = []
    for job_id in all_job_ids:
        # Try to get from memory first
        if job_id in jobs:
            job = jobs[job_id]
        elif job_store:
            job = job_store.get_job(job_id)
        else:
            continue

        if job:
            job_summaries.append(
                {
                    "job_id": job_id,
                    "status": job.get("status"),
                    "created_at": job.get("created_at"),
                    "completed_at": job.get("completed_at"),
                }
            )

    # Sort by created_at descending (newest first)
    job_summaries.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)

    return {"total": len(job_summaries), "jobs": job_summaries}


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job from both memory and persistent storage"""
    deleted = False

    # Delete from memory
    with job_lock:
        if job_id in jobs:
            # Don't delete if actively solving
            if jobs[job_id].get("status") in ["SOLVING_ACTIVE", "SOLVING_SCHEDULED"]:
                if "solver" in jobs[job_id]:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot delete job that is currently solving",
                    )
            del jobs[job_id]
            deleted = True

    # Delete from persistent storage
    if job_store:
        try:
            job_store.delete_job(job_id)
            deleted = True
        except Exception:
            pass

    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": f"Job {job_id} deleted successfully"}


@app.post("/api/jobs/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Clean up old jobs from storage"""
    deleted_count = 0

    if job_store and hasattr(job_store, "cleanup_old_jobs"):
        deleted_count = job_store.cleanup_old_jobs(max_age_hours)

    # Also clean up old in-memory jobs
    with job_lock:
        cutoff = datetime.now()
        cutoff = cutoff.replace(hour=cutoff.hour - max_age_hours)

        to_delete = []
        for job_id, job in jobs.items():
            # Skip active jobs
            if job.get("status") in ["SOLVING_ACTIVE", "SOLVING_SCHEDULED"]:
                continue

            # Check if old enough
            created_at = job.get("created_at") or job.get("completed_at")
            if created_at and created_at < cutoff:
                to_delete.append(job_id)

        for job_id in to_delete:
            del jobs[job_id]
            deleted_count += 1

    return {
        "deleted_count": deleted_count,
        "message": f"Cleaned up {deleted_count} jobs older than {max_age_hours} hours",
    }


# Emergency Management Endpoints


@app.post("/api/shifts/solve-emergency")
async def solve_emergency_mode(request: ShiftScheduleRequest):
    """Start solving in emergency mode (supports dynamic changes)"""
    # Convert to domain model
    problem = convert_request_to_domain(request)

    # Create emergency job
    job_id = create_emergency_job(problem)

    return {
        "job_id": job_id,
        "status": "SOLVING_SCHEDULED",
        "message": "Emergency solving started. Job will remain active for emergency changes.",
        "employees": len(problem.employees),
        "shifts": len(problem.shifts),
    }


@app.post("/api/shifts/{job_id}/add-employee-emergency")
async def add_employee_emergency(
    job_id: str,
    employee: EmployeeRequest,
    auto_assign_shift_ids: list[str] | None = None,
):
    """Add employee for emergency staffing using Problem Fact Change"""
    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]

        # Check if job is in emergency mode and has active solver
        if not job.get("emergency_mode"):
            raise HTTPException(
                status_code=400,
                detail="Job is not in emergency mode. Use /api/shifts/solve-emergency to start.",
            )

        if "solver" not in job:
            raise HTTPException(
                status_code=400,
                detail="No active solver found. Job may have completed or failed.",
            )

        solver = job["solver"]

    # Convert employee to domain model
    from .converters import convert_employee_request_to_domain

    new_employee = convert_employee_request_to_domain(employee)

    # Mark as emergency addition
    new_employee.mark_as_emergency_addition()

    # Create and apply problem fact change
    change = AddEmployeeProblemFactChange(new_employee, auto_assign_shift_ids)

    try:
        solver.add_problem_fact_change(change)

        # Track the change
        with job_lock:
            jobs[job_id]["emergency_changes"].append(
                {
                    "type": "add_employee",
                    "employee_id": employee.id,
                    "employee_name": employee.name,
                    "timestamp": datetime.now(),
                    "auto_assigned_shifts": auto_assign_shift_ids or [],
                }
            )
            _sync_job_to_store(job_id)

        return {
            "message": f"Emergency employee {employee.name} added successfully",
            "job_id": job_id,
            "employee_id": employee.id,
            "status": "SUCCESS",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add emergency employee: {str(e)}",
        ) from e


@app.get("/api/shifts/{job_id}/emergency-status")
async def get_emergency_job_status(job_id: str):
    """Get status of emergency job including changes made"""
    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]

        if not job.get("emergency_mode"):
            raise HTTPException(
                status_code=400,
                detail="Not an emergency job",
            )

        response = {
            "job_id": job_id,
            "status": job["status"],
            "emergency_mode": True,
            "has_active_solver": "solver" in job,
            "created_at": job.get("created_at"),
            "completed_at": job.get("completed_at"),
            "emergency_changes": job.get("emergency_changes", []),
            "changes_count": len(job.get("emergency_changes", [])),
        }

        # Include solution if available
        if "solution" in job and job["solution"]:
            solution = job["solution"]
            response["solution"] = convert_domain_to_response(solution)
            response["score"] = str(solution.score)
            response["assigned_shifts"] = sum(
                1 for s in solution.shifts if s.employee is not None
            )
            response["total_shifts"] = len(solution.shifts)

        return response
