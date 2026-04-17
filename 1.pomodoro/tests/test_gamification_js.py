"""Tests for gamification.js pure helpers via Node.js."""
import subprocess
import json
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
JS_DIR = os.path.join(os.path.dirname(TESTS_DIR), "static", "js")


def _run_node(script: str) -> dict:
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=JS_DIR,
    )
    assert result.returncode == 0, f"Node error: {result.stderr}"
    return json.loads(result.stdout.strip())


def test_level_progress_percent_zero():
    out = _run_node("""
import { levelProgressPercent } from './gamification.js';
console.log(JSON.stringify(levelProgressPercent(0, 100)));
""")
    assert out == 0


def test_level_progress_percent_half():
    out = _run_node("""
import { levelProgressPercent } from './gamification.js';
console.log(JSON.stringify(levelProgressPercent(50, 100)));
""")
    assert out == 50


def test_level_progress_percent_zero_denominator():
    out = _run_node("""
import { levelProgressPercent } from './gamification.js';
console.log(JSON.stringify(levelProgressPercent(10, 0)));
""")
    assert out == 0


def test_chart_bar_heights_normalize_to_max():
    out = _run_node("""
import { chartBarHeights } from './gamification.js';
const data = [
  { date: '2026-04-11', completed_sessions: 1, focused_seconds: 1500 },
  { date: '2026-04-12', completed_sessions: 4, focused_seconds: 6000 },
  { date: '2026-04-13', completed_sessions: 2, focused_seconds: 3000 },
];
console.log(JSON.stringify(chartBarHeights(data)));
""")
    # 4 が最大 → 25, 100, 50
    assert out == [25, 100, 50]


def test_chart_bar_heights_all_zero():
    out = _run_node("""
import { chartBarHeights } from './gamification.js';
const data = [
  { date: '2026-04-11', completed_sessions: 0, focused_seconds: 0 },
  { date: '2026-04-12', completed_sessions: 0, focused_seconds: 0 },
];
console.log(JSON.stringify(chartBarHeights(data)));
""")
    assert out == [0, 0]


def test_chart_bar_heights_empty():
    out = _run_node("""
import { chartBarHeights } from './gamification.js';
console.log(JSON.stringify(chartBarHeights([])));
""")
    assert out == []


def test_format_day_label():
    out = _run_node("""
import { formatDayLabel } from './gamification.js';
console.log(JSON.stringify(formatDayLabel('2026-04-17')));
""")
    assert out == "4/17"
