"""
Job management for asynchronous optimization
"""

import threading
from datetime import datetime
from typing import Any, Dict

from ..core.models.schedule import ShiftSchedule
from .solver import solver_factory

# Job management dictionary
jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def solve_problem_async(job_id: str, problem: ShiftSchedule):
    """Execute shift optimization asynchronously"""
    try:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_ACTIVE"

        solver = solver_factory.build_solver()

        # Store solver reference for continuous planning
        with job_lock:
            jobs[job_id]["solver"] = solver
            jobs[job_id]["status"] = "SOLVING_SCHEDULED"

        solution = solver.solve(problem)

        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()
            # Remove solver reference after completion
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]

    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)
            # Remove solver reference on failure
            if "solver" in jobs[job_id]:
                del jobs[job_id]["solver"]
