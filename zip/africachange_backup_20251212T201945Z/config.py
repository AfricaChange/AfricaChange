import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Charge .env en local (ne pas committer .env)
load_dotenv()

def _normalize_database_url(url: str | None) -> str | None:
    """
    Normalise DATABASE_URL pour SQLAlchemy selon le driver installé.
    - Si url commence par "postgresql://" et tu utilises psycopg v3, transforme en
      "postgresql+psycopg://..."
    - Si tu utilises psycopg2, transforme en "postgresql+psycopg2://..."
    Si l'URL contient déjà un +driver, on la retourne telle quelle.
    """
    if not url:
        return None
    # déjà spécifié driver ? on renvoie tel quel
    if "postgresql+" in url:
        return url
    # heuristique : si l'env FORCE_PSYCOG2 existe -> utiliser psycopg2
    force_psycopg2 = os.getenv("FORCE_PSYCOPG2", "0") == "1"
    if force_psycopg2:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    # sinon on privilégie psycopg (v3)
    return url.replace("postgresql://", "postgresql+psycopg://", 1)

class Config:
    # Environment
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"

    # Secret key
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-CHANGE-MOI")

    # DATABASE
    # Render / Heroku style: DATABASE_URL
    raw_db = os.getenv("DATABASE_URL", None)
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(raw_db) or "sqlite:///instance/database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Maintenance
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "0") == "1"
    MAINTENANCE_MESSAGE = os.getenv(
        "MAINTENANCE_MESSAGE",
        "Nous effectuons une maintenance. Merci de revenir plus tard."
    )

    # Cookies — secure uniquement en production (évite blocage local HTTP)
    IS_PRODUCTION = ENV == "production"
    SESSION_COOKIE_SECURE = bool(os.getenv("SESSION_COOKIE_SECURE", "1")) if IS_PRODUCTION else False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True

    PREFERRED_URL_SCHEME = "https" if IS_PRODUCTION else "http"

    # Flask-WTF / CSRF
    WTF_CSRF_ENABLED = True
    # définir un time limit si souhaité (en secondes) ou None
    WTF_CSRF_TIME_LIMIT = None

    # Content Security Policy (Talisman) — adapter si nécessaire
    CSP = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https://cdn.jsdelivr.net", "https://cdn.tailwindcss.com"],
        "style-src": ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
    }

    # Rate limiter default (Flask-Limiter)
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")

    # Services (laisser en ENV, pas dans le repo)
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

    # MAIL (Mailjet ou autre)
    MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
    MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")
