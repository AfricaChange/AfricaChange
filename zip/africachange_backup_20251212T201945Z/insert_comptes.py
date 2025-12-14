from app import app
from database import db
from models import CompteSysteme

with app.app_context():
    comptes = [
        CompteSysteme(nom="Compte Wave Sénégal", fournisseur="Wave", pays="SN", numero="+221770001122"),
        CompteSysteme(nom="Compte Orange Money Sénégal", fournisseur="Orange Money", pays="SN", numero="+221770001133"),
        CompteSysteme(nom="Compte Orange Money Guinée", fournisseur="Orange Money", pays="GN", numero="+224620001144"),
    ]

    db.session.add_all(comptes)
    db.session.commit()
    print("✅ Comptes systèmes créés avec succès.")
