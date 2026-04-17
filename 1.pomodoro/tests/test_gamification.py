"""ゲーミフィケーション純粋ロジックの単体テスト。"""
from datetime import date

from pomodoro.domain.gamification import (
    XP_PER_LEVEL,
    XP_PER_SESSION,
    compute_gamification_stats,
    compute_level,
    compute_streak,
)
from pomodoro.domain.models import DailyAggregate


def _agg(day: str, sessions: int, focused: int = 1500) -> DailyAggregate:
    return DailyAggregate(date=day, completed_sessions=sessions, focused_seconds=focused)


class TestComputeLevel:
    def test_zero_xp_is_level_1(self):
        level, in_level, to_next = compute_level(0)
        assert level == 1
        assert in_level == 0
        assert to_next == XP_PER_LEVEL

    def test_xp_below_threshold_stays_level_1(self):
        level, in_level, to_next = compute_level(XP_PER_LEVEL - 10)
        assert level == 1
        assert in_level == XP_PER_LEVEL - 10
        assert to_next == 10

    def test_xp_at_threshold_advances_to_level_2(self):
        level, in_level, to_next = compute_level(XP_PER_LEVEL)
        assert level == 2
        assert in_level == 0
        assert to_next == XP_PER_LEVEL

    def test_negative_xp_is_clamped(self):
        level, in_level, to_next = compute_level(-50)
        assert level == 1
        assert in_level == 0
        assert to_next == XP_PER_LEVEL


class TestComputeStreak:
    def test_empty_aggregates_returns_zero(self):
        assert compute_streak([], date(2026, 4, 17)) == 0

    def test_single_day_today(self):
        aggs = [_agg("2026-04-17", 1)]
        assert compute_streak(aggs, date(2026, 4, 17)) == 1

    def test_three_consecutive_days_including_today(self):
        aggs = [_agg("2026-04-15", 1), _agg("2026-04-16", 2), _agg("2026-04-17", 1)]
        assert compute_streak(aggs, date(2026, 4, 17)) == 3

    def test_broken_streak(self):
        # 4/14 と 4/16, 4/17 がアクティブ。4/15 が抜けているので 4/17 からのストリークは 2
        aggs = [_agg("2026-04-14", 1), _agg("2026-04-16", 1), _agg("2026-04-17", 1)]
        assert compute_streak(aggs, date(2026, 4, 17)) == 2

    def test_continues_from_yesterday_if_today_empty(self):
        aggs = [_agg("2026-04-15", 1), _agg("2026-04-16", 1)]
        # 本日 4/17 は未完了でも、昨日 4/16 に完了していればストリークは継続中
        assert compute_streak(aggs, date(2026, 4, 17)) == 2

    def test_resets_after_two_day_gap(self):
        aggs = [_agg("2026-04-14", 1), _agg("2026-04-15", 1)]
        # 本日 4/17、4/16 と 4/17 両方完了なしならストリーク 0
        assert compute_streak(aggs, date(2026, 4, 17)) == 0

    def test_ignores_days_with_zero_sessions(self):
        aggs = [_agg("2026-04-17", 0)]
        assert compute_streak(aggs, date(2026, 4, 17)) == 0


class TestComputeGamificationStats:
    def test_empty_returns_zero_stats(self):
        stats = compute_gamification_stats([], date(2026, 4, 17))
        assert stats.xp == 0
        assert stats.level == 1
        assert stats.streak_days == 0
        assert stats.total_sessions == 0
        assert stats.total_focused_seconds == 0
        assert len(stats.weekly) == 7
        assert len(stats.monthly) == 30
        assert stats.weekly_total_sessions == 0
        assert stats.monthly_total_sessions == 0
        # 全バッジが未獲得
        assert all(not b.achieved for b in stats.badges)

    def test_xp_scales_with_total_sessions(self):
        aggs = [_agg("2026-04-10", 3, 4500), _agg("2026-04-17", 2, 3000)]
        stats = compute_gamification_stats(aggs, date(2026, 4, 17))
        assert stats.total_sessions == 5
        assert stats.xp == 5 * XP_PER_SESSION
        assert stats.total_focused_seconds == 7500

    def test_weekly_window_is_seven_days_ending_today(self):
        # 8 日前（範囲外）と 6 日前（範囲内）にセッション
        aggs = [_agg("2026-04-09", 1), _agg("2026-04-11", 2)]
        stats = compute_gamification_stats(aggs, date(2026, 4, 17))
        assert stats.weekly_total_sessions == 2
        assert stats.weekly[0].date == "2026-04-11"
        assert stats.weekly[-1].date == "2026-04-17"

    def test_first_session_badge_awarded(self):
        aggs = [_agg("2026-04-17", 1)]
        stats = compute_gamification_stats(aggs, date(2026, 4, 17))
        badge = next(b for b in stats.badges if b.id == "first_session")
        assert badge.achieved is True

    def test_streak_3_badge_awarded(self):
        aggs = [
            _agg("2026-04-15", 1),
            _agg("2026-04-16", 1),
            _agg("2026-04-17", 1),
        ]
        stats = compute_gamification_stats(aggs, date(2026, 4, 17))
        assert stats.streak_days == 3
        badge = next(b for b in stats.badges if b.id == "streak_3")
        assert badge.achieved is True
        # まだ 7 日連続は未達成
        badge7 = next(b for b in stats.badges if b.id == "streak_7")
        assert badge7.achieved is False

    def test_weekly_10_badge(self):
        aggs = [_agg("2026-04-17", 10, 15000)]
        stats = compute_gamification_stats(aggs, date(2026, 4, 17))
        badge = next(b for b in stats.badges if b.id == "weekly_10")
        assert badge.achieved is True

    def test_level_5_badge_requires_enough_xp(self):
        # レベル 5 には 400 XP 必要 → 40 セッション
        aggs = [_agg("2026-04-17", 40, 60000)]
        stats = compute_gamification_stats(aggs, date(2026, 4, 17))
        assert stats.level >= 5
        badge = next(b for b in stats.badges if b.id == "level_5")
        assert badge.achieved is True
