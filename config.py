"""
Configuration settings for the Trio Snacks application
(Local SQLite + Vercel Serverless & PostgreSQL compatible)
"""
import os
import shutil
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))

secret_key = os.environ.get("SECRET_KEY")
database_url = os.environ.get("DATABASE_URL")

if IS_VERCEL and not secret_key:
    logger.warning(
        "SECRET_KEY environment variable is not set on Vercel. "
        "Using fallback key; set SECRET_KEY in Vercel project settings for production."
    )

# Normalizepostgres:// URI from Supabase / Neon / Render / Heroku for SQLAlchemy 2.x
if database_url:
    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

# Determine database URI
if database_url:
    SQLALCHEMY_DATABASE_URI = database_url
elif IS_VERCEL:
    # On Vercel without DATABASE_URL configured yet, copy bundled seed DB to writable /tmp
    tmp_db_path = "/tmp/database.db"
    bundled_db_path = os.path.join(BASE_DIR, "instance", "database.db")
    if not os.path.exists(tmp_db_path) and os.path.exists(bundled_db_path):
        try:
            shutil.copy2(bundled_db_path, tmp_db_path)
        except Exception as exc:
            logger.warning("Could not copy seed database to /tmp: %s", exc)
    logger.warning(
        "DATABASE_URL is not set on Vercel. Using ephemeral SQLite in /tmp/database.db. "
        "Configure DATABASE_URL with a PostgreSQL connection string for persistent storage."
    )
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_db_path}"
else:
    instance_dir = os.path.join(BASE_DIR, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(instance_dir, 'database.db')}"


class Config:
    """Application configuration class"""

    BASE_DIR = BASE_DIR
    IS_VERCEL = IS_VERCEL

    # ---------------- Flask & Security ----------------
    SECRET_KEY = secret_key or "trio-snacks-dev-secret-key-change-in-production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ---------------- Database ----------------
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ---------------- File Uploads ----------------
    UPLOAD_FOLDER = (
        "/tmp/static/images/products"
        if IS_VERCEL
        else os.path.join(BASE_DIR, "static", "images", "products")
    )
    LOGO_UPLOAD_FOLDER = (
        "/tmp/static/images"
        if IS_VERCEL
        else os.path.join(BASE_DIR, "static", "images")
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max request payload
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

    # ---------------- App Defaults ----------------
    DEFAULT_TAX_RATE = 5.0
    DEFAULT_GST_RATE = 0.0
    DEFAULT_SHOP_NAME = "Trio Snacks"
    DEFAULT_STOCK_ALERT_THRESHOLD = 10
