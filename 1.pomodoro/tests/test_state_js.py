"""Tests for state.js reducer logic via Node.js."""
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


def test_initial_state():
    out = _run_node("""
import { createInitialState } from './state.js';
console.log(JSON.stringify(createInitialState()));
""")
    assert out["mode"] == "work"
    assert out["status"] == "idle"
    assert out["remainingSeconds"] == 1500
    assert out["sessionDurationSeconds"] == 1500


def test_start_from_idle():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
const s = reducer(createInitialState(), { type: 'START' });
console.log(JSON.stringify(s));
""")
    assert out["status"] == "running"


def test_pause_from_running():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'PAUSE' });
console.log(JSON.stringify(s));
""")
    assert out["status"] == "paused"


def test_pause_from_idle_is_noop():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
const s = reducer(createInitialState(), { type: 'PAUSE' });
console.log(JSON.stringify(s));
""")
    assert out["status"] == "idle"


def test_tick_updates_remaining():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'TICK', remainingSeconds: 1200 });
console.log(JSON.stringify(s));
""")
    assert out["remainingSeconds"] == 1200
    assert out["status"] == "running"


def test_tick_while_idle_is_noop():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
const s = reducer(createInitialState(), { type: 'TICK', remainingSeconds: 100 });
console.log(JSON.stringify(s));
""")
    assert out["remainingSeconds"] == 1500


def test_reset():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'TICK', remainingSeconds: 500 });
s = reducer(s, { type: 'RESET' });
console.log(JSON.stringify(s));
""")
    assert out["status"] == "idle"
    assert out["remainingSeconds"] == 1500


def test_complete_work_session():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'COMPLETE' });
console.log(JSON.stringify(s));
""")
    assert out["status"] == "completed"
    assert out["remainingSeconds"] == 0
    assert out["todayCompleted"] == 1
    assert out["todayFocusedSeconds"] == 1500


def test_complete_break_session_does_not_count():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'SWITCH_MODE' });
s = reducer(s, { type: 'START' });
s = reducer(s, { type: 'COMPLETE' });
console.log(JSON.stringify(s));
""")
    assert out["todayCompleted"] == 0
    assert out["todayFocusedSeconds"] == 0


def test_switch_mode_work_to_break():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
const s = reducer(createInitialState(), { type: 'SWITCH_MODE' });
console.log(JSON.stringify(s));
""")
    assert out["mode"] == "break"
    assert out["remainingSeconds"] == 300
    assert out["status"] == "idle"


def test_switch_mode_blocked_during_running():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'SWITCH_MODE' });
console.log(JSON.stringify(s));
""")
    assert out["mode"] == "work"
    assert out["status"] == "running"
