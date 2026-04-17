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

function lerp(a, b, t) {
	return Math.round(a + (b - a) * t);
}

function toHex(channel) {
	return channel.toString(16).padStart(2, "0");
}

// 進捗 (0.0 〜 1.0) に応じて、青 → 黄 → 赤 のグラデーション色を返す。
// 0.0 付近 : 青系（集中開始）
// 0.5 付近 : 黄系（中盤）
// 1.0 付近 : 赤系（終盤・完了間近）
export function computeRingColor(progress) {
	const safe = Number.isFinite(progress) ? progress : 0;
	const clamped = Math.min(1, Math.max(0, safe));
	const blue = [74, 144, 226];    // #4a90e2
	const yellow = [245, 197, 66];  // #f5c542
	const red = [226, 74, 74];      // #e24a4a

	let from;
	let to;
	let t;
	if (clamped < 0.5) {
		from = blue;
		to = yellow;
		t = clamped / 0.5;
	} else {
		from = yellow;
		to = red;
		t = (clamped - 0.5) / 0.5;
	}

	const r = lerp(from[0], to[0], t);
	const g = lerp(from[1], to[1], t);
	const b = lerp(from[2], to[2], t);
	return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
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
