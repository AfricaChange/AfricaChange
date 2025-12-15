# extensions.py
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# CSRF global
csrf = CSRFProtect()

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://"  # OK en dev, Redis plus tard
    ),
)
