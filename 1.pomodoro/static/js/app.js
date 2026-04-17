import {
	ALLOWED_BREAK_MINUTES,
	ALLOWED_WORK_MINUTES,
	createInitialState,
	reducer,
} from "./state.js";
import {
	calculateProgressRatio,
	calculateRemainingSeconds,
	formatFocusedTime,
	formatSeconds,
} from "./timer.js";

const SETTINGS_STORAGE_KEY = "pomodoro.settings.v1";
const DEFAULT_SETTINGS = {
	workMinutes: 25,
	breakMinutes: 5,
	theme: "light",
	sounds: { start: true, end: true, tick: false },
};

const ALLOWED_THEMES = ["light", "dark", "focus"];

function loadSettings() {
	try {
		const raw = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
		if (!raw) return { ...DEFAULT_SETTINGS, sounds: { ...DEFAULT_SETTINGS.sounds } };
		const parsed = JSON.parse(raw);
		return sanitizeSettings(parsed);
	} catch {
		return { ...DEFAULT_SETTINGS, sounds: { ...DEFAULT_SETTINGS.sounds } };
	}
}

function sanitizeSettings(s) {
	const workMinutes = ALLOWED_WORK_MINUTES.includes(Number(s?.workMinutes))
		? Number(s.workMinutes)
		: DEFAULT_SETTINGS.workMinutes;
	const breakMinutes = ALLOWED_BREAK_MINUTES.includes(Number(s?.breakMinutes))
		? Number(s.breakMinutes)
		: DEFAULT_SETTINGS.breakMinutes;
	const theme = ALLOWED_THEMES.includes(s?.theme) ? s.theme : DEFAULT_SETTINGS.theme;
	const sounds = {
		start: typeof s?.sounds?.start === "boolean" ? s.sounds.start : DEFAULT_SETTINGS.sounds.start,
		end: typeof s?.sounds?.end === "boolean" ? s.sounds.end : DEFAULT_SETTINGS.sounds.end,
		tick: typeof s?.sounds?.tick === "boolean" ? s.sounds.tick : DEFAULT_SETTINGS.sounds.tick,
	};
	return { workMinutes, breakMinutes, theme, sounds };
}

function persistSettings() {
	try {
		window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
	} catch {
		// storage unavailable — silently continue
	}
}

let settings = loadSettings();
let state = createInitialState({
	workDurationSeconds: settings.workMinutes * 60,
	breakDurationSeconds: settings.breakMinutes * 60,
});
let timerIntervalId = null;
let endTimeMs = null;
let sessionStartedAt = null;
let lastDisplayedSeconds = null;
let audioContext = null;

const elements = {
	modeText: document.getElementById("mode-text"),
	timerValue: document.getElementById("timer-value"),
	timerRing: document.getElementById("timer-ring"),
	startBtn: document.getElementById("start-btn"),
	resetBtn: document.getElementById("reset-btn"),
	statusMessage: document.getElementById("status-message"),
	todayCompleted: document.getElementById("today-completed"),
	todayFocused: document.getElementById("today-focused"),
	workSelect: document.getElementById("work-minutes-select"),
	breakSelect: document.getElementById("break-minutes-select"),
	themeSelect: document.getElementById("theme-select"),
	soundStart: document.getElementById("sound-start-toggle"),
	soundEnd: document.getElementById("sound-end-toggle"),
	soundTick: document.getElementById("sound-tick-toggle"),
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
			playSound("end");
			reportCompletion();
			return;
		}

		if (settings.sounds.tick && remainingSeconds !== lastDisplayedSeconds) {
			playSound("tick");
		}
		lastDisplayedSeconds = remainingSeconds;
		updateState({ type: "TICK", remainingSeconds });
	}, 250);
}

function playSound(kind) {
	if (!settings.sounds[kind]) return;
	try {
		if (!audioContext) {
			const Ctx = window.AudioContext || window.webkitAudioContext;
			if (!Ctx) return;
			audioContext = new Ctx();
		}
		const ctx = audioContext;
		const osc = ctx.createOscillator();
		const gain = ctx.createGain();
		const now = ctx.currentTime;

		// Distinct timbres per sound kind.
		const profile = {
			start: { freq: 660, duration: 0.18, peak: 0.25 },
			end: { freq: 880, duration: 0.35, peak: 0.3 },
			tick: { freq: 1200, duration: 0.04, peak: 0.08 },
		}[kind] || { freq: 440, duration: 0.1, peak: 0.2 };

		osc.type = "sine";
		osc.frequency.setValueAtTime(profile.freq, now);
		gain.gain.setValueAtTime(0, now);
		gain.gain.linearRampToValueAtTime(profile.peak, now + 0.01);
		gain.gain.exponentialRampToValueAtTime(0.0001, now + profile.duration);

		osc.connect(gain).connect(ctx.destination);
		osc.start(now);
		osc.stop(now + profile.duration + 0.02);
	} catch {
		// ignore audio failures
	}
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
	lastDisplayedSeconds = null;
	updateState({ type: "START" });
	playSound("start");
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

function applyTheme(theme) {
	document.body.setAttribute("data-theme", theme);
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

	// Duration selects are disabled while timer is active to prevent mid-session changes.
	const durationDisabled = state.status === "running" || state.status === "paused";
	if (elements.workSelect) elements.workSelect.disabled = durationDisabled;
	if (elements.breakSelect) elements.breakSelect.disabled = durationDisabled;
}

function initSettingsControls() {
	if (elements.workSelect) {
		elements.workSelect.value = String(settings.workMinutes);
		elements.workSelect.addEventListener("change", () => {
			const value = Number(elements.workSelect.value);
			if (!ALLOWED_WORK_MINUTES.includes(value)) return;
			settings.workMinutes = value;
			persistSettings();
			updateState({
				type: "UPDATE_DURATIONS",
				workDurationSeconds: value * 60,
			});
		});
	}

	if (elements.breakSelect) {
		elements.breakSelect.value = String(settings.breakMinutes);
		elements.breakSelect.addEventListener("change", () => {
			const value = Number(elements.breakSelect.value);
			if (!ALLOWED_BREAK_MINUTES.includes(value)) return;
			settings.breakMinutes = value;
			persistSettings();
			updateState({
				type: "UPDATE_DURATIONS",
				breakDurationSeconds: value * 60,
			});
		});
	}

	if (elements.themeSelect) {
		elements.themeSelect.value = settings.theme;
		elements.themeSelect.addEventListener("change", () => {
			const value = elements.themeSelect.value;
			if (!ALLOWED_THEMES.includes(value)) return;
			settings.theme = value;
			applyTheme(value);
			persistSettings();
		});
	}

	const bindSoundToggle = (el, key) => {
		if (!el) return;
		el.checked = Boolean(settings.sounds[key]);
		el.addEventListener("change", () => {
			settings.sounds[key] = el.checked;
			persistSettings();
		});
	};
	bindSoundToggle(elements.soundStart, "start");
	bindSoundToggle(elements.soundEnd, "end");
	bindSoundToggle(elements.soundTick, "tick");
}

elements.startBtn.addEventListener("click", startOrPauseTimer);
elements.resetBtn.addEventListener("click", resetTimer);

document.addEventListener("visibilitychange", () => {
	if (document.hidden || state.status !== "running" || endTimeMs === null) {
		return;
	}
	updateState({ type: "TICK", remainingSeconds: calculateRemainingSeconds(endTimeMs) });
});

applyTheme(settings.theme);
initSettingsControls();
fetchTodayProgress();
render();
