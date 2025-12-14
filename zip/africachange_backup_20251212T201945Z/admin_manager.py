from flask import Flask
from config import Config
from database import db
from models import Utilisateur


def create_cli_app():
    """
    Crée une petite app Flask juste pour les commandes en ligne (admin).
    On évite d'importer l'app principale pour ne pas déclencher
    des choses inutiles (blueprints, gunicorn, etc.).
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


app = create_cli_app()


def ajouter_admin(email):
    with app.app_context():
        user = Utilisateur.query.filter_by(email=email).first()
        if not user:
            print(f"❌ Utilisateur introuvable : {email}")
            return
        user.is_admin = True
        db.session.commit()
        print(f"✅ Admin ajouté : {email}")


def retirer_admin(email):
    with app.app_context():
        user = Utilisateur.query.filter_by(email=email).first()
        if not user:
            print(f"❌ Utilisateur introuvable : {email}")
            return
        user.is_admin = False
        db.session.commit()
        print(f"❌ Admin retiré : {email}")


def lister_admins():
    with app.app_context():
        admins = Utilisateur.query.filter_by(is_admin=True).all()
        if not admins:
            print("⚠️ Aucun admin enregistré.")
            return
        print("📌 Liste des admins :")
        for a in admins:
            print(f"- {a.email}")


if __name__ == "__main__":
    print("=== Gestion des admins AfricaChange ===")
    print("1 → Ajouter un admin")
    print("2 → Retirer un admin")
    print("3 → Lister les admins")
    choix = input("Votre choix : ").strip()

    if choix == "1":
        email = input("Email de l'utilisateur à promouvoir admin : ").strip()
        ajouter_admin(email)

    elif choix == "2":
        email = input("Email de l'utilisateur à retirer admin : ").strip()
        retirer_admin(email)

    elif choix == "3":
        lister_admins()

    else:
        print("❌ Choix invalide.")
