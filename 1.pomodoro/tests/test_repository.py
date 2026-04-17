import sqlite3
from datetime import date, datetime, timezone

import pytest

from pomodoro.domain.models import DurationSeconds, SessionRecord, SessionType
from pomodoro.infrastructure.db import init_db
from pomodoro.infrastructure.repositories.sqlite_repository import (
    SQLiteSessionRepository,
)


@pytest.fixture()
def repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return SQLiteSessionRepository(conn)


def _make_record(
    session_type: SessionType = SessionType.WORK,
    started_at: str = "2026-04-17T10:00:00+00:00",
    duration: int = 1500,
) -> SessionRecord:
    return SessionRecord(
        session_type=session_type,
        started_at=datetime.fromisoformat(started_at),
        ended_at=datetime.fromisoformat("2026-04-17T10:25:00+00:00"),
        duration_seconds=DurationSeconds(duration),
        completed=True,
    )


class TestSQLiteSessionRepository:
    def test_save_assigns_id(self, repo):
        record = _make_record()
        saved = repo.save(record)
        assert saved.id is not None
        assert saved.id >= 1

    def test_save_increments_id(self, repo):
        r1 = repo.save(_make_record())
        r2 = repo.save(_make_record())
        assert r2.id == r1.id + 1

    def test_get_today_progress_empty(self, repo):
        progress = repo.get_today_progress(date(2026, 4, 17))
        assert progress.completed_sessions == 0
        assert progress.focused_seconds == 0

    def test_get_today_progress_counts_work(self, repo):
        repo.save(_make_record())
        repo.save(_make_record())
        repo.save(_make_record(session_type=SessionType.BREAK, duration=300))

        progress = repo.get_today_progress(date(2026, 4, 17))
        assert progress.completed_sessions == 2
        assert progress.focused_seconds == 3000

    def test_get_today_progress_ignores_other_dates(self, repo):
        repo.save(_make_record())
        progress = repo.get_today_progress(date(2026, 4, 18))
        assert progress.completed_sessions == 0

    def test_midnight_boundary(self, repo):
        repo.save(_make_record(started_at="2026-04-16T23:59:00+00:00"))
        repo.save(_make_record(started_at="2026-04-17T00:01:00+00:00"))
        progress = repo.get_today_progress(date(2026, 4, 17))
        assert progress.completed_sessions == 1

    def test_get_daily_work_aggregates_empty(self, repo):
        assert repo.get_daily_work_aggregates() == []

    def test_get_daily_work_aggregates_groups_by_day(self, repo):
        repo.save(_make_record(started_at="2026-04-15T09:00:00+00:00"))
        repo.save(_make_record(started_at="2026-04-15T10:00:00+00:00"))
        repo.save(_make_record(started_at="2026-04-17T10:00:00+00:00"))
        # break セッションは集計対象外
        repo.save(
            _make_record(
                session_type=SessionType.BREAK,
                started_at="2026-04-17T11:00:00+00:00",
                duration=300,
            )
        )
        aggs = repo.get_daily_work_aggregates()
        assert [a.date for a in aggs] == ["2026-04-15", "2026-04-17"]
        assert aggs[0].completed_sessions == 2
        assert aggs[0].focused_seconds == 3000
        assert aggs[1].completed_sessions == 1
        assert aggs[1].focused_seconds == 1500
