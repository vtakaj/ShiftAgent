"""
Job management for asynchronous optimization
"""

import logging
import threading
from datetime import datetime
from typing import Any

from ..core.models.schedule import ShiftSchedule
from .job_store import job_store
from .solver import SOLVER_LOG_LEVEL, SOLVER_TIMEOUT_SECONDS, solver_factory

# Configure logging
logger = logging.getLogger(__name__)

# Job management dictionary
jobs: dict[str, dict[str, Any]] = {}
job_lock = threading.Lock()


def _sync_job_to_store(job_id: str):
    """Sync job data to persistent storage if available"""
    if job_store and job_id in jobs:
        try:
            job_store.save_job(job_id, jobs[job_id])
        except Exception as e:
            print(f"Error saving job {job_id} to storage: {e}")


def solve_problem_async(job_id: str, problem: ShiftSchedule):
    """Execute shift optimization asynchronously"""
    try:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_ACTIVE"
            _sync_job_to_store(job_id)

        solver = solver_factory.build_solver()

        start_time = datetime.now()
        logger.info(
            f"[Job {job_id}] Starting optimization with {len(problem.shifts)} shifts "
            f"and {len(problem.employees)} employees (timeout: {SOLVER_TIMEOUT_SECONDS}s)"
        )

        # Log additional details in debug mode
        if SOLVER_LOG_LEVEL == "DEBUG":
            logger.debug(
                f"[Job {job_id}] Employees: {[e.name for e in problem.employees]}"
            )
            logger.debug(
                f"[Job {job_id}] Shifts: {[(s.id, s.start_time, s.required_skills) for s in problem.shifts]}"
            )

        # Store solver reference for continuous planning
        with job_lock:
            jobs[job_id]["solver"] = solver
            jobs[job_id]["status"] = "SOLVING_SCHEDULED"
            jobs[job_id]["start_time"] = start_time
            _sync_job_to_store(job_id)

        solution = solver.solve(problem)

        elapsed = (datetime.now() - start_time).total_seconds()

        # Log final results
        assigned_count = sum(
            1 for shift in solution.shifts if shift.employee is not None
        )
        logger.info(
            f"[Job {job_id}] Optimization completed in {elapsed:.1f}s. "
            f"Final score: {solution.score}, "
            f"Assigned shifts: {assigned_count}/{len(solution.shifts)}"
        )

        # Log score breakdown in debug mode
        if SOLVER_LOG_LEVEL == "DEBUG" and solution.score:
            logger.debug(
                f"[Job {job_id}] Score breakdown - "
                f"Hard: {solution.score.hard_score}, "
                f"Medium: {solution.score.medium_score}, "
                f"Soft: {solution.score.soft_score}"
            )

        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()
            jobs[job_id]["final_score"] = str(solution.score)
            # Remove solver reference after completion
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]
            _sync_job_to_store(job_id)

    except Exception as e:
        logger.error(f"[Job {job_id}] Optimization failed: {str(e)}")
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)
            # Remove solver reference on failure
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]
            _sync_job_to_store(job_id)


def add_employee_to_completed_job(job_id: str, new_employee) -> bool:
    """Add employee to completed job using Problem Fact Changes"""
    try:
        with job_lock:
            if job_id not in jobs:
                logger.error(f"Job {job_id} not found")
                return False

            job = jobs[job_id]

            # Only allow adding to completed jobs
            if job["status"] != "SOLVING_COMPLETED":
                logger.error(f"Job {job_id} status is {job['status']}, not completed")
                return False

            if "solution" not in job:
                logger.error(f"Job {job_id} has no solution")
                return False

            # Get the current solution
            current_solution = job["solution"]

            # Mark job as being modified
            jobs[job_id]["status"] = "ADDING_EMPLOYEE"
            _sync_job_to_store(job_id)

        # Pin all existing assignments to preserve them during re-optimization
        logger.info(
            f"[Job {job_id}] Adding {new_employee.name} using Solver with pinned assignments"
        )

        # Pin only valid assignments - allow constraint violations to be fixed
        pinned_count = 0
        unpinned_violations = 0

        for shift in current_solution.shifts:
            if shift.employee is not None and not shift.pinned:
                # Check if current assignment has constraint violations
                current_emp = shift.employee
                has_violation = False

                # Check for hard constraint violations that should be fixed
                if not current_emp.has_required_skills(shift.required_skills):
                    has_violation = True
                    unpinned_violations += 1
                    logger.info(
                        f"[Job {job_id}] Not pinning shift {shift.id} due to skill mismatch. "
                        f"Employee {current_emp.name} has skills {current_emp.skills}, "
                        f"but shift requires {shift.required_skills}"
                    )
                elif current_emp.is_unavailable_on_date(shift.start_time):
                    has_violation = True
                    unpinned_violations += 1
                    logger.info(
                        f"[Job {job_id}] Not pinning shift {shift.id} due to unavailability"
                    )

                # Only pin assignments without violations
                if not has_violation:
                    shift.pin()
                    pinned_count += 1

        logger.info(
            f"[Job {job_id}] Pinned {pinned_count} valid assignments, "
            f"left {unpinned_violations} constraint violations unpinned for fixing"
        )

        # Add new employee to the solution
        current_solution.employees.append(new_employee)
        logger.info(
            f"[Job {job_id}] Added new employee {new_employee.name} with skills: {new_employee.skills}"
        )

        # Use existing solver factory with pinned assignments
        solver = solver_factory.build_solver()

        logger.info(f"[Job {job_id}] Running solver with pinned assignments...")
        updated_solution = solver.solve(current_solution)

        # Unpin shifts for future modifications
        for shift in updated_solution.shifts:
            if shift.pinned:
                shift.pinned = False

        # Count changes made
        assigned_count = sum(
            1
            for shift in updated_solution.shifts
            if shift.employee and shift.employee.id == new_employee.id
        )

        # Update the job with new solution
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = updated_solution
            jobs[job_id]["updated_at"] = datetime.now()
            jobs[job_id]["final_score"] = str(updated_solution.score)

            # Track the addition
            if "employee_additions" not in jobs[job_id]:
                jobs[job_id]["employee_additions"] = []
            jobs[job_id]["employee_additions"].append(
                {
                    "employee_id": new_employee.id,
                    "employee_name": new_employee.name,
                    "timestamp": datetime.now(),
                }
            )
            _sync_job_to_store(job_id)

        total_assigned = sum(
            1 for s in updated_solution.shifts if s.employee is not None
        )

        logger.info(
            f"[Job {job_id}] Employee addition completed using pinned optimization. "
            f"Score: {updated_solution.score}, "
            f"Total assigned shifts: {total_assigned}/{len(updated_solution.shifts)}, "
            f"New employee assigned to: {assigned_count} shifts"
        )

        return True

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to add employee: {str(e)}")
        with job_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = f"Employee addition failed: {str(e)}"
                _sync_job_to_store(job_id)
        return False


def update_employee_skills(job_id: str, employee_id: str, new_skills: set[str]) -> bool:
    """Update employee skills and re-optimize only necessary parts"""
    try:
        with job_lock:
            if job_id not in jobs:
                logger.error(f"Job {job_id} not found")
                return False

            job = jobs[job_id]

            # Only allow updating completed jobs
            if job["status"] != "SOLVING_COMPLETED":
                logger.error(f"Job {job_id} status is {job['status']}, not completed")
                return False

            if "solution" not in job:
                logger.error(f"Job {job_id} has no solution")
                return False

            # Get the current solution
            current_solution = job["solution"]

            # Find the employee to update
            target_employee = None
            for emp in current_solution.employees:
                if emp.id == employee_id:
                    target_employee = emp
                    break

            if not target_employee:
                logger.error(f"Employee {employee_id} not found in job {job_id}")
                return False

            # Mark job as being modified
            jobs[job_id]["status"] = "UPDATING_EMPLOYEE_SKILLS"
            _sync_job_to_store(job_id)

        logger.info(
            f"[Job {job_id}] Updating skills for {target_employee.name} "
            f"from {target_employee.skills} to {new_skills}"
        )

        # Update employee skills
        old_skills = target_employee.skills.copy()
        target_employee.skills = new_skills
        added_skills = new_skills - old_skills
        removed_skills = old_skills - new_skills

        logger.info(
            f"[Job {job_id}] Skills changed for {target_employee.name}: "
            f"added {added_skills}, removed {removed_skills}"
        )

        # Pin assignments that should be preserved - more nuanced approach
        pinned_count = 0
        unpinned_for_improvement = 0

        for shift in current_solution.shifts:
            if shift.employee is not None and not shift.pinned:
                should_pin = True

                # Don't pin if this employee's assignment could be improved with new skills
                if shift.employee.id == employee_id:
                    # Check if the employee now has better skill coverage
                    if added_skills and shift.required_skills.intersection(
                        added_skills
                    ):
                        should_pin = True  # Keep assignment, skills are now better
                    elif removed_skills and shift.required_skills.intersection(
                        removed_skills
                    ):
                        should_pin = False  # May need reassignment due to lost skills
                        unpinned_for_improvement += 1
                        logger.info(
                            f"[Job {job_id}] Unpinning {shift.id} - employee lost required skills"
                        )
                else:
                    # Check if current assignment has constraint violations
                    current_emp = shift.employee
                    if not current_emp.has_required_skills(shift.required_skills):
                        # Check if updated employee could now handle this shift better
                        if target_employee.has_required_skills(shift.required_skills):
                            should_pin = False  # Allow reassignment to updated employee
                            unpinned_for_improvement += 1
                            logger.info(
                                f"[Job {job_id}] Unpinning {shift.id} - updated employee can resolve violation"
                            )

                if should_pin:
                    shift.pin()
                    pinned_count += 1

        logger.info(
            f"[Job {job_id}] Pinned {pinned_count} assignments, "
            f"left {unpinned_for_improvement} unpinned for potential improvement"
        )

        # Use solver with pinned assignments for targeted optimization
        solver = solver_factory.build_solver()

        logger.info(f"[Job {job_id}] Running solver with updated skills...")
        updated_solution = solver.solve(current_solution)

        # Unpin shifts for future modifications
        for shift in updated_solution.shifts:
            if shift.pinned:
                shift.pinned = False

        # Count changes made
        changes_count = 0
        for old_shift, new_shift in zip(
            current_solution.shifts, updated_solution.shifts, strict=False
        ):
            if old_shift.employee != new_shift.employee:
                changes_count += 1
                if old_shift.employee and new_shift.employee:
                    logger.info(
                        f"[Job {job_id}] Shift {new_shift.id} reassigned from "
                        f"{old_shift.employee.name} to {new_shift.employee.name}"
                    )
                elif new_shift.employee:
                    logger.info(
                        f"[Job {job_id}] Shift {new_shift.id} assigned to {new_shift.employee.name}"
                    )

        # Update the job with new solution
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = updated_solution
            jobs[job_id]["updated_at"] = datetime.now()
            jobs[job_id]["final_score"] = str(updated_solution.score)

            # Track the skill update
            if "skill_updates" not in jobs[job_id]:
                jobs[job_id]["skill_updates"] = []
            jobs[job_id]["skill_updates"].append(
                {
                    "employee_id": employee_id,
                    "employee_name": target_employee.name,
                    "old_skills": list(old_skills),
                    "new_skills": list(new_skills),
                    "timestamp": datetime.now(),
                    "changes_made": changes_count,
                }
            )
            _sync_job_to_store(job_id)

        total_assigned = sum(
            1 for s in updated_solution.shifts if s.employee is not None
        )

        logger.info(
            f"[Job {job_id}] Skill update completed. "
            f"Score: {updated_solution.score}, "
            f"Total assigned shifts: {total_assigned}/{len(updated_solution.shifts)}, "
            f"Assignment changes made: {changes_count}"
        )

        return True

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to update employee skills: {str(e)}")
        with job_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = f"Skill update failed: {str(e)}"
                _sync_job_to_store(job_id)
        return False


def reassign_shift_in_job(
    job_id: str, shift_id: str, new_employee_id: str | None, force: bool = False
) -> tuple[bool, list[str]]:
    """Reassign a shift to a specific employee or unassign it"""
    warnings = []

    try:
        with job_lock:
            if job_id not in jobs:
                logger.error(f"Job {job_id} not found")
                return False, [f"Job {job_id} not found"]

            job = jobs[job_id]

            # Only allow reassigning in completed jobs
            if job["status"] != "SOLVING_COMPLETED":
                logger.error(f"Job {job_id} status is {job['status']}, not completed")
                return False, [f"Job {job_id} is not completed"]

            if "solution" not in job:
                logger.error(f"Job {job_id} has no solution")
                return False, [f"Job {job_id} has no solution"]

            # Get the current solution
            current_solution = job["solution"]

            # Find the shift to reassign
            target_shift = None
            for shift in current_solution.shifts:
                if shift.id == shift_id:
                    target_shift = shift
                    break

            if target_shift is None:
                logger.error(f"Shift {shift_id} not found in solution")
                return False, [f"Shift {shift_id} not found"]

            # Find the new employee if specified
            new_employee = None
            if new_employee_id is not None:
                for emp in current_solution.employees:
                    if emp.id == new_employee_id:
                        new_employee = emp
                        break

                if new_employee is None:
                    logger.error(f"Employee {new_employee_id} not found in solution")
                    return False, [f"Employee {new_employee_id} not found"]

            # Mark job as being modified
            jobs[job_id]["status"] = "REASSIGNING_SHIFT"
            _sync_job_to_store(job_id)

        # Perform validation
        validation_errors = []

        if new_employee is not None:
            # Check skill requirements
            if not new_employee.has_required_skills(target_shift.required_skills):
                missing_skills = target_shift.required_skills - new_employee.skills
                error_msg = f"Employee {new_employee.name} lacks required skills: {missing_skills}"
                if force:
                    warnings.append(f"WARNING: {error_msg} (forced)")
                    logger.warning(f"[Job {job_id}] {error_msg} - forced by user")
                else:
                    validation_errors.append(error_msg)

            # Check availability
            if new_employee.is_unavailable_on_date(target_shift.start_time):
                error_msg = f"Employee {new_employee.name} is unavailable on {target_shift.start_time.date()}"
                if force:
                    warnings.append(f"WARNING: {error_msg} (forced)")
                    logger.warning(f"[Job {job_id}] {error_msg} - forced by user")
                else:
                    validation_errors.append(error_msg)

            # Check for shift overlap
            for other_shift in current_solution.shifts:
                if (
                    other_shift.id != shift_id
                    and other_shift.employee == new_employee
                    and target_shift.overlaps_with(other_shift)
                ):
                    error_msg = f"Employee {new_employee.name} already has overlapping shift {other_shift.id} ({other_shift.start_time} - {other_shift.end_time})"
                    if force:
                        warnings.append(f"WARNING: {error_msg} (forced)")
                        logger.warning(f"[Job {job_id}] {error_msg} - forced by user")
                    else:
                        validation_errors.append(error_msg)

        # If validation failed and not forced, return errors
        if validation_errors and not force:
            error_msg = (
                f"Reassignment validation failed: {'; '.join(validation_errors)}"
            )
            logger.error(f"[Job {job_id}] {error_msg}")
            with job_lock:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = error_msg
                _sync_job_to_store(job_id)
            return False, validation_errors

        # Store the old assignment for logging
        old_employee = target_shift.employee
        old_employee_name = old_employee.name if old_employee else "unassigned"
        new_employee_name = new_employee.name if new_employee else "unassigned"

        logger.info(
            f"[Job {job_id}] Reassigning shift {shift_id} from {old_employee_name} to {new_employee_name}"
        )

        # Pin all other assignments to preserve them during re-optimization
        pinned_count = 0
        for shift in current_solution.shifts:
            if shift.id != shift_id and shift.employee is not None and not shift.pinned:
                # Only pin assignments without violations
                current_emp = shift.employee
                has_violation = False

                # Check for hard constraint violations
                if not current_emp.has_required_skills(shift.required_skills):
                    has_violation = True
                elif current_emp.is_unavailable_on_date(shift.start_time):
                    has_violation = True

                # Only pin valid assignments
                if not has_violation:
                    shift.pin()
                    pinned_count += 1

        logger.info(f"[Job {job_id}] Pinned {pinned_count} other assignments")

        # Directly set the new assignment
        target_shift.employee = new_employee

        # Use solver to validate and optimize around the new assignment
        solver = solver_factory.build_solver()

        logger.info(f"[Job {job_id}] Running solver to validate reassignment...")
        updated_solution = solver.solve(current_solution)

        # Unpin shifts for future modifications
        for shift in updated_solution.shifts:
            if shift.pinned:
                shift.pinned = False

        # Update the job with new solution
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = updated_solution
            jobs[job_id]["updated_at"] = datetime.now()
            jobs[job_id]["final_score"] = str(updated_solution.score)

            # Track the reassignment
            if "shift_reassignments" not in jobs[job_id]:
                jobs[job_id]["shift_reassignments"] = []
            jobs[job_id]["shift_reassignments"].append(
                {
                    "shift_id": shift_id,
                    "old_employee_id": old_employee.id if old_employee else None,
                    "old_employee_name": old_employee_name,
                    "new_employee_id": new_employee.id if new_employee else None,
                    "new_employee_name": new_employee_name,
                    "forced": force,
                    "warnings": warnings,
                    "timestamp": datetime.now(),
                }
            )
            _sync_job_to_store(job_id)

        total_assigned = sum(
            1 for s in updated_solution.shifts if s.employee is not None
        )

        logger.info(
            f"[Job {job_id}] Shift reassignment completed successfully. "
            f"Score: {updated_solution.score}, "
            f"Total assigned shifts: {total_assigned}/{len(updated_solution.shifts)}"
        )

        return True, warnings

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to reassign shift: {str(e)}")
        with job_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = f"Shift reassignment failed: {str(e)}"
                _sync_job_to_store(job_id)
        return False, [f"Internal error: {str(e)}"]


def swap_shifts_in_job(job_id: str, shift1_id: str, shift2_id: str) -> bool:
    """Swap employee assignments between two shifts in a completed job"""
    try:
        with job_lock:
            if job_id not in jobs:
                logger.error(f"Job {job_id} not found")
                return False

            job = jobs[job_id]

            # Only allow swapping in completed jobs
            if job["status"] != "SOLVING_COMPLETED":
                logger.error(f"Job {job_id} status is {job['status']}, not completed")
                return False

            if "solution" not in job:
                logger.error(f"Job {job_id} has no solution")
                return False

            # Get the current solution
            current_solution = job["solution"]

            # Find the shifts to swap
            shift1 = None
            shift2 = None
            for shift in current_solution.shifts:
                if shift.id == shift1_id:
                    shift1 = shift
                elif shift.id == shift2_id:
                    shift2 = shift

            if shift1 is None:
                logger.error(f"Shift {shift1_id} not found in solution")
                jobs[job_id]["error"] = f"Shift {shift1_id} not found"
                return False

            if shift2 is None:
                logger.error(f"Shift {shift2_id} not found in solution")
                jobs[job_id]["error"] = f"Shift {shift2_id} not found"
                return False

            # Mark job as being modified
            jobs[job_id]["status"] = "SWAPPING_SHIFTS"
            _sync_job_to_store(job_id)

        # Validate the swap before executing
        employee1 = shift1.employee
        employee2 = shift2.employee

        logger.info(
            f"[Job {job_id}] Validating swap between shifts {shift1_id} and {shift2_id}"
        )

        # Validate skill compatibility
        swap_valid = True
        validation_errors = []

        # Check if employee1 (going to shift2) has required skills for shift2
        if employee1 is not None and not employee1.has_required_skills(
            shift2.required_skills
        ):
            swap_valid = False
            validation_errors.append(
                f"Employee {employee1.name} lacks skills {shift2.required_skills - employee1.skills} "
                f"required for shift {shift2_id}"
            )

        # Check if employee2 (going to shift1) has required skills for shift1
        if employee2 is not None and not employee2.has_required_skills(
            shift1.required_skills
        ):
            swap_valid = False
            validation_errors.append(
                f"Employee {employee2.name} lacks skills {shift1.required_skills - employee2.skills} "
                f"required for shift {shift1_id}"
            )

        # Check availability constraints
        if employee1 is not None and employee1.is_unavailable_on_date(
            shift2.start_time
        ):
            swap_valid = False
            validation_errors.append(
                f"Employee {employee1.name} is unavailable on {shift2.start_time.date()}"
            )

        if employee2 is not None and employee2.is_unavailable_on_date(
            shift1.start_time
        ):
            swap_valid = False
            validation_errors.append(
                f"Employee {employee2.name} is unavailable on {shift1.start_time.date()}"
            )

        # Check for shift overlap (if both employees are assigned)
        if employee1 is not None and employee2 is not None:
            # Get all shifts for each employee to check for conflicts
            employee1_shifts = [
                s
                for s in current_solution.shifts
                if s.employee == employee1 and s.id != shift1_id
            ]
            employee2_shifts = [
                s
                for s in current_solution.shifts
                if s.employee == employee2 and s.id != shift2_id
            ]

            # Check if employee1 (moving to shift2) has conflicts
            for other_shift in employee1_shifts:
                if shift2.overlaps_with(other_shift):
                    swap_valid = False
                    validation_errors.append(
                        f"Employee {employee1.name} already has overlapping shift {other_shift.id} "
                        f"({other_shift.start_time} - {other_shift.end_time})"
                    )

            # Check if employee2 (moving to shift1) has conflicts
            for other_shift in employee2_shifts:
                if shift1.overlaps_with(other_shift):
                    swap_valid = False
                    validation_errors.append(
                        f"Employee {employee2.name} already has overlapping shift {other_shift.id} "
                        f"({other_shift.start_time} - {other_shift.end_time})"
                    )

        if not swap_valid:
            error_msg = f"Swap validation failed: {'; '.join(validation_errors)}"
            logger.error(f"[Job {job_id}] {error_msg}")
            with job_lock:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = error_msg
                _sync_job_to_store(job_id)
            return False

        logger.info(f"[Job {job_id}] Swap validation passed, executing swap...")

        # Execute the swap by directly modifying the solution
        # This is simpler than using problem fact changes for a straightforward swap
        shift1.employee = employee2
        shift2.employee = employee1

        # Use solver to validate and potentially improve the solution after swap
        solver = solver_factory.build_solver()

        logger.info(f"[Job {job_id}] Running solver to validate swap...")
        updated_solution = solver.solve(current_solution)

        # Update the job with new solution
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = updated_solution
            jobs[job_id]["updated_at"] = datetime.now()
            jobs[job_id]["final_score"] = str(updated_solution.score)

            # Track the swap
            if "shift_swaps" not in jobs[job_id]:
                jobs[job_id]["shift_swaps"] = []
            jobs[job_id]["shift_swaps"].append(
                {
                    "shift1_id": shift1_id,
                    "shift2_id": shift2_id,
                    "employee1_id": employee1.id if employee1 else None,
                    "employee1_name": employee1.name if employee1 else None,
                    "employee2_id": employee2.id if employee2 else None,
                    "employee2_name": employee2.name if employee2 else None,
                    "timestamp": datetime.now(),
                }
            )
            _sync_job_to_store(job_id)

        total_assigned = sum(
            1 for s in updated_solution.shifts if s.employee is not None
        )

        logger.info(
            f"[Job {job_id}] Shift swap completed successfully. "
            f"Score: {updated_solution.score}, "
            f"Total assigned shifts: {total_assigned}/{len(updated_solution.shifts)}"
        )

        return True

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to swap shifts: {str(e)}")
        with job_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = f"Shift swap failed: {str(e)}"
                _sync_job_to_store(job_id)
        return False


def add_employees_to_completed_job(job_id: str, new_employees: list, auto_assign: bool = False) -> tuple[bool, dict]:
    """Add multiple employees to completed job with validation and detailed reporting"""
    results = []
    successful_additions = 0
    failed_additions = 0
    skipped_additions = 0
    
    try:
        with job_lock:
            if job_id not in jobs:
                logger.error(f"Job {job_id} not found")
                return False, {
                    "error": "Job not found",
                    "results": [],
                    "successful_additions": 0,
                    "failed_additions": 0,
                    "skipped_additions": 0,
                }

            job = jobs[job_id]

            # Only allow adding to completed jobs
            if job["status"] != "SOLVING_COMPLETED":
                logger.error(f"Job {job_id} status is {job['status']}, not completed")
                return False, {
                    "error": f"Job status is {job['status']}, not completed",
                    "results": [],
                    "successful_additions": 0,
                    "failed_additions": 0,
                    "skipped_additions": 0,
                }

            if "solution" not in job:
                logger.error(f"Job {job_id} has no solution")
                return False, {
                    "error": "Job has no solution",
                    "results": [],
                    "successful_additions": 0,
                    "failed_additions": 0,
                    "skipped_additions": 0,
                }

            # Get the current solution
            current_solution = job["solution"]
            
            # Mark job as being modified
            jobs[job_id]["status"] = "ADDING_EMPLOYEES_BATCH"
            _sync_job_to_store(job_id)

        # Phase 1: Validate all employees before adding any
        logger.info(f"[Job {job_id}] Starting batch validation of {len(new_employees)} employees")
        
        validation_results = []
        existing_employee_ids = {emp.id for emp in current_solution.employees}
        new_employee_ids = set()
        
        for employee in new_employees:
            employee_result = {
                "employee_id": employee.id,
                "employee_name": employee.name,
                "status": "PENDING",
                "message": "",
                "errors": [],
                "warnings": [],
                "assigned_shifts": 0,
            }
            
            # Check for duplicate ID within existing employees
            if employee.id in existing_employee_ids:
                employee_result["status"] = "SKIPPED"
                employee_result["message"] = f"Employee ID {employee.id} already exists in job"
                employee_result["errors"].append("Duplicate employee ID")
                skipped_additions += 1
                
            # Check for duplicate ID within the batch
            elif employee.id in new_employee_ids:
                employee_result["status"] = "FAILED"
                employee_result["message"] = f"Duplicate employee ID {employee.id} in batch"
                employee_result["errors"].append("Duplicate ID in batch")
                failed_additions += 1
                
            else:
                # Validate required fields
                errors = []
                if not employee.name.strip():
                    errors.append("Employee name cannot be empty")
                if not employee.skills:
                    errors.append("Employee must have at least one skill")
                if not employee.id.strip():
                    errors.append("Employee ID cannot be empty")
                    
                if errors:
                    employee_result["status"] = "FAILED"
                    employee_result["message"] = f"Validation failed: {'; '.join(errors)}"
                    employee_result["errors"] = errors
                    failed_additions += 1
                else:
                    employee_result["status"] = "VALIDATED"
                    employee_result["message"] = "Ready to add"
                    new_employee_ids.add(employee.id)
                    
            validation_results.append(employee_result)
            
        logger.info(f"[Job {job_id}] Validation complete. Valid: {len(new_employee_ids)}, Failed: {failed_additions}, Skipped: {skipped_additions}")
        
        # Phase 2: Add valid employees if any exist
        if new_employee_ids:
            logger.info(f"[Job {job_id}] Adding {len(new_employee_ids)} valid employees using batch optimization")
            
            # Pin all existing assignments to preserve them during re-optimization
            pinned_count = 0
            unpinned_violations = 0

            for shift in current_solution.shifts:
                if shift.employee is not None and not shift.pinned:
                    # Check if current assignment has constraint violations
                    current_emp = shift.employee
                    has_violation = False

                    # Check for hard constraint violations that should be fixed
                    if not current_emp.has_required_skills(shift.required_skills):
                        has_violation = True
                        unpinned_violations += 1
                        logger.info(
                            f"[Job {job_id}] Not pinning shift {shift.id} due to skill mismatch"
                        )
                    elif current_emp.is_unavailable_on_date(shift.start_time):
                        has_violation = True
                        unpinned_violations += 1
                        logger.info(
                            f"[Job {job_id}] Not pinning shift {shift.id} due to unavailability"
                        )

                    # Only pin assignments without violations
                    if not has_violation:
                        shift.pin()
                        pinned_count += 1

            logger.info(
                f"[Job {job_id}] Pinned {pinned_count} valid assignments, "
                f"left {unpinned_violations} constraint violations unpinned for fixing"
            )

            # Add all valid employees to the solution
            employees_to_add = []
            for i, employee in enumerate(new_employees):
                if validation_results[i]["status"] == "VALIDATED":
                    current_solution.employees.append(employee)
                    employees_to_add.append(employee)
                    logger.info(
                        f"[Job {job_id}] Added employee {employee.name} with skills: {employee.skills}"
                    )

            # Use existing solver factory with pinned assignments
            solver = solver_factory.build_solver()

            logger.info(f"[Job {job_id}] Running solver with {len(employees_to_add)} new employees...")
            updated_solution = solver.solve(current_solution)

            # Unpin shifts for future modifications
            for shift in updated_solution.shifts:
                if shift.pinned:
                    shift.pinned = False

            # Update results with assignment counts
            for i, employee in enumerate(new_employees):
                if validation_results[i]["status"] == "VALIDATED":
                    assigned_count = sum(
                        1
                        for shift in updated_solution.shifts
                        if shift.employee and shift.employee.id == employee.id
                    )
                    validation_results[i]["assigned_shifts"] = assigned_count
                    validation_results[i]["status"] = "SUCCESS"
                    validation_results[i]["message"] = f"Successfully added and assigned to {assigned_count} shifts"
                    successful_additions += 1

            # Update the job with new solution
            with job_lock:
                jobs[job_id]["status"] = "SOLVING_COMPLETED"
                jobs[job_id]["solution"] = updated_solution
                jobs[job_id]["updated_at"] = datetime.now()
                jobs[job_id]["final_score"] = str(updated_solution.score)

                # Track the batch addition
                if "batch_employee_additions" not in jobs[job_id]:
                    jobs[job_id]["batch_employee_additions"] = []
                jobs[job_id]["batch_employee_additions"].append(
                    {
                        "timestamp": datetime.now(),
                        "total_employees": len(new_employees),
                        "successful_additions": successful_additions,
                        "failed_additions": failed_additions,
                        "skipped_additions": skipped_additions,
                        "auto_assign": auto_assign,
                        "employee_results": validation_results,
                    }
                )
                _sync_job_to_store(job_id)

            total_assigned = sum(
                1 for s in updated_solution.shifts if s.employee is not None
            )

            logger.info(
                f"[Job {job_id}] Batch employee addition completed. "
                f"Score: {updated_solution.score}, "
                f"Total assigned shifts: {total_assigned}/{len(updated_solution.shifts)}, "
                f"Successful additions: {successful_additions}, "
                f"Failed additions: {failed_additions}, "
                f"Skipped additions: {skipped_additions}"
            )
        else:
            # No valid employees to add
            logger.info(f"[Job {job_id}] No valid employees to add")
            with job_lock:
                jobs[job_id]["status"] = "SOLVING_COMPLETED"
                _sync_job_to_store(job_id)

        return True, {
            "results": validation_results,
            "successful_additions": successful_additions,
            "failed_additions": failed_additions,
            "skipped_additions": skipped_additions,
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to add employees in batch: {str(e)}")
        with job_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "SOLVING_FAILED"
                jobs[job_id]["error"] = f"Batch employee addition failed: {str(e)}"
                _sync_job_to_store(job_id)
        return False, {
            "error": f"Internal error: {str(e)}",
            "results": results,
            "successful_additions": successful_additions,
            "failed_additions": failed_additions,
            "skipped_additions": skipped_additions,
        }
