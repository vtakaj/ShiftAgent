"""
Timefold Solver configuration and factory
"""

import logging
import os

from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)

from ..core.constraints.shift_constraints import shift_scheduling_constraints
from ..core.models.schedule import ShiftSchedule
from ..core.models.shift import Shift

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration from environment with defaults
SOLVER_TIMEOUT_SECONDS = int(
    os.getenv("SOLVER_TIMEOUT_SECONDS", "120")
)  # Default: 2 minutes
SOLVER_LOG_LEVEL = os.getenv("SOLVER_LOG_LEVEL", "INFO")  # INFO or DEBUG


# Configure Timefold logging based on environment
def configure_timefold_logging():
    """Configure all Timefold-related loggers with the appropriate log level"""
    log_level = logging.DEBUG if SOLVER_LOG_LEVEL == "DEBUG" else logging.INFO

    # Configure all Timefold-related loggers
    timefold_loggers = [
        "timefold",
        "timefold.solver",
        "timefold.solver.score",
        "timefold.solver.construction",
        "timefold.solver.local",
        "timefold.solver.phase",
    ]

    # First, set all loggers to INFO level
    for logger_name in timefold_loggers:
        logging.getLogger(logger_name).setLevel(logging.INFO)

    # Then, if DEBUG is enabled, set specific loggers to DEBUG
    if SOLVER_LOG_LEVEL == "DEBUG":
        for logger_name in timefold_loggers:
            logging.getLogger(logger_name).setLevel(logging.DEBUG)
        logger.info("Timefold solver logging set to DEBUG level")
    else:
        # Ensure solver debug logs are suppressed
        logging.getLogger("timefold.solver").setLevel(logging.INFO)
        logging.getLogger("timefold.solver.local").setLevel(logging.INFO)
        logger.info("Timefold solver logging set to INFO level")


# Configure logging
configure_timefold_logging()
logger.info(f"Solver timeout configured: {SOLVER_TIMEOUT_SECONDS} seconds")

# Solver settings
solver_config = SolverConfig(
    solution_class=ShiftSchedule,
    entity_class_list=[Shift],
    score_director_factory_config=ScoreDirectorFactoryConfig(
        constraint_provider_function=shift_scheduling_constraints
    ),
    termination_config=TerminationConfig(
        spent_limit=Duration(seconds=SOLVER_TIMEOUT_SECONDS)
    ),
)

# Note: Solver internal logging is controlled via Python logging configuration above

solver_factory = SolverFactory.create(solver_config)
