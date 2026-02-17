# backend/db/seed.py
import csv
from db.database import get_connection
from config import CSV_PATH


def seed_exercises():
    """ملء جدول exercises من CSV أو defaults"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM exercises")
        count = cursor.fetchone()["count"]

        if count > 0:
            print(f"✅ Exercises: {count} rows exist. Skipping.")
            return

        # محاولة تحميل من CSV
        if CSV_PATH.exists():
            try:
                print("📂 Loading from CSV...")
                with open(CSV_PATH, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows_inserted = 0
                    for row in reader:
                        # التحقق من وجود الأعمدة المطلوبة
                        if 'id' not in row or 'name_ar' not in row:
                            print("⚠️  CSV missing headers, using defaults...")
                            _seed_defaults(cursor)
                            conn.commit()
                            return
                        
                        cursor.execute("""
                            INSERT INTO exercises
                            (id, name_ar, type, default_reps, default_duration_sec, target_area, description_ar)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(row['id']), row['name_ar'], row['type'],
                            int(row['default_reps']), int(row['default_duration_sec']),
                            row['target_area'], row['description_ar']
                        ))
                        rows_inserted += 1
                    
                    conn.commit()
                    print(f"✅ {rows_inserted} exercises loaded from CSV!")
                    return
            except Exception as e:
                print(f"⚠️  Error reading CSV: {e}")
                print("📝 Using default exercises...")

        # إذا فشل كل شي، استخدم defaults
        _seed_defaults(cursor)
        conn.commit()


def _seed_defaults(cursor):
    """تمارين افتراضية"""
    defaults = [
        (1, 'ضغط', 'reps', 15, 60, 'صدر', 'تمرين ضغط كلاسيكي'),
        (2, 'قرفصاء', 'reps', 20, 60, 'أرجل', 'قرفصاء بوزن الجسم'),
        (3, 'بلانك', 'duration', 0, 45, 'بطن', 'ثبات على وضع البلانك'),
        (4, 'قفز', 'reps', 30, 60, 'كارديو', 'قفز في المكان'),
        (5, 'لنجز', 'reps', 12, 60, 'أرجل', 'لنجز أمامي متبادل'),
        (6, 'جسر', 'reps', 15, 60, 'ظهر', 'رفع الوركين'),
        (7, 'سوبرمان', 'duration', 0, 30, 'ظهر', 'رفع اليدين والرجلين'),
        (8, 'تمدد الرقبة', 'duration', 0, 60, 'رقبة', 'تمدد جانبي للرقبة'),
    ]
    
    for ex in defaults:
        cursor.execute("""
            INSERT INTO exercises
            (id, name_ar, type, default_reps, default_duration_sec, target_area, description_ar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ex)
    
    print(f"✅ {len(defaults)} default exercises inserted!")
