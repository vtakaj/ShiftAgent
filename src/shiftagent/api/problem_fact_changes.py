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
            matching_shifts = [s for s in working_solution.shifts if s.id == shift_id]
            if matching_shifts:
                shift = matching_shifts[0]
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
        matching_employees = [
            e for e in working_solution.employees if e.id == self.employee_id
        ]
        if not matching_employees:
            logger.warning(f"Employee {self.employee_id} not found")
            return
        employee = matching_employees[0]

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


class SwapShiftsProblemFactChange:
    """Swap employee assignments between two shifts"""

    def __init__(self, shift1_id: str, shift2_id: str):
        self.shift1_id = shift1_id
        self.shift2_id = shift2_id

    def do_change(self, score_director) -> None:
        """Swap the employee assignments between two shifts"""
        working_solution: ShiftSchedule = score_director.get_working_solution()

        # Find the shifts to swap
        shift1 = None
        shift2 = None
        for shift in working_solution.shifts:
            if shift.id == self.shift1_id:
                shift1 = shift
            elif shift.id == self.shift2_id:
                shift2 = shift

        if shift1 is None:
            logger.error(f"Shift {self.shift1_id} not found")
            return

        if shift2 is None:
            logger.error(f"Shift {self.shift2_id} not found")
            return

        # Get the current employees
        employee1 = shift1.employee
        employee2 = shift2.employee

        logger.info(
            f"Swapping shifts: {shift1.id} ({employee1.name if employee1 else 'unassigned'}) "
            f"<-> {shift2.id} ({employee2.name if employee2 else 'unassigned'})"
        )

        # Perform the swap
        score_director.before_variable_changed(shift1, "employee")
        shift1.employee = employee2
        score_director.after_variable_changed(shift1, "employee")

        score_director.before_variable_changed(shift2, "employee")
        shift2.employee = employee1
        score_director.after_variable_changed(shift2, "employee")

        logger.info(
            f"Completed swap: {shift1.id} -> {employee2.name if employee2 else 'unassigned'}, "
            f"{shift2.id} -> {employee1.name if employee1 else 'unassigned'}"
        )

        # Trigger score recalculation
        score_director.trigger_variable_listeners()
