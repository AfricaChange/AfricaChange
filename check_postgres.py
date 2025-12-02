from app import app
from database import db

with app.app_context():
    engine = db.engine

    print("📌 Connexion active vers :", engine.url)

    # Liste des tables PostgreSQL
    inspector = db.inspect(engine)
    tables = inspector.get_table_names()

    print("📋 Tables trouvées dans PostgreSQL :")
    for t in tables:
        print("   ✔", t)

    if not tables:
        print("❌ Aucune table trouvée — migration NON réussie")
    else:
        print("✅ Migration réussie — tables visibles !")
