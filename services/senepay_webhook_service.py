import hashlib
from typing import Any, Dict, Optional

from database import db
from models import AuditLog, PaymentEvent


class SenePayWebhookService:
    @staticmethod
    def _build_nonce(*, payload: Dict[str, Any], event_type: str) -> str:
        session_token = payload.get("sessionToken") or payload.get("session_token") or ""
        order_reference = payload.get("orderReference") or payload.get("order_reference") or ""
        transaction_id = payload.get("transactionId") or payload.get("transaction_id") or ""
        status = payload.get("status") or ""
        raw = f"senepay|{event_type}|{session_token}|{order_reference}|{transaction_id}|{status}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _transaction_reference(payload: Dict[str, Any]) -> Optional[str]:
        return (
            payload.get("orderReference")
            or payload.get("order_reference")
            or payload.get("sessionToken")
            or payload.get("session_token")
            or payload.get("transactionId")
            or payload.get("transaction_id")
        )

    @classmethod
    def record_webhook(
        cls,
        *,
        payload: Dict[str, Any],
        raw_payload: str,
        headers: Dict[str, Any],
        ip_address: Optional[str],
    ) -> Dict[str, Any]:
        event_type = headers.get("X-SenePay-Event") or payload.get("event") or "unknown"
        nonce = cls._build_nonce(payload=payload, event_type=event_type)

        existing = PaymentEvent.query.filter_by(nonce=nonce).first()
        if existing:
            return {
                "duplicate": True,
                "event_id": existing.id,
                "nonce": nonce,
            }

        reference = cls._transaction_reference(payload)
        signature = headers.get("X-SenePay-Signature") or headers.get("x-senepay-signature")
        status = payload.get("status")
        transaction_id = payload.get("transactionId") or payload.get("transaction_id")
        fees = payload.get("fees")
        net_amount = payload.get("netAmount") or payload.get("net_amount")

        payment_event = PaymentEvent(
            transaction_reference=reference,
            provider="senepay",
            event_type=event_type,
            payload={
                "event": event_type,
                "sessionToken": payload.get("sessionToken") or payload.get("session_token"),
                "orderReference": payload.get("orderReference") or payload.get("order_reference"),
                "status": status,
                "transactionId": transaction_id,
                "fees": fees,
                "netAmount": net_amount,
                "raw_payload": raw_payload,
                "signature": signature,
                "headers": {k: v for k, v in headers.items() if k.lower().startswith("x-senepay")},
            },
            ip_address=ip_address,
            nonce=nonce,
        )
        db.session.add(payment_event)

        db.session.add(
            AuditLog(
                actor_type="provider_webhook",
                actor_id=None,
                event="senepay_webhook_received",
                payload={
                    "event": event_type,
                    "sessionToken": payload.get("sessionToken") or payload.get("session_token"),
                    "orderReference": payload.get("orderReference") or payload.get("order_reference"),
                    "status": status,
                    "transactionId": transaction_id,
                    "fees": fees,
                    "netAmount": net_amount,
                    "nonce": nonce,
                },
                ip_address=ip_address,
            )
        )

        return {
            "duplicate": False,
            "event_type": event_type,
            "nonce": nonce,
            "reference": reference,
        }
