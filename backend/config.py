# backend/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "fitops.db"
CSV_PATH = DATA_DIR / "exercises.csv"

# Production: أوقات حقيقية
FOCUS_DURATION = 25 * 60
EXERCISE_DURATION = 5 * 60

# وضع التشغيل
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

STATE_IDLE = "IDLE"
STATE_FOCUS = "FOCUS"
STATE_EXERCISE = "EXERCISE"
