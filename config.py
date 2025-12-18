import os
from dotenv import load_dotenv
from typing import Optional

# Charge .env en local (NE PAS committer .env)
load_dotenv()


def _normalize_database_url(url: Optional[str]) -> Optional[str]:
    """
    Normalise DATABASE_URL pour SQLAlchemy selon le driver installé.
    """
    if not url:
        return None

    # Déjà spécifié
    if "postgresql+" in url:
        return url

    force_psycopg2 = os.getenv("FORCE_PSYCOPG2", "0") == "1"

    if force_psycopg2:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return url.replace("postgresql://", "postgresql+psycopg://", 1)


class Config:
    # --------------------------------------------------
    # ENV
    # --------------------------------------------------
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    IS_PRODUCTION = ENV == "production"

    APP_NAME = "AfricaChange"

    # --------------------------------------------------
    # SECRET
    # --------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-CHANGE-MOI")

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------
    raw_db = os.getenv("DATABASE_URL")

    SQLALCHEMY_DATABASE_URI = (
        _normalize_database_url(raw_db)
        or "sqlite:///instance/database.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ⚠️ Sécurité sans crash brutal
    if IS_PRODUCTION and not raw_db:
        print("⚠️ WARNING: DATABASE_URL not set in production")

    # --------------------------------------------------
    # MAINTENANCE
    # --------------------------------------------------
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "0") == "1"
    MAINTENANCE_MESSAGE = os.getenv(
        "MAINTENANCE_MESSAGE",
        "Nous effectuons une maintenance. Merci de revenir plus tard."
    )

    # --------------------------------------------------
    # COOKIES / SESSION
    # --------------------------------------------------
    SESSION_COOKIE_SECURE = True if IS_PRODUCTION else False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True

    PREFERRED_URL_SCHEME = "https" if IS_PRODUCTION else "http"

    # --------------------------------------------------
    # CSRF
    # --------------------------------------------------
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # --------------------------------------------------
    # SECURITY HEADERS (Talisman)
    # --------------------------------------------------
    CSP = {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://cdn.tailwindcss.com"
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.tailwindcss.com"
        ],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
    }

    # --------------------------------------------------
    # RATE LIMIT
    # --------------------------------------------------
    RATELIMIT_DEFAULT = os.getenv(
        "RATELIMIT_DEFAULT",
        "200 per day;50 per hour"
    )

    # --------------------------------------------------
    # SERVICES (ENV ONLY)
    # --------------------------------------------------
    OM_API_KEY = os.getenv("OM_API_KEY")
    OM_CLIENT_ID = os.getenv("OM_CLIENT_ID")
    OM_CLIENT_SECRET = os.getenv("OM_CLIENT_SECRET")
    OM_MERCHANT_KEY = os.getenv("OM_MERCHANT_KEY")
    OM_COUNTRY = os.getenv("OM_COUNTRY")
    OM_CURRENCY = os.getenv("OM_CURRENCY")

    MTN_API_KEY = os.getenv("MTN_API_KEY")
    MTN_USER_ID = os.getenv("MTN_USER_ID")
    MTN_PRIMARY_KEY = os.getenv("MTN_PRIMARY_KEY")
    MTN_ENVIRONMENT = os.getenv("MTN_ENVIRONMENT")

    PAYDUNYA_MASTER_KEY = os.getenv("PAYDUNYA_MASTER_KEY")
    PAYDUNYA_PRIVATE_KEY = os.getenv("PAYDUNYA_PRIVATE_KEY")
    PAYDUNYA_TOKEN = os.getenv("PAYDUNYA_TOKEN")
    PAYDUNYA_MODE = os.getenv("PAYDUNYA_MODE")

    MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
    MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")
