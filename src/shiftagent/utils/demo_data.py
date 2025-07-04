"""
Demo data generation for testing - Logistics Warehouse
"""

from datetime import datetime, timedelta

from ..core.models import Employee, Shift, ShiftSchedule


def get_next_monday() -> datetime:
    """Get the next Monday from today (or today if it's Monday)"""
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7

    # If it's Monday and already past 6 PM, use next Monday instead
    if days_until_monday == 0 and today.hour >= 18:
        days_until_monday = 7

    next_monday = today + timedelta(days=days_until_monday)
    # Normalize to start of day at 9 AM
    return next_monday.replace(hour=9, minute=0, second=0, microsecond=0)


def create_demo_schedule() -> ShiftSchedule:
    """Create a logistics warehouse shift schedule"""
    # Get next Monday as the start date for demo data
    monday = get_next_monday()
    friday_date = monday + timedelta(days=4)

    # Create warehouse workers (including employment type and preferences)
    employees = [
        Employee(
            "emp1",
            "田中太郎",
            {"フォークリフト", "検品", "正社員"},
            preferred_days_off={"friday", "saturday"},  # Prefers weekends off
            preferred_work_days={"monday", "tuesday"},
        ),
        Employee(
            "emp2",
            "佐藤花子",
            {"ピッキング", "梱包", "正社員"},
            preferred_work_days={"sunday", "saturday"},  # Prefers weekend work
            unavailable_dates={friday_date},  # Unavailable on specific Friday
        ),
        Employee(
            "emp3",
            "鈴木一郎",
            {"フォークリフト", "入庫管理", "正社員"},
            preferred_days_off={"wednesday"},  # Prefers Wednesday off
        ),
        Employee(
            "emp4",
            "山田美咲",
            {"検品", "在庫管理", "パート"},
            preferred_work_days={
                "monday",
                "tuesday",
                "wednesday",
            },  # Prefers weekday work
            preferred_days_off={"saturday", "sunday"},
        ),
        Employee(
            "emp5",
            "高橋健太",
            {"ピッキング", "梱包", "パート"},
            preferred_days_off={
                "thursday",
                "friday",
            },  # Prefers Thursday and Friday off (student)
        ),
        Employee(
            "emp6",
            "伊藤さくら",
            {"出荷管理", "梱包", "正社員"},
            preferred_work_days={"monday", "wednesday", "friday"},
        ),
        Employee(
            "emp7",
            "渡辺大輔",
            {"フォークリフト", "出荷管理", "正社員"},
            preferred_days_off={"sunday", "monday"},  # Prefers Sunday and Monday off
        ),
    ]

    # Create shifts for one week (considering weekly work hours)
    # Starting from Monday

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
        # day_name_jp = [
        #     "月曜",
        #     "火曜",
        #     "水曜",
        #     "木曜",
        #     "金曜",
        #     "土曜",
        #     "日曜",
        # ][day]  # Unused variable, kept for reference

        # Early morning receiving work (6:00-14:00) - 8 hours
        shifts.append(
            Shift(
                id=f"入庫_{day_name}",
                start_time=day_start.replace(hour=6),
                end_time=day_start.replace(hour=14),
                required_skills={"入庫管理", "フォークリフト"},
                location="入庫エリア",
                priority=1,  # High priority
            )
        )

        # Morning picking work (8:00-16:00) - 8 hours
        shifts.append(
            Shift(
                id=f"ピッキング午前_{day_name}",
                start_time=day_start.replace(hour=8),
                end_time=day_start.replace(hour=16),
                required_skills={"ピッキング"},
                location="ピッキングエリア",
                priority=2,
            )
        )

        # Afternoon picking and packaging work (14:00-22:00) - 8 hours
        shifts.append(
            Shift(
                id=f"ピッキング午後_{day_name}",
                start_time=day_start.replace(hour=14),
                end_time=day_start.replace(hour=22),
                required_skills={"ピッキング", "梱包"},
                location="ピッキングエリア",
                priority=2,
            )
        )

        # Shipping work (16:00-24:00) - 8 hours
        if day < 6:  # Except Sunday
            shifts.append(
                Shift(
                    id=f"出荷_{day_name}",
                    start_time=day_start.replace(hour=16),
                    end_time=day_start.replace(hour=23, minute=59),
                    required_skills={"出荷管理", "フォークリフト"},
                    location="出荷エリア",
                    priority=1,  # High priority
                )
            )

        # Inspection work (for part-time workers) (9:00-13:00) - 4 hours
        if day < 5:  # Weekdays only
            shifts.append(
                Shift(
                    id=f"検品午前_{day_name}",
                    start_time=day_start.replace(hour=9),
                    end_time=day_start.replace(hour=13),
                    required_skills={"検品"},
                    location="検品エリア",
                    priority=3,
                )
            )

            # Inventory management work (for part-time workers) (13:00-17:00) - 4 hours
            shifts.append(
                Shift(
                    id=f"在庫管理_{day_name}",
                    start_time=day_start.replace(hour=13),
                    end_time=day_start.replace(hour=17),
                    required_skills={"在庫管理"},
                    location="在庫管理エリア",
                    priority=4,
                )
            )

        # Administrative work (weekdays only) (9:00-18:00) - 9 hours
        if day < 5:  # Weekdays only
            shifts.append(
                Shift(
                    id=f"事務作業_{day_name}",
                    start_time=day_start.replace(hour=9),
                    end_time=day_start.replace(hour=18),
                    required_skills={"正社員"},
                    location="事務所",
                    priority=1,
                )
            )

        # Special Saturday shift (for busy periods)
        if day == 5:  # Saturday
            shifts.append(
                Shift(
                    id=f"土曜特別_{day_name}",
                    start_time=day_start.replace(hour=10),
                    end_time=day_start.replace(hour=18),
                    required_skills={"ピッキング", "梱包"},
                    location="ピッキングエリア",
                    priority=3,
                )
            )

    return ShiftSchedule(employees=employees, shifts=shifts)
