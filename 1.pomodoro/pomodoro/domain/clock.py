from __future__ import annotations

import abc
from datetime import date, datetime, timezone


class Clock(abc.ABC):
    @abc.abstractmethod
    def now(self) -> datetime: ...

    def today(self) -> date:
        return self.now().date()


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock(Clock):
    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed

    def set(self, dt: datetime) -> None:
        self._fixed = dt
