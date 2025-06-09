"""
Continuous planning service for partial schedule modifications
"""

from typing import Callable, List, Optional

from timefold.solver import Solver
from timefold.solver.score import HardMediumSoftScore

from ..core.models.employee import Employee
from ..core.models.schedule import ShiftSchedule
from ..core.models.shift import Shift


class ContinuousPlanningService:
    """Service for handling continuous planning operations"""

    @staticmethod
    def swap_shifts(solver: Solver, shift1_id: str, shift2_id: str) -> None:
        """
        Swap employees between two shifts using ProblemChangeDirector

        Args:
            solver: The active Timefold solver instance
            shift1_id: ID of the first shift
            shift2_id: ID of the second shift
        """

        def shift_swap_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            # Find the shifts by ID
            shift1 = next(
                (s for s in working_solution.shifts if s.id == shift1_id), None
            )
            shift2 = next(
                (s for s in working_solution.shifts if s.id == shift2_id), None
            )

            # Validate that both shifts exist
            if not shift1:
                raise ValueError(f"Shift with ID '{shift1_id}' not found in solution")
            if not shift2:
                raise ValueError(f"Shift with ID '{shift2_id}' not found in solution")

            # Store current assignments
            employee1 = shift1.employee
            employee2 = shift2.employee

            # Use ProblemChangeDirector to swap assignments
            problem_change_director.change_variable(shift1, "employee", employee2)
            problem_change_director.change_variable(shift2, "employee", employee1)

        # Add the problem change to the solver
        solver.add_problem_change(shift_swap_problem_change)

    @staticmethod
    def find_replacement_for_shift(
        solver: Solver, shift_id: str, unavailable_employee_id: str
    ) -> None:
        """
        Find a replacement for a shift when an employee becomes unavailable

        Args:
            solver: The active Timefold solver instance
            shift_id: ID of the shift needing replacement
            unavailable_employee_id: ID of the employee who cannot work
        """

        def shift_replacement_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            # Find the shift that needs a replacement
            shift = next((s for s in working_solution.shifts if s.id == shift_id), None)

            # Validate that the shift exists
            if not shift:
                raise ValueError(f"Shift with ID '{shift_id}' not found in solution")

            # Check if the shift is currently assigned to the unavailable employee
            if not shift.employee:
                raise ValueError(
                    f"Shift '{shift_id}' is not currently assigned to any employee"
                )

            if shift.employee.id != unavailable_employee_id:
                raise ValueError(
                    f"Shift '{shift_id}' is not assigned to employee '{unavailable_employee_id}' (currently assigned to '{shift.employee.id}')"
                )

            # Remove the current assignment
            problem_change_director.change_variable(shift, "employee", None)
            # The solver will continue running and find a suitable replacement

        solver.add_problem_change(shift_replacement_problem_change)

    @staticmethod
    def pin_shifts(solver: Solver, shift_ids: List[str]) -> None:
        """
        Pin multiple shifts to prevent changes during solving

        Args:
            solver: The active Timefold solver instance
            shift_ids: List of shift IDs to pin
        """

        def pin_shifts_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            missing_shifts = []
            for shift_id in shift_ids:
                shift = next(
                    (s for s in working_solution.shifts if s.id == shift_id), None
                )
                if not shift:
                    missing_shifts.append(shift_id)
                else:
                    # Create a new shift instance with pinned=True
                    shift_dict = shift.__dict__.copy()
                    shift_dict["pinned"] = True
                    updated_shift = Shift(**shift_dict)

                    # Replace the shift in the solution
                    problem_change_director.remove_entity(shift)
                    problem_change_director.add_entity(updated_shift)

            # Report missing shifts if any
            if missing_shifts:
                raise ValueError(
                    f"Shifts not found in solution: {', '.join(missing_shifts)}"
                )

        solver.add_problem_change(pin_shifts_problem_change)

    @staticmethod
    def unpin_shifts(solver: Solver, shift_ids: List[str]) -> None:
        """
        Unpin multiple shifts to allow changes during solving

        Args:
            solver: The active Timefold solver instance
            shift_ids: List of shift IDs to unpin
        """

        def unpin_shifts_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            missing_shifts = []
            for shift_id in shift_ids:
                shift = next(
                    (s for s in working_solution.shifts if s.id == shift_id), None
                )
                if not shift:
                    missing_shifts.append(shift_id)
                else:
                    # Create a new shift instance with pinned=False
                    shift_dict = shift.__dict__.copy()
                    shift_dict["pinned"] = False
                    updated_shift = Shift(**shift_dict)

                    # Replace the shift in the solution
                    problem_change_director.remove_entity(shift)
                    problem_change_director.add_entity(updated_shift)

            # Report missing shifts if any
            if missing_shifts:
                raise ValueError(
                    f"Shifts not found in solution: {', '.join(missing_shifts)}"
                )

        solver.add_problem_change(unpin_shifts_problem_change)

    @staticmethod
    def reassign_shift(
        solver: Solver, shift_id: str, new_employee_id: Optional[str]
    ) -> None:
        """
        Reassign a shift to a specific employee or unassign it

        Args:
            solver: The active Timefold solver instance
            shift_id: ID of the shift to reassign
            new_employee_id: ID of the new employee (None to unassign)
        """

        def reassign_shift_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            shift = next((s for s in working_solution.shifts if s.id == shift_id), None)

            # Validate that the shift exists
            if not shift:
                raise ValueError(f"Shift with ID '{shift_id}' not found in solution")

            new_employee = None
            if new_employee_id:
                new_employee = next(
                    (e for e in working_solution.employees if e.id == new_employee_id),
                    None,
                )
                # Validate that the employee exists
                if not new_employee:
                    raise ValueError(
                        f"Employee with ID '{new_employee_id}' not found in solution"
                    )

            problem_change_director.change_variable(shift, "employee", new_employee)

        solver.add_problem_change(reassign_shift_problem_change)
