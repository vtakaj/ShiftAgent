"""
Timefold Solver configuration and factory
"""
from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)

from ..core.models.shift import Shift
from ..core.models.schedule import ShiftSchedule
from ..core.constraints.shift_constraints import shift_scheduling_constraints

# Solver settings
solver_config = SolverConfig(
    solution_class=ShiftSchedule,
    entity_class_list=[Shift],
    score_director_factory_config=ScoreDirectorFactoryConfig(
        constraint_provider_function=shift_scheduling_constraints
    ),
    termination_config=TerminationConfig(spent_limit=Duration(seconds=30)),
)

solver_factory = SolverFactory.create(solver_config)