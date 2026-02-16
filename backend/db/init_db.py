# backend/db/init_db.py
from db.database import get_connection


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY,
                name_ar TEXT NOT NULL,
                type TEXT NOT NULL,
                default_reps INTEGER DEFAULT 0,
                default_duration_sec INTEGER DEFAULT 0,
                target_area TEXT,
                description_ar TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                exercise_id INTEGER NOT NULL,
                reps INTEGER DEFAULT 0,
                duration_seconds INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (exercise_id) REFERENCES exercises(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        conn.commit()
        print("All tables created successfully!")


def verify_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t['name'] for t in cursor.fetchall()]

        required = ['exercises', 'sessions', 'system_state']
        missing = [t for t in required if t not in tables]

        if missing:
            print(f"Missing tables: {missing}")
            return False

        cursor.execute("SELECT COUNT(*) as count FROM exercises")
        count = cursor.fetchone()['count']
        print(f"Exercises: {count}, Tables: {tables}")

        if count == 0:
            print("No exercises! Run seed_exercises()")
            return False

        return True
