#!/usr/bin/env python3
"""
migrate_sqlite_to_postgres.py
Copie toutes les tables et leurs données d'un fichier SQLite vers la BDD PostgreSQL
(lu depuis Config.DATABASE_URL ou .env DATABASE_URL).
Exécuter une seule fois.
"""

import os
import sys
from sqlalchemy import create_engine, MetaData, select, text
from sqlalchemy.exc import SQLAlchemyError
from config import Config

# ------------- Configuration (pas besoin de toucher si .env est bon) --------------
PG_URL = Config.SQLALCHEMY_DATABASE_URI  # doit pointer vers postgresql+psycopg://...
# Emplacements possibles du fichier sqlite (on prend le premier trouvé)
CANDIDATE_SQLITE_PATHS = [
    "instance/africachange.db",
    "instance/database.db",
    "instance/africa_change.db",
    "africachange.db",
    "database.db",
]

def find_sqlite_url():
    env = os.getenv("SQLITE_PATH")
    if env:
        if not env.startswith("sqlite:///"):
            return f"sqlite:///{env}"
        return env
    for p in CANDIDATE_SQLITE_PATHS:
        if os.path.exists(p):
            return f"sqlite:///{os.path.abspath(p)}"
    return None

def main():
    sqlite_url = find_sqlite_url()
    if not sqlite_url:
        print("❌ Aucun fichier SQLite trouvé. Cherche dans :", CANDIDATE_SQLITE_PATHS)
        sys.exit(1)

    print("🔎 Source SQLite :", sqlite_url)
    print("🔎 Destination PostgreSQL :", PG_URL)

    # Connexions
    src_engine = create_engine(sqlite_url, future=True)
    dst_engine = create_engine(PG_URL, future=True)

    src_meta = MetaData()
    dst_meta = MetaData()

    try:
        # refléter la base sqlite
        src_meta.reflect(bind=src_engine)
        if not src_meta.tables:
            print("⚠️ Aucune table trouvée dans le fichier SQLite.")
            return

        # Copier la structure dans dst_meta (créera les tables si absentes)
        for tbl in src_meta.sorted_tables:
            # avoid copying SQLite-specific constraints that postgres won't like? We use to_metadata
            tbl.to_metadata(dst_meta)

        print("⏳ Création des tables manquantes sur PostgreSQL...")
        dst_meta.create_all(bind=dst_engine)
        print("✅ Structure créée (ou déjà présente).")

        # Copier les données table par table
        with src_engine.connect() as src_conn, dst_engine.connect() as dst_conn:
            for src_table in src_meta.sorted_tables:
                tbl_name = src_table.name
                print(f"\n➡️ Traitement table: {tbl_name}")

                # table correspondante dans la meta destination
                dst_table = dst_meta.tables.get(tbl_name)
                if dst_table is None:
                    print(f"  ⚠️ Table {tbl_name} absente dans destination — elle sera ignorée.")
                    continue

                # Lire toutes les lignes depuis sqlite
                sel = select(src_table)
                rows = src_conn.execute(sel).mappings().all()
                n = len(rows)
                if n == 0:
                    print(f"  (0 lignes) — rien à copier.")
                    continue

                # Convertir en liste de dicts (SQLAlchemy fonctionne avec dict)
                dict_rows = [dict(r) for r in rows]

                # Insérer par lots
                try:
                    # Utiliser transaction
                    with dst_conn.begin():
                        dst_conn.execute(dst_table.insert(), dict_rows)
                    print(f"  ✅ {n} lignes copiées dans {tbl_name}.")
                except Exception as e:
                    print(f"  ❌ Erreur insertion pour {tbl_name} : {e}")
                    # essayer une insertion ligne à ligne (plus lente) pour repérer l'erreur
                    failed = 0
                    with dst_conn.begin():
                        for r in dict_rows:
                            try:
                                dst_conn.execute(dst_table.insert(), r)
                            except Exception as e2:
                                failed += 1
                                print(f"    - ligne échouée: {e2}")
                    print(f"  Résultat insertion ligne-à-ligne: {n - failed} insérées, {failed} échouées.")

                # Ajuster sequence si la table a une colonne id numérique (Postgres SERIAL/IDENTITY)
                # On tente de récupérer la valeur maximale de la PK nommée 'id'
                try:
                    if 'id' in dst_table.c:
                        max_id = dst_conn.execute(select(dst_table.c.id).order_by(dst_table.c.id.desc()).limit(1)).scalar()
                        if max_id is not None:
                            seq_name = f"{tbl_name}_id_seq"
                            # setval — si la séquence existe
                            try:
                                dst_conn.execute(text(f"SELECT setval(:seq, :val, true)"), {"seq": seq_name, "val": int(max_id)})
                                print(f"  🔁 Séquence {seq_name} réglée sur {max_id}.")
                            except Exception:
                                # alternative: essayer find sequence name via pg_get_serial_sequence
                                try:
                                    q = dst_conn.execute(text("SELECT pg_get_serial_sequence(:tbl, 'id')"), {"tbl": tbl_name}).scalar()
                                    if q:
                                        dst_conn.execute(text("SELECT setval(:seq, :val, true)"), {"seq": q, "val": int(max_id)})
                                        print(f"  🔁 Séquence {q} réglée sur {max_id}.")
                                except Exception as e_seq:
                                    print(f"  ⚠️ Impossible d'ajuster la séquence par défaut pour {tbl_name}: {e_seq}")
                except Exception as e_seq_all:
                    print(f"  ⚠️ Erreur lors du réglage des séquences : {e_seq_all}")

        print("\n🎉 Migration terminée.")
        print("→ Vérifie maintenant dans PostgreSQL que les tables et données sont présentes.")
        print("→ Si tout est OK supprime le fichier SQLite si tu veux, ou garde-le comme archive.")
    except SQLAlchemyError as sqle:
        print("❌ Erreur SQLAlchemy :", sqle)
        raise
    except Exception as e:
        print("❌ Erreur inattendue :", e)
        raise

if __name__ == "__main__":
    main()
