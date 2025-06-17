"""
Job management for asynchronous optimization
"""

import logging
import threading
import uuid
from datetime import datetime
from typing import Any

from timefold.solver.config import Duration, TerminationConfig

from ..core.models.schedule import ShiftSchedule
from ..core.models.shift import Shift
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


def create_emergency_job(problem: ShiftSchedule) -> str:
    """Create a long-running job for emergency modifications"""
    job_id = str(uuid.uuid4())

    with job_lock:
        jobs[job_id] = {
            "status": "SOLVING_SCHEDULED",
            "problem": problem,
            "solver": None,
            "emergency_changes": [],
            "created_at": datetime.now(),
            "emergency_mode": True,
        }
        _sync_job_to_store(job_id)

    # Start solving in background thread with emergency support
    thread = threading.Thread(
        target=solve_with_emergency_support,
        args=(job_id, problem),
    )
    thread.daemon = True
    thread.start()

    return job_id


def solve_with_emergency_support(job_id: str, problem: ShiftSchedule):
    """Solve with support for emergency problem fact changes"""
    try:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_ACTIVE"
            _sync_job_to_store(job_id)

        # Build solver with longer timeout for emergency mode
        from timefold.solver.config import ScoreDirectorFactoryConfig, SolverConfig

        from ..core.constraints.shift_constraints import shift_scheduling_constraints

        # Create emergency config with longer timeout
        emergency_config = SolverConfig(
            solution_class=ShiftSchedule,
            entity_class_list=[Shift],
            score_director_factory_config=ScoreDirectorFactoryConfig(
                constraint_provider_function=shift_scheduling_constraints
            ),
            termination_config=TerminationConfig(
                spent_limit=Duration(minutes=30),  # Longer timeout for emergency mode
                unimproved_spent_limit=Duration(minutes=5),  # Stop if no improvement
            ),
        )

        # Create emergency solver factory with the new config
        from timefold.solver import SolverFactory
        emergency_solver_factory = SolverFactory.create(emergency_config)
        solver = emergency_solver_factory.build_solver()

        # Store solver reference for problem fact changes
        with job_lock:
            jobs[job_id]["solver"] = solver
            jobs[job_id]["start_time"] = datetime.now()
            _sync_job_to_store(job_id)

        logger.info(
            f"[Emergency Job {job_id}] Starting optimization with "
            f"{len(problem.shifts)} shifts and {len(problem.employees)} employees"
        )

        # Solve the problem
        solution = solver.solve(problem)

        elapsed = (datetime.now() - jobs[job_id]["start_time"]).total_seconds()

        # Keep job active for emergency changes
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED_EMERGENCY_READY"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()
            jobs[job_id]["final_score"] = str(solution.score)
            # Keep solver reference for emergency changes
            _sync_job_to_store(job_id)

        assigned_count = sum(
            1 for shift in solution.shifts if shift.employee is not None
        )
        logger.info(
            f"[Emergency Job {job_id}] Initial optimization completed in {elapsed:.1f}s. "
            f"Final score: {solution.score}, "
            f"Assigned shifts: {assigned_count}/{len(solution.shifts)}. "
            f"Job remains active for emergency changes."
        )

    except Exception as e:
        logger.error(f"[Emergency Job {job_id}] Optimization failed: {str(e)}")
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]
            _sync_job_to_store(job_id)
