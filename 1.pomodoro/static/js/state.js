const DEFAULT_WORK_SECONDS = 25 * 60;
const DEFAULT_BREAK_SECONDS = 5 * 60;

export const ALLOWED_WORK_MINUTES = [15, 25, 35, 45];
export const ALLOWED_BREAK_MINUTES = [5, 10, 15];

export function createInitialState(overrides = {}) {
	const workDurationSeconds =
		typeof overrides.workDurationSeconds === "number"
			? overrides.workDurationSeconds
			: DEFAULT_WORK_SECONDS;
	const breakDurationSeconds =
		typeof overrides.breakDurationSeconds === "number"
			? overrides.breakDurationSeconds
			: DEFAULT_BREAK_SECONDS;

	return {
		mode: "work",
		status: "idle",
		workDurationSeconds,
		breakDurationSeconds,
		sessionDurationSeconds: workDurationSeconds,
		remainingSeconds: workDurationSeconds,
		todayCompleted: 0,
		todayFocusedSeconds: 0,
	};
}

function durationForMode(state, mode) {
	return mode === "work" ? state.workDurationSeconds : state.breakDurationSeconds;
}

export function reducer(state, event) {
	switch (event.type) {
		case "START": {
			if (state.status === "running") {
				return state;
			}

			return {
				...state,
				status: "running",
			};
		}

		case "PAUSE": {
			if (state.status !== "running") {
				return state;
			}

			return {
				...state,
				status: "paused",
			};
		}

		case "TICK": {
			if (state.status !== "running") {
				return state;
			}

			return {
				...state,
				remainingSeconds: event.remainingSeconds,
			};
		}

		case "RESET": {
			const duration = durationForMode(state, state.mode);
			return {
				...state,
				status: "idle",
				sessionDurationSeconds: duration,
				remainingSeconds: duration,
			};
		}

		case "COMPLETE": {
			const incrementCompleted = state.mode === "work" ? 1 : 0;
			const incrementFocusedSeconds = state.mode === "work" ? state.sessionDurationSeconds : 0;

			return {
				...state,
				status: "completed",
				remainingSeconds: 0,
				todayCompleted: state.todayCompleted + incrementCompleted,
				todayFocusedSeconds: state.todayFocusedSeconds + incrementFocusedSeconds,
			};
		}

		case "SWITCH_MODE": {
			if (state.status === "running") {
				return state;
			}

			const nextMode = state.mode === "work" ? "break" : "work";
			const duration = durationForMode(state, nextMode);
			return {
				...state,
				mode: nextMode,
				status: "idle",
				sessionDurationSeconds: duration,
				remainingSeconds: duration,
			};
		}

		case "UPDATE_DURATIONS": {
			if (state.status === "running" || state.status === "paused") {
				return state;
			}

			const nextWork =
				typeof event.workDurationSeconds === "number"
					? event.workDurationSeconds
					: state.workDurationSeconds;
			const nextBreak =
				typeof event.breakDurationSeconds === "number"
					? event.breakDurationSeconds
					: state.breakDurationSeconds;
			const next = {
				...state,
				workDurationSeconds: nextWork,
				breakDurationSeconds: nextBreak,
			};
			const duration = durationForMode(next, next.mode);
			return {
				...next,
				status: "idle",
				sessionDurationSeconds: duration,
				remainingSeconds: duration,
			};
		}

		default:
			return state;
	}
}
