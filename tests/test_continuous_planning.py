"""
Tests for continuous planning features
"""

from datetime import datetime, timedelta

import pytest
from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)

from src.natural_shift_planner.core.constraints.shift_constraints import (
    shift_scheduling_constraints,
)
from src.natural_shift_planner.core.models import Employee, Shift, ShiftSchedule

# Skip this entire test module until continuous planning is implemented
pytest.skip("Continuous planning module not yet implemented", allow_module_level=True)

# TODO: Import ContinuousPlanningService when implemented
# from src.natural_shift_planner.api.continuous_planning import ContinuousPlanningService


# Placeholder class until actual implementation
class ContinuousPlanningService:
    @staticmethod
    def swap_shifts(solver, shift1_id, shift2_id):
        pass

    @staticmethod
    def find_replacement_for_shift(solver, shift_id, employee_id):
        pass

    @staticmethod
    def reassign_shift(solver, shift_id, employee_id):
        pass

    @staticmethod
    def pin_shifts(solver, shift_ids):
        pass


@pytest.fixture
def sample_employees() -> list[Employee]:
    """Create sample employees for testing"""
    return [
        Employee(id="emp1", name="John Smith", skills={"Nurse", "CPR"}),
        Employee(id="emp2", name="Sarah Johnson", skills={"Nurse"}),
        Employee(id="emp3", name="Michael Brown", skills={"Security"}),
        Employee(id="emp4", name="Emily Davis", skills={"Reception", "Admin"}),
    ]


@pytest.fixture
def sample_shifts() -> list[Shift]:
    """Create sample shifts for testing"""
    base_date = datetime(2025, 6, 1)
    return [
        Shift(
            id="shift1",
            start_time=base_date.replace(hour=8),
            end_time=base_date.replace(hour=16),
            required_skills={"Nurse"},
            employee=None,
        ),
        Shift(
            id="shift2",
            start_time=base_date.replace(hour=16),
            end_time=(base_date + timedelta(days=1)).replace(hour=0),
            required_skills={"Nurse"},
            employee=None,
        ),
        Shift(
            id="shift3",
            start_time=base_date.replace(hour=22),
            end_time=(base_date + timedelta(days=1)).replace(hour=6),
            required_skills={"Security"},
            employee=None,
        ),
    ]


@pytest.fixture
def solver_config():
    """Create solver configuration for testing"""
    return SolverConfig(
        solution_class=ShiftSchedule,
        entity_class_list=[Shift],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=shift_scheduling_constraints
        ),
        termination_config=TerminationConfig(spent_limit=Duration(seconds=5)),
    )


def test_pin_unpin_functionality(sample_employees, sample_shifts):
    """Test that pinning prevents shift reassignment"""
    # Create schedule
    schedule = ShiftSchedule(employees=sample_employees, shifts=sample_shifts)

    # Assign employees to shifts
    schedule.shifts[0].employee = sample_employees[0]  # John to shift1
    schedule.shifts[1].employee = sample_employees[1]  # Sarah to shift2

    # Test pinning
    schedule.shifts[0].pin()
    assert schedule.shifts[0].is_pinned()
    assert schedule.shifts[0].pinned is True

    # Test unpinning
    schedule.shifts[0].unpin()
    assert not schedule.shifts[0].is_pinned()
    assert schedule.shifts[0].pinned is False


@pytest.mark.skip(reason="Timefold API has changed, needs update")
def test_shift_swap_problem_change(sample_employees, sample_shifts, solver_config):
    """Test shift swapping using ProblemChangeDirector"""
    # Create and solve initial schedule
    schedule = ShiftSchedule(employees=sample_employees, shifts=sample_shifts)

    # Pre-assign some shifts
    schedule.shifts[0].employee = sample_employees[0]  # John to shift1
    schedule.shifts[1].employee = sample_employees[1]  # Sarah to shift2

    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()

    # Start solving in a separate thread (simulating async operation)
    import threading

    solve_thread = threading.Thread(target=lambda: solver.solve(schedule))
    solve_thread.daemon = True
    solve_thread.start()

    # Wait a bit for solver to start
    import time

    time.sleep(0.1)

    # Apply swap
    ContinuousPlanningService.swap_shifts(solver, "shift1", "shift2")

    # Wait for solving to complete
    solve_thread.join(timeout=10)

    # Get final solution
    solution = solver.get_best_solution()

    # Find the shifts in the solution
    shift1 = next(s for s in solution.shifts if s.id == "shift1")
    shift2 = next(s for s in solution.shifts if s.id == "shift2")

    # Verify swap occurred
    assert shift1.employee.id == "emp2"  # Sarah now on shift1
    assert shift2.employee.id == "emp1"  # John now on shift2


@pytest.mark.skip(reason="Timefold API has changed, needs update")
def test_find_replacement_problem_change(
    sample_employees, sample_shifts, solver_config
):
    """Test finding replacement using ProblemChangeDirector"""
    # Create schedule with assigned shift
    schedule = ShiftSchedule(employees=sample_employees, shifts=sample_shifts)

    # Assign John to shift1
    schedule.shifts[0].employee = sample_employees[0]

    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()

    # Start solving
    import threading

    solve_thread = threading.Thread(target=lambda: solver.solve(schedule))
    solve_thread.daemon = True
    solve_thread.start()

    # Wait a bit
    import time

    time.sleep(0.1)

    # John becomes unavailable
    ContinuousPlanningService.find_replacement_for_shift(solver, "shift1", "emp1")

    # Wait for completion
    solve_thread.join(timeout=10)

    # Get final solution
    solution = solver.get_best_solution()
    shift1 = next(s for s in solution.shifts if s.id == "shift1")

    # Verify John is no longer assigned
    assert shift1.employee is None or shift1.employee.id != "emp1"
    # If assigned, should be someone with Nurse skill
    if shift1.employee:
        assert "Nurse" in shift1.employee.skills


@pytest.mark.skip(reason="Timefold API has changed, needs update")
def test_reassign_shift(sample_employees, sample_shifts, solver_config):
    """Test reassigning a shift to specific employee"""
    schedule = ShiftSchedule(employees=sample_employees, shifts=sample_shifts)

    # Initially assign John to shift1
    schedule.shifts[0].employee = sample_employees[0]

    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()

    # Start solving
    import threading

    solve_thread = threading.Thread(target=lambda: solver.solve(schedule))
    solve_thread.daemon = True
    solve_thread.start()

    # Wait a bit
    import time

    time.sleep(0.1)

    # Reassign to Sarah
    ContinuousPlanningService.reassign_shift(solver, "shift1", "emp2")

    # Wait for completion
    solve_thread.join(timeout=10)

    # Get final solution
    solution = solver.get_best_solution()
    shift1 = next(s for s in solution.shifts if s.id == "shift1")

    # Verify reassignment
    assert shift1.employee.id == "emp2"


def test_pin_shifts_problem_change(sample_employees, sample_shifts, solver_config):
    """Test pinning shifts during solving"""
    schedule = ShiftSchedule(employees=sample_employees, shifts=sample_shifts)

    # Assign employees
    schedule.shifts[0].employee = sample_employees[0]
    schedule.shifts[1].employee = sample_employees[1]

    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()

    # Start solving
    import threading

    solve_thread = threading.Thread(target=lambda: solver.solve(schedule))
    solve_thread.daemon = True
    solve_thread.start()

    # Wait a bit
    import time

    time.sleep(0.1)

    # Pin shifts
    ContinuousPlanningService.pin_shifts(solver, ["shift1", "shift2"])

    # Wait for completion
    solve_thread.join(timeout=10)

    # Note: We can't directly verify pinning in the solution since
    # the solver might have already completed. This test mainly ensures
    # the operation doesn't cause errors.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
