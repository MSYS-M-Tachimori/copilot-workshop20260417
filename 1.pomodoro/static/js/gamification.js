// ゲーミフィケーション表示の純粋ヘルパー。
// DOM 操作は app.js に集約し、ここは入出力が明確なユーティリティだけを置く。

export function clampPercent(value) {
	if (!Number.isFinite(value)) {
		return 0;
	}
	if (value < 0) return 0;
	if (value > 100) return 100;
	return value;
}

export function levelProgressPercent(xpInLevel, xpPerLevel) {
	if (!xpPerLevel || xpPerLevel <= 0) {
		return 0;
	}
	return clampPercent((xpInLevel / xpPerLevel) * 100);
}

export function chartBarHeights(dailyAggregates) {
	// 各日の完了数を 0–100% の高さに正規化する（空なら全て 0）。
	if (!Array.isArray(dailyAggregates) || dailyAggregates.length === 0) {
		return [];
	}
	const max = dailyAggregates.reduce(
		(acc, d) => Math.max(acc, d.completed_sessions || 0),
		0,
	);
	if (max === 0) {
		return dailyAggregates.map(() => 0);
	}
	return dailyAggregates.map((d) =>
		clampPercent(((d.completed_sessions || 0) / max) * 100),
	);
}

export function formatDayLabel(isoDate) {
	// "2026-04-17" → "4/17"
	if (typeof isoDate !== "string") return "";
	const parts = isoDate.split("-");
	if (parts.length !== 3) return isoDate;
	return `${Number(parts[1])}/${Number(parts[2])}`;
}
