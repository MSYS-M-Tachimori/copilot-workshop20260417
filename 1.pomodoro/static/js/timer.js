export function formatSeconds(totalSeconds) {
	const safe = Math.max(0, Math.floor(totalSeconds));
	const minutes = Math.floor(safe / 60);
	const seconds = safe % 60;
	return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function calculateProgressRatio(remainingSeconds, sessionDurationSeconds) {
	if (sessionDurationSeconds <= 0) {
		return 0;
	}

	const elapsed = sessionDurationSeconds - remainingSeconds;
	const ratio = elapsed / sessionDurationSeconds;
	return Math.min(1, Math.max(0, ratio));
}

export function calculateRemainingSeconds(endTimeMs, nowMs = Date.now()) {
	const diffMs = Math.max(0, endTimeMs - nowMs);
	return Math.ceil(diffMs / 1000);
}

export function formatFocusedTime(totalSeconds) {
	const safe = Math.max(0, Math.floor(totalSeconds));
	const hours = Math.floor(safe / 3600);
	const minutes = Math.floor((safe % 3600) / 60);

	if (hours === 0) {
		return `${minutes}分`;
	}

	if (minutes === 0) {
		return `${hours}時間`;
	}

	return `${hours}時間${minutes}分`;
}
