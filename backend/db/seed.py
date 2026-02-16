# backend/db/seed.py
import csv
from db.database import get_connection
from config import CSV_PATH


def seed_exercises():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM exercises")
        count = cursor.fetchone()["count"]

        if count > 0:
            print(f"Exercises: {count} rows exist. Skipping.")
            return

        if not CSV_PATH.exists():
            print("CSV not found. Inserting defaults...")
            _seed_defaults(cursor)
            conn.commit()
            return

        print("Loading from CSV...")
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT INTO exercises
                    (id, name_ar, type, default_reps, default_duration_sec, target_area, description_ar)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['id']), row['name_ar'], row['type'],
                    int(row['default_reps']), int(row['default_duration_sec']),
                    row['target_area'], row['description_ar']
                ))

        conn.commit()
        print("Exercises seeded from CSV!")


def _seed_defaults(cursor):
    defaults = [
        (1, 'ضغط', 'reps', 15, 60, 'صدر', 'تمرين ضغط كلاسيكي'),
        (2, 'قرفصاء', 'reps', 20, 60, 'أرجل', 'قرفصاء بوزن الجسم'),
        (3, 'بلانك', 'duration', 0, 45, 'بطن', 'ثبات على وضع البلانك'),
        (4, 'قفز', 'reps', 25, 60, 'كارديو', 'قفز في المكان'),
        (5, 'لنجز', 'reps', 12, 60, 'أرجل', 'لنجز أمامي متبادل'),
    ]
    for ex in defaults:
        cursor.execute("""
            INSERT INTO exercises
            (id, name_ar, type, default_reps, default_duration_sec, target_area, description_ar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ex)
    print("Default exercises inserted!")
