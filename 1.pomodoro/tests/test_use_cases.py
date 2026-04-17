from datetime import datetime, timezone

from pomodoro.application.use_cases import CompleteSession, GetTodayProgress
from pomodoro.domain.clock import FixedClock
from pomodoro.domain.models import CompleteSessionCommand
from tests.fake_repository import InMemorySessionRepository


def _make_command(session_type: str = "work", duration: int = 1500) -> CompleteSessionCommand:
    return CompleteSessionCommand(
        session_type=session_type,
        started_at="2026-04-17T10:00:00+00:00",
        ended_at="2026-04-17T10:25:00+00:00",
        duration_seconds=duration,
        completed=True,
    )


class TestCompleteSession:
    def test_saves_and_returns_id(self):
        repo = InMemorySessionRepository()
        uc = CompleteSession(repo)
        result = uc.execute(_make_command())
        assert result["id"] == 1
        assert result["session_type"] == "work"
        assert result["duration_seconds"] == 1500
        assert result["completed"] is True

    def test_increments_id(self):
        repo = InMemorySessionRepository()
        uc = CompleteSession(repo)
        uc.execute(_make_command())
        result = uc.execute(_make_command(session_type="break", duration=300))
        assert result["id"] == 2
        assert result["session_type"] == "break"


class TestGetTodayProgress:
    def test_empty(self):
        repo = InMemorySessionRepository()
        clock = FixedClock(datetime(2026, 4, 17, 12, 0, 0, tzinfo=timezone.utc))
        uc = GetTodayProgress(repo, clock)
        progress = uc.execute()
        assert progress.completed_sessions == 0
        assert progress.focused_seconds == 0

    def test_counts_work_sessions(self):
        repo = InMemorySessionRepository()
        clock = FixedClock(datetime(2026, 4, 17, 12, 0, 0, tzinfo=timezone.utc))
        cs = CompleteSession(repo)
        cs.execute(_make_command())
        cs.execute(_make_command())
        cs.execute(_make_command(session_type="break", duration=300))

        uc = GetTodayProgress(repo, clock)
        progress = uc.execute()
        assert progress.completed_sessions == 2
        assert progress.focused_seconds == 3000

    def test_ignores_other_dates(self):
        repo = InMemorySessionRepository()
        clock = FixedClock(datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc))
        cs = CompleteSession(repo)
        cs.execute(_make_command())

        uc = GetTodayProgress(repo, clock)
        progress = uc.execute()
        assert progress.completed_sessions == 0
