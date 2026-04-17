const WORK_SECONDS = 25 * 60;
const BREAK_SECONDS = 5 * 60;

export function createInitialState() {
	return {
		mode: "work",
		status: "idle",
		sessionDurationSeconds: WORK_SECONDS,
		remainingSeconds: WORK_SECONDS,
		todayCompleted: 0,
		todayFocusedSeconds: 0,
	};
}

function durationForMode(mode) {
	return mode === "work" ? WORK_SECONDS : BREAK_SECONDS;
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
			const duration = durationForMode(state.mode);
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
			const duration = durationForMode(nextMode);
			return {
				...state,
				mode: nextMode,
				status: "idle",
				sessionDurationSeconds: duration,
				remainingSeconds: duration,
			};
		}

		default:
			return state;
	}
}
