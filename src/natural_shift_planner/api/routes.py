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
from .partial_modifications import (
    apply_shift_modification,
    calculate_weekly_impact,
    check_shift_modification_constraints,
)
from .partial_solver import (
    filter_shifts_by_scope,
    solve_partial_schedule_async,
)
from .schemas import (
    ShiftScheduleRequest,
    SolutionResponse,
    SolveResponse,
    ShiftModificationRequest,
    ShiftModificationResponse,
    ShiftLockRequest,
    ShiftLockResponse,
    ChangeImpactResponse,
    ImpactSummary,
    PartialOptimizationRequest,
    PartialOptimizationResponse,
)
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


# Partial modification endpoints
@app.patch("/api/shifts/{shift_id}", response_model=ShiftModificationResponse)
async def modify_shift(shift_id: str, request: ShiftModificationRequest):
    """Modify an individual shift assignment"""
    # For now, we need to get the schedule from a job
    # In a real implementation, you might store schedules in a database
    # This is a simplified version that requires a job_id parameter
    job_id = request.dict().get("job_id")  # This would come from query params in real impl
    
    with job_lock:
        if not jobs:
            raise HTTPException(status_code=404, detail="No schedules available")
        
        # Find a completed job with the schedule
        # In real implementation, you'd look up the specific schedule
        schedule = None
        for jid, job in jobs.items():
            if job["status"] == "SOLVING_COMPLETED" and "solution" in job:
                schedule = job["solution"]
                break
        
        if not schedule:
            raise HTTPException(status_code=404, detail="No completed schedule found")
        
        # Find the shift
        shift = None
        for s in schedule.shifts:
            if s.id == shift_id:
                shift = s
                break
        
        if not shift:
            raise HTTPException(status_code=404, detail=f"Shift {shift_id} not found")
        
        # Find the new employee if specified
        new_employee = None
        if request.employee_id:
            for emp in schedule.employees:
                if emp.id == request.employee_id:
                    new_employee = emp
                    break
            
            if not new_employee:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Employee {request.employee_id} not found"
                )
        
        # Check constraints
        violations, warnings = check_shift_modification_constraints(
            shift, new_employee, schedule
        )
        
        # Calculate impact
        old_employee = shift.employee
        weekly_impacts = calculate_weekly_impact(
            shift, old_employee, new_employee, schedule
        )
        
        # Check if we have hard constraint violations
        hard_violations = [v for v in violations if v.type == "hard"]
        success = len(hard_violations) == 0
        
        # Apply modification if no hard violations and not a dry run
        if success and not request.dry_run:
            apply_shift_modification(shift, new_employee, request.dry_run)
        
        # Prepare response
        shift_data = {
            "id": shift.id,
            "start_time": shift.start_time.isoformat(),
            "end_time": shift.end_time.isoformat(),
            "employee": {
                "id": shift.employee.id,
                "name": shift.employee.name
            } if shift.employee else None,
            "is_locked": shift.is_locked,
            "required_skills": list(shift.required_skills),
            "location": shift.location,
        }
        
        # Get the primary weekly impact (for the new employee)
        primary_impact = None
        if new_employee and new_employee.id in weekly_impacts:
            primary_impact = weekly_impacts[new_employee.id]
        
        return ShiftModificationResponse(
            shift=shift_data,
            success=success,
            warnings=warnings,
            constraint_violations=violations,
            weekly_impact=primary_impact
        )


@app.post("/api/shifts/lock", response_model=ShiftLockResponse)
async def lock_shifts(request: ShiftLockRequest):
    """Lock or unlock multiple shifts"""
    with job_lock:
        if not jobs:
            raise HTTPException(status_code=404, detail="No schedules available")
        
        # Find a completed job with the schedule
        schedule = None
        for jid, job in jobs.items():
            if job["status"] == "SOLVING_COMPLETED" and "solution" in job:
                schedule = job["solution"]
                break
        
        if not schedule:
            raise HTTPException(status_code=404, detail="No completed schedule found")
        
        locked_count = 0
        unlocked_count = 0
        failed_locks = []
        
        for shift_id in request.shift_ids:
            # Find the shift
            shift = None
            for s in schedule.shifts:
                if s.id == shift_id:
                    shift = s
                    break
            
            if not shift:
                failed_locks.append({
                    "shift_id": shift_id,
                    "reason": "Shift not found"
                })
                continue
            
            try:
                if request.action == "lock":
                    if not shift.is_locked:
                        shift.lock(
                            locked_by=request.locked_by or "system",
                            reason=request.reason
                        )
                        locked_count += 1
                else:  # unlock
                    if shift.is_locked:
                        shift.unlock()
                        unlocked_count += 1
            except Exception as e:
                failed_locks.append({
                    "shift_id": shift_id,
                    "reason": str(e)
                })
        
        if request.action == "lock":
            message = f"Successfully locked {locked_count} shifts"
        else:
            message = f"Successfully unlocked {unlocked_count} shifts"
        
        if failed_locks:
            message += f", {len(failed_locks)} failed"
        
        return ShiftLockResponse(
            success=len(failed_locks) == 0,
            locked_count=locked_count,
            unlocked_count=unlocked_count,
            failed_locks=failed_locks,
            message=message
        )


@app.get("/api/shifts/change-impact/{shift_id}", response_model=ChangeImpactResponse)
async def analyze_change_impact(shift_id: str, new_employee: Optional[str] = None):
    """Analyze the impact of changing a shift assignment"""
    with job_lock:
        if not jobs:
            raise HTTPException(status_code=404, detail="No schedules available")
        
        # Find a completed job with the schedule
        schedule = None
        for jid, job in jobs.items():
            if job["status"] == "SOLVING_COMPLETED" and "solution" in job:
                schedule = job["solution"]
                break
        
        if not schedule:
            raise HTTPException(status_code=404, detail="No completed schedule found")
        
        # Find the shift
        shift = None
        for s in schedule.shifts:
            if s.id == shift_id:
                shift = s
                break
        
        if not shift:
            raise HTTPException(status_code=404, detail=f"Shift {shift_id} not found")
        
        # Find the new employee if specified
        new_emp_obj = None
        if new_employee:
            for emp in schedule.employees:
                if emp.id == new_employee:
                    new_emp_obj = emp
                    break
            
            if not new_emp_obj:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Employee {new_employee} not found"
                )
        
        # Check constraints
        violations, warnings = check_shift_modification_constraints(
            shift, new_emp_obj, schedule
        )
        
        # Calculate impact
        old_employee = shift.employee
        weekly_impacts = calculate_weekly_impact(
            shift, old_employee, new_emp_obj, schedule
        )
        
        # Determine affected employees
        affected_employees = []
        if old_employee:
            affected_employees.append(old_employee.id)
        if new_emp_obj:
            affected_employees.append(new_emp_obj.id)
        
        # Format weekly hours impact
        weekly_hours_impact = {}
        for emp_id, impact in weekly_impacts.items():
            weekly_hours_impact[emp_id] = {
                "old": impact.old_hours,
                "new": impact.new_hours,
                "change": impact.change,
                "status": impact.status
            }
        
        # Generate recommendations
        recommendations = []
        hard_violations = [v for v in violations if v.type == "hard"]
        
        if hard_violations:
            recommendations.append("This change cannot be applied due to hard constraint violations")
        else:
            if warnings:
                recommendations.append("Consider the warnings before applying this change")
            
            for emp_id, impact in weekly_impacts.items():
                if impact.status == "overtime_warning":
                    recommendations.append(
                        f"Consider redistributing some of {impact.employee_name}'s other shifts"
                    )
                elif impact.status == "undertime":
                    recommendations.append(
                        f"{impact.employee_name} will have insufficient hours - consider assigning more shifts"
                    )
        
        is_valid = len(hard_violations) == 0
        
        return ChangeImpactResponse(
            impact_summary=ImpactSummary(
                constraint_violations=violations,
                warnings=warnings,
                affected_employees=affected_employees,
                weekly_hours_impact=weekly_hours_impact,
                recommendations=recommendations
            ),
            is_valid=is_valid
        )


@app.post("/api/shifts/partial-solve", response_model=PartialOptimizationResponse)
async def partial_solve_shifts(request: PartialOptimizationRequest):
    """Partial schedule optimization with scope constraints"""
    with job_lock:
        # Find the base schedule
        if request.base_schedule_id not in jobs:
            raise HTTPException(status_code=404, detail="Base schedule not found")
        
        base_job = jobs[request.base_schedule_id]
        if base_job["status"] != "SOLVING_COMPLETED" or "solution" not in base_job:
            raise HTTPException(status_code=400, detail="Base schedule is not ready")
        
        base_schedule = base_job["solution"]
        
        # Calculate scope summary
        in_scope_shifts = filter_shifts_by_scope(
            base_schedule.shifts,
            request.optimization_scope
        )
        
        locked_shifts = [s for s in base_schedule.shifts if s.is_locked]
        locked_in_scope = [s for s in locked_shifts if s.id in in_scope_shifts]
        
        scope_summary = {
            "total_shifts_in_scope": len(in_scope_shifts),
            "locked_shifts_preserved": len(locked_in_scope) if request.preserve_locked else 0,
            "shifts_to_optimize": len(in_scope_shifts) - (len(locked_in_scope) if request.preserve_locked else 0),
            "total_shifts": len(base_schedule.shifts)
        }
        
        # Create new job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "status": "SOLVING_SCHEDULED",
            "created_at": datetime.now(),
            "base_schedule_id": request.base_schedule_id,
            "optimization_request": request.dict(),
        }
        
        # Start partial optimization asynchronously
        thread = threading.Thread(
            target=solve_partial_schedule_async,
            args=(job_id, base_schedule, request)
        )
        thread.daemon = True
        thread.start()
        
        return PartialOptimizationResponse(
            job_id=job_id,
            status="SOLVING_SCHEDULED",
            scope_summary=scope_summary,
            message=f"Optimizing {scope_summary['shifts_to_optimize']} shifts out of {scope_summary['total_shifts_in_scope']} in scope"
        )