#!/usr/bin/env python3
"""
package_project.py

Usage:
  python package_project.py                # crée l'archive sans .env
  python package_project.py --include-env  # inclut .env dans l'archive (attention)
  python package_project.py --exclude "*.sqlite,instance/*.db"  # exclude patterns comma-separated

Sortie:
 - africachange_backup_YYYYMMDDTHHMMSSZ.zip
 - MANIFEST.md
 - files.json
"""
import os
import zipfile
import hashlib
import json
import argparse
from datetime import datetime
from fnmatch import fnmatch

ROOT = os.path.abspath(os.path.dirname(__file__))

DEFAULT_EXCLUDES = [
    ".git", ".git/*", "__pycache__", "venv", ".venv",
    "*.pyc", "*.pyo", "*.swp", "*.swo", "*.tmp",
    "node_modules", "dist", "build", ".pytest_cache",
    ".idea", ".vscode",
    "instance/*.sqbpro", "instance/*.db.bak", "instance/*.db",  # garder si nécessaire mais recommandé d'exclure
    "*.zip"
]

def parse_args():
    p = argparse.ArgumentParser(description="Pack project into zip + manifest")
    p.add_argument("--include-env", action="store_true", help="Inclure le fichier .env (ATTENTION: contient des secrets)")
    p.add_argument("--exclude", type=str, default="", help="Liste patterns séparés par des virgules à exclure en plus")
    p.add_argument("--outdir", type=str, default=".", help="Dossier de sortie pour l'archive et manifest")
    return p.parse_args()

def build_exclude_list(include_env: bool, extra: str):
    excludes = list(DEFAULT_EXCLUDES)
    if not include_env:
        excludes.append(".env")
        excludes.append(".env.*")
    # parse extra
    if extra:
        for it in extra.split(","):
            it = it.strip()
            if it:
                excludes.append(it)
    # normalize patterns to use forward slashes
    return [p.replace("\\", "/") for p in excludes]

def should_exclude(relpath, exclude_patterns):
    # normalize to posix style
    rel = relpath.replace("\\", "/")
    for pat in exclude_patterns:
        if fnmatch(rel, pat) or rel.startswith(pat.rstrip("*")):
            return True
    # ignore the output zip(s) created by this script
    if rel.startswith("africachange_backup_") and rel.endswith(".zip"):
        return True
    return False

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def gather_files(root, exclude_patterns):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # remove excluded directories from traversal early
        # convert dirpath to rel
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        # skip hidden .git etc if matched
        # modify dirnames in-place to prevent walking
        dirnames[:] = [d for d in dirnames if not should_exclude(os.path.normpath(os.path.join(rel_dir, d)).replace("\\","/"), exclude_patterns)]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if should_exclude(rel, exclude_patterns):
                continue
            # skip editor swap/backups
            if fn.endswith("~") or fn.endswith(".swp") or fn.endswith(".swo"):
                continue
            files.append((full, rel))
    return files

def write_manifest_and_json(outdir, zip_name, manifest_list):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    mdpath = os.path.join(outdir, "MANIFEST.md")
    jsonpath = os.path.join(outdir, "files.json")
    with open(mdpath, "w", encoding="utf-8") as f:
        f.write(f"# Manifest du projet AfricaChange\n\n")
        f.write(f"- Archive: `{zip_name}`\n")
        f.write(f"- Généré: {ts}\n\n")
        f.write("## Fichiers inclus (path — sha256)\n\n")
        for item in manifest_list:
            f.write(f"- `{item['path']}` — `{item['sha256']}`\n")
    with open(jsonpath, "w", encoding="utf-8") as j:
        json.dump({
            "archive": zip_name,
            "generated": ts,
            "files": manifest_list
        }, j, indent=2, ensure_ascii=False)
    return mdpath, jsonpath

def main():
    args = parse_args()
    exclude_patterns = build_exclude_list(args.include_env, args.exclude)
    outdir = os.path.abspath(args.outdir)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    zip_name = f"africachange_backup_{timestamp}.zip"
    zip_path = os.path.join(outdir, zip_name)

    print("Racine projet :", ROOT)
    print("Exclure patterns :", exclude_patterns)
    print("Création de l'archive...")

    files = gather_files(ROOT, exclude_patterns)
    print(f"Fichiers collectés: {len(files)}")

    manifest = []
    # write zip
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for full, rel in files:
            z.write(full, rel)
            sha = sha256_of_file(full)
            manifest.append({"path": rel, "sha256": sha})
    mdpath, jsonpath = write_manifest_and_json(outdir, zip_name, manifest)

    print("Archive créée :", zip_path)
    print("Manifest :", mdpath)
    print("Fichier JSON :", jsonpath)
    print("\nATTENTION : si tu as inclus .env, vérifie son contenu avant de partager l'archive.")
    print("Si tu veux que je prenne l'archive, dis-moi où tu l'as placé ou envoie-la via l'interface.")

if __name__ == "__main__":
    main()
