# Solver Configuration Guide

## Overview

The Shift Scheduler now supports configurable solver timeout and verbose logging to improve optimization results and debugging capabilities.

## Environment Variables

### SOLVER_TIMEOUT_SECONDS

Controls how long the solver will run before terminating.

- **Default**: 120 seconds (2 minutes)
- **Recommended**: 120-300 seconds for production use
- **Example**: `SOLVER_TIMEOUT_SECONDS=300` (5 minutes)

### SOLVER_LOG_LEVEL

Controls the verbosity of solver-specific logging.

- **Default**: INFO
- **Options**: INFO, DEBUG
- **Example**: `SOLVER_LOG_LEVEL=DEBUG`

### LOG_LEVEL

Controls the overall application logging level.

- **Default**: INFO
- **Options**: DEBUG, INFO, WARNING, ERROR
- **Example**: `LOG_LEVEL=DEBUG`

## Usage Examples

### Running with Extended Timeout

```bash
SOLVER_TIMEOUT_SECONDS=300 make run
```

### Running with Debug Logging

```bash
SOLVER_LOG_LEVEL=DEBUG LOG_LEVEL=INFO make run
```

### Running with All Features

```bash
SOLVER_TIMEOUT_SECONDS=300 SOLVER_LOG_LEVEL=DEBUG LOG_LEVEL=INFO make run
```

## What You'll See

### INFO Level Logging

```
2024-01-15 10:30:45 - natural_shift_planner.api.solver - INFO - Solver timeout configured: 300 seconds
2024-01-15 10:30:50 - natural_shift_planner.api.jobs - INFO - [Job abc-123] Starting optimization with 20 shifts and 10 employees
2024-01-15 10:30:52 - natural_shift_planner.api.jobs - INFO - [Job abc-123] New best score: 0hard/0medium/-50soft (time: 2.1s, improvements: 1)
2024-01-15 10:30:55 - natural_shift_planner.api.jobs - INFO - [Job abc-123] New best score: 0hard/0medium/-30soft (time: 5.2s, improvements: 2)
2024-01-15 10:31:45 - natural_shift_planner.api.jobs - INFO - [Job abc-123] Optimization completed. Final score: 0hard/0medium/-10soft, Assigned shifts: 19/20
```

### DEBUG Level Logging

With `SOLVER_LOG_LEVEL=DEBUG`, you'll additionally see:

```
2024-01-15 10:30:52 - natural_shift_planner.api.jobs - DEBUG - [Job abc-123] Score details - Hard: 0, Medium: 0, Soft: -50
2024-01-15 10:30:52 - timefold.solver - DEBUG - Construction Heuristic phase started
2024-01-15 10:30:53 - timefold.solver - DEBUG - Local Search phase started
```

## Benefits

1. **Better Solutions**: Longer timeout allows the solver to explore more possibilities
2. **Progress Monitoring**: See real-time score improvements
3. **Debugging**: Identify which constraints are being violated
4. **Performance Insights**: Track solving phases and timing

## Recommendations

- For small problems (< 10 shifts): 30-60 seconds
- For medium problems (10-50 shifts): 120-300 seconds  
- For large problems (> 50 shifts): 300-600 seconds
- Use DEBUG logging during development, INFO in production