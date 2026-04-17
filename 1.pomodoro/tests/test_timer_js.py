"""Tests for timer.js equivalent logic validation (pure function tests via Node.js)."""
import subprocess
import json
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
JS_DIR = os.path.join(os.path.dirname(TESTS_DIR), "static", "js")


def _run_node(script: str) -> str:
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=JS_DIR,
    )
    assert result.returncode == 0, f"Node error: {result.stderr}"
    return result.stdout.strip()


def test_format_seconds_normal():
    out = _run_node("""
import { formatSeconds } from './timer.js';
console.log(JSON.stringify([
    formatSeconds(1500),
    formatSeconds(0),
    formatSeconds(59),
    formatSeconds(60),
    formatSeconds(3599),
]));
""")
    assert json.loads(out) == ["25:00", "00:00", "00:59", "01:00", "59:59"]


def test_format_seconds_boundary():
    out = _run_node("""
import { formatSeconds } from './timer.js';
console.log(JSON.stringify([
    formatSeconds(-1),
    formatSeconds(0.5),
]));
""")
    assert json.loads(out) == ["00:00", "00:00"]


def test_calculate_progress_ratio():
    out = _run_node("""
import { calculateProgressRatio } from './timer.js';
console.log(JSON.stringify([
    calculateProgressRatio(1500, 1500),
    calculateProgressRatio(750, 1500),
    calculateProgressRatio(0, 1500),
    calculateProgressRatio(0, 0),
]));
""")
    assert json.loads(out) == [0, 0.5, 1, 0]


def test_calculate_remaining_seconds():
    out = _run_node("""
import { calculateRemainingSeconds } from './timer.js';
const now = 1000000;
console.log(JSON.stringify([
    calculateRemainingSeconds(now + 5000, now),
    calculateRemainingSeconds(now, now),
    calculateRemainingSeconds(now - 1000, now),
]));
""")
    assert json.loads(out) == [5, 0, 0]


def test_format_focused_time():
    out = _run_node("""
import { formatFocusedTime } from './timer.js';
console.log(JSON.stringify([
    formatFocusedTime(0),
    formatFocusedTime(300),
    formatFocusedTime(3600),
    formatFocusedTime(6000),
]));
""")
    assert json.loads(out) == ["0分", "5分", "1時間", "1時間40分"]


def test_compute_ring_color_endpoints():
    """進捗の両端と中央で、青→黄→赤のグラデーション色になることを確認する。"""
    out = _run_node("""
import { computeRingColor } from './timer.js';
console.log(JSON.stringify([
    computeRingColor(0),
    computeRingColor(0.5),
    computeRingColor(1),
]));
""")
    assert json.loads(out) == ["#4a90e2", "#f5c542", "#e24a4a"]


def test_compute_ring_color_clamps_out_of_range():
    """範囲外の入力や NaN を 0〜1 にクランプし、安全な色を返すことを確認する。"""
    out = _run_node("""
import { computeRingColor } from './timer.js';
console.log(JSON.stringify([
    computeRingColor(-0.5),
    computeRingColor(1.5),
    computeRingColor(Number.NaN),
]));
""")
    assert json.loads(out) == ["#4a90e2", "#e24a4a", "#4a90e2"]
