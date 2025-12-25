from database import db
from models import LedgerEntry


class LedgerService:

    @staticmethod
    def record(
        *,
        reference: str,
        compte: str,
        sens: str,
        montant: float,
        devise: str,
        provider: str = None,
        description: str = None,
        transaction_id=None,
        conversion_id=None,
        paiement_id=None,
    ):
        entry = LedgerEntry(
            reference=reference,
            compte=compte,
            sens=sens,
            montant=montant,
            devise=devise,
            provider=provider,
            description=description,
            transaction_id=transaction_id,
            conversion_id=conversion_id,
            paiement_id=paiement_id,
        )

        db.session.add(entry)
        return entry
