from flask import Flask, jsonify, render_template, request

from pomodoro.application.use_cases import (
    CompleteSession,
    GetGamificationStats,
    GetTodayProgress,
)
from pomodoro.domain.clock import SystemClock
from pomodoro.domain.models import CompleteSessionCommand
from pomodoro.domain.services import SessionRepository
from pomodoro.infrastructure.db import get_connection, init_db
from pomodoro.infrastructure.repositories.sqlite_repository import (
    SQLiteSessionRepository,
)


def create_app(repository: SessionRepository | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    if repository is None:
        conn = get_connection()
        init_db(conn)
        repository = SQLiteSessionRepository(conn)

    clock = SystemClock()
    complete_session_uc = CompleteSession(repository)
    get_today_progress_uc = GetTodayProgress(repository, clock)
    get_gamification_stats_uc = GetGamificationStats(repository, clock)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.post("/api/sessions/complete")
    def complete_session():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        required = ["session_type", "started_at", "ended_at", "duration_seconds", "completed"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        if data["session_type"] not in ("work", "break"):
            return jsonify({"error": "session_type must be 'work' or 'break'"}), 400

        if not isinstance(data["duration_seconds"], int) or data["duration_seconds"] <= 0:
            return jsonify({"error": "duration_seconds must be a positive integer"}), 400

        try:
            command = CompleteSessionCommand(
                session_type=data["session_type"],
                started_at=data["started_at"],
                ended_at=data["ended_at"],
                duration_seconds=data["duration_seconds"],
                completed=bool(data["completed"]),
            )
            result = complete_session_uc.execute(command)
            return jsonify(result), 201
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400

    @app.get("/api/progress/today")
    def today_progress():
        progress = get_today_progress_uc.execute()
        return jsonify({
            "completed_sessions": progress.completed_sessions,
            "focused_seconds": progress.focused_seconds,
        }), 200

    @app.get("/api/stats/gamification")
    def gamification_stats():
        return jsonify(get_gamification_stats_uc.execute_as_dict()), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
