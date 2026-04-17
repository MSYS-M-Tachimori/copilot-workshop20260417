from __future__ import annotations

import sqlite3
from datetime import date

from pomodoro.domain.models import (
    DailyAggregate,
    DurationSeconds,
    SessionRecord,
    SessionType,
    TodayProgress,
)
from pomodoro.domain.services import SessionRepository


class SQLiteSessionRepository(SessionRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, record: SessionRecord) -> SessionRecord:
        cursor = self._conn.execute(
            """
            INSERT INTO sessions (session_type, started_at, ended_at, duration_seconds, completed, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.session_type.value,
                record.started_at.isoformat(),
                record.ended_at.isoformat(),
                record.duration_seconds.value,
                int(record.completed),
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()
        record.id = cursor.lastrowid
        return record

    def get_today_progress(self, today: date) -> TodayProgress:
        today_str = today.isoformat()
        row = self._conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN session_type = 'work' THEN 1 ELSE 0 END), 0) AS completed_sessions,
                COALESCE(SUM(CASE WHEN session_type = 'work' THEN duration_seconds ELSE 0 END), 0) AS focused_seconds
            FROM sessions
            WHERE completed = 1
              AND date(started_at) = ?
            """,
            (today_str,),
        ).fetchone()
        return TodayProgress(
            completed_sessions=row["completed_sessions"],
            focused_seconds=row["focused_seconds"],
        )

    def get_daily_work_aggregates(self) -> list[DailyAggregate]:
        rows = self._conn.execute(
            """
            SELECT
                date(started_at) AS day,
                COUNT(*) AS completed_sessions,
                COALESCE(SUM(duration_seconds), 0) AS focused_seconds
            FROM sessions
            WHERE completed = 1
              AND session_type = 'work'
            GROUP BY date(started_at)
            ORDER BY date(started_at) ASC
            """
        ).fetchall()
        return [
            DailyAggregate(
                date=row["day"],
                completed_sessions=row["completed_sessions"],
                focused_seconds=row["focused_seconds"],
            )
            for row in rows
        ]
