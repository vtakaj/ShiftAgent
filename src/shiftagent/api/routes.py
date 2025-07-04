"""
API route handlers
"""

import threading
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..utils import create_demo_schedule
from .analysis import analyze_weekly_hours, generate_recommendations
from .converters import convert_domain_to_response, convert_request_to_domain
from .job_store import job_store
from .jobs import (
    _sync_job_to_store,
    add_employee_to_completed_job,
    find_replacement_candidates,
    job_lock,
    jobs,
    reassign_shift_in_job,
    replace_employee_in_job,
    solve_problem_async,
    swap_shifts_in_job,
    update_employee_skills,
)
from .schemas import (
    CandidateEmployee,
    EmployeeRequest,
    ReassignShiftRequest,
    ReassignShiftResponse,
    ReplaceEmployeeRequest,
    ReplaceEmployeeResponse,
    ShiftScheduleRequest,
    SolutionResponse,
    SolveResponse,
    SwapShiftsRequest,
    SwapShiftsResponse,
)
from .solver import solver_factory

# Create router
router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ShiftAgent API", "version": "1.0.0", "docs": "/docs"}


@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "UP",
        "service": "shiftagent",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/shifts/demo")
async def get_demo_data():
    """Get demo data"""
    schedule = create_demo_schedule()
    return convert_domain_to_response(schedule)


@router.post("/api/shifts/solve", response_model=SolveResponse)
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


@router.get("/api/shifts/solve/{job_id}", response_model=SolutionResponse)
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

        response = SolutionResponse(
            job_id=job_id, status=job["status"], html_report_url=None
        )

        if job["status"] == "SOLVING_COMPLETED":
            solution = job["solution"]
            response.solution = convert_domain_to_response(solution)
            response.score = str(solution.score)
            response.assigned_shifts = solution.get_assigned_shift_count()
            response.unassigned_shifts = solution.get_unassigned_shift_count()
            response.html_report_url = f"/api/shifts/solve/{job_id}/html"
        elif job["status"] == "SOLVING_FAILED":
            response.message = job.get("error", "Unknown error occurred")

        return response


@router.post("/api/shifts/solve-sync")
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

        # For sync solve, we'll need to create a temporary job ID for HTML report
        temp_job_id = str(uuid.uuid4())
        with job_lock:
            jobs[temp_job_id] = {
                "status": "SOLVING_COMPLETED",
                "created_at": datetime.now(),
                "solution": solution,
                "temporary": True,  # Mark as temporary for cleanup
            }
            _sync_job_to_store(temp_job_id)

        result = convert_domain_to_response(solution)
        result["html_report_url"] = f"/api/shifts/solve/{temp_job_id}/html"
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/api/shifts/weekly-analysis/{job_id}")
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


@router.post("/api/shifts/analyze-weekly")
async def analyze_weekly_hours_sync(request: ShiftScheduleRequest):
    """Immediate analysis of weekly working hours (without optimization)"""
    try:
        schedule = convert_request_to_domain(request)
        analysis = analyze_weekly_hours(schedule)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/api/shifts/test-weekly")
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
@router.get("/api/jobs")
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


@router.delete("/api/jobs/{job_id}")
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


@router.post("/api/jobs/cleanup")
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


# Employee Addition to Completed Jobs


@router.post("/api/shifts/{job_id}/add-employee")
async def add_employee_to_job(job_id: str, employee: EmployeeRequest):
    """Add employee to completed job and re-optimize"""
    # Convert employee to domain model
    from .converters import convert_employee_request_to_domain

    new_employee = convert_employee_request_to_domain(employee)

    # Add the employee to the job
    success = add_employee_to_completed_job(job_id, new_employee)

    if success:
        # Get updated job info
        with job_lock:
            job = jobs[job_id]
            solution = job["solution"]

        return {
            "message": f"Employee {employee.name} added successfully",
            "job_id": job_id,
            "employee_id": employee.id,
            "status": "SUCCESS",
            "final_score": str(solution.score),
            "assigned_shifts": sum(
                1 for s in solution.shifts if s.employee is not None
            ),
            "total_shifts": len(solution.shifts),
            "html_report_url": f"/api/shifts/solve/{job_id}/html",
        }
    else:
        # Get error details from job
        with job_lock:
            if job_id in jobs:
                error_msg = jobs[job_id].get("error", "Unknown error occurred")
            else:
                error_msg = "Job not found"

        raise HTTPException(status_code=400, detail=error_msg)


@router.patch("/api/shifts/{job_id}/employee/{employee_id}/skills")
async def update_employee_skills_api(job_id: str, employee_id: str, skills: list[str]):
    """Update employee skills and re-optimize affected assignments"""
    # Convert skills list to set
    new_skills = set(skills)

    # Update the employee skills
    success = update_employee_skills(job_id, employee_id, new_skills)

    if success:
        # Get updated job info
        with job_lock:
            job = jobs[job_id]
            solution = job["solution"]

            # Find the updated employee
            updated_employee = None
            for emp in solution.employees:
                if emp.id == employee_id:
                    updated_employee = emp
                    break

        if updated_employee:
            return {
                "message": f"Skills updated successfully for {updated_employee.name}",
                "job_id": job_id,
                "employee_id": employee_id,
                "employee_name": updated_employee.name,
                "updated_skills": list(updated_employee.skills),
                "status": "SUCCESS",
                "final_score": str(solution.score),
                "assigned_shifts": sum(
                    1 for s in solution.shifts if s.employee is not None
                ),
                "total_shifts": len(solution.shifts),
                "html_report_url": f"/api/shifts/solve/{job_id}/html",
            }
        else:
            raise HTTPException(
                status_code=404, detail="Employee not found after update"
            )
    else:
        # Get error details from job
        with job_lock:
            if job_id in jobs:
                error_msg = jobs[job_id].get("error", "Unknown error occurred")
            else:
                error_msg = "Job not found"

        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/api/shifts/{job_id}/swap", response_model=SwapShiftsResponse)
async def swap_shifts(job_id: str, request: SwapShiftsRequest):
    """Swap employee assignments between two shifts"""
    # Perform the swap
    success = swap_shifts_in_job(job_id, request.shift1_id, request.shift2_id)

    if success:
        # Get updated job info
        with job_lock:
            job = jobs[job_id]
            solution = job["solution"]

        # Find the swapped shifts to show current assignments
        shift1_employee = None
        shift2_employee = None
        for shift in solution.shifts:
            if shift.id == request.shift1_id:
                shift1_employee = (
                    shift.employee.name if shift.employee else "unassigned"
                )
            elif shift.id == request.shift2_id:
                shift2_employee = (
                    shift.employee.name if shift.employee else "unassigned"
                )

        return SwapShiftsResponse(
            job_id=job_id,
            shift1_id=request.shift1_id,
            shift2_id=request.shift2_id,
            status="SUCCESS",
            message=f"Successfully swapped shifts. {request.shift1_id} -> {shift1_employee}, {request.shift2_id} -> {shift2_employee}",
            final_score=str(solution.score),
            html_report_url=f"/api/shifts/solve/{job_id}/html",
        )
    else:
        # Get error details from job
        with job_lock:
            if job_id in jobs:
                error_msg = jobs[job_id].get("error", "Unknown error occurred")
            else:
                error_msg = "Job not found"

        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/api/shifts/{job_id}/reassign", response_model=ReassignShiftResponse)
async def reassign_shift(job_id: str, request: ReassignShiftRequest):
    """Reassign a shift to a specific employee or unassign it"""
    # Perform the reassignment
    success, warnings_or_errors = reassign_shift_in_job(
        job_id, request.shift_id, request.employee_id, request.force
    )

    if success:
        # Get updated job info
        with job_lock:
            job = jobs[job_id]
            solution = job["solution"]

        # Find the reassigned shift to get current assignment
        current_employee = None
        current_employee_name = None
        for shift in solution.shifts:
            if shift.id == request.shift_id:
                current_employee = shift.employee
                current_employee_name = shift.employee.name if shift.employee else None
                break

        return ReassignShiftResponse(
            job_id=job_id,
            shift_id=request.shift_id,
            employee_id=current_employee.id if current_employee else None,
            employee_name=current_employee_name,
            status="SUCCESS",
            message=f"Successfully reassigned shift {request.shift_id} to {current_employee_name or 'unassigned'}",
            warnings=warnings_or_errors,  # These are warnings when success=True
            final_score=str(solution.score),
            html_report_url=f"/api/shifts/solve/{job_id}/html",
        )
    else:
        # Get error details from job
        with job_lock:
            if job_id in jobs:
                error_msg = jobs[job_id].get("error", "Unknown error occurred")
            else:
                error_msg = "Job not found"

        # Use the specific errors returned from the function
        if warnings_or_errors:
            error_msg = "; ".join(warnings_or_errors)

        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/api/shifts/{job_id}/replace", response_model=ReplaceEmployeeResponse)
async def replace_employee(job_id: str, request: ReplaceEmployeeRequest):
    """Find and assign replacement for unavailable employee"""
    try:
        # Find the unavailable employee name for response
        unavailable_employee_name = None
        with job_lock:
            if job_id in jobs and "solution" in jobs[job_id]:
                solution = jobs[job_id]["solution"]
                for emp in solution.employees:
                    if emp.id == request.unavailable_employee_id:
                        unavailable_employee_name = emp.name
                        break

        # If only finding candidates (not auto_assign and no specific candidate)
        if not request.auto_assign and request.candidate_employee_id is None:
            # Just find candidates without assignment
            success, candidates, error_msg = find_replacement_candidates(
                job_id, request.shift_id, request.unavailable_employee_id
            )
            
            if not success:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Convert candidates to response format
            candidate_responses = [
                CandidateEmployee(
                    employee_id=c["employee_id"],
                    employee_name=c["employee_name"],
                    skills=c["skills"],
                    score=c["score"],
                    reasons=c["reasons"]
                )
                for c in candidates
            ]
            
            return ReplaceEmployeeResponse(
                job_id=job_id,
                shift_id=request.shift_id,
                unavailable_employee_id=request.unavailable_employee_id,
                unavailable_employee_name=unavailable_employee_name,
                status="CANDIDATES_FOUND",
                message=f"Found {len(candidates)} qualified replacement candidates",
                candidates=candidate_responses,
            )
        
        # Perform the replacement
        success, result, error_msg = replace_employee_in_job(
            job_id,
            request.shift_id,
            request.unavailable_employee_id,
            request.candidate_employee_id,
            request.auto_assign
        )
        
        if not success:
            # If result contains candidates, it means no employee was selected
            if result and "candidates" in result:
                candidate_responses = [
                    CandidateEmployee(
                        employee_id=c["employee_id"],
                        employee_name=c["employee_name"],
                        skills=c["skills"],
                        score=c["score"],
                        reasons=c["reasons"]
                    )
                    for c in result["candidates"]
                ]
                
                return ReplaceEmployeeResponse(
                    job_id=job_id,
                    shift_id=request.shift_id,
                    unavailable_employee_id=request.unavailable_employee_id,
                    unavailable_employee_name=unavailable_employee_name,
                    status="CANDIDATES_FOUND",
                    message="Please select an employee from the candidates or use auto_assign=true",
                    candidates=candidate_responses,
                )
            else:
                raise HTTPException(status_code=400, detail=error_msg)
        
        # Success - convert result to response format
        candidate_responses = [
            CandidateEmployee(
                employee_id=c["employee_id"],
                employee_name=c["employee_name"],
                skills=c["skills"],
                score=c["score"],
                reasons=c["reasons"]
            )
            for c in result["candidates"]
        ]
        
        selected_employee = result["selected_employee"]
        
        return ReplaceEmployeeResponse(
            job_id=job_id,
            shift_id=request.shift_id,
            unavailable_employee_id=request.unavailable_employee_id,
            unavailable_employee_name=unavailable_employee_name,
            status="SUCCESS",
            message=f"Successfully replaced {unavailable_employee_name or 'unavailable employee'} with {selected_employee['employee_name']}",
            candidates=candidate_responses,
            selected_employee_id=selected_employee["employee_id"],
            selected_employee_name=selected_employee["employee_name"],
            final_score=result["final_score"],
            html_report_url=f"/api/shifts/solve/{job_id}/html",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# HTML Report Generation
@router.get("/api/shifts/solve/{job_id}/html")
async def get_solution_html(job_id: str):
    """Get optimization result as HTML report"""
    from fastapi.responses import HTMLResponse

    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]

        if job["status"] != "SOLVING_COMPLETED":
            raise HTTPException(status_code=400, detail="Job not completed")

        solution = job["solution"]
        solution_data = convert_domain_to_response(solution)

        # Generate HTML report with embedded data
        html_content = generate_html_report_with_data(solution_data)

        return HTMLResponse(content=html_content)


def generate_html_report_with_data(solution_data):
    """Generate HTML report with embedded solution data"""
    import json
    import logging

    logger = logging.getLogger(__name__)

    # Read the template file from project directory
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "shift-schedule-template.html")
    try:
        with open(template_path, encoding="utf-8") as f:
            html_template = f.read()
        logger.info(
            f"Successfully loaded template from {template_path}, size: {len(html_template)} chars"
        )
    except FileNotFoundError as e:
        logger.error(f"Template file not found at {template_path}: {e}")
        # Fallback to simple HTML if template not found
        return generate_simple_html_report(solution_data)
    except Exception as e:
        logger.error(f"Error reading template file: {e}")
        return generate_simple_html_report(solution_data)

    # Prepare solution data with proper structure
    solution_json = json.dumps(
        {"solution": solution_data}, ensure_ascii=False, indent=2
    )

    # Check if the replacement pattern exists
    search_pattern = (
        'placeholder=\'{"solution": {"employees": [...], "shifts": [...]}}\''
    )
    if search_pattern not in html_template:
        logger.error(
            f"Search pattern not found in template. Looking for: {search_pattern}"
        )
        # Find actual pattern for debugging
        import re

        patterns = re.findall(r"placeholder=\'[^\']*\'>", html_template)
        logger.error(f"Found patterns: {patterns}")
        return generate_simple_html_report(solution_data)

    # Replace the textarea content with actual data
    replacement = f'placeholder=\'{{"solution": {{"employees": [...], "shifts": [...]}}}}\' style="display:none;">{solution_json}</textarea>\n            <button onclick="generateSchedule()">シフト表を生成</button>'
    html_content = html_template.replace(
        search_pattern + ">\n            </textarea>", replacement
    )

    # Add auto-generation script that runs after page loads
    auto_script = """
    <script>
    window.addEventListener('load', function() {
        // Hide the input section since we're auto-generating
        const inputSection = document.querySelector('.data-input');
        if (inputSection) {
            inputSection.style.display = 'none';
        }

        // Small delay to ensure all elements are loaded
        setTimeout(function() {
            // Auto-generate the schedule
            if (typeof generateSchedule === 'function') {
                generateSchedule();
            }
        }, 100);
    });
    </script>
    """

    html_content = html_content.replace("</body>", auto_script + "</body>")

    logger.info(f"Generated HTML with template, final size: {len(html_content)} chars")
    return html_content


def generate_simple_html_report(solution_data):
    """Generate a simple HTML report if template is not available"""
    import json

    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>シフト表</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #333; text-align: center; }}
            .data {{ background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto; }}
            pre {{ font-size: 12px; line-height: 1.4; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>シフト表レポート</h1>
            <div class="data">
                <pre>{json.dumps(solution_data, ensure_ascii=False, indent=2)}</pre>
            </div>
        </div>
    </body>
    </html>
    """
    return html
