from sqlalchemy import text
from database import db

def ensure_paiement_transaction_reference():
    """
    Ajoute la colonne paiement.transaction_reference si elle n'existe pas
    Compatible Render (sans shell)
    """
    sql_check = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name='paiement'
    AND column_name='transaction_reference';
    """

    sql_add = """
    ALTER TABLE paiement
    ADD COLUMN transaction_reference VARCHAR(100);
    """

    sql_index = """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_paiement_tx_ref
    ON paiement (transaction_reference);
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(sql_check)).fetchone()
        if not result:
            print("🔧 Ajout colonne paiement.transaction_reference")
            conn.execute(text(sql_add))
            conn.execute(text(sql_index))
            conn.commit()
        else:
            print("✅ Colonne paiement.transaction_reference déjà présente")


def ensure_paiement_idempotency_key():
    with db.engine.connect() as conn:
        res = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='paiement'
              AND column_name='idempotency_key'
        """))
        if not res.fetchone():
            print("🔧 Ajout colonne paiement.idempotency_key")
            conn.execute(text("""
                ALTER TABLE paiement
                ADD COLUMN idempotency_key VARCHAR(100)
            """))
        else:
            print("✅ Colonne paiement.idempotency_key déjà présente")