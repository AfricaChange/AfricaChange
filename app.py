
from flask import Flask, render_template
from config import Config
from database import db
from routes.main import main
from routes.auth import auth
from routes.exchange import exchange  # 👈 AJOUT
from routes.admin import admin  # 👈 AJOUT
from routes.paiement import paiement
from routes.convert import convert
from flask_wtf.csrf import CSRFError, generate_csrf
from extensions import csrf



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)              # Initialisation de la base de données

# Initialisation CSRF
csrf.init_app(app)

# 🔁 Injection du helper csrf_token() dans les templates
@app.context_processor
def inject_globals():
    return dict(
        csrf_token=generate_csrf,
        config=app.config
    )
    
    
    
    
    
# 🔴🔴🔴 MIDDLEWARE DE MAINTENANCE 🔴🔴🔴
@app.before_request
def check_maintenance_mode():
    # On ignore les fichiers statiques
    if request.endpoint == 'static':
        return

    # Si pas en maintenance → on laisse passer
    if not app.config.get("MAINTENANCE_MODE", False):
        return

    # Si l’admin est connecté → il peut continuer à tout utiliser
    if session.get("is_admin"):
        return

    # On laisse quand même la page de maintenance elle-même
    if request.endpoint == 'maintenance':
        return

    # Sinon : on affiche la page maintenance avec un code 503
    message = app.config.get("MAINTENANCE_MESSAGE", "")
    return render_template("maintenance.html", message=message), 503


# Route dédiée (permet aussi de la tester directement)
@app.route("/maintenance")
def maintenance():
    message = app.config.get("MAINTENANCE_MESSAGE", "")
    return render_template("maintenance.html", message=message), 503

    


# Enregistrement de la route principale
app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(exchange)      # 👈 AJOUT
app.register_blueprint(admin)   # 👈 AJOUT
app.register_blueprint(paiement)
app.register_blueprint(convert)




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
    with app.app_context():
        db.create_all()       # Crée les tables automatiquement
    app.run(debug=True)
