"""
Continuous planning service for partial schedule modifications
"""


from timefold.solver import Solver

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
    def pin_shifts(solver: Solver, shift_ids: list[str]) -> None:
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
    def unpin_shifts(solver: Solver, shift_ids: list[str]) -> None:
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
        solver: Solver, shift_id: str, new_employee_id: str | None
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

    @staticmethod
    def add_employee(
        solver: Solver,
        employee_id: str,
        name: str,
        skills: set[str],
        preferred_days_off: set[str] = None,
        preferred_work_days: set[str] = None,
        unavailable_dates: set = None,
    ) -> None:
        """
        Add a new employee to the running solver

        Args:
            solver: The active Timefold solver instance
            employee_id: ID of the new employee
            name: Name of the new employee
            skills: Set of skills the employee has
            preferred_days_off: Days employee prefers not to work
            preferred_work_days: Days employee prefers to work
            unavailable_dates: Specific dates when employee is unavailable
        """

        def add_employee_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            # Check if employee already exists
            existing_employee = next(
                (e for e in working_solution.employees if e.id == employee_id), None
            )

            if existing_employee:
                raise ValueError(f"Employee with ID '{employee_id}' already exists")

            # Create new employee with preferences
            new_employee = Employee(
                id=employee_id,
                name=name,
                skills=skills,
                preferred_days_off=preferred_days_off or set(),
                preferred_work_days=preferred_work_days or set(),
                unavailable_dates=unavailable_dates or set(),
            )

            # Add employee to the solution using ProblemChangeDirector
            problem_change_director.add_problem_fact(
                new_employee, working_solution.employees
            )

        solver.add_problem_change(add_employee_problem_change)

    @staticmethod
    def add_employees_batch(solver: Solver, employees: list[dict]) -> None:
        """
        Add multiple employees to the running solver

        Args:
            solver: The active Timefold solver instance
            employees: List of employee dictionaries with id, name, skills, etc.
        """

        def add_employees_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            # Get existing employee IDs
            existing_ids = {e.id for e in working_solution.employees}

            new_employees = []
            for emp_data in employees:
                if emp_data["id"] in existing_ids:
                    continue  # Skip if already exists

                # Create new employee
                new_employee = Employee(
                    id=emp_data["id"],
                    name=emp_data["name"],
                    skills=set(emp_data["skills"]),
                    preferred_days_off=set(emp_data.get("preferred_days_off", [])),
                    preferred_work_days=set(emp_data.get("preferred_work_days", [])),
                    unavailable_dates=set(emp_data.get("unavailable_dates", [])),
                )
                new_employees.append(new_employee)

                # Add employee to the solution
                problem_change_director.add_problem_fact(
                    new_employee, working_solution.employees
                )

            if not new_employees:
                raise ValueError("No new employees to add (all IDs already exist)")

        solver.add_problem_change(add_employees_problem_change)

    @staticmethod
    def remove_employee(solver: Solver, employee_id: str) -> None:
        """
        Remove an employee from the running solver

        Args:
            solver: The active Timefold solver instance
            employee_id: ID of the employee to remove
        """

        def remove_employee_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            # Find the employee
            employee_to_remove = next(
                (e for e in working_solution.employees if e.id == employee_id), None
            )

            if not employee_to_remove:
                raise ValueError(f"Employee with ID '{employee_id}' not found")

            # First, unassign all shifts assigned to this employee
            for shift in working_solution.shifts:
                if shift.employee and shift.employee.id == employee_id:
                    problem_change_director.change_variable(shift, "employee", None)

            # Then remove the employee from the solution
            problem_change_director.remove_problem_fact(
                employee_to_remove, working_solution.employees
            )

        solver.add_problem_change(remove_employee_problem_change)

    @staticmethod
    def add_employee_and_assign_shift(
        solver: Solver,
        employee_id: str,
        name: str,
        skills: set[str],
        shift_id: str,
        preferred_days_off: set[str] = None,
        preferred_work_days: set[str] = None,
        unavailable_dates: set = None,
    ) -> None:
        """
        Add a new employee and immediately assign them to a specific shift

        Args:
            solver: The active Timefold solver instance
            employee_id: ID of the new employee
            name: Name of the new employee
            skills: Set of skills the employee has
            shift_id: ID of the shift to assign to the new employee
            preferred_days_off: Days employee prefers not to work
            preferred_work_days: Days employee prefers to work
            unavailable_dates: Specific dates when employee is unavailable
        """

        def add_and_assign_problem_change(
            working_solution: ShiftSchedule, problem_change_director
        ):
            # Check if employee already exists
            existing_employee = next(
                (e for e in working_solution.employees if e.id == employee_id), None
            )

            if existing_employee:
                raise ValueError(f"Employee with ID '{employee_id}' already exists")

            # Find the target shift
            target_shift = next(
                (s for s in working_solution.shifts if s.id == shift_id), None
            )

            if not target_shift:
                raise ValueError(f"Shift with ID '{shift_id}' not found")

            # Create new employee
            new_employee = Employee(
                id=employee_id,
                name=name,
                skills=skills,
                preferred_days_off=preferred_days_off or set(),
                preferred_work_days=preferred_work_days or set(),
                unavailable_dates=unavailable_dates or set(),
            )

            # Add employee to the solution
            problem_change_director.add_problem_fact(
                new_employee, working_solution.employees
            )

            # Assign the employee to the shift
            problem_change_director.change_variable(
                target_shift, "employee", new_employee
            )

        solver.add_problem_change(add_and_assign_problem_change)
