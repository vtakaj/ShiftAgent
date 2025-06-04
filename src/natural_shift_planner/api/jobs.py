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
        solution = solver.solve(problem)

        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()

    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)