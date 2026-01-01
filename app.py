from flask import Flask, render_template,session, request
from config import Config
from database import db
from routes.main import main
from routes.auth import auth
from routes.admin import admin  # 👈 AJOUT
from routes.paiement import paiement
from routes.convert import convert
from flask_wtf.csrf import CSRFError, generate_csrf
from extensions import csrf
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from datetime import timedelta
from extensions import limiter
from routes.admin_transactions import admin_tx
from routes.admin_actions_routes import admin_actions_bp
import models 





app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)              # Initialisation de la base de données

#from migrations.ensure_schema import( ensure_paiement_transaction_reference,
#    ensure_paiement_idempotency_key
#)
#
#with app.app_context():
#   ensure_paiement_transaction_reference()
#  ensure_paiement_idempotency_key()


#une expiration de session
app.permanent_session_lifetime = timedelta(minutes=30)

# Initialisation CSRF
csrf.init_app(app)

# 🔁 Injection du helper csrf_token() dans les templates
@app.context_processor
def inject_globals():
    return {
        "csrf_token": generate_csrf,
        "config": app.config,   # 👈 permet d’utiliser config.MAINTENANCE_MODE dans les templates
    }

  

limiter.init_app(app)

# ---------- CSRF ----------
# si tu as blueprints, CSRFProtect couvrira tout automatiquement

# ---------- Security Headers via Talisman ----------
csp = app.config.get("CSP", None)
talisman = Talisman(
    app,
    content_security_policy=csp,
    force_https=True,               # redirige vers HTTPS en prod
    session_cookie_secure=True,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,  # 1 an
    strict_transport_security_include_subdomains=True,
)


# ---------- Logging : ne pas logguer secret (production) ----------
if not app.debug:
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "africachange_errors.log")

    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)

  
   
    
# 🔴🔴🔴 MIDDLEWARE DE MAINTENANCE 🔴🔴🔴
@app.before_request
def check_maintenance_mode():
    # Laisser passer les fichiers statiques
    if request.endpoint == 'static':
        return

    # Laisser passer la page de maintenance elle-même
    if request.endpoint in ('maintenance',):
        return

    # Admin connecté : accès complet même en maintenance
    if session.get("is_admin"):
        return

    # 1️⃣ Regarder d'abord en base
    try:
        param = Parametre.query.filter_by(cle="maintenance_mode").first()
        db_mode_on = bool(param and param.valeur == "on")
    except Exception:
        # En cas de souci de DB → on tombe sur la config
        db_mode_on = False

    # 2️⃣ Si pas de paramètre en base → fallback config (MAINTENANCE_MODE via .env)
    maintenance_on = db_mode_on or app.config.get("MAINTENANCE_MODE", False)

    if not maintenance_on:
        return

    # Message perso : d’abord DB, sinon config
    msg_param = Parametre.query.filter_by(cle="maintenance_message").first()
    message = (
        msg_param.valeur if msg_param and msg_param.valeur
        else app.config.get("MAINTENANCE_MESSAGE", "")
    )

    return render_template("maintenance.html", message=message), 503

def maintenance():
    message = app.config.get("MAINTENANCE_MESSAGE", "")
    return render_template("maintenance.html", message=message), 503

    


# Enregistrement de la route principale
app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(admin)   # 👈 AJOUT
app.register_blueprint(paiement)
app.register_blueprint(convert)
app.register_blueprint(admin_tx)
app.register_blueprint(admin_actions_bp)



# -----------------------------
# 🔴 GESTION DES PAGES D’ERREUR
# -----------------------------

# 404 – Page non trouvée
@app.errorhandler(404)
def page_not_found(error):
    # Le template 404.html doit être dans /templates
    return render_template("404.html"), 404

# 500 – Erreur interne serveur
@app.errorhandler(500)
def internal_server_error(error):
    # Le template 500.html doit être dans /templates
    return render_template("500.html"), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    # Template simple qui explique que le formulaire a expiré
    return render_template("csrf_error.html", reason=e.description), 400





if __name__ == '__main__':
    # ⚠️ Créer les tables UNIQUEMENT en local avec SQLite
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        with app.app_context():
            db.create_all()

    app.run(debug=True)

