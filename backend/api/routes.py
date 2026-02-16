# backend/api/routes.py
from flask import Blueprint, jsonify, request
from core import timer
from db.database import get_connection
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/state')
def get_state():
    return jsonify(timer.get_state())


@api_bp.route('/start_focus', methods=['POST'])
def start_focus():
    success = timer.start_focus()
    if success:
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Not in IDLE state"}), 400


@api_bp.route('/complete_exercise', methods=['POST'])
def complete_exercise():
    success = timer.complete_exercise()
    if success:
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Not in EXERCISE state"}), 400


@api_bp.route('/history')
def get_history():
    history = timer.get_history()
    return jsonify({"sessions": history})


@api_bp.route('/stats/today')
def today_stats():
    today = datetime.utcnow().date().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total_sessions,
                   SUM(reps) as total_reps,
                   SUM(duration_seconds) as total_duration
            FROM sessions
            WHERE date = ?
        """, (today,))
        row = cursor.fetchone()
        
        total_sessions = row['total_sessions'] or 0
        total_reps = row['total_reps'] or 0
        total_duration = row['total_duration'] or 0
        
        cursor.execute("""
            SELECT e.name_ar, COUNT(*) as count, SUM(s.reps) as reps
            FROM sessions s
            JOIN exercises e ON s.exercise_id = e.id
            WHERE s.date = ?
            GROUP BY e.id
            ORDER BY count DESC
        """, (today,))
        exercises = [dict(r) for r in cursor.fetchall()]
    
    return jsonify({
        "date": today,
        "total_sessions": total_sessions,
        "total_reps": total_reps,
        "total_duration_minutes": round(total_duration / 60, 1),
        "exercises": exercises
    })


@api_bp.route('/settings', methods=['GET'])
def get_settings():
    """جلب الإعدادات الحالية"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_state WHERE key LIKE 'setting_%'")
        rows = {r['key']: r['value'] for r in cursor.fetchall()}
    
    return jsonify({
        "focus_duration": int(rows.get('setting_focus_duration', 25)),
        "exercise_duration": int(rows.get('setting_exercise_duration', 5))
    })


@api_bp.route('/settings', methods=['POST'])
def save_settings():
    """حفظ الإعدادات"""
    data = request.get_json()
    
    focus = data.get('focus_duration', 25)
    exercise = data.get('exercise_duration', 5)
    
    # التحقق من القيم
    if not (5 <= focus <= 120):
        return jsonify({"status": "error", "message": "Focus must be 5-120 minutes"}), 400
    if not (1 <= exercise <= 30):
        return jsonify({"status": "error", "message": "Exercise must be 1-30 minutes"}), 400
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
            ('setting_focus_duration', str(focus))
        )
        cursor.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
            ('setting_exercise_duration', str(exercise))
        )
        conn.commit()
    
    # تحديث الإعدادات في timer
    timer.update_durations(focus * 60, exercise * 60)
    
    return jsonify({"status": "ok"})


@api_bp.route('/health')
def health():
    return jsonify({"status": "healthy"})
