from app import app
from database import db

with app.app_context():
    db.create_all()
    print("🎉 Tables PostgreSQL créées avec succès !")
