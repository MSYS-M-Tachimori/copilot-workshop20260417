from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SessionType(Enum):
    WORK = "work"
    BREAK = "break"


@dataclass(frozen=True)
class DurationSeconds:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError(f"duration_seconds must be positive, got {self.value}")


@dataclass
class SessionRecord:
    session_type: SessionType
    started_at: datetime
    ended_at: datetime
    duration_seconds: DurationSeconds
    completed: bool
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CompleteSessionCommand:
    session_type: str
    started_at: str
    ended_at: str
    duration_seconds: int
    completed: bool

    def to_record(self) -> SessionRecord:
        st = SessionType(self.session_type)
        started = datetime.fromisoformat(self.started_at)
        ended = datetime.fromisoformat(self.ended_at)
        dur = DurationSeconds(self.duration_seconds)
        return SessionRecord(
            session_type=st,
            started_at=started,
            ended_at=ended,
            duration_seconds=dur,
            completed=self.completed,
        )


@dataclass(frozen=True)
class TodayProgress:
    completed_sessions: int
    focused_seconds: int


@dataclass(frozen=True)
class DailyAggregate:
    """完了した作業セッションの日別集計。"""

    date: str  # ISO 形式 YYYY-MM-DD
    completed_sessions: int
    focused_seconds: int


@dataclass(frozen=True)
class Badge:
    id: str
    name: str
    description: str
    achieved: bool


@dataclass(frozen=True)
class GamificationStats:
    """ゲーミフィケーション表示に必要な全情報。"""

    xp: int
    level: int
    xp_in_level: int
    xp_to_next_level: int
    streak_days: int
    total_sessions: int
    total_focused_seconds: int
    weekly: list[DailyAggregate]
    monthly: list[DailyAggregate]
    weekly_total_sessions: int
    weekly_total_focused_seconds: int
    monthly_total_sessions: int
    monthly_total_focused_seconds: int
    badges: list[Badge]
