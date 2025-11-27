
from flask import Flask
from config import Config
from database import db
from routes.main import main
from routes.auth import auth
from routes.exchange import exchange  # 👈 AJOUT
from routes.admin import admin  # 👈 AJOUT
from routes.paiement import paiement
from routes.convert import convert



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)              # Initialisation de la base de données


# Enregistrement de la route principale
app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(exchange)      # 👈 AJOUT
app.register_blueprint(admin)   # 👈 AJOUT
app.register_blueprint(paiement)
app.register_blueprint(convert)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()       # Crée les tables automatiquement
    app.run(debug=True)
