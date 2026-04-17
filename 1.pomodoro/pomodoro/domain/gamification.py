"""ゲーミフィケーション（XP / レベル / ストリーク / バッジ）の純粋なドメインロジック。

永続化や I/O には依存せず、日別集計（``DailyAggregate``）を入力として
``GamificationStats`` を算出します。テスト容易性のため関数はすべて純粋関数です。
"""
from __future__ import annotations

from datetime import date, timedelta

from pomodoro.domain.models import Badge, DailyAggregate, GamificationStats

# 1 回の作業セッション完了で得られる XP
XP_PER_SESSION = 10

# 1 レベルアップに必要な XP
XP_PER_LEVEL = 100

# ストリーク判定で遡る最大日数（これ以上古いセッションは無視）
MAX_STREAK_LOOKBACK_DAYS = 365


def compute_level(xp: int) -> tuple[int, int, int]:
    """総 XP からレベル情報を算出する。

    戻り値は ``(level, xp_in_level, xp_to_next_level)``。
    level は 1 始まり、xp_in_level は現在レベル内での XP、
    xp_to_next_level は次のレベルまでに必要な残り XP。
    """
    safe_xp = max(0, int(xp))
    level = safe_xp // XP_PER_LEVEL + 1
    xp_in_level = safe_xp % XP_PER_LEVEL
    xp_to_next_level = XP_PER_LEVEL - xp_in_level
    return level, xp_in_level, xp_to_next_level


def compute_streak(aggregates: list[DailyAggregate], today: date) -> int:
    """本日または昨日から遡る「セッションを完了した連続日数」を返す。

    当日のセッションが未完了でも、前日に完了していればストリークは継続中とみなす。
    （1 日の猶予を設けることで、まだ着手前の早朝にストリークがリセット表示されるのを防ぐ）
    """
    active_days = {
        date.fromisoformat(a.date)
        for a in aggregates
        if a.completed_sessions > 0
    }
    if not active_days:
        return 0

    # 本日完了済みなら本日から、そうでなく昨日完了済みなら昨日から数える
    if today in active_days:
        cursor = today
    elif (today - timedelta(days=1)) in active_days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    for _ in range(MAX_STREAK_LOOKBACK_DAYS):
        if cursor in active_days:
            streak += 1
            cursor = cursor - timedelta(days=1)
        else:
            break
    return streak


def _range_aggregates(
    aggregates_by_date: dict[date, DailyAggregate],
    start: date,
    end: date,
) -> list[DailyAggregate]:
    """``start`` から ``end`` まで（両端含む）の日別集計を、空の日も 0 埋めして返す。"""
    result: list[DailyAggregate] = []
    cursor = start
    while cursor <= end:
        key = cursor
        if key in aggregates_by_date:
            agg = aggregates_by_date[key]
            result.append(agg)
        else:
            result.append(
                DailyAggregate(
                    date=cursor.isoformat(),
                    completed_sessions=0,
                    focused_seconds=0,
                )
            )
        cursor = cursor + timedelta(days=1)
    return result


def _sum_sessions(aggs: list[DailyAggregate]) -> tuple[int, int]:
    total_sessions = sum(a.completed_sessions for a in aggs)
    total_focused = sum(a.focused_seconds for a in aggs)
    return total_sessions, total_focused


def compute_badges(
    total_sessions: int,
    streak_days: int,
    weekly_total_sessions: int,
    monthly_total_sessions: int,
    level: int,
) -> list[Badge]:
    """達成状況に応じたバッジ一覧（未獲得も含む）を返す。

    バッジ定義を一箇所に集約することでフロントエンドへ渡す形式の一貫性を保つ。
    """
    definitions: list[tuple[str, str, str, bool]] = [
        (
            "first_session",
            "はじめの一歩",
            "初めてのポモドーロを完了",
            total_sessions >= 1,
        ),
        (
            "streak_3",
            "3日連続",
            "3 日連続で作業セッションを完了",
            streak_days >= 3,
        ),
        (
            "streak_7",
            "週間継続",
            "7 日連続で作業セッションを完了",
            streak_days >= 7,
        ),
        (
            "weekly_10",
            "今週10回完了",
            "直近 7 日間で 10 セッション以上完了",
            weekly_total_sessions >= 10,
        ),
        (
            "monthly_30",
            "今月30回完了",
            "直近 30 日間で 30 セッション以上完了",
            monthly_total_sessions >= 30,
        ),
        (
            "level_5",
            "レベル5到達",
            "レベル 5 に到達",
            level >= 5,
        ),
    ]
    return [
        Badge(id=bid, name=name, description=desc, achieved=achieved)
        for bid, name, desc, achieved in definitions
    ]


def compute_gamification_stats(
    aggregates: list[DailyAggregate],
    today: date,
) -> GamificationStats:
    """全日別集計を元に ``GamificationStats`` を組み立てる純粋関数。"""
    aggregates_by_date: dict[date, DailyAggregate] = {}
    for a in aggregates:
        aggregates_by_date[date.fromisoformat(a.date)] = a

    total_sessions, total_focused_seconds = _sum_sessions(aggregates)

    xp = total_sessions * XP_PER_SESSION
    level, xp_in_level, xp_to_next_level = compute_level(xp)

    streak_days = compute_streak(aggregates, today)

    weekly = _range_aggregates(
        aggregates_by_date, today - timedelta(days=6), today
    )
    monthly = _range_aggregates(
        aggregates_by_date, today - timedelta(days=29), today
    )

    weekly_total_sessions, weekly_total_focused_seconds = _sum_sessions(weekly)
    monthly_total_sessions, monthly_total_focused_seconds = _sum_sessions(monthly)

    badges = compute_badges(
        total_sessions=total_sessions,
        streak_days=streak_days,
        weekly_total_sessions=weekly_total_sessions,
        monthly_total_sessions=monthly_total_sessions,
        level=level,
    )

    return GamificationStats(
        xp=xp,
        level=level,
        xp_in_level=xp_in_level,
        xp_to_next_level=xp_to_next_level,
        streak_days=streak_days,
        total_sessions=total_sessions,
        total_focused_seconds=total_focused_seconds,
        weekly=weekly,
        monthly=monthly,
        weekly_total_sessions=weekly_total_sessions,
        weekly_total_focused_seconds=weekly_total_focused_seconds,
        monthly_total_sessions=monthly_total_sessions,
        monthly_total_focused_seconds=monthly_total_focused_seconds,
        badges=badges,
    )
