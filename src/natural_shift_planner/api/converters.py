"""
Converters between API schemas and domain models
"""

from typing import Any

from ..core.models import Employee, Shift, ShiftSchedule
from .schemas import ShiftScheduleRequest


def convert_request_to_domain(request: ShiftScheduleRequest) -> ShiftSchedule:
    """Convert API request to domain objects"""
    # Convert employees
    employees = [
        Employee(
            id=emp.id,
            name=emp.name,
            skills=set(emp.skills),
            preferred_days_off=set(emp.preferred_days_off),
            preferred_work_days=set(emp.preferred_work_days),
            unavailable_dates=set(emp.unavailable_dates),
        )
        for emp in request.employees
    ]

    # Convert shifts
    shifts = [
        Shift(
            id=shift.id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            required_skills=set(shift.required_skills),
            location=shift.location,
            priority=shift.priority,
        )
        for shift in request.shifts
    ]

    return ShiftSchedule(employees=employees, shifts=shifts)


def convert_domain_to_response(schedule: ShiftSchedule) -> dict[str, Any]:
    """Convert domain objects to API response"""
    return {
        "employees": [
            {
                "id": emp.id,
                "name": emp.name,
                "skills": list(emp.skills),
                "preferred_days_off": list(emp.preferred_days_off),
                "preferred_work_days": list(emp.preferred_work_days),
                "unavailable_dates": [
                    date.isoformat() for date in emp.unavailable_dates
                ],
            }
            for emp in schedule.employees
        ],
        "shifts": [
            {
                "id": shift.id,
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat(),
                "required_skills": list(shift.required_skills),
                "location": shift.location,
                "priority": shift.priority,
                "employee": (
                    {"id": shift.employee.id, "name": shift.employee.name}
                    if shift.employee
                    else None
                ),
                "pinned": shift.pinned,
            }
            for shift in schedule.shifts
        ],
        "statistics": {
            "total_employees": schedule.get_employee_count(),
            "total_shifts": schedule.get_shift_count(),
            "assigned_shifts": schedule.get_assigned_shift_count(),
            "unassigned_shifts": schedule.get_unassigned_shift_count(),
        },
    }
