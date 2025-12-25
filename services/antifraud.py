from datetime import datetime, timedelta
from models import Transaction

class AntiFraud:

    CALLBACK_WINDOW = timedelta(minutes=10)

    @staticmethod
    def check_transaction(reference):
        tx = Transaction.query.filter_by(reference=reference).first()

        if not tx:
            raise ValueError("Transaction inconnue")

        if tx.statut in ["valide", "echoue"]:
           raise ValueError("Transaction déjà finalisée")


        if tx.date_transaction < datetime.utcnow() - AntiFraud.CALLBACK_WINDOW:
            raise ValueError("Callback hors délai")

        return tx
