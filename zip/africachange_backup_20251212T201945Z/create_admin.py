from app import app
from database import db
from models import Utilisateur
from werkzeug.security import generate_password_hash

with app.app_context():
    email = "admin@africachange.com"
    password = "admin1234"

    # Vérifier si un admin existe déjà
    admin = Utilisateur.query.filter_by(email=email).first()

    if admin:
        print("⚠️ Un admin avec cet email existe déjà.")
    else:
        # Création de l’admin
        admin = Utilisateur(
            nom="Admin",
            prenom="AfricaChange",
            email=email,
            telephone="0000000000",
            mot_de_passe=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin créé avec succès !")
        print(f"Email : {email}")
        print(f"Mot de passe : {password}")
