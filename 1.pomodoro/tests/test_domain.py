import pytest

from pomodoro.domain.models import (
    CompleteSessionCommand,
    DurationSeconds,
    SessionType,
)


class TestSessionType:
    def test_valid_work(self):
        assert SessionType("work") == SessionType.WORK

    def test_valid_break(self):
        assert SessionType("break") == SessionType.BREAK

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            SessionType("nap")


class TestDurationSeconds:
    def test_positive(self):
        d = DurationSeconds(100)
        assert d.value == 100

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            DurationSeconds(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            DurationSeconds(-1)


class TestCompleteSessionCommand:
    def test_to_record_valid(self):
        cmd = CompleteSessionCommand(
            session_type="work",
            started_at="2026-04-17T10:00:00+09:00",
            ended_at="2026-04-17T10:25:00+09:00",
            duration_seconds=1500,
            completed=True,
        )
        record = cmd.to_record()
        assert record.session_type == SessionType.WORK
        assert record.duration_seconds.value == 1500
        assert record.completed is True

    def test_to_record_invalid_type(self):
        cmd = CompleteSessionCommand(
            session_type="nap",
            started_at="2026-04-17T10:00:00+09:00",
            ended_at="2026-04-17T10:25:00+09:00",
            duration_seconds=1500,
            completed=True,
        )
        with pytest.raises(ValueError):
            cmd.to_record()

    def test_to_record_invalid_duration(self):
        cmd = CompleteSessionCommand(
            session_type="work",
            started_at="2026-04-17T10:00:00+09:00",
            ended_at="2026-04-17T10:25:00+09:00",
            duration_seconds=-5,
            completed=True,
        )
        with pytest.raises(ValueError):
            cmd.to_record()
