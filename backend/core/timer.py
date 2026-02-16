# backend/core/timer.py
import logging
from datetime import datetime
from db.database import get_connection
from config import STATE_IDLE, STATE_FOCUS, STATE_EXERCISE

logger = logging.getLogger(__name__)
STATE_KEYS = ["current_state", "state_start_timestamp", "current_exercise_id"]

# الأوقات الافتراضية (بالثواني)
FOCUS_DURATION = 25 * 60
EXERCISE_DURATION = 5 * 60


def _load_durations():
    """تحميل الأوقات من قاعدة البيانات"""
    global FOCUS_DURATION, EXERCISE_DURATION
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM system_state WHERE key LIKE 'setting_%'")
            rows = {r['key']: r['value'] for r in cursor.fetchall()}
            
            if 'setting_focus_duration' in rows:
                FOCUS_DURATION = int(rows['setting_focus_duration']) * 60
            if 'setting_exercise_duration' in rows:
                EXERCISE_DURATION = int(rows['setting_exercise_duration']) * 60
    except:
        pass


def update_durations(focus_seconds, exercise_seconds):
    """تحديث الأوقات"""
    global FOCUS_DURATION, EXERCISE_DURATION
    FOCUS_DURATION = focus_seconds
    EXERCISE_DURATION = exercise_seconds
    logger.info(f"Durations updated: Focus={focus_seconds}s, Exercise={exercise_seconds}s")


def get_state():
    _load_durations()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value FROM system_state WHERE key IN (?, ?, ?)",
            STATE_KEYS
        )
        rows = {r["key"]: r["value"] for r in cursor.fetchall()}

        current_state = rows.get("current_state", STATE_IDLE)
        start_ts_str = rows.get("state_start_timestamp")
        exercise_id = rows.get("current_exercise_id")

        now = datetime.utcnow()
        remaining = 0
        total_duration = 0
        exercise = None
        auto_transition = None

        if current_state == STATE_FOCUS and start_ts_str:
            start_ts = datetime.fromisoformat(start_ts_str)
            elapsed = (now - start_ts).total_seconds()
            remaining = max(0, FOCUS_DURATION - elapsed)
            total_duration = FOCUS_DURATION
            if remaining == 0:
                auto_transition = "to_exercise"

        elif current_state == STATE_EXERCISE and start_ts_str:
            start_ts = datetime.fromisoformat(start_ts_str)
            elapsed = (now - start_ts).total_seconds()
            remaining = max(0, EXERCISE_DURATION - elapsed)
            total_duration = EXERCISE_DURATION

        else:
            current_state = STATE_IDLE
            remaining = 0
            total_duration = FOCUS_DURATION

    if auto_transition == "to_exercise":
        logger.info("Focus done -> Exercise")
        _start_exercise()
        return get_state()

    if exercise_id:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
            row = cursor.fetchone()
            if row:
                exercise = dict(row)

    # حساب نسبة التقدم
    progress = 0
    if total_duration > 0:
        progress = ((total_duration - remaining) / total_duration) * 100

    return {
        "state": current_state,
        "remaining_seconds": int(remaining),
        "total_seconds": int(total_duration),
        "progress": round(progress, 1),
        "exercise": exercise
    }


def _set_state(state, exercise_id=None):
    now_str = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
            ("current_state", state)
        )
        cursor.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
            ("state_start_timestamp", now_str)
        )
        if exercise_id is not None:
            cursor.execute(
                "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
                ("current_exercise_id", str(exercise_id))
            )
        else:
            cursor.execute("DELETE FROM system_state WHERE key='current_exercise_id'")
        conn.commit()
    logger.info(f"State -> {state}")


def start_focus():
    state = get_state()
    if state["state"] != STATE_IDLE:
        return False
    _set_state(STATE_FOCUS)
    logger.info("Focus started")
    return True


def _start_exercise():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM exercises ORDER BY RANDOM() LIMIT 1")
        exercise = cursor.fetchone()
    if exercise:
        _set_state(STATE_EXERCISE, exercise["id"])
    else:
        _set_state(STATE_IDLE)


def complete_exercise():
    state = get_state()
    if state["state"] != STATE_EXERCISE:
        return False

    exercise = state.get("exercise")
    if exercise:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (date, exercise_id, reps, duration_seconds)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.utcnow().date().isoformat(),
                exercise["id"],
                exercise.get("default_reps", 0),
                exercise.get("default_duration_sec", 0)
            ))
            conn.commit()
        logger.info(f"Recorded: {exercise.get('name_ar')}")

    _set_state(STATE_IDLE)
    return True


def get_history(limit=10):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.date, e.name_ar, s.reps, s.duration_seconds
            FROM sessions s
            JOIN exercises e ON s.exercise_id = e.id
            ORDER BY s.id DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
