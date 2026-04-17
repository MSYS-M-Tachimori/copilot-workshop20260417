from __future__ import annotations

from datetime import date

from pomodoro.domain.models import DailyAggregate, SessionRecord, TodayProgress
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

    def get_daily_work_aggregates(self) -> list[DailyAggregate]:
        buckets: dict[str, tuple[int, int]] = {}
        for r in self._records:
            if not r.completed or r.session_type.value != "work":
                continue
            key = r.started_at.date().isoformat()
            sessions, focused = buckets.get(key, (0, 0))
            buckets[key] = (sessions + 1, focused + r.duration_seconds.value)
        return [
            DailyAggregate(
                date=day,
                completed_sessions=sessions,
                focused_seconds=focused,
            )
            for day, (sessions, focused) in sorted(buckets.items())
        ]
