"""
Weekly working hours analysis functions
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

from ..core.models import Employee, ShiftSchedule


def get_week_key(date: datetime) -> str:
    """Generate week key (year-week number) from date"""
    year, week_num, _ = date.isocalendar()
    return f"{year}-W{week_num:02d}"


def is_full_time_employee(employee: Employee) -> bool:
    """Check if employee is full-time"""
    return "Full-time" in employee.skills or "Full-time" in employee.skills


def get_target_hours(employee: Employee) -> int:
    """Get employee's target working hours"""
    if "Part-time" in employee.skills:
        return 20  # Part-time: 20 hours/week
    elif "Full-time" in employee.skills or "Full-time" in employee.skills:
        return 40  # Full-time: 40 hours/week
    else:
        return 32  # Default: 32 hours/week


def analyze_weekly_hours(schedule: ShiftSchedule) -> dict[str, Any]:
    """Detailed analysis of weekly working hours"""

    # Aggregate weekly working hours
    weekly_hours_by_employee: dict[str, dict[str, Any]] = defaultdict(dict)
    week_summary: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "total_shifts": 0,
        "assigned_shifts": 0,
        "total_hours": 0.0,
        "employees": set(),
    })

    for shift in schedule.shifts:
        if shift.employee is None:
            continue

        emp_id = shift.employee.id
        week_key = get_week_key(shift.start_time)
        duration_minutes = shift.get_duration_minutes()

        # Aggregate by employee
        # defaultdict will auto-create nested structure
        if "total_minutes" not in weekly_hours_by_employee[emp_id][week_key]:
            weekly_hours_by_employee[emp_id][week_key] = {
                "total_minutes": 0,
                "shift_count": 0,
                "shifts": [],
            }

        weekly_hours_by_employee[emp_id][week_key]["total_minutes"] += duration_minutes
        weekly_hours_by_employee[emp_id][week_key]["shift_count"] += 1
        weekly_hours_by_employee[emp_id][week_key]["shifts"].append(
            {
                "id": shift.id,
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat(),
                "duration_hours": duration_minutes / 60,
                "location": shift.location,
            }
        )

        # Weekly summary (defaultdict will auto-create)

        week_summary[week_key]["total_shifts"] += 1
        week_summary[week_key]["assigned_shifts"] += 1
        week_summary[week_key]["total_hours"] += duration_minutes / 60
        week_summary[week_key]["employees"].add(emp_id)

    # Count unassigned shifts
    for shift in schedule.shifts:
        if shift.employee is None:
            week_key = get_week_key(shift.start_time)
            if week_key in week_summary:
                week_summary[week_key]["total_shifts"] += 1

    # Generate analysis results
    analysis = {
        "by_employee": {},
        "by_week": {},
        "violations": {
            "overtime": [],  # Over 45 hours (hard constraint violation)
            "excessive_hours": [],  # Over 40 hours (overtime)
            "undertime": [],  # Insufficient working hours
            "target_deviation": [],  # Significant deviation from target
        },
        "statistics": {
            "total_employees": len(schedule.employees),
            "weeks_analyzed": len(week_summary),
            "average_weekly_hours": 0,
            "max_weekly_hours": 0,
            "min_weekly_hours": float("inf"),
            "compliance_rate": 0,
        },
    }

    total_hours = 0
    total_employee_weeks = 0
    compliant_weeks = 0

    # Detailed analysis by employee
    for employee in schedule.employees:
        emp_id = employee.id
        employee_analysis: dict[str, Any] = {
            "name": employee.name,
            "employment_type": (
                "Full-time" if is_full_time_employee(employee) else "Part-time"
            ),
            "target_hours": get_target_hours(employee),
            "weeks": {},
        }

        if emp_id in weekly_hours_by_employee:
            for week_key, week_data in weekly_hours_by_employee[emp_id].items():
                hours = week_data["total_minutes"] / 60
                target = get_target_hours(employee)

                week_analysis = {
                    "hours": round(hours, 1),
                    "target": target,
                    "deviation": round(hours - target, 1),
                    "shift_count": week_data["shift_count"],
                    "shifts": week_data["shifts"],
                    "status": "compliant",
                }

                # Constraint violation checks
                if hours > 45:  # Hard constraint violation
                    analysis["violations"]["overtime"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "overtime": round(hours - 45, 1),
                            "severity": "critical",
                        }
                    )
                    week_analysis["status"] = "overtime_violation"

                elif hours > 40:  # Overtime
                    analysis["violations"]["excessive_hours"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "overtime": round(hours - 40, 1),
                            "severity": "warning",
                        }
                    )
                    week_analysis["status"] = "overtime"

                if is_full_time_employee(employee) and hours < 32:  # Insufficient hours
                    analysis["violations"]["undertime"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "shortage": round(32 - hours, 1),
                            "severity": "warning",
                        }
                    )
                    if week_analysis["status"] == "compliant":
                        week_analysis["status"] = "undertime"

                if abs(hours - target) > 5:  # More than 5 hours deviation from target
                    analysis["violations"]["target_deviation"].append(
                        {
                            "employee_id": emp_id,
                            "employee_name": employee.name,
                            "week": week_key,
                            "hours": round(hours, 1),
                            "target": target,
                            "deviation": round(hours - target, 1),
                            "severity": "info",
                        }
                    )

                # Update statistics
                total_hours += hours
                total_employee_weeks += 1
                if week_analysis["status"] == "compliant":
                    compliant_weeks += 1

                analysis["statistics"]["max_weekly_hours"] = max(
                    analysis["statistics"]["max_weekly_hours"], hours
                )
                analysis["statistics"]["min_weekly_hours"] = min(
                    analysis["statistics"]["min_weekly_hours"], hours
                )

                employee_analysis["weeks"][week_key] = week_analysis

        analysis["by_employee"][emp_id] = employee_analysis

    # Weekly summary
    for week_key, summary in week_summary.items():
        analysis["by_week"][week_key] = {
            "total_shifts": summary["total_shifts"],
            "assigned_shifts": summary["assigned_shifts"],
            "unassigned_shifts": (summary["total_shifts"] - summary["assigned_shifts"]),
            "total_hours": round(summary["total_hours"], 1),
            "active_employees": len(summary["employees"]),
            "average_hours_per_employee": round(
                (
                    summary["total_hours"] / len(summary["employees"])
                    if summary["employees"]
                    else 0
                ),
                1,
            ),
        }

    # Complete statistics
    if total_employee_weeks > 0:
        analysis["statistics"]["average_weekly_hours"] = round(
            total_hours / total_employee_weeks, 1
        )
        analysis["statistics"]["compliance_rate"] = round(
            compliant_weeks / total_employee_weeks * 100, 1
        )

    if analysis["statistics"]["min_weekly_hours"] == float("inf"):
        analysis["statistics"]["min_weekly_hours"] = 0
    else:
        analysis["statistics"]["min_weekly_hours"] = round(
            analysis["statistics"]["min_weekly_hours"], 1
        )

    analysis["statistics"]["max_weekly_hours"] = round(
        analysis["statistics"]["max_weekly_hours"], 1
    )

    return analysis


def generate_recommendations(analysis: dict[str, Any]) -> list[str]:
    """Generate improvement recommendations based on analysis"""
    recommendations = []

    if analysis["violations"]["overtime"]:
        recommendations.append(
            f"⚠️ {len(analysis['violations']['overtime'])} "
            "critical working hours violations. "
            "Consider hiring additional staff."
        )

    if analysis["violations"]["excessive_hours"]:
        recommendations.append(
            f"🔶 {len(analysis['violations']['excessive_hours'])} "
            "overtime cases. "
            "Consider redistributing shifts."
        )

    if analysis["violations"]["undertime"]:
        recommendations.append(
            f"📉 {len(analysis['violations']['undertime'])} "
            "cases of insufficient hours. "
            "Increase shifts for full-time employees or "
            "assign additional tasks."
        )

    if analysis["statistics"]["compliance_rate"] < 80:
        recommendations.append(
            f"📊 Compliance rate is low at "
            f"{analysis['statistics']['compliance_rate']}%. "
            "Review constraint settings and optimize staff allocation."
        )

    if not recommendations:
        recommendations.append("✅ Weekly working hours constraints are well managed.")

    return recommendations
