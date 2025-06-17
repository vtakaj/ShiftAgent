"""
Problem Fact Changes for dynamic schedule modifications
"""

import logging

# Note: ScoreDirector type hints will be applied at runtime
from ..core.models import Employee, ShiftSchedule

logger = logging.getLogger(__name__)


class AddEmployeeProblemFactChange:
    """Add a new employee to an active solving session"""

    def __init__(
        self,
        new_employee: Employee,
        auto_assign_shift_ids: list[str] | None = None,
    ):
        self.new_employee = new_employee
        self.auto_assign_shift_ids = auto_assign_shift_ids or []

    def do_change(self, score_director) -> None:
        """Apply the employee addition to the working solution"""
        # Get the working solution
        working_solution: ShiftSchedule = score_director.get_working_solution()

        # Add the new employee to the solution
        score_director.before_problem_fact_added(self.new_employee)
        working_solution.employees.append(self.new_employee)
        score_director.after_problem_fact_added(self.new_employee)

        logger.info(
            f"Added emergency employee: {self.new_employee.name} "
            f"with skills: {self.new_employee.skills}"
        )

        # Find unassigned shifts that match the employee's skills
        unassigned_shifts = [
            shift for shift in working_solution.shifts if shift.employee is None
        ]

        # Auto-assign to compatible unassigned shifts if not manually specified
        if not self.auto_assign_shift_ids and unassigned_shifts:
            for shift in unassigned_shifts:
                if self.new_employee.has_required_skills(shift.required_skills):
                    score_director.before_variable_changed(shift, "employee")
                    shift.employee = self.new_employee
                    score_director.after_variable_changed(shift, "employee")
                    logger.info(
                        f"Auto-assigned {self.new_employee.name} to shift {shift.id}"
                    )
                    break  # Assign to first compatible shift

        # Handle specific shift assignments if requested
        for shift_id in self.auto_assign_shift_ids:
            shift = next(
                (s for s in working_solution.shifts if s.id == shift_id), None
            )
            if shift:
                # Check if shift is unassigned or can be reassigned
                if shift.employee is None:
                    score_director.before_variable_changed(shift, "employee")
                    shift.employee = self.new_employee
                    score_director.after_variable_changed(shift, "employee")
                    logger.info(
                        f"Assigned {self.new_employee.name} to requested shift {shift_id}"
                    )
                else:
                    logger.warning(
                        f"Shift {shift_id} already assigned to {shift.employee.name}"
                    )

        # Trigger score recalculation
        score_director.trigger_variable_listeners()


class RemoveEmployeeProblemFactChange:
    """Remove an employee from active solving (unassigns their shifts)"""

    def __init__(self, employee_id: str):
        self.employee_id = employee_id

    def do_change(self, score_director) -> None:
        """Remove employee and unassign their shifts"""
        working_solution: ShiftSchedule = score_director.get_working_solution()

        # Find the employee
        employee = next(
            (e for e in working_solution.employees if e.id == self.employee_id), None
        )
        if not employee:
            logger.warning(f"Employee {self.employee_id} not found")
            return

        # Unassign all shifts for this employee
        for shift in working_solution.shifts:
            if shift.employee and shift.employee.id == self.employee_id:
                score_director.before_variable_changed(shift, "employee")
                shift.employee = None
                score_director.after_variable_changed(shift, "employee")
                logger.info(f"Unassigned shift {shift.id} from {employee.name}")

        # Remove the employee
        score_director.before_problem_fact_removed(employee)
        working_solution.employees.remove(employee)
        score_director.after_problem_fact_removed(employee)

        logger.info(f"Removed employee: {employee.name}")
