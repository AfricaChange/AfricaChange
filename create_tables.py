from app import app
from database import db
from models import Parametre  # important : importer le modèle pour qu'il soit connu

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tables créées / mises à jour dans PostgreSQL.")
