import sqlite3
from app import app, db
from sqlalchemy import inspect

# === CONFIGURATION ===
DB_PATH = "instance/africachange.db"

# Correspondance des renommages manuels
RENAMES = {
    "conversion": {
        "montant": "montant_initial",
    }
}


def get_existing_columns(cursor, table_name):
    """Retourne la liste des colonnes d'une table SQLite (protège les noms réservés)"""
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    return [col[1] for col in cursor.fetchall()]


def get_all_models():
    """Récupère toutes les classes de modèles SQLAlchemy (compatible SQLAlchemy 2.x)"""
    models = []
    try:
        models = db.Model._decl_class_registry.values()  # SQLAlchemy < 2.0
    except AttributeError:
        registry = getattr(db.Model, "registry", None)
        if registry and hasattr(registry, "mappers"):
            models = [mapper.class_ for mapper in registry.mappers]
    return [m for m in models if hasattr(m, "__tablename__")]


def sync_database():
    """Synchronise la base SQLite avec les modèles SQLAlchemy"""
    with app.app_context():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        inspector = inspect(db.engine)

        print("\n🔍 Vérification de la cohérence base ↔ modèles...\n")

        models = get_all_models()
        modified = False  # Indique si des changements ont été effectués

        for model in models:
            table = model.__tablename__
            print(f"📋 Table : {table}")

            existing_cols = get_existing_columns(cursor, table)
            model_cols = {col.name: col.type for col in model.__table__.columns}

            for col_name, col_type in model_cols.items():
                if col_name not in existing_cols:
                    print(f"  ➕ Ajout de colonne manquante : {col_name}")

                    sql_type = "TEXT"
                    if "INTEGER" in str(col_type).upper():
                        sql_type = "INTEGER"
                    elif "FLOAT" in str(col_type).upper() or "REAL" in str(col_type).upper():
                        sql_type = "REAL"
                    elif "DATETIME" in str(col_type).upper():
                        sql_type = "DATETIME"

                    # ✅ Protège les noms de table et colonne avec guillemets
                    cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col_name}" {sql_type}')
                    modified = True

            # ✅ Gérer les renommages (facultatif)
            if table in RENAMES:
                for old_col, new_col in RENAMES[table].items():
                    if old_col in existing_cols and new_col not in existing_cols:
                        print(f"  🔄 Renommage de colonne : {old_col} → {new_col}")
                        cursor.execute(f'ALTER TABLE "{table}" RENAME COLUMN "{old_col}" TO "{new_col}"')
                        modified = True

        conn.commit()
        conn.close()

        if modified:
            print("\n✅ Synchronisation terminée avec succès. Les changements ont été appliqués !\n")
        else:
            print("\n✅ Base de données déjà à jour — aucune modification nécessaire.\n")


if __name__ == "__main__":
    sync_database()
