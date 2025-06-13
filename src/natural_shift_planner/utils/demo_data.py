"""
Demo data generation for testing - Logistics Warehouse
物流倉庫用のデモデータ生成
"""

from datetime import datetime, timedelta

from ..core.models import Employee, Shift, ShiftSchedule


def create_demo_schedule() -> ShiftSchedule:
    """物流倉庫のシフトスケジュールを作成"""
    # Get specific dates for unavailable examples
    base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    monday = base_date - timedelta(days=base_date.weekday())
    friday_date = monday + timedelta(days=4)

    # 倉庫作業員の作成 (雇用形態と希望を含む)
    employees = [
        Employee(
            "emp1",
            "田中太郎",
            {"フォークリフト", "検品", "正社員"},
            preferred_days_off={"friday", "saturday"},  # 週末休み希望
            preferred_work_days={"monday", "tuesday"},
        ),
        Employee(
            "emp2",
            "佐藤花子",
            {"ピッキング", "梱包", "正社員"},
            preferred_work_days={"sunday", "saturday"},  # 週末勤務希望
            unavailable_dates={friday_date},  # 特定の金曜日は不可
        ),
        Employee(
            "emp3",
            "鈴木一郎",
            {"フォークリフト", "入庫管理", "正社員"},
            preferred_days_off={"wednesday"},  # 水曜日休み希望
        ),
        Employee(
            "emp4",
            "山田美咲",
            {"検品", "在庫管理", "パート"},
            preferred_work_days={"monday", "tuesday", "wednesday"},  # 平日勤務希望
            preferred_days_off={"saturday", "sunday"},
        ),
        Employee(
            "emp5",
            "高橋健太",
            {"ピッキング", "梱包", "パート"},
            preferred_days_off={
                "thursday",
                "friday",
            },  # 木・金休み希望（学生）
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
            preferred_days_off={"sunday", "monday"},  # 日・月休み希望
        ),
    ]

    # 一週間分のシフトを作成（週間労働時間を考慮）
    # 月曜日から開始

    shifts = []

    for day in range(7):  # 一週間
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

        # 早朝入庫作業 (6:00-14:00) - 8時間
        shifts.append(
            Shift(
                id=f"入庫_{day_name}",
                start_time=day_start.replace(hour=6),
                end_time=day_start.replace(hour=14),
                required_skills={"入庫管理", "フォークリフト"},
                location="入庫エリア",
                priority=1,  # 高優先度
            )
        )

        # 午前ピッキング作業 (8:00-16:00) - 8時間
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

        # 午後ピッキング・梱包作業 (14:00-22:00) - 8時間
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

        # 出荷作業 (16:00-24:00) - 8時間
        if day < 6:  # 日曜日以外
            shifts.append(
                Shift(
                    id=f"出荷_{day_name}",
                    start_time=day_start.replace(hour=16),
                    end_time=day_start.replace(hour=23, minute=59),
                    required_skills={"出荷管理", "フォークリフト"},
                    location="出荷エリア",
                    priority=1,  # 高優先度
                )
            )

        # 検品作業（パートタイム向け）(9:00-13:00) - 4時間
        if day < 5:  # 平日のみ
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

            # 在庫管理作業（パートタイム向け）(13:00-17:00) - 4時間
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

        # 事務作業（平日のみ）(9:00-18:00) - 9時間
        if day < 5:  # 平日のみ
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

        # 土曜日の特別シフト（繁忙期対応）
        if day == 5:  # 土曜日
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
