"""
API route handlers
"""

import io
import threading
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from ..utils import create_demo_schedule
from .analysis import analyze_weekly_hours, generate_recommendations
from .app import app
from .continuous_planning import ContinuousPlanningService
from .converters import convert_domain_to_response, convert_request_to_domain
from .job_store import job_store
from .jobs import job_lock, jobs, solve_problem_async, _sync_job_to_store
from .schemas import (
    ContinuousPlanningResponse,
    ShiftPinRequest,
    ShiftReassignRequest,
    ShiftReplacementRequest,
    ShiftScheduleRequest,
    ShiftSwapRequest,
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




# Continuous Planning endpoints
@app.post("/api/shifts/{job_id}/swap", response_model=ContinuousPlanningResponse)
async def swap_shifts(job_id: str, request: ShiftSwapRequest):
    """Swap employees between two shifts"""
    with job_lock:
        # Find the specific job
        if job_id not in jobs and job_store:
            # Try to load from persistent storage
            stored_job = job_store.get_job(job_id)
            if stored_job:
                jobs[job_id] = stored_job
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]
        
        if job["status"] != "SOLVING_SCHEDULED" or "solver" not in job:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} is not in an active solving state. Current status: {job['status']}",
            )
        
        active_solver = job["solver"]

        try:
            # Apply the swap using ProblemChangeDirector
            ContinuousPlanningService.swap_shifts(
                active_solver, request.shift1_id, request.shift2_id
            )

            # Get current solution to return affected shifts
            solution = active_solver.get_best_solution()
            affected_shifts = []

            for shift in solution.shifts:
                if shift.id in [request.shift1_id, request.shift2_id]:
                    affected_shifts.append(
                        {
                            "id": shift.id,
                            "start_time": shift.start_time.isoformat(),
                            "end_time": shift.end_time.isoformat(),
                            "employee": (
                                {"id": shift.employee.id, "name": shift.employee.name}
                                if shift.employee
                                else None
                            ),
                            "pinned": shift.pinned,
                        }
                    )

            return ContinuousPlanningResponse(
                success=True,
                message=f"Successfully swapped shifts {request.shift1_id} and {request.shift2_id}",
                operation="swap",
                affected_shifts=affected_shifts,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shifts/{job_id}/replace", response_model=ContinuousPlanningResponse)
async def find_replacement(job_id: str, request: ShiftReplacementRequest):
    """Find replacement for a shift when an employee becomes unavailable"""
    with job_lock:
        # Find the specific job
        if job_id not in jobs and job_store:
            # Try to load from persistent storage
            stored_job = job_store.get_job(job_id)
            if stored_job:
                jobs[job_id] = stored_job
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]
        
        if job["status"] != "SOLVING_SCHEDULED" or "solver" not in job:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} is not in an active solving state. Current status: {job['status']}",
            )
        
        active_solver = job["solver"]

        try:
            # Apply the replacement using ProblemChangeDirector
            ContinuousPlanningService.find_replacement_for_shift(
                active_solver, request.shift_id, request.unavailable_employee_id
            )

            return ContinuousPlanningResponse(
                success=True,
                message=f"Finding replacement for shift {request.shift_id}. Solver will assign a suitable employee.",
                operation="replace",
                affected_shifts=[],
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shifts/{job_id}/pin", response_model=ContinuousPlanningResponse)
async def pin_shifts(job_id: str, request: ShiftPinRequest):
    """Pin or unpin shifts for continuous planning"""
    with job_lock:
        # Find the specific job
        if job_id not in jobs and job_store:
            # Try to load from persistent storage
            stored_job = job_store.get_job(job_id)
            if stored_job:
                jobs[job_id] = stored_job
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]
        
        if job["status"] != "SOLVING_SCHEDULED" or "solver" not in job:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} is not in an active solving state. Current status: {job['status']}",
            )
        
        active_solver = job["solver"]

        try:
            if request.action == "pin":
                ContinuousPlanningService.pin_shifts(active_solver, request.shift_ids)
                message = f"Successfully pinned {len(request.shift_ids)} shifts"
            else:
                ContinuousPlanningService.unpin_shifts(active_solver, request.shift_ids)
                message = f"Successfully unpinned {len(request.shift_ids)} shifts"

            return ContinuousPlanningResponse(
                success=True,
                message=message,
                operation=request.action,
                affected_shifts=[],
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shifts/{job_id}/reassign", response_model=ContinuousPlanningResponse)
async def reassign_shift(job_id: str, request: ShiftReassignRequest):
    """Reassign a shift to a specific employee"""
    with job_lock:
        # Find the specific job
        if job_id not in jobs and job_store:
            # Try to load from persistent storage
            stored_job = job_store.get_job(job_id)
            if stored_job:
                jobs[job_id] = stored_job
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]
        
        if job["status"] != "SOLVING_SCHEDULED" or "solver" not in job:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} is not in an active solving state. Current status: {job['status']}",
            )
        
        active_solver = job["solver"]

        try:
            ContinuousPlanningService.reassign_shift(
                active_solver, request.shift_id, request.new_employee_id
            )

            employee_msg = (
                f"employee {request.new_employee_id}"
                if request.new_employee_id
                else "unassigned"
            )

            return ContinuousPlanningResponse(
                success=True,
                message=f"Successfully reassigned shift {request.shift_id} to {employee_msg}",
                operation="reassign",
                affected_shifts=[],
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


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
            job_summaries.append({
                "job_id": job_id,
                "status": job.get("status"),
                "created_at": job.get("created_at"),
                "completed_at": job.get("completed_at")
            })
    
    # Sort by created_at descending (newest first)
    job_summaries.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)
    
    return {
        "total": len(job_summaries),
        "jobs": job_summaries
    }


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
                        detail="Cannot delete job that is currently solving"
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
    
    if job_store and hasattr(job_store, 'cleanup_old_jobs'):
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
        "message": f"Cleaned up {deleted_count} jobs older than {max_age_hours} hours"
    }
