# backend/main.py
import logging
import os
from flask import Flask
from config import DEBUG
from db.init_db import init_db, verify_db
from db.seed import seed_exercises
from api.routes import api_bp

# Logging
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(
        __name__,
        static_folder='../frontend',
        static_url_path='/'
    )
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    return app


def startup_checks():
    logger.info("=" * 50)
    logger.info("🚀 FitOps Timer Starting...")
    logger.info(f"📁 Mode: {'Development' if DEBUG else 'Production'}")
    logger.info("=" * 50)

    init_db()
    seed_exercises()

    if verify_db():
        logger.info("✅ Database ready")
    else:
        logger.error("❌ Database failed!")
        raise RuntimeError("Database not ready")


# تشغيل startup عند الاستيراد
startup_checks()
app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)
