"""
package_release.py
- Zippe le projet en excluant fichiers sensibles par défaut
- Crée manifest.txt (liste de fichiers inclus)
- Génère deployment_notes PDF (reportlab) et un fallback TXT
- Calcule SHA256 du zip et écrit zipname.sha256
- Optionnel : génère LICENSE (MIT) si demandé via ARG --license
- Place tous les artefacts dans ZIP_DIR

Usage:
  python package_release.py
  python package_release.py --include-env    # inclure .env (danger : contient secrets)
  python package_release.py --license MIT    # créer un fichier LICENSE (MIT) inclus
"""

import os
import sys
import zipfile
import hashlib
from datetime import datetime
from argparse import ArgumentParser

# ---------- CONFIG ----------
PROJECT_DIR = os.path.abspath(".")
ZIP_DIR = r"C:\Users\7MAKSACOD PC\Documents\Africa_change_project\africa-change-dev\zip"
PROJECT_NAME = os.path.basename(PROJECT_DIR.rstrip(os.sep)) or "project"
EXCLUDE_PATTERNS = [
    ".git", ".venv", "venv", "__pycache__", ".pyc", ".db", ".sqlite", ".sqlite3",
    "node_modules", ".cache", ZIP_DIR  # avoid zipping output dir
]
# ----------------------------

parser = ArgumentParser()
parser.add_argument("--include-env", action="store_true", help="Inclure .env (ATTENTION: risques de fuite de secrets)")
parser.add_argument("--license", nargs="?", const="MIT", help="Ajouter un fichier LICENSE (par ex. MIT)")
args = parser.parse_args()

if not os.path.exists(ZIP_DIR):
    os.makedirs(ZIP_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
zip_name = f"{PROJECT_NAME}_release_{timestamp}.zip"
zip_path = os.path.join(ZIP_DIR, zip_name)
manifest_path = os.path.join(ZIP_DIR, f"{PROJECT_NAME}_manifest_{timestamp}.txt")
pdf_path = os.path.join(ZIP_DIR, f"deployment_notes_{timestamp}.pdf")
sha_path = zip_path + ".sha256"
license_path = os.path.join(ZIP_DIR, f"LICENSE_{timestamp}.txt") if args.license else None

# Adjust exclude if user requested include-env
excluded = list(EXCLUDE_PATTERNS)
if not args.include_env:
    excluded.append(".env")

print("Packaging project:", PROJECT_DIR)
print("Output dir:", ZIP_DIR)
print("Excluded patterns:", excluded)

# Helper: should we exclude this file/dir?
def is_excluded(path):
    for pat in excluded:
        # match by name or prefix
        if pat and (pat in path or os.path.basename(path) == pat or path.startswith(os.path.abspath(pat))):
            return True
    return False

# Create manifest & zip
files_included = []
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(PROJECT_DIR):
        # skip zip output dir
        if os.path.abspath(root).startswith(os.path.abspath(ZIP_DIR)):
            continue
        # filter dirs in-place to speed up os.walk
        dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, PROJECT_DIR)
            if is_excluded(rel) or is_excluded(full):
                continue
            # skip large binary caches optionally (keep code)
            if f.endswith((".pyc", ".pyo", ".db", ".sqlite", ".zip")):
                continue
            files_included.append(rel)
            zf.write(full, arcname=rel)

# Write manifest
with open(manifest_path, "w", encoding="utf-8") as mf:
    mf.write(f"Manifest for {PROJECT_NAME} - generated {datetime.now().isoformat()}\n\n")
    for p in sorted(files_included):
        mf.write(p + "\n")

print("ZIP créé :", zip_path)
print("Manifest créé :", manifest_path)

# Calculate SHA256
h = hashlib.sha256()
with open(zip_path, "rb") as fh:
    for chunk in iter(lambda: fh.read(8192), b""):
        h.update(chunk)
digest = h.hexdigest()
with open(sha_path, "w") as sf:
    sf.write(f"{digest}  {os.path.basename(zip_path)}\n")

print("SHA256 écrit :", sha_path)

# Optionally add LICENSE (minimal MIT)
if args.license:
    mit_text = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
... (texte abrégé : remplace par ton texte complet si besoin) ...
""".format(year=datetime.now().year, author=os.getenv("USER", "AfricaChange"))
    with open(license_path, "w", encoding="utf-8") as lf:
        lf.write(mit_text)
    print("LICENSE créé :", license_path)
    # also append license to zip
    with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as zf:
        zf.write(license_path, arcname=os.path.basename(license_path))

# Generate deployment notes PDF (requires reportlab)
notes = f"""
AfricaChange - Deployment Notes
Generated: {datetime.now().isoformat()}

Project: {PROJECT_NAME}
Source: {PROJECT_DIR}
Zip: {zip_path}
SHA256: {digest}

Included files (excerpt):
{os.linesep.join(sorted(files_included)[:200])}

Commands importantes :
- git init / add / commit / push
- pip install -r requirements.txt
- pip install reportlab
- Procfile: web: gunicorn --bind 0.0.0.0:$PORT app:app

Variables d'environnement à vérifier :
- DATABASE_URL (postgresql+psycopg://...)
- SECRET_KEY
- OM_CLIENT_ID OM_CLIENT_SECRET OM_MERCHANT_KEY OM_API_KEY
- WAVE_API_KEY, WAVE_API_URL

Ne pas oublier :
- Ne pas committer .env ni clefs privées
- Configurer Render/Railway variables d'environnement
"""
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    width, height = A4
    c = canvas.Canvas(pdf_path, pagesize=A4)
    margin = 40
    textobject = c.beginText(margin, height - margin)
    textobject.setFont("Helvetica", 10)
    for line in notes.splitlines():
        textobject.textLine(line)
        if textobject.getY() < margin:
            c.drawText(textobject)
            c.showPage()
            textobject = c.beginText(margin, height - margin)
            textobject.setFont("Helvetica", 10)
    c.drawText(textobject)
    c.showPage()
    c.save()
    print("PDF généré :", pdf_path)
except Exception as e:
    # fallback: write TXT
    txt_path = os.path.join(ZIP_DIR, f"deployment_notes_{timestamp}.txt")
    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write(notes)
    print("Reportlab absent ou erreur PDF. Fallback TXT écrit :", txt_path)

print("\nTous les artefacts sont dans :", ZIP_DIR)
