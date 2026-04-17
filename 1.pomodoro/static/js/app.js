import { createInitialState, reducer } from "./state.js";
import {
	calculateProgressRatio,
	calculateRemainingSeconds,
	computeRingColor,
	formatFocusedTime,
	formatSeconds,
} from "./timer.js";

let state = createInitialState();
let timerIntervalId = null;
let endTimeMs = null;
let sessionStartedAt = null;

const elements = {
	modeText: document.getElementById("mode-text"),
	timerValue: document.getElementById("timer-value"),
	timerRing: document.getElementById("timer-ring"),
	startBtn: document.getElementById("start-btn"),
	resetBtn: document.getElementById("reset-btn"),
	statusMessage: document.getElementById("status-message"),
	todayCompleted: document.getElementById("today-completed"),
	todayFocused: document.getElementById("today-focused"),
};

function updateState(event) {
	state = reducer(state, event);
	render();
}

function stopTimerLoop() {
	if (timerIntervalId !== null) {
		window.clearInterval(timerIntervalId);
		timerIntervalId = null;
	}
	endTimeMs = null;
}

function beginTimerLoop() {
	stopTimerLoop();
	timerIntervalId = window.setInterval(() => {
		if (endTimeMs === null) {
			return;
		}

		const remainingSeconds = calculateRemainingSeconds(endTimeMs);
		if (remainingSeconds <= 0) {
			stopTimerLoop();
			updateState({ type: "COMPLETE" });
			reportCompletion();
			return;
		}

		updateState({ type: "TICK", remainingSeconds });
	}, 250);
}

async function reportCompletion() {
	const endedAt = new Date().toISOString();
	const payload = {
		session_type: state.mode,
		started_at: sessionStartedAt,
		ended_at: endedAt,
		duration_seconds: state.sessionDurationSeconds,
		completed: true,
	};

	try {
		const resp = await fetch("/api/sessions/complete", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
		});
		if (!resp.ok) {
			showError("セッションの保存に失敗しました。");
		}
		await fetchTodayProgress();
	} catch {
		showError("サーバーとの通信に失敗しました。");
	}
}

async function fetchTodayProgress() {
	try {
		const resp = await fetch("/api/progress/today");
		if (!resp.ok) {
			return;
		}
		const data = await resp.json();
		state = {
			...state,
			todayCompleted: data.completed_sessions,
			todayFocusedSeconds: data.focused_seconds,
		};
		render();
	} catch {
		// ignore – progress will be fetched on next opportunity
	}
}

function showError(msg) {
	elements.statusMessage.textContent = msg;
	elements.statusMessage.classList.add("error");
	setTimeout(() => {
		elements.statusMessage.classList.remove("error");
		render();
	}, 4000);
}

function startOrPauseTimer() {
	if (state.status === "running") {
		stopTimerLoop();
		updateState({ type: "PAUSE" });
		return;
	}

	if (state.status === "completed") {
		updateState({ type: "SWITCH_MODE" });
	}

	if (state.status !== "paused") {
		sessionStartedAt = new Date().toISOString();
	}

	endTimeMs = Date.now() + state.remainingSeconds * 1000;
	updateState({ type: "START" });
	beginTimerLoop();
}

function resetTimer() {
	stopTimerLoop();
	sessionStartedAt = null;
	updateState({ type: "RESET" });
}

function messageForStatus() {
	if (state.status === "running") {
		return state.mode === "work" ? "集中中です。" : "休憩中です。";
	}

	if (state.status === "paused") {
		return "一時停止中です。再開できます。";
	}

	if (state.status === "completed") {
		return "完了しました。開始を押すと次のセッションへ進みます。";
	}

	return "開始ボタンを押すとタイマーが動きます。";
}

function startButtonLabel() {
	if (state.status === "running") {
		return "一時停止";
	}
	if (state.status === "paused") {
		return "再開";
	}
	if (state.status === "completed") {
		return "次へ";
	}
	return "開始";
}

function render() {
	const modeLabel = state.mode === "work" ? "作業中" : "休憩中";
	const progress = calculateProgressRatio(state.remainingSeconds, state.sessionDurationSeconds);
	const progressDeg = Math.round(progress * 360);

	elements.modeText.textContent = modeLabel;
	elements.timerValue.textContent = formatSeconds(state.remainingSeconds);
	elements.startBtn.textContent = startButtonLabel();

	if (!elements.statusMessage.classList.contains("error")) {
		elements.statusMessage.textContent = messageForStatus();
	}

	elements.todayCompleted.textContent = String(state.todayCompleted);
	elements.todayFocused.textContent = formatFocusedTime(state.todayFocusedSeconds);

	const ringColor = computeRingColor(progress);
	elements.timerRing.style.setProperty("--ring-active", ringColor);
	elements.timerRing.style.background = `conic-gradient(var(--ring-active) ${progressDeg}deg, var(--ring-rest) ${progressDeg}deg 360deg)`;

	const isFocusing = state.status === "running" && state.mode === "work";
	document.body.classList.toggle("is-focusing", isFocusing);

	elements.resetBtn.disabled = state.status === "idle";
}

elements.startBtn.addEventListener("click", startOrPauseTimer);
elements.resetBtn.addEventListener("click", resetTimer);

document.addEventListener("visibilitychange", () => {
	if (document.hidden || state.status !== "running" || endTimeMs === null) {
		return;
	}
	updateState({ type: "TICK", remainingSeconds: calculateRemainingSeconds(endTimeMs) });
});

fetchTodayProgress();
render();

document.addEventListener("visibilitychange", () => {
	if (document.hidden || state.status !== "running" || endTimeMs === null) {
		return;
	}
	updateState({ type: "TICK", remainingSeconds: calculateRemainingSeconds(endTimeMs) });
});

render();
