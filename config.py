import os
from dotenv import load_dotenv

load_dotenv()  # Charge les variables depuis .env (en local)

class Config:
    # 🌱 Environnement : "development" ou "production"
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"

    # 🔐 Clé secrète
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-CHANGE-MOI")

    # 🗄 Base de données
    # Render te fournit DATABASE_URL dans les variables d'env
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "sqlite:///instance/database.db"  # fallback en local si pas de DB
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
     # 🔐 Maintenance
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "0") == "1"
    MAINTENANCE_MESSAGE = os.getenv(
        "MAINTENANCE_MESSAGE",
        "Nous effectuons une maintenance. Merci de revenir plus tard."
    )

    # 🔐 Sécurité des cookies
    SESSION_COOKIE_SECURE = True        # cookie envoyé seulement en HTTPS
    SESSION_COOKIE_HTTPONLY = True      # non accessible via JS
    SESSION_COOKIE_SAMESITE = "Lax"     # limite CSRF basique

    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    PREFERRED_URL_SCHEME = "https"
       
    # Flask-WTF (CSRF)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # ou un nombre en secondes si tu veux expirer tokens

    # Talisman / CSP - valeurs par défaut ; adapte si besoin
    CSP = {
        "default-src": ["'self'"],
        "script-src": ["'self'","https://cdn.jsdelivr.net","https://cdn.tailwindcss.com"],
        "style-src": ["'self'","'unsafe-inline'","https://cdn.tailwindcss.com"],
        "img-src": ["'self'","data:"],
        "font-src": ["'self'","https://fonts.gstatic.com"],
    }

    # Rate limiter defaults (Flask-Limiter)
    RATELIMIT_DEFAULT = "200 per day;50 per hour"   
       
    # Orange Money (on garde, mais en pause pour l’instant)
    OM_API_KEY = os.getenv("OM_API_KEY")
    OM_CLIENT_ID = os.getenv("OM_CLIENT_ID")
    OM_CLIENT_SECRET = os.getenv("OM_CLIENT_SECRET")
    OM_MERCHANT_KEY = os.getenv("OM_MERCHANT_KEY")
    OM_COUNTRY = os.getenv("OM_COUNTRY")
    OM_CURRENCY = os.getenv("OM_CURRENCY")

    # MTN MoMo
    MTN_API_KEY = os.getenv("MTN_API_KEY")
    MTN_USER_ID = os.getenv("MTN_USER_ID")
    MTN_PRIMARY_KEY = os.getenv("MTN_PRIMARY_KEY")
    MTN_ENVIRONMENT = os.getenv("MTN_ENVIRONMENT")

    # PayDunya
    PAYDUNYA_MASTER_KEY = os.getenv("PAYDUNYA_MASTER_KEY")
    PAYDUNYA_PRIVATE_KEY = os.getenv("PAYDUNYA_PRIVATE_KEY")
    PAYDUNYA_TOKEN = os.getenv("PAYDUNYA_TOKEN")
    PAYDUNYA_MODE = os.getenv("PAYDUNYA_MODE")
