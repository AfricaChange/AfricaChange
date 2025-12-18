from database import db
from models import PaymentEvent
from services.antifraud import AntiFraud

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
        tx = AntiFraud.check_transaction(reference)

        CallbackManager.log(
            provider=provider,
            reference=reference,
            payload=payload,
            ip=ip,
            event_type="callback"
        )

        return tx
