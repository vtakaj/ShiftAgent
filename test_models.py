import pytest
from datetime import datetime, timedelta
from models import Employee, Shift, ShiftSchedule
from constraints import (
    get_week_key, 
    is_full_time_employee, 
    get_target_hours
)


def test_employee_creation():
    """従業員作成のテスト"""
    employee = Employee("emp1", "田中太郎", {"看護師", "CPR"})
    
    assert employee.id == "emp1"
    assert employee.name == "田中太郎"
    assert employee.has_skill("看護師")
    assert employee.has_skill("CPR")
    assert not employee.has_skill("警備員")
    assert employee.has_all_skills({"看護師"})
    assert employee.has_all_skills({"看護師", "CPR"})
    assert not employee.has_all_skills({"看護師", "警備員"})


def test_shift_creation():
    """シフト作成のテスト"""
    start_time = datetime(2025, 6, 1, 9, 0)
    end_time = datetime(2025, 6, 1, 17, 0)
    
    shift = Shift(
        id="shift1",
        start_time=start_time,
        end_time=end_time,
        required_skills={"看護師"},
        location="病院"
    )
    
    assert shift.id == "shift1"
    assert shift.get_duration_minutes() == 480  # 8時間 = 480分
    assert not shift.is_assigned()
    assert shift.location == "病院"


def test_shift_overlap():
    """シフト重複チェックのテスト"""
    shift1 = Shift(
        id="shift1",
        start_time=datetime(2025, 6, 1, 9, 0),
        end_time=datetime(2025, 6, 1, 17, 0),
        required_skills={"看護師"}
    )
    
    # 重複するシフト
    shift2 = Shift(
        id="shift2",
        start_time=datetime(2025, 6, 1, 14, 0),
        end_time=datetime(2025, 6, 1, 22, 0),
        required_skills={"看護師"}
    )
    
    # 重複しないシフト
    shift3 = Shift(
        id="shift3",
        start_time=datetime(2025, 6, 1, 17, 0),
        end_time=datetime(2025, 6, 2, 1, 0),
        required_skills={"看護師"}
    )
    
    assert shift1.overlaps_with(shift2)  # 重複
    assert not shift1.overlaps_with(shift3)  # 重複しない
    assert shift1.overlaps_with(shift1)  # 自分自身とは重複


def test_schedule_creation():
    """スケジュール作成のテスト"""
    employees = [
        Employee("emp1", "田中太郎", {"看護師"}),
        Employee("emp2", "佐藤花子", {"警備員"})
    ]
    
    shifts = [
        Shift("shift1", datetime(2025, 6, 1, 9, 0), datetime(2025, 6, 1, 17, 0), {"看護師"}),
        Shift("shift2", datetime(2025, 6, 1, 22, 0), datetime(2025, 6, 2, 6, 0), {"警備員"})
    ]
    
    schedule = ShiftSchedule(employees, shifts)
    
    assert schedule.get_employee_count() == 2
    assert schedule.get_shift_count() == 2
    assert schedule.get_assigned_shift_count() == 0  # まだ誰も割り当てられていない
    assert schedule.get_unassigned_shift_count() == 2


def test_week_key_generation():
    """週キー生成のテスト"""
    date1 = datetime(2025, 6, 1)  # 日曜日
    date2 = datetime(2025, 6, 2)  # 月曜日
    
    week1 = get_week_key(date1)
    week2 = get_week_key(date2)
    
    assert isinstance(week1, str)
    assert isinstance(week2, str)
    assert "2025-W" in week1
    assert "2025-W" in week2


def test_employee_type_detection():
    """従業員タイプ検出のテスト"""
    full_time_emp = Employee("emp1", "田中太郎", {"看護師", "フルタイム"})
    part_time_emp = Employee("emp2", "佐藤花子", {"受付", "パートタイム"})
    regular_emp = Employee("emp3", "鈴木一郎", {"警備員"})
    
    assert is_full_time_employee(full_time_emp)
    assert not is_full_time_employee(part_time_emp)
    assert not is_full_time_employee(regular_emp)


def test_target_hours_calculation():
    """目標勤務時間計算のテスト"""
    full_time_emp = Employee("emp1", "田中太郎", {"看護師", "フルタイム"})
    part_time_emp = Employee("emp2", "佐藤花子", {"受付", "パートタイム"})
    regular_emp = Employee("emp3", "鈴木一郎", {"警備員"})
    
    assert get_target_hours(full_time_emp) == 40
    assert get_target_hours(part_time_emp) == 20
    assert get_target_hours(regular_emp) == 32


def test_shift_assignment():
    """シフト割り当てのテスト"""
    employee = Employee("emp1", "田中太郎", {"看護師"})
    shift = Shift("shift1", datetime(2025, 6, 1, 9, 0), datetime(2025, 6, 1, 17, 0), {"看護師"})
    
    assert not shift.is_assigned()
    
    shift.employee = employee
    
    assert shift.is_assigned()
    assert shift.employee.name == "田中太郎"


@pytest.fixture
def sample_schedule():
    """テスト用のサンプルスケジュール"""
    employees = [
        Employee("emp1", "田中太郎", {"看護師", "フルタイム"}),
        Employee("emp2", "佐藤花子", {"看護師", "パートタイム"}),
        Employee("emp3", "鈴木一郎", {"警備員", "フルタイム"})
    ]
    
    shifts = [
        Shift("morning1", datetime(2025, 6, 1, 8, 0), datetime(2025, 6, 1, 16, 0), {"看護師"}),
        Shift("evening1", datetime(2025, 6, 1, 16, 0), datetime(2025, 6, 2, 0, 0), {"看護師"}),
        Shift("security1", datetime(2025, 6, 1, 22, 0), datetime(2025, 6, 2, 6, 0), {"警備員"})
    ]
    
    return ShiftSchedule(employees, shifts)


def test_schedule_statistics(sample_schedule):
    """スケジュール統計のテスト"""
    schedule = sample_schedule
    
    assert schedule.get_employee_count() == 3
    assert schedule.get_shift_count() == 3
    assert schedule.get_unassigned_shift_count() == 3
    
    # 1つのシフトを割り当て
    schedule.shifts[0].employee = schedule.employees[0]
    
    assert schedule.get_assigned_shift_count() == 1
    assert schedule.get_unassigned_shift_count() == 2