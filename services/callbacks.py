from database import db
from models import PaymentEvent
from services.antifraud import AntiFraud
from sqlalchemy.exc import IntegrityError



class CallbackManager:
    

    @staticmethod
    def log(provider, reference, payload, ip, event_type):
        event = PaymentEvent(
            transaction_reference=reference,
            provider=provider,
            event_type=event_type,
            payload=payload,
            ip_address=ip
        )
        db.session.add(event)

    @staticmethod
    def validate(reference, provider, payload, ip):
        # 🔐 1️⃣ NONCE UNIQUE (ANTI-REPLAY ABSOLU)
        if nonce:
            exists = PaymentEvent.query.filter_by(nonce=nonce).first()
            if exists:
                raise ValueError("Callback rejoué (nonce déjà utilisé)")
        # 🔐 1) Vérification métier antifraude
        tx = AntiFraud.check_transaction(reference)

        # 🧾 2) Tentative d’enregistrement du callback (idempotence DB)
        event = PaymentEvent(
            transaction_reference=reference,
            provider=provider,
            event_type="callback",
            payload=payload,
            ip_address=ip
        )

        try:
            db.session.add(event)
            db.session.flush()  # ⚠️ clé FINTECH
        except IntegrityError:
            # 🔁 Callback déjà reçu → on ignore silencieusement
            db.session.rollback()
            return tx

        return tx
