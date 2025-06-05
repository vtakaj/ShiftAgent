"""
Demo data generation for testing
"""
from datetime import datetime, timedelta

from ..core.models import Employee, Shift, ShiftSchedule


def create_demo_schedule() -> ShiftSchedule:
    """Create demo shift schedule"""
    # Get specific dates for unavailable examples
    base_date = datetime.now().replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0
    )
    monday = base_date - timedelta(days=base_date.weekday())
    friday_date = monday + timedelta(days=4)
    
    # Create employees (with employment type and preferences)
    employees = [
        Employee(
            "emp1",
            "John Smith",
            {"Nurse", "CPR", "Full-time"},
            preferred_days_off={"friday", "saturday"},  # Prefers weekends off
            preferred_work_days={"monday", "tuesday"}
        ),
        Employee(
            "emp2",
            "Sarah Johnson", 
            {"Nurse", "Full-time"},
            preferred_work_days={"sunday", "saturday"},  # Prefers weekends
            unavailable_dates={friday_date}  # Unavailable on specific Friday
        ),
        Employee(
            "emp3",
            "Michael Brown",
            {"Security", "Full-time"},
            preferred_days_off={"wednesday"}  # Prefers Wednesdays off
        ),
        Employee(
            "emp4",
            "Emily Davis",
            {"Reception", "Admin", "Part-time"},
            preferred_work_days={"monday", "tuesday", "wednesday"},  # Prefers weekdays
            preferred_days_off={"saturday", "sunday"}
        ),
        Employee(
            "emp5",
            "David Wilson",
            {"Nurse", "Part-time"},
            preferred_days_off={"thursday", "friday"}  # Student who prefers Thu/Fri off
        ),
    ]

    # Create shifts for one week (considering weekly working hours)
    # Start from Monday (already calculated above)

    shifts = []

    for day in range(7):  # One week
        day_start = monday + timedelta(days=day)
        day_name = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ][day]

        # Morning shift (8:00-16:00) - 8 hours
        shifts.append(
            Shift(
                id=f"morning_{day_name}",
                start_time=day_start.replace(hour=8),
                end_time=day_start.replace(hour=16),
                required_skills={"Nurse"},
                location="Hospital",
            )
        )

        # Evening shift (16:00-24:00) - 8 hours
        shifts.append(
            Shift(
                id=f"evening_{day_name}",
                start_time=day_start.replace(hour=16),
                end_time=day_start.replace(hour=23, minute=59),
                required_skills={"Nurse"},
                location="Hospital",
            )
        )

        # Night security (22:00-06:00) - 8 hours
        if day < 6:  # Except Sunday
            shifts.append(
                Shift(
                    id=f"security_{day_name}",
                    start_time=day_start.replace(hour=22),
                    end_time=(day_start + timedelta(days=1)).replace(hour=6),
                    required_skills={"Security"},
                    location="Hospital",
                )
            )

        # Reception shift (9:00-13:00) - 4 hours (for part-time)
        if day < 5:  # Weekdays only
            shifts.append(
                Shift(
                    id=f"reception_morning_{day_name}",
                    start_time=day_start.replace(hour=9),
                    end_time=day_start.replace(hour=13),
                    required_skills={"Reception"},
                    location="Reception",
                )
            )

            shifts.append(
                Shift(
                    id=f"reception_afternoon_{day_name}",
                    start_time=day_start.replace(hour=13),
                    end_time=day_start.replace(hour=17),
                    required_skills={"Reception"},
                    location="Reception",
                )
            )

    return ShiftSchedule(employees=employees, shifts=shifts)