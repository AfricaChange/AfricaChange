from database import db
from models import Conversion, Transaction, Paiement
from datetime import datetime
from flask import session
import uuid
from services.constants import PaymentStatus


class PaymentService:

    # ==================================================
    # 🔒 LOCK CONVERSION
    # ==================================================
    @staticmethod
    def lock_conversion(reference: str) -> Conversion:
        conversion = (
            db.session.query(Conversion)
            .filter_by(reference=reference)
            .with_for_update()
            .first()
        )

        if not conversion:
            raise ValueError("Conversion introuvable")

        if conversion.user_id:
            if conversion.user_id != session.get("user_id"):
                raise PermissionError("Accès non autorisé à cette conversion")

        if conversion.statut != PaymentStatus.EN_ATTENTE.value:
            raise ValueError("Conversion déjà traitée")

        conversion.statut = PaymentStatus.EN_COURS.value
        db.session.flush()

        return conversion

    # ==================================================
    # 🧾 CREATE TRANSACTION
    # ==================================================
    @staticmethod
    def create_transaction(conversion, fournisseur: str, montant: float):
        transaction = Transaction(
            user_id=conversion.user_id,
            type="paiement",
            montant=montant,
            statut=PaymentStatus.EN_ATTENTE.value,
            fournisseur=fournisseur,
            reference=str(uuid.uuid4())[:12],
            date_transaction=datetime.utcnow()
        )
        db.session.add(transaction)
        return transaction

    # ==================================================
    # 💳 CREATE PAIEMENT
    # ==================================================
    @staticmethod
    def create_paiement(conversion, transaction_ref: str, sender_phone: str):
        paiement = Paiement(
            conversion_id=conversion.id,
            montant_envoye=conversion.montant_initial,
            montant_recu=conversion.montant_converti,
            devise_source=conversion.from_currency,
            devise_cible=conversion.to_currency,
            sender_phone=sender_phone,
            receiver_phone=conversion.receiver_phone,
            statut=PaymentStatus.EN_ATTENTE.value,
            idempotency_key=PaymentService.generate_idempotency_key(),
            transaction_reference=transaction_ref,
            date_paiement=datetime.utcnow()
        )
        db.session.add(paiement)
        return paiement

    # ==================================================
    # 🔑 IDEMPOTENCY
    # ==================================================
    @staticmethod
    def generate_idempotency_key():
        return str(uuid.uuid4())

    # ==================================================
    # ↩️ ROLLBACK
    # ==================================================
    @staticmethod
    def rollback(conversion):
        if conversion.statut == PaymentStatus.EN_COURS.value:
            conversion.statut = PaymentStatus.ECHOUE.value
        db.session.commit()
