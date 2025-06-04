"""
Partial optimization solver functionality
"""
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set

from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)

from ..core.models import Employee, Shift, ShiftSchedule
from ..core.constraints import shift_scheduling_constraints
from .jobs import job_lock, jobs
from .schemas import OptimizationScope, PartialOptimizationRequest


def filter_shifts_by_scope(
    shifts: List[Shift],
    scope: OptimizationScope
) -> Set[str]:
    """
    Determine which shifts are in scope for optimization
    
    Returns:
        Set of shift IDs that are in scope
    """
    in_scope_ids = set()
    
    for shift in shifts:
        # Check date range
        if scope.date_range:
            if not (scope.date_range.start_date <= shift.start_time <= scope.date_range.end_date):
                continue
        
        # Check locations
        if scope.locations and shift.location not in scope.locations:
            continue
        
        # Check shift types (morning, evening, etc.)
        # This is a simplified check - you might want to add a shift_type field
        if scope.shift_types:
            # Extract shift type from ID (e.g., "morning_monday" -> "morning")
            shift_type = shift.id.split('_')[0] if '_' in shift.id else None
            if shift_type not in scope.shift_types:
                continue
        
        # Check employees
        if scope.employees:
            if shift.employee and shift.employee.id not in scope.employees:
                # Only include if currently assigned to one of the specified employees
                # OR if unassigned (so it can be assigned to them)
                if shift.employee is not None:
                    continue
        
        in_scope_ids.add(shift.id)
    
    return in_scope_ids


def create_partial_schedule(
    base_schedule: ShiftSchedule,
    scope: OptimizationScope,
    preserve_locked: bool
) -> ShiftSchedule:
    """
    Create a new schedule for partial optimization
    
    This creates a copy of the schedule where:
    - Locked shifts keep their assignments
    - Out-of-scope shifts keep their assignments
    - In-scope unlocked shifts can be reassigned
    """
    # Get shifts in scope
    in_scope_ids = filter_shifts_by_scope(base_schedule.shifts, scope)
    
    # Create new schedule with copies of employees and shifts
    new_employees = [
        Employee(e.id, e.name, e.skills.copy())
        for e in base_schedule.employees
    ]
    
    # Filter employees if specified in scope
    if scope.employees:
        new_employees = [e for e in new_employees if e.id in scope.employees]
    
    new_shifts = []
    employee_map = {e.id: e for e in new_employees}
    
    for shift in base_schedule.shifts:
        # Create a copy of the shift
        new_shift = Shift(
            id=shift.id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            required_skills=shift.required_skills.copy(),
            location=shift.location,
            priority=shift.priority
        )
        
        # Copy locking fields
        new_shift.is_locked = shift.is_locked
        new_shift.locked_at = shift.locked_at
        new_shift.locked_by = shift.locked_by
        new_shift.lock_reason = shift.lock_reason
        
        # Handle assignment based on scope and locking
        if shift.id not in in_scope_ids or (preserve_locked and shift.is_locked):
            # Keep existing assignment for out-of-scope or locked shifts
            if shift.employee and shift.employee.id in employee_map:
                new_shift.employee = employee_map[shift.employee.id]
                # Pin the assignment if locked
                if preserve_locked and shift.is_locked:
                    new_shift._pinned = True
            elif shift.employee:
                # Employee not in scope, keep shift but unassign
                new_shift.employee = None
        else:
            # In-scope and not locked - can be reassigned
            # Start with current assignment if employee is in scope
            if shift.employee and shift.employee.id in employee_map:
                new_shift.employee = employee_map[shift.employee.id]
            else:
                new_shift.employee = None
        
        new_shifts.append(new_shift)
    
    return ShiftSchedule(employees=new_employees, shifts=new_shifts)


def solve_partial_schedule_async(
    job_id: str,
    base_schedule: ShiftSchedule,
    request: PartialOptimizationRequest
):
    """
    Execute partial shift optimization asynchronously
    """
    try:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_ACTIVE"
            jobs[job_id]["optimization_type"] = "partial"
        
        # Create partial schedule
        partial_schedule = create_partial_schedule(
            base_schedule,
            request.optimization_scope,
            request.preserve_locked
        )
        
        # Configure solver with shorter time limit for partial optimization
        solver_config = SolverConfig(
            solution_class=ShiftSchedule,
            entity_class_list=[Shift],
            score_director_factory_config=ScoreDirectorFactoryConfig(
                constraint_provider_function=shift_scheduling_constraints
            ),
            termination_config=TerminationConfig(spent_limit=Duration(seconds=10)),
        )
        
        solver_factory = SolverFactory.create(solver_config)
        solver = solver_factory.build_solver()
        
        # Solve the partial schedule
        solution = solver.solve(partial_schedule)
        
        # Merge solution back into base schedule
        merged_schedule = merge_partial_solution(
            base_schedule,
            solution,
            request.optimization_scope
        )
        
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = merged_schedule
            jobs[job_id]["completed_at"] = datetime.now()
            jobs[job_id]["partial_optimization_summary"] = {
                "total_shifts": len(base_schedule.shifts),
                "shifts_in_scope": len(filter_shifts_by_scope(
                    base_schedule.shifts, 
                    request.optimization_scope
                )),
                "shifts_modified": count_modified_shifts(base_schedule, merged_schedule)
            }
    
    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)


def merge_partial_solution(
    base_schedule: ShiftSchedule,
    partial_solution: ShiftSchedule,
    scope: OptimizationScope
) -> ShiftSchedule:
    """
    Merge the partial solution back into the base schedule
    """
    # Create a mapping of shift assignments from partial solution
    partial_assignments = {
        shift.id: shift.employee
        for shift in partial_solution.shifts
    }
    
    # Get shifts in scope
    in_scope_ids = filter_shifts_by_scope(base_schedule.shifts, scope)
    
    # Create merged schedule
    merged_schedule = ShiftSchedule(
        employees=base_schedule.employees,
        shifts=[]
    )
    
    for shift in base_schedule.shifts:
        if shift.id in in_scope_ids and shift.id in partial_assignments:
            # Update assignment from partial solution if not locked
            if not shift.is_locked:
                shift.employee = partial_assignments[shift.id]
        
        merged_schedule.shifts.append(shift)
    
    return merged_schedule


def count_modified_shifts(
    original: ShiftSchedule,
    modified: ShiftSchedule
) -> int:
    """
    Count how many shifts were modified
    """
    count = 0
    
    original_assignments = {
        shift.id: shift.employee.id if shift.employee else None
        for shift in original.shifts
    }
    
    for shift in modified.shifts:
        original_emp = original_assignments.get(shift.id)
        new_emp = shift.employee.id if shift.employee else None
        if original_emp != new_emp:
            count += 1
    
    return count