from flask_talisman import Talisman
from flask_wtf.csrf import generate_csrf

from extensions import limiter


def register_template_globals(app):
    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": generate_csrf,
            "config": app.config,
        }


def configure_runtime_security(app):
    limiter.init_app(app)
    return Talisman(
        app,
        content_security_policy=None,
        force_https=bool(app.config.get("IS_PRODUCTION", False)),
        session_cookie_secure=bool(app.config.get("SESSION_COOKIE_SECURE", False)),
        strict_transport_security=bool(app.config.get("IS_PRODUCTION", False)),
        strict_transport_security_max_age=31536000 if app.config.get("IS_PRODUCTION", False) else None,
        strict_transport_security_include_subdomains=bool(app.config.get("IS_PRODUCTION", False)),
    )
