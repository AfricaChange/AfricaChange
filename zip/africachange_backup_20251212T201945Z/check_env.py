"""
check_env.py
Audit des variables d'environnement pour AfricaChange
À lancer AVANT tout déploiement (local / Render / prod).
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("FLASK_ENV", "production")
DEBUG = ENV == "development"

REQUIRED_ALWAYS = [
    "SECRET_KEY",
    "DATABASE_URL",
]

OPTIONAL_BUT_SENSITIVE = [
    "OM_CLIENT_ID",
    "OM_CLIENT_SECRET",
    "OM_API_KEY",
    "OM_MERCHANT_KEY",
    "WAVE_API_KEY",
    "MAILJET_API_KEY",
    "MAILJET_SECRET_KEY",
]

WARNINGS = []
ERRORS = []

def check_required():
    for var in REQUIRED_ALWAYS:
        if not os.getenv(var):
            ERRORS.append(f"❌ Variable obligatoire manquante : {var}")

def check_secret_strength():
    key = os.getenv("SECRET_KEY", "")
    if DEBUG:
        return
    if len(key) < 32:
        WARNINGS.append(
            "⚠️ SECRET_KEY trop courte (< 32 caractères). Utilise une clé forte."
        )

def check_database():
    db = os.getenv("DATABASE_URL", "")
    if db.startswith("sqlite") and not DEBUG:
        WARNINGS.append(
            "⚠️ DATABASE_URL utilise SQLite en production (fortement déconseillé)."
        )

def check_sensitive_vars():
    for var in OPTIONAL_BUT_SENSITIVE:
        if not os.getenv(var):
            WARNINGS.append(f"ℹ️ Variable optionnelle non définie : {var}")

def summary():
    print("\n================ AfricaChange – ENV CHECK ================\n")
    print(f"ENVIRONMENT : {ENV}")
    print(f"DEBUG       : {DEBUG}")
    print("----------------------------------------------------------")

    if ERRORS:
        print("\n🚨 ERREURS BLOQUANTES :")
        for e in ERRORS:
            print(" ", e)
    else:
        print("\n✅ Aucune erreur bloquante détectée.")

    if WARNINGS:
        print("\n⚠️ AVERTISSEMENTS :")
        for w in WARNINGS:
            print(" ", w)
    else:
        print("\n✅ Aucun avertissement.")

    print("\n==========================================================")

    if ERRORS:
        print("\n⛔ Déploiement INTERDIT tant que les erreurs existent.\n")
        sys.exit(1)
    else:
        print("\n✅ Environnement OK pour exécution.\n")
        sys.exit(0)

if __name__ == "__main__":
    check_required()
    check_secret_strength()
    check_database()
    check_sensitive_vars()
    summary()
