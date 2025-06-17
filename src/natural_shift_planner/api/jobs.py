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
