"""
Job management for asynchronous optimization
"""

import threading
from datetime import datetime
from typing import Any, Dict

from ..core.models.schedule import ShiftSchedule
from .job_store import job_store
from .solver import solver_factory

# Job management dictionary
jobs: Dict[str, Dict[str, Any]] = {}
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

        # Store solver reference for continuous planning
        with job_lock:
            jobs[job_id]["solver"] = solver
            jobs[job_id]["status"] = "SOLVING_SCHEDULED"
            _sync_job_to_store(job_id)

        solution = solver.solve(problem)

        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()
            # Remove solver reference after completion
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]
            _sync_job_to_store(job_id)

    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)
            # Remove solver reference on failure
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]
            _sync_job_to_store(job_id)
