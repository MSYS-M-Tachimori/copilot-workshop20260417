import json

import pytest

from app import create_app
from tests.fake_repository import InMemorySessionRepository


@pytest.fixture()
def client():
    repo = InMemorySessionRepository()
    app = create_app(repository=repo)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _valid_payload(**overrides):
    base = {
        "session_type": "work",
        "started_at": "2026-04-17T10:00:00+00:00",
        "ended_at": "2026-04-17T10:25:00+00:00",
        "duration_seconds": 1500,
        "completed": True,
    }
    base.update(overrides)
    return base


class TestCompleteSessionAPI:
    def test_success(self, client):
        resp = client.post(
            "/api/sessions/complete",
            data=json.dumps(_valid_payload()),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["id"] == 1
        assert data["session_type"] == "work"

    def test_missing_body(self, client):
        resp = client.post("/api/sessions/complete", content_type="application/json")
        assert resp.status_code == 400

    def test_missing_fields(self, client):
        resp = client.post(
            "/api/sessions/complete",
            data=json.dumps({"session_type": "work"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Missing fields" in resp.get_json()["error"]

    def test_invalid_session_type(self, client):
        resp = client.post(
            "/api/sessions/complete",
            data=json.dumps(_valid_payload(session_type="nap")),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_duration(self, client):
        resp = client.post(
            "/api/sessions/complete",
            data=json.dumps(_valid_payload(duration_seconds=-1)),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestTodayProgressAPI:
    def test_empty(self, client):
        resp = client.get("/api/progress/today")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["completed_sessions"] == 0
        assert data["focused_seconds"] == 0

    def test_after_complete(self, client):
        client.post(
            "/api/sessions/complete",
            data=json.dumps(_valid_payload()),
            content_type="application/json",
        )
        resp = client.get("/api/progress/today")
        data = resp.get_json()
        assert data["completed_sessions"] == 1
        assert data["focused_seconds"] == 1500
