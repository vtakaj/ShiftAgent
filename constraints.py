from datetime import datetime, timedelta

from timefold.solver.score import (
    Constraint,
    ConstraintCollectors,
    ConstraintFactory,
    HardMediumSoftScore,
    Joiners,
    constraint_provider,
)

from models import Employee, Shift, ShiftSchedule


@constraint_provider
def shift_scheduling_constraints(
    constraint_factory: ConstraintFactory,
) -> list[Constraint]:
    """シフトスケジューリングの制約を定義"""
    return [
        # ハード制約（絶対に守る必要がある）
        required_skill_constraint(constraint_factory),
        no_overlapping_shifts_constraint(constraint_factory),
        weekly_maximum_hours_constraint(constraint_factory),
        # ミディアム制約（重要だが、ある程度の違反は許容）
        minimum_rest_time_constraint(constraint_factory),
        weekly_minimum_hours_constraint(constraint_factory),
        # ソフト制約（最適化目標）
        minimize_unassigned_shifts_constraint(constraint_factory),
        fair_workload_distribution_constraint(constraint_factory),
        weekly_hours_target_constraint(constraint_factory),
    ]


def required_skill_constraint(constraint_factory: ConstraintFactory) -> Constraint:
    """必要なスキルを持つ従業員のみがシフトに割り当てられる"""
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
    """従業員は同時に複数のシフトに割り当てられない"""
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
    """最低休憩時間の確保（8時間）"""
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
    """未割り当てシフトを最小化（優先度を考慮）"""
    return (
        constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is None)
        .penalize(HardMediumSoftScore.of_soft(1), lambda shift: shift.priority * 10)
        .as_constraint("Minimize unassigned shifts")
    )


def fair_workload_distribution_constraint(constraint_factory: ConstraintFactory):
    """公平な労働時間配分（8時間からの差を最小化）"""
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
        )  # 8時間 = 480分
        .as_constraint("Fair workload distribution")
    )


def weekly_maximum_hours_constraint(constraint_factory: ConstraintFactory):
    """週最大勤務時間制約（法定40時間）- ハード制約"""
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
        )  # 45時間超過で違反
        .penalize(
            HardMediumSoftScore.ONE_HARD,
            lambda employee, week, total_minutes: (total_minutes - 45 * 60) // 60,
        )
        .as_constraint("Weekly maximum hours constraint")
    )


def weekly_minimum_hours_constraint(constraint_factory: ConstraintFactory):
    """週最小勤務時間制約（フルタイム従業員）"""
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
        )  # 32時間未満
        .penalize(
            HardMediumSoftScore.ONE_MEDIUM,
            lambda employee, week, total_minutes: (32 * 60 - total_minutes) // 60,
        )
        .as_constraint("Weekly minimum hours constraint")
    )


def weekly_hours_target_constraint(constraint_factory: ConstraintFactory):
    """週勤務時間目標制約（ソフト制約）"""
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


# ヘルパー関数
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
