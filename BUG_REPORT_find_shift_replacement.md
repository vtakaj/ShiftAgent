# Bug Report: find_shift_replacement API Error

## Issue Summary
The `find_shift_replacement` MCP tool returns a 400 Bad Request error when attempting to find a replacement for a shift.

## Error Details
- **Error Message**: `Client error '400 Bad Request' for url 'http://localhost:8081/api/shifts/97901313-fff6-4959-a2e5-e38f498e23e2/replace'`
- **HTTP Status**: 400 Bad Request
- **Endpoint**: `/api/shifts/{job_id}/replace`

## Request Data
```json
{
  "job_id": "97901313-fff6-4959-a2e5-e38f498e23e2",
  "shift_id": "土曜特別_saturday",
  "unavailable_employee_id": "emp5"
}
```

## Likely Causes

Based on code analysis, the 400 error occurs when:

1. **Job Not Found**: The job ID doesn't exist in memory or persistent storage
2. **Invalid Job Status**: The job is not in `SOLVING_SCHEDULED` status
3. **Missing Solver**: The job doesn't have an active solver instance

The specific error check in `routes.py:252-256`:
```python
if job["status"] != "SOLVING_SCHEDULED" or "solver" not in job:
    raise HTTPException(
        status_code=400,
        detail=f"Job {job_id} is not in an active solving state. Current status: {job['status']}",
    )
```

## Root Cause Analysis

The most likely cause is that the job has already completed (status is `SOLVING_COMPLETED`) and the solver reference has been removed. According to `jobs.py:48-50`, the solver reference is deleted after completion:

```python
jobs[job_id]["status"] = "SOLVING_COMPLETED"
# Remove solver reference after completion
if "solver" in jobs[job_id]:
    del jobs[job_id]["solver"]
```

## Steps to Reproduce

1. Start an async optimization job using `solve_schedule_async`
2. Wait for the job to complete (status becomes `SOLVING_COMPLETED`)
3. Attempt to call `find_shift_replacement` with the completed job ID
4. Receive 400 Bad Request error

## Expected Behavior

The API should either:
1. Provide a more descriptive error message indicating the job has already completed
2. Allow continuous planning operations on completed jobs by restarting the solver
3. Document that continuous planning operations are only available during active solving

## Suggested Fix

### Option 1: Improve Error Message
```python
if job["status"] == "SOLVING_COMPLETED":
    raise HTTPException(
        status_code=400,
        detail=f"Job {job_id} has already completed. Continuous planning operations are only available during active solving."
    )
elif job["status"] != "SOLVING_SCHEDULED" or "solver" not in job:
    raise HTTPException(
        status_code=400,
        detail=f"Job {job_id} is not in an active solving state. Current status: {job['status']}",
    )
```

### Option 2: Support Post-Completion Modifications
Allow restarting a completed job for continuous planning:
```python
if job["status"] == "SOLVING_COMPLETED" and "solution" in job:
    # Restart solver with the completed solution
    solver = solver_factory.build_solver()
    job["solver"] = solver
    job["status"] = "SOLVING_SCHEDULED"
    # Continue with problem change...
```

### Option 3: Add Job Status Check to MCP Tool
Add validation in the MCP tool before making the API call:
```python
async def find_shift_replacement(...):
    # First check job status
    status_response = await call_api("GET", f"/api/shifts/solve/{job_id}")
    if status_response.get("status") != "SOLVING_SCHEDULED":
        raise ValueError(f"Job {job_id} is not actively solving. Current status: {status_response.get('status')}")
    
    # Then proceed with replacement request
    ...
```

## Workaround

For now, continuous planning operations should only be used while a job is actively solving. To use these features:

1. Start an async job with a longer timeout
2. Immediately use continuous planning operations while status is `SOLVING_SCHEDULED`
3. Or implement a "continuous mode" that keeps the solver running

## Additional Notes

- The API documentation should clarify that continuous planning operations require an active solver
- Consider adding a `/api/shifts/{job_id}/restart` endpoint to restart completed jobs for modifications
- The MCP documentation should include timing requirements for continuous planning operations