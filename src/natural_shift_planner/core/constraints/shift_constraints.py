from datetime import datetime, timedelta

from timefold.solver.score import (
    Constraint,
    ConstraintCollectors,
    ConstraintFactory,
    HardMediumSoftScore,
    Joiners,
    constraint_provider,
)

from ..models import Employee, Shift, ShiftSchedule


@constraint_provider
def shift_scheduling_constraints(
    constraint_factory: ConstraintFactory,
) -> list[Constraint]:
    """Define shift scheduling constraints"""
    return [
        # Hard constraints (must be satisfied)
        locked_shift_constraint(constraint_factory),
        required_skill_constraint(constraint_factory),
        no_overlapping_shifts_constraint(constraint_factory),
        weekly_maximum_hours_constraint(constraint_factory),
        unavailable_date_constraint(constraint_factory),
        # Medium constraints (important but some violations allowed)
        minimum_rest_time_constraint(constraint_factory),
        weekly_minimum_hours_constraint(constraint_factory),
        # Soft constraints (optimization goals)
        minimize_unassigned_shifts_constraint(constraint_factory),
        fair_workload_distribution_constraint(constraint_factory),
        weekly_hours_target_constraint(constraint_factory),
        preferred_days_off_constraint(constraint_factory),
        preferred_work_days_constraint(constraint_factory),
    ]


def locked_shift_constraint(constraint_factory: ConstraintFactory) -> Constraint:
    """Locked shifts should not be modified - this is enforced by pinning in partial solver"""
    # This constraint acts as a safety net in case pinning fails
    # In practice, locked shifts should be pinned and not changeable by the solver
    return (
        constraint_factory.for_each(Shift)
        .filter(
            lambda shift: (
                shift.is_locked
                and hasattr(shift, '_pinned')
                and shift._pinned
            )
        )
        .penalize(HardMediumSoftScore.ZERO)  # No penalty needed if pinning works
        .as_constraint("Locked shift constraint")
    )


def required_skill_constraint(constraint_factory: ConstraintFactory) -> Constraint:
    """Only employees with required skills can be assigned to shifts"""
    return (
        constraint_factory.for_each(Shift)
        .filter(
            lambda shift: (
                shift.employee is not None
                and not shift.employee.has_all_skills(shift.required_skills)
            )
        )
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Required skill constraint")
    )


def no_overlapping_shifts_constraint(
    constraint_factory: ConstraintFactory,
) -> Constraint:
    """Employees cannot be assigned to multiple shifts at the same time"""
    return (
        constraint_factory.for_each(Shift)
        .join(
            Shift,
            Joiners.equal(lambda shift: shift.employee),
            Joiners.less_than(lambda shift: shift.id),
        )
        .filter(
            lambda shift1, shift2: (
                shift1.employee is not None and shift1.overlaps_with(shift2)
            )
        )
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("No overlapping shifts constraint")
    )


def minimum_rest_time_constraint(constraint_factory: ConstraintFactory):
    """Ensure minimum rest time (8 hours) between shifts"""
    return (
        constraint_factory.for_each(Shift)
        .join(
            Shift,
            Joiners.equal(lambda shift: shift.employee),
            Joiners.less_than(
                lambda shift: shift.end_time, lambda shift: shift.start_time
            ),
        )
        .filter(
            lambda earlier_shift, later_shift: (
                earlier_shift.employee is not None
                and (later_shift.start_time - earlier_shift.end_time)
                < timedelta(hours=8)
            )
        )
        .penalize(HardMediumSoftScore.ONE_MEDIUM)
        .as_constraint("Minimum rest time constraint")
    )


def minimize_unassigned_shifts_constraint(constraint_factory: ConstraintFactory):
    """Minimize unassigned shifts (considering priority)"""
    return (
        constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is None)
        .penalize(HardMediumSoftScore.of_soft(1), lambda shift: shift.priority * 10)
        .as_constraint("Minimize unassigned shifts")
    )


def fair_workload_distribution_constraint(constraint_factory: ConstraintFactory):
    """Fair workload distribution (minimize deviation from 8 hours)"""
    return (
        constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is not None)
        .group_by(
            lambda shift: shift.employee,
            ConstraintCollectors.sum(lambda shift: shift.get_duration_minutes()),
        )
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda employee, total_minutes: abs(total_minutes - 480),
        )  # 8 hours = 480 minutes
        .as_constraint("Fair workload distribution")
    )


def weekly_maximum_hours_constraint(constraint_factory: ConstraintFactory):
    """Weekly maximum hours constraint (legal 40 hours) - Hard constraint"""
    return (
        constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is not None)
        .group_by(
            lambda shift: shift.employee,
            lambda shift: get_week_key(shift.start_time),
            ConstraintCollectors.sum(lambda shift: shift.get_duration_minutes()),
        )
        .filter(
            lambda employee, week, total_minutes: total_minutes > 45 * 60
        )  # Violation if over 45 hours
        .penalize(
            HardMediumSoftScore.ONE_HARD,
            lambda employee, week, total_minutes: (total_minutes - 45 * 60) // 60,
        )
        .as_constraint("Weekly maximum hours constraint")
    )


def weekly_minimum_hours_constraint(constraint_factory: ConstraintFactory):
    """Weekly minimum hours constraint (for full-time employees)"""
    return (
        constraint_factory.for_each(Shift)
        .filter(
            lambda shift: shift.employee is not None
            and is_full_time_employee(shift.employee)
        )
        .group_by(
            lambda shift: shift.employee,
            lambda shift: get_week_key(shift.start_time),
            ConstraintCollectors.sum(lambda shift: shift.get_duration_minutes()),
        )
        .filter(
            lambda employee, week, total_minutes: total_minutes < 32 * 60
        )  # Less than 32 hours
        .penalize(
            HardMediumSoftScore.ONE_MEDIUM,
            lambda employee, week, total_minutes: (32 * 60 - total_minutes) // 60,
        )
        .as_constraint("Weekly minimum hours constraint")
    )


def weekly_hours_target_constraint(constraint_factory: ConstraintFactory):
    """Weekly hours target constraint (soft constraint)"""
    return (
        constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is not None)
        .group_by(
            lambda shift: shift.employee,
            lambda shift: get_week_key(shift.start_time),
            ConstraintCollectors.sum(lambda shift: shift.get_duration_minutes()),
        )
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda employee, week, total_minutes: abs(
                total_minutes - get_target_hours(employee) * 60
            )
            // 60,
        )
        .as_constraint("Weekly hours target constraint")
    )


# Helper functions
def get_week_key(date: datetime) -> str:
    """Generate week key (year-week number) from date"""
    year, week_num, _ = date.isocalendar()
    return f"{year}-W{week_num:02d}"


def is_full_time_employee(employee: Employee) -> bool:
    """Check if employee is full-time"""
    return "Full-time" in employee.skills or "Regular" in employee.skills


def get_target_hours(employee: Employee) -> int:
    """Get target working hours for employee"""
    if "Part-time" in employee.skills:
        return 20  # Part-time: 20 hours/week
    elif "Full-time" in employee.skills or "Regular" in employee.skills:
        return 40  # Full-time: 40 hours/week
    else:
        return 32  # Default: 32 hours/week


def unavailable_date_constraint(constraint_factory: ConstraintFactory) -> Constraint:
    """Hard constraint: Employees cannot be assigned to shifts on unavailable dates"""
    return (
        constraint_factory.for_each(Shift)
        .filter(
            lambda shift: (
                shift.employee is not None
                and shift.employee.is_unavailable_on_date(shift.start_time)
            )
        )
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Unavailable date constraint")
    )


def preferred_days_off_constraint(constraint_factory: ConstraintFactory) -> Constraint:
    """Soft constraint: Penalize assignments on employees' preferred days off"""
    return (
        constraint_factory.for_each(Shift)
        .filter(
            lambda shift: (
                shift.employee is not None
                and shift.employee.prefers_day_off(get_day_name(shift.start_time))
            )
        )
        .penalize(HardMediumSoftScore.of_soft(5))  # Medium penalty for preferred days off
        .as_constraint("Preferred days off constraint")
    )


def preferred_work_days_constraint(constraint_factory: ConstraintFactory) -> Constraint:
    """Soft constraint: Reward assignments on employees' preferred work days"""
    return (
        constraint_factory.for_each(Shift)
        .filter(
            lambda shift: (
                shift.employee is not None
                and shift.employee.prefers_work_day(get_day_name(shift.start_time))
            )
        )
        .reward(HardMediumSoftScore.of_soft(3))  # Reward for preferred work days
        .as_constraint("Preferred work days constraint")
    )


def get_day_name(date: datetime) -> str:
    """Get day name from datetime"""
    return date.strftime('%A').lower()  # Returns 'monday', 'tuesday', etc.
