"""ゲーミフィケーション API / ユースケース / リポジトリの統合テスト。"""
import json
from datetime import datetime, timezone

import pytest

from app import create_app
from pomodoro.application.use_cases import CompleteSession, GetGamificationStats
from pomodoro.domain.clock import FixedClock
from pomodoro.domain.models import CompleteSessionCommand
from tests.fake_repository import InMemorySessionRepository


@pytest.fixture()
def client():
    repo = InMemorySessionRepository()
    app = create_app(repository=repo)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestGamificationAPI:
    def test_empty_returns_base_stats(self, client):
        resp = client.get("/api/stats/gamification")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["xp"] == 0
        assert data["level"] == 1
        assert data["streak_days"] == 0
        assert data["total_sessions"] == 0
        assert len(data["weekly"]) == 7
        assert len(data["monthly"]) == 30
        assert isinstance(data["badges"], list)
        assert all(b["achieved"] is False for b in data["badges"])

    def test_after_completing_session_xp_and_badge(self, client):
        payload = {
            "session_type": "work",
            "started_at": "2026-04-17T10:00:00+00:00",
            "ended_at": "2026-04-17T10:25:00+00:00",
            "duration_seconds": 1500,
            "completed": True,
        }
        client.post(
            "/api/sessions/complete",
            data=json.dumps(payload),
            content_type="application/json",
        )
        resp = client.get("/api/stats/gamification")
        data = resp.get_json()
        assert data["total_sessions"] == 1
        assert data["xp"] >= 10
        first_session = next(b for b in data["badges"] if b["id"] == "first_session")
        assert first_session["achieved"] is True

    def test_break_sessions_not_counted(self, client):
        payload = {
            "session_type": "break",
            "started_at": "2026-04-17T10:00:00+00:00",
            "ended_at": "2026-04-17T10:05:00+00:00",
            "duration_seconds": 300,
            "completed": True,
        }
        client.post(
            "/api/sessions/complete",
            data=json.dumps(payload),
            content_type="application/json",
        )
        resp = client.get("/api/stats/gamification")
        data = resp.get_json()
        assert data["total_sessions"] == 0
        assert data["xp"] == 0


class TestGetGamificationStatsUseCase:
    def test_streak_and_xp_accumulate(self):
        repo = InMemorySessionRepository()
        cs = CompleteSession(repo)
        # 4/15, 4/16, 4/17 に 1 件ずつ
        for day in ("2026-04-15", "2026-04-16", "2026-04-17"):
            cs.execute(
                CompleteSessionCommand(
                    session_type="work",
                    started_at=f"{day}T10:00:00+00:00",
                    ended_at=f"{day}T10:25:00+00:00",
                    duration_seconds=1500,
                    completed=True,
                )
            )
        clock = FixedClock(datetime(2026, 4, 17, 12, 0, 0, tzinfo=timezone.utc))
        uc = GetGamificationStats(repo, clock)
        stats = uc.execute()
        assert stats.total_sessions == 3
        assert stats.streak_days == 3
        assert stats.xp == 30
