from __future__ import annotations

from pomodoro.domain.clock import Clock
from pomodoro.domain.models import CompleteSessionCommand, TodayProgress
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
