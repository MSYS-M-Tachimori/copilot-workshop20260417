from __future__ import annotations

from dataclasses import asdict

from pomodoro.domain.clock import Clock
from pomodoro.domain.gamification import compute_gamification_stats
from pomodoro.domain.models import (
    CompleteSessionCommand,
    GamificationStats,
    TodayProgress,
)
from pomodoro.domain.services import SessionRepository


class CompleteSession:
    def __init__(self, repository: SessionRepository) -> None:
        self._repository = repository

    def execute(self, command: CompleteSessionCommand) -> dict:
        record = command.to_record()
        saved = self._repository.save(record)
        return {
            "id": saved.id,
            "session_type": saved.session_type.value,
            "duration_seconds": saved.duration_seconds.value,
            "completed": saved.completed,
        }


class GetTodayProgress:
    def __init__(self, repository: SessionRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self) -> TodayProgress:
        return self._repository.get_today_progress(self._clock.today())


class GetGamificationStats:
    """ゲーミフィケーション（XP / レベル / ストリーク / バッジ / 週間・月間統計）を返すユースケース。"""

    def __init__(self, repository: SessionRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self) -> GamificationStats:
        aggregates = self._repository.get_daily_work_aggregates()
        return compute_gamification_stats(aggregates, self._clock.today())

    def execute_as_dict(self) -> dict:
        """JSON 応答に使いやすい辞書形式で返す。"""
        return asdict(self.execute())
