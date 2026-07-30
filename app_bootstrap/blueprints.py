from paiements.routes import paiements_bp
from routes.admin import admin
from routes.admin_actions_routes import admin_actions_bp
from routes.admin_transactions import admin_tx
from routes.auth import auth
from routes.convert import convert
from routes.data import data_bp
from routes.legal import legal
from routes.main import main
from routes.paiement import paiement
from routes.support import support
from webhook import webhook_bp


def register_blueprints(app):
    """Register active application blueprints in their historical order."""
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(paiement)
    app.register_blueprint(convert)
    app.register_blueprint(admin_tx)
    app.register_blueprint(admin_actions_bp)
    app.register_blueprint(support)
    app.register_blueprint(paiements_bp, url_prefix="/paiements")
    app.register_blueprint(webhook_bp)
    app.register_blueprint(legal)
    app.register_blueprint(data_bp)

    # Legacy active component:
    # `routes/admin_realtime.py` remains intentionally unregistered here.
    # It is still referenced by the admin UI and must be handled explicitly
    # in a future structural pass before any behavioral change is introduced.
