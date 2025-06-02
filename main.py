from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import uuid
import asyncio
from datetime import datetime, timedelta
import threading
import time

from timefold.solver import SolverFactory
from timefold.solver.config import SolverConfig, TerminationConfig, ScoreDirectorFactoryConfig, Duration
from models import (
    Employee, Shift, ShiftSchedule,
    EmployeeRequest, ShiftRequest, ShiftScheduleRequest,
    SolveResponse, SolutionResponse
)
from constraints import shift_scheduling_constraints

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Shift Scheduler API",
    description="Timefold Solverを使ったシフト作成API",
    version="1.0.0"
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
    termination_config=TerminationConfig(
        spent_limit=Duration(seconds=30)
    )
)

solver_factory = SolverFactory.create(solver_config)

# ジョブ管理用の辞書
jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def convert_request_to_domain(request: ShiftScheduleRequest) -> ShiftSchedule:
    """APIリクエストをドメインオブジェクトに変換"""
    # 従業員の変換
    employees = [
        Employee(
            id=emp.id,
            name=emp.name,
            skills=set(emp.skills)
        )
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
            priority=shift.priority
        )
        for shift in request.shifts
    ]
    
    return ShiftSchedule(employees=employees, shifts=shifts)


def convert_domain_to_response(schedule: ShiftSchedule) -> Dict[str, Any]:
    """ドメインオブジェクトをAPIレスポンスに変換"""
    return {
        "employees": [
            {
                "id": emp.id,
                "name": emp.name,
                "skills": list(emp.skills)
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
                "employee": {
                    "id": shift.employee.id,
                    "name": shift.employee.name
                } if shift.employee else None
            }
            for shift in schedule.shifts
        ],
        "statistics": {
            "total_employees": schedule.get_employee_count(),
            "total_shifts": schedule.get_shift_count(),
            "assigned_shifts": schedule.get_assigned_shift_count(),
            "unassigned_shifts": schedule.get_unassigned_shift_count()
        }
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
    return {
        "message": "Shift Scheduler API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "UP",
        "service": "shift-scheduler",
        "timestamp": datetime.now().isoformat()
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
            "problem": problem
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
        
        response = SolutionResponse(
            job_id=job_id,
            status=job["status"]
        )
        
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
        Employee("emp5", "山田次郎", {"看護師", "パートタイム"})
    ]
    
    # 1週間分のシフトを作成（週勤務時間を考慮）
    base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    # 月曜日から開始
    monday = base_date - timedelta(days=base_date.weekday())
    
    shifts = []
    
    for day in range(7):  # 1週間
        day_start = monday + timedelta(days=day)
        day_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][day]
        
        # 朝シフト (8:00-16:00) - 8時間
        shifts.append(Shift(
            id=f"morning_{day_name}",
            start_time=day_start.replace(hour=8),
            end_time=day_start.replace(hour=16),
            required_skills={"看護師"},
            location="病院"
        ))
        
        # 夜シフト (16:00-24:00) - 8時間
        shifts.append(Shift(
            id=f"evening_{day_name}",
            start_time=day_start.replace(hour=16),
            end_time=day_start.replace(hour=23, minute=59),
            required_skills={"看護師"},
            location="病院"
        ))
        
        # 夜間警備 (22:00-06:00) - 8時間
        if day < 6:  # 日曜以外
            shifts.append(Shift(
                id=f"security_{day_name}",
                start_time=day_start.replace(hour=22),
                end_time=(day_start + timedelta(days=1)).replace(hour=6),
                required_skills={"警備員"},
                location="病院"
            ))
        
        # 受付シフト (9:00-13:00) - 4時間（パートタイム向け）
        if day < 5:  # 平日のみ
            shifts.append(Shift(
                id=f"reception_morning_{day_name}",
                start_time=day_start.replace(hour=9),
                end_time=day_start.replace(hour=13),
                required_skills={"受付"},
                location="受付"
            ))
            
            shifts.append(Shift(
                id=f"reception_afternoon_{day_name}",
                start_time=day_start.replace(hour=13),
                end_time=day_start.replace(hour=17),
                required_skills={"受付"},
                location="受付"
            ))
    
    return ShiftSchedule(employees=employees, shifts=shifts)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
