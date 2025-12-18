from database import db
from models import Conversion, Transaction, Paiement
from datetime import datetime
import uuid

class PaymentService:

    @staticmethod
    def lock_conversion(reference: str) -> Conversion:
        """
        Verrouille une conversion pour éviter les doubles paiements
        """
        conversion = (
            db.session.query(Conversion)
            .filter_by(reference=reference)
            .with_for_update()
            .first()
        )

        if not conversion:
            raise ValueError("Conversion introuvable")

        if conversion.statut != "en_attente":
            raise ValueError("Conversion déjà traitée")

        conversion.statut = "paiement_en_cours"
        db.session.flush()

        return conversion

    @staticmethod
    def create_transaction(conversion, fournisseur: str, montant: float):
        """
        Crée la transaction interne AfricaChange
        """
        transaction = Transaction(
            user_id=conversion.user_id,
            type="paiement",
            montant=montant,
            statut="en_attente",
            fournisseur=fournisseur,
            reference=str(uuid.uuid4())[:12],
            date_transaction=datetime.utcnow()
        )
        db.session.add(transaction)
        return transaction

    @staticmethod
    def create_paiement(conversion, transaction_ref: str, sender_phone: str):
        """
        Trace le paiement métier
        """
        paiement = Paiement(
            conversion_id=conversion.id,
            montant_envoye=conversion.montant_initial,
            montant_recu=conversion.montant_converti,
            devise_source=conversion.from_currency,
            devise_cible=conversion.to_currency,
            sender_phone=sender_phone,
            receiver_phone=conversion.receiver_phone,
            statut="en_attente",
            transaction_reference=transaction_ref,
            date_paiement=datetime.utcnow()
        )
        db.session.add(paiement)
        return paiement

    @staticmethod
    def rollback(conversion):
        conversion.statut = "en_attente"
        db.session.commit()
