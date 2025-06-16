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
if SOLVER_LOG_LEVEL == "DEBUG":
    # Set both timefold and timefold.solver loggers to DEBUG
    logging.getLogger("timefold").setLevel(logging.DEBUG)
    logging.getLogger("timefold.solver").setLevel(logging.DEBUG)
    logger.info("Timefold solver logging set to DEBUG level")
else:
    # Set both timefold and timefold.solver loggers to INFO
    logging.getLogger("timefold").setLevel(logging.INFO)
    logging.getLogger("timefold.solver").setLevel(logging.INFO)

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
