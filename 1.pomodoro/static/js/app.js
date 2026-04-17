import { createInitialState, reducer } from "./state.js";
import {
	calculateProgressRatio,
	calculateRemainingSeconds,
	formatFocusedTime,
	formatSeconds,
} from "./timer.js";
import {
	chartBarHeights,
	formatDayLabel,
	levelProgressPercent,
} from "./gamification.js";

let state = createInitialState();
let timerIntervalId = null;
let endTimeMs = null;
let sessionStartedAt = null;
let gamification = null;

const elements = {
	modeText: document.getElementById("mode-text"),
	timerValue: document.getElementById("timer-value"),
	timerRing: document.getElementById("timer-ring"),
	startBtn: document.getElementById("start-btn"),
	resetBtn: document.getElementById("reset-btn"),
	statusMessage: document.getElementById("status-message"),
	todayCompleted: document.getElementById("today-completed"),
	todayFocused: document.getElementById("today-focused"),
	gamiLevel: document.getElementById("gami-level"),
	gamiXpInLevel: document.getElementById("gami-xp-in-level"),
	gamiXpPerLevel: document.getElementById("gami-xp-per-level"),
	gamiXpTotal: document.getElementById("gami-xp-total"),
	gamiLevelBar: document.getElementById("gami-level-bar"),
	gamiLevelFill: document.getElementById("gami-level-fill"),
	gamiStreak: document.getElementById("gami-streak"),
	gamiWeeklySessions: document.getElementById("gami-weekly-sessions"),
	gamiMonthlySessions: document.getElementById("gami-monthly-sessions"),
	gamiWeeklyChart: document.getElementById("gami-weekly-chart"),
	gamiBadges: document.getElementById("gami-badges"),
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
		await fetchGamification();
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

async function fetchGamification() {
	try {
		const resp = await fetch("/api/stats/gamification");
		if (!resp.ok) {
			return;
		}
		gamification = await resp.json();
		renderGamification();
	} catch {
		// ignore – will refresh on next completion
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
	elements.timerRing.style.background = `conic-gradient(var(--accent) ${progressDeg}deg, var(--ring-rest) ${progressDeg}deg 360deg)`;

	elements.resetBtn.disabled = state.status === "idle";
}

function renderGamification() {
	if (!gamification || !elements.gamiLevel) {
		return;
	}

	const xpPerLevel = gamification.xp_in_level + gamification.xp_to_next_level;
	elements.gamiLevel.textContent = String(gamification.level);
	elements.gamiXpInLevel.textContent = String(gamification.xp_in_level);
	elements.gamiXpPerLevel.textContent = String(xpPerLevel);
	elements.gamiXpTotal.textContent = String(gamification.xp);

	const pct = levelProgressPercent(gamification.xp_in_level, xpPerLevel);
	elements.gamiLevelFill.style.width = `${pct}%`;
	elements.gamiLevelBar.setAttribute("aria-valuenow", String(Math.round(pct)));

	elements.gamiStreak.textContent = String(gamification.streak_days);
	elements.gamiWeeklySessions.textContent = String(gamification.weekly_total_sessions);
	elements.gamiMonthlySessions.textContent = String(gamification.monthly_total_sessions);

	const heights = chartBarHeights(gamification.weekly);
	elements.gamiWeeklyChart.innerHTML = "";
	gamification.weekly.forEach((day, idx) => {
		const bar = document.createElement("div");
		bar.className = "chart-bar";
		const fill = document.createElement("div");
		fill.className = "chart-bar-fill";
		fill.style.height = `${heights[idx]}%`;
		if ((day.completed_sessions || 0) > 0) {
			fill.classList.add("has-sessions");
		}
		const label = document.createElement("span");
		label.className = "chart-bar-label";
		label.textContent = formatDayLabel(day.date);
		const count = document.createElement("span");
		count.className = "chart-bar-count";
		count.textContent = String(day.completed_sessions || 0);
		bar.title = `${day.date}: ${day.completed_sessions}件`;
		bar.appendChild(count);
		bar.appendChild(fill);
		bar.appendChild(label);
		elements.gamiWeeklyChart.appendChild(bar);
	});

	elements.gamiBadges.innerHTML = "";
	gamification.badges.forEach((badge) => {
		const li = document.createElement("li");
		li.className = badge.achieved ? "badge badge-achieved" : "badge badge-locked";
		li.title = badge.description;
		const icon = document.createElement("span");
		icon.className = "badge-icon";
		icon.setAttribute("aria-hidden", "true");
		icon.textContent = badge.achieved ? "🏅" : "🔒";
		const name = document.createElement("span");
		name.className = "badge-name";
		name.textContent = badge.name;
		li.appendChild(icon);
		li.appendChild(name);
		elements.gamiBadges.appendChild(li);
	});
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
fetchGamification();
render();
renderGamification();

document.addEventListener("visibilitychange", () => {
	if (document.hidden || state.status !== "running" || endTimeMs === null) {
		return;
	}
	updateState({ type: "TICK", remainingSeconds: calculateRemainingSeconds(endTimeMs) });
});

render();
