from __future__ import annotations

import abc
from datetime import date

from pomodoro.domain.models import DailyAggregate, SessionRecord, TodayProgress


class SessionRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, record: SessionRecord) -> SessionRecord: ...

    @abc.abstractmethod
    def get_today_progress(self, today: date) -> TodayProgress: ...

    @abc.abstractmethod
    def get_daily_work_aggregates(self) -> list[DailyAggregate]:
        """完了済みの作業（work）セッションの日別集計を、日付昇順で返す。

        返される各要素は ``date`` が ISO 形式 (YYYY-MM-DD) の文字列で、
        ``completed_sessions`` は 1 以上、``focused_seconds`` は合計集中秒数。
        セッションが 1 件も無い日はリストに含まれない。
        """
        ...
