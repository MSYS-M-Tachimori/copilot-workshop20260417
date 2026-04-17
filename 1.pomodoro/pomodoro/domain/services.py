from __future__ import annotations

import abc
from datetime import date

from pomodoro.domain.models import SessionRecord, TodayProgress


class SessionRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, record: SessionRecord) -> SessionRecord: ...

    @abc.abstractmethod
    def get_today_progress(self, today: date) -> TodayProgress: ...
