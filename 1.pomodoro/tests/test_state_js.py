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


def test_initial_state_accepts_custom_durations():
    out = _run_node("""
import { createInitialState } from './state.js';
const s = createInitialState({ workDurationSeconds: 15 * 60, breakDurationSeconds: 10 * 60 });
console.log(JSON.stringify(s));
""")
    assert out["workDurationSeconds"] == 900
    assert out["breakDurationSeconds"] == 600
    assert out["sessionDurationSeconds"] == 900
    assert out["remainingSeconds"] == 900


def test_update_durations_resets_work_to_new_value_when_idle():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = createInitialState();
s = reducer(s, { type: 'UPDATE_DURATIONS', workDurationSeconds: 45 * 60 });
console.log(JSON.stringify(s));
""")
    assert out["workDurationSeconds"] == 2700
    assert out["sessionDurationSeconds"] == 2700
    assert out["remainingSeconds"] == 2700
    assert out["status"] == "idle"


def test_update_durations_only_break_keeps_current_work_duration():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = createInitialState();
s = reducer(s, { type: 'UPDATE_DURATIONS', breakDurationSeconds: 15 * 60 });
console.log(JSON.stringify(s));
""")
    assert out["workDurationSeconds"] == 1500
    assert out["breakDurationSeconds"] == 900


def test_update_durations_in_break_mode_reflects_new_break_duration():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = createInitialState();
s = reducer(s, { type: 'SWITCH_MODE' });
s = reducer(s, { type: 'UPDATE_DURATIONS', breakDurationSeconds: 10 * 60 });
console.log(JSON.stringify(s));
""")
    assert out["mode"] == "break"
    assert out["breakDurationSeconds"] == 600
    assert out["sessionDurationSeconds"] == 600
    assert out["remainingSeconds"] == 600


def test_update_durations_blocked_while_running():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'UPDATE_DURATIONS', workDurationSeconds: 45 * 60 });
console.log(JSON.stringify(s));
""")
    assert out["workDurationSeconds"] == 1500
    assert out["status"] == "running"


def test_update_durations_blocked_while_paused():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = reducer(createInitialState(), { type: 'START' });
s = reducer(s, { type: 'PAUSE' });
s = reducer(s, { type: 'UPDATE_DURATIONS', workDurationSeconds: 45 * 60 });
console.log(JSON.stringify(s));
""")
    assert out["workDurationSeconds"] == 1500
    assert out["status"] == "paused"


def test_reset_respects_custom_work_duration():
    out = _run_node("""
import { createInitialState, reducer } from './state.js';
let s = createInitialState({ workDurationSeconds: 35 * 60 });
s = reducer(s, { type: 'START' });
s = reducer(s, { type: 'TICK', remainingSeconds: 100 });
s = reducer(s, { type: 'PAUSE' });
s = reducer(s, { type: 'RESET' });
console.log(JSON.stringify(s));
""")
    assert out["status"] == "idle"
    assert out["remainingSeconds"] == 2100
    assert out["sessionDurationSeconds"] == 2100


def test_allowed_minutes_exported():
    out = _run_node("""
import { ALLOWED_WORK_MINUTES, ALLOWED_BREAK_MINUTES } from './state.js';
console.log(JSON.stringify({ work: ALLOWED_WORK_MINUTES, brk: ALLOWED_BREAK_MINUTES }));
""")
    assert out["work"] == [15, 25, 35, 45]
    assert out["brk"] == [5, 10, 15]
