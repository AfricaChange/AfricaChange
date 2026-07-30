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
        force_https=True,
        session_cookie_secure=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
    )
