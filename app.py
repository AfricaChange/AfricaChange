import os

if __name__ == "__main__":
    # Local runs via `python app.py` default to development unless explicitly overridden.
    os.environ.setdefault("FLASK_ENV", "development")

from flask import Flask

from app_bootstrap.blueprints import register_blueprints
from app_bootstrap.errors import register_error_handlers
from app_bootstrap.hooks import register_request_hooks
from app_bootstrap.observability import configure_logging
from app_bootstrap.security import configure_runtime_security, register_template_globals
from config import Config
from database import db
import models


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

register_request_hooks(app)
register_template_globals(app)
talisman = configure_runtime_security(app)
configure_logging(app)
register_blueprints(app)
register_error_handlers(app)


if __name__ == "__main__":
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        with app.app_context():
            db.create_all()

    app.run(debug=True)
