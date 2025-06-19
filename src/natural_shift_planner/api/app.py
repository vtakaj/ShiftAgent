"""
FastAPI application instance and configuration
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routes
from .job_store import job_store
from .jobs import job_lock, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup: Load persisted jobs
    if job_store:
        print("Loading persisted jobs from storage...")
        try:
            for job_id in job_store.list_jobs():
                stored_job = job_store.get_job(job_id)
                if stored_job:
                    # Only load completed or failed jobs
                    # (active jobs would have been interrupted)
                    if stored_job.get("status") in [
                        "SOLVING_COMPLETED",
                        "SOLVING_FAILED",
                    ]:
                        with job_lock:
                            jobs[job_id] = stored_job
            print(f"Loaded {len(jobs)} jobs from storage")
        except Exception as e:
            print(f"Error loading persisted jobs: {e}")

    yield

    # Shutdown: Nothing special needed as jobs are saved in real-time
    print("Shutting down Shift Scheduler API")


# Create FastAPI application
app = FastAPI(
    title="Shift Scheduler API",
    description="Shift creation API using Timefold Solver",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(routes.router)
