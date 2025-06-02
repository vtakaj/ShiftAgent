import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)

from constraints import shift_scheduling_constraints
from models import (
    Employee,
    EmployeeRequest,
    Shift,
    ShiftRequest,
    ShiftSchedule,
    ShiftScheduleRequest,
    SolutionResponse,
    SolveResponse,
)

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Shift Scheduler API",
    description="Timefold Solverを使ったシフト作成API",
    version="1.0.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ソルバーの設定
solver_config = SolverConfig(
    solution_class=ShiftSchedule,
    entity_class_list=[Shift],
    score_director_factory_config=ScoreDirectorFactoryConfig(
        constraint_provider_function=shift_scheduling_constraints
    ),
    termination_config=TerminationConfig(spent_limit=Duration(seconds=30)),
)

solver_factory = SolverFactory.create(solver_config)

# ジョブ管理用の辞書
jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def convert_request_to_domain(request: ShiftScheduleRequest) -> ShiftSchedule:
    """APIリクエストをドメインオブジェクトに変換"""
    # 従業員の変換
    employees = [
        Employee(id=emp.id, name=emp.name, skills=set(emp.skills))
        for emp in request.employees
    ]

    # シフトの変換
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


def convert_domain_to_response(schedule: ShiftSchedule) -> Dict[str, Any]:
    """ドメインオブジェクトをAPIレスポンスに変換"""
    return {
        "employees": [
            {"id": emp.id, "name": emp.name, "skills": list(emp.skills)}
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


def solve_problem_async(job_id: str, problem: ShiftSchedule):
    """非同期でシフト最適化を実行"""
    try:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_ACTIVE"

        solver = solver_factory.build_solver()
        solution = solver.solve(problem)

        with job_lock:
            jobs[job_id]["status"] = "SOLVING_COMPLETED"
            jobs[job_id]["solution"] = solution
            jobs[job_id]["completed_at"] = datetime.now()

    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "SOLVING_FAILED"
            jobs[job_id]["error"] = str(e)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "Shift Scheduler API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "UP",
        "service": "shift-scheduler",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/shifts/demo")
async def get_demo_data():
    """デモデータの取得"""
    schedule = create_demo_schedule()
    return convert_domain_to_response(schedule)


@app.post("/api/shifts/solve", response_model=SolveResponse)
async def solve_shifts(request: ShiftScheduleRequest):
    """シフト最適化（非同期）"""
    job_id = str(uuid.uuid4())
    problem = convert_request_to_domain(request)

    # ジョブを登録
    with job_lock:
        jobs[job_id] = {
            "status": "SOLVING_SCHEDULED",
            "created_at": datetime.now(),
            "problem": problem,
        }

    # 非同期で最適化を開始
    thread = threading.Thread(target=solve_problem_async, args=(job_id, problem))
    thread.daemon = True
    thread.start()

    return SolveResponse(job_id=job_id, status="SOLVING_SCHEDULED")


@app.get("/api/shifts/solve/{job_id}", response_model=SolutionResponse)
async def get_solution(job_id: str):
    """最適化結果の取得"""
    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]

        response = SolutionResponse(job_id=job_id, status=job["status"])

        if job["status"] == "SOLVING_COMPLETED":
            solution = job["solution"]
            response.solution = convert_domain_to_response(solution)
            response.score = str(solution.score)
            response.assigned_shifts = solution.get_assigned_shift_count()
            response.unassigned_shifts = solution.get_unassigned_shift_count()
        elif job["status"] == "SOLVING_FAILED":
            response.message = job.get("error", "Unknown error occurred")

        return response


@app.post("/api/shifts/solve-sync")
async def solve_shifts_sync(request: ShiftScheduleRequest):
    """シフト最適化（同期）"""
    try:
        problem = convert_request_to_domain(request)
        solver = solver_factory.build_solver()
        solution = solver.solve(problem)

        return convert_domain_to_response(solution)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_demo_schedule() -> ShiftSchedule:
    """デモ用のシフトスケジュールを作成"""
    # 従業員の作成（雇用形態を明示）
    employees = [
        Employee("emp1", "田中太郎", {"看護師", "CPR", "フルタイム"}),
        Employee("emp2", "佐藤花子", {"看護師", "フルタイム"}),
        Employee("emp3", "鈴木一郎", {"警備員", "フルタイム"}),
        Employee("emp4", "高橋美咲", {"受付", "事務", "パートタイム"}),
        Employee("emp5", "山田次郎", {"看護師", "パートタイム"}),
    ]

    # 1週間分のシフトを作成（週勤務時間を考慮）
    base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    # 月曜日から開始
    monday = base_date - timedelta(days=base_date.weekday())

    shifts = []

    for day in range(7):  # 1週間
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

        # 朝シフト (8:00-16:00) - 8時間
        shifts.append(
            Shift(
                id=f"morning_{day_name}",
                start_time=day_start.replace(hour=8),
                end_time=day_start.replace(hour=16),
                required_skills={"看護師"},
                location="病院",
            )
        )

        # 夜シフト (16:00-24:00) - 8時間
        shifts.append(
            Shift(
                id=f"evening_{day_name}",
                start_time=day_start.replace(hour=16),
                end_time=day_start.replace(hour=23, minute=59),
                required_skills={"看護師"},
                location="病院",
            )
        )

        # 夜間警備 (22:00-06:00) - 8時間
        if day < 6:  # 日曜以外
            shifts.append(
                Shift(
                    id=f"security_{day_name}",
                    start_time=day_start.replace(hour=22),
                    end_time=(day_start + timedelta(days=1)).replace(hour=6),
                    required_skills={"警備員"},
                    location="病院",
                )
            )

        # 受付シフト (9:00-13:00) - 4時間（パートタイム向け）
        if day < 5:  # 平日のみ
            shifts.append(
                Shift(
                    id=f"reception_morning_{day_name}",
                    start_time=day_start.replace(hour=9),
                    end_time=day_start.replace(hour=13),
                    required_skills={"受付"},
                    location="受付",
                )
            )

            shifts.append(
                Shift(
                    id=f"reception_afternoon_{day_name}",
                    start_time=day_start.replace(hour=13),
                    end_time=day_start.replace(hour=17),
                    required_skills={"受付"},
                    location="受付",
                )
            )

    return ShiftSchedule(employees=employees, shifts=shifts)


# 週勤務時間分析のヘルパー関数
def get_week_key(date: datetime) -> str:
    """日付から週キー（年-週番号）を生成"""
    year, week_num, _ = date.isocalendar()
    return f"{year}-W{week_num:02d}"


def is_full_time_employee(employee: Employee) -> bool:
    """フルタイム従業員かどうかの判定"""
    return "フルタイム" in employee.skills or "正社員" in employee.skills


def get_target_hours(employee: Employee) -> int:
    """従業員の目標勤務時間を取得"""
    if "パートタイム" in employee.skills:
        return 20  # パートタイム: 20時間/週
    elif "フルタイム" in employee.skills or "正社員" in employee.skills:
        return 40  # フルタイム: 40時間/週
    else:
        return 32  # デフォルト: 32時間/週


@app.get("/api/shifts/weekly-analysis/{job_id}")
async def get_weekly_analysis(job_id: str):
    """週勤務時間の詳細分析"""
    with job_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = jobs[job_id]
        if job["status"] != "SOLVING_COMPLETED":
            raise HTTPException(status_code=400, detail="Job not completed")

        solution = job["solution"]
        analysis = analyze_weekly_hours(solution)

        return analysis


@app.post("/api/shifts/analyze-weekly")
async def analyze_weekly_hours_sync(request: ShiftScheduleRequest):
    """週勤務時間の即座分析（最適化なし）"""
    try:
        schedule = convert_request_to_domain(request)
        analysis = analyze_weekly_hours(schedule)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def analyze_weekly_hours(schedule: ShiftSchedule) -> Dict[str, Any]:
    """週勤務時間の詳細分析"""

    # 週別勤務時間の集計
    weekly_hours_by_employee = {}
    week_summary = {}

    for shift in schedule.shifts:
        if shift.employee is None:
            continue

        emp_id = shift.employee.id
        week_key = get_week_key(shift.start_time)
        duration_minutes = shift.get_duration_minutes()

        # 従業員別集計
        if emp_id not in weekly_hours_by_employee:
            weekly_hours_by_employee[emp_id] = {}

        if week_key not in weekly_hours_by_employee[emp_id]:
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

        # 週別サマリー
        if week_key not in week_summary:
            week_summary[week_key] = {
                "total_shifts": 0,
                "assigned_shifts": 0,
                "total_hours": 0,
                "employees": set(),
            }

        week_summary[week_key]["total_shifts"] += 1
        week_summary[week_key]["assigned_shifts"] += 1
        week_summary[week_key]["total_hours"] += duration_minutes / 60
        week_summary[week_key]["employees"].add(emp_id)

    # 未割り当てシフトも集計
    for shift in schedule.shifts:
        if shift.employee is None:
            week_key = get_week_key(shift.start_time)
            if week_key in week_summary:
                week_summary[week_key]["total_shifts"] += 1

    # 分析結果の生成
    analysis = {
        "by_employee": {},
        "by_week": {},
        "violations": {
            "overtime": [],  # 45時間超過（ハード制約違反）
            "excessive_hours": [],  # 40時間超過（残業）
            "undertime": [],  # 勤務時間不足
            "target_deviation": [],  # 目標からの大幅乖離
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

    # 従業員別詳細分析
    for employee in schedule.employees:
        emp_id = employee.id
        employee_analysis = {
            "name": employee.name,
            "employment_type": (
                "フルタイム" if is_full_time_employee(employee) else "パートタイム"
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

                # 制約違反チェック
                if hours > 45:  # ハード制約違反
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

                elif hours > 40:  # 残業
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

                if is_full_time_employee(employee) and hours < 32:  # 勤務時間不足
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

                if abs(hours - target) > 5:  # 目標から5時間以上の乖離
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

                # 統計情報更新
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

    # 週別サマリー
    for week_key, summary in week_summary.items():
        analysis["by_week"][week_key] = {
            "total_shifts": summary["total_shifts"],
            "assigned_shifts": summary["assigned_shifts"],
            "unassigned_shifts": summary["total_shifts"] - summary["assigned_shifts"],
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

    # 統計情報の完成
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


@app.get("/api/shifts/test-weekly")
async def test_weekly_constraints():
    """週勤務時間制約のテスト"""
    schedule = create_demo_schedule()
    analysis = analyze_weekly_hours(schedule)

    return {
        "demo_schedule": convert_domain_to_response(schedule),
        "weekly_analysis": analysis,
        "summary": {
            "total_violations": (
                len(analysis["violations"]["overtime"])
                + len(analysis["violations"]["excessive_hours"])
                + len(analysis["violations"]["undertime"])
                + len(analysis["violations"]["target_deviation"])
            ),
            "compliance_rate": analysis["statistics"]["compliance_rate"],
            "recommendations": generate_recommendations(analysis),
        },
    }


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """分析結果に基づく改善提案"""
    recommendations = []

    if analysis["violations"]["overtime"]:
        recommendations.append(
            f"⚠️ {len(analysis['violations']['overtime'])}件の重大な労働時間違反があります。"
            "追加スタッフの採用を検討してください。"
        )

    if analysis["violations"]["excessive_hours"]:
        recommendations.append(
            f"🔶 {len(analysis['violations']['excessive_hours'])}件の残業があります。"
            "シフトの再配分を検討してください。"
        )

    if analysis["violations"]["undertime"]:
        recommendations.append(
            f"📉 {len(analysis['violations']['undertime'])}件の勤務時間不足があります。"
            "フルタイム従業員のシフトを増やすか、追加業務を割り当ててください。"
        )

    if analysis["statistics"]["compliance_rate"] < 80:
        recommendations.append(
            f"📊 コンプライアンス率が{analysis['statistics']['compliance_rate']}%と低いです。"
            "制約設定の見直しやスタッフ配置の最適化が必要です。"
        )

    if not recommendations:
        recommendations.append("✅ 週勤務時間の制約は適切に管理されています。")

    return recommendations


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
