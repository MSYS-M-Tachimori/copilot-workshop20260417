from __future__ import annotations

from datetime import date

from pomodoro.domain.models import SessionRecord, TodayProgress
from pomodoro.domain.services import SessionRepository


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._records: list[SessionRecord] = []
        self._next_id = 1

    def save(self, record: SessionRecord) -> SessionRecord:
        record.id = self._next_id
        self._next_id += 1
        self._records.append(record)
        return record

    def get_today_progress(self, today: date) -> TodayProgress:
        completed = 0
        focused = 0
        for r in self._records:
            if r.completed and r.started_at.date() == today:
                if r.session_type.value == "work":
                    completed += 1
                    focused += r.duration_seconds.value
        return TodayProgress(completed_sessions=completed, focused_seconds=focused)
