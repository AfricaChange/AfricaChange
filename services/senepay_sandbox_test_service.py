import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from flask import current_app

from database import db
from models import AuditLog
from providers.factory import ProviderFactory


class SenePaySandboxTestService:
    ACTIONS = {
        "create_checkout_session": "create_checkout_session",
        "get_checkout_session_status": "get_checkout_session_status",
        "create_direct_payin": "initiate_direct_payin",
        "get_direct_payin_status": "get_direct_payin_status",
        "get_wallet_balance": "get_wallet_balance",
        "estimate_payout": "estimate_payout",
        "create_payout": "create_payout",
        "get_payout_status": "get_payout_status",
    }

    @classmethod
    def execute_action(
        cls,
        *,
        action: str,
        payload: Dict[str, Any],
        admin_user_id: Optional[int],
        ip_address: Optional[str],
    ) -> Dict[str, Any]:
        if action not in cls.ACTIONS:
            raise ValueError("Action Sandbox SenePay invalide")

        provider = ProviderFactory.create(
            "senepay",
            mode=current_app.config.get("SENEPAY_MODE", "sandbox"),
            base_url=current_app.config.get("SENEPAY_BASE_URL"),
            public_key=current_app.config.get("SENEPAY_PUBLIC_KEY"),
            secret_key=current_app.config.get("SENEPAY_SECRET_KEY"),
            webhook_secret=current_app.config.get("SENEPAY_WEBHOOK_SECRET"),
        )

        internal_reference = payload.get("internal_reference") or cls._generate_internal_reference(action)
        normalized_payload = cls._normalize_payload(action=action, payload=payload, internal_reference=internal_reference)

        current_app.logger.info(
            "SenePay Sandbox request action=%s reference=%s payload=%s",
            action,
            internal_reference,
            cls._safe_log_payload(normalized_payload),
        )

        method_name = cls.ACTIONS[action]
        result = getattr(provider, method_name)(**normalized_payload)
        senepay_status = result.get("status")

        current_app.logger.info(
            "SenePay Sandbox response action=%s reference=%s success=%s status=%s",
            action,
            internal_reference,
            result.get("success"),
            senepay_status,
        )

        trace = {
            "action": action,
            "reference_interne": internal_reference,
            "statut_senepay": senepay_status,
            "requete": result.get("payload", {}).get("request", {}),
            "reponse": result.get("payload", {}).get("response", {}),
            "http_status_code": result.get("payload", {}).get("http_status_code"),
            "erreur": None if result.get("success") else result.get("message"),
            "horodatage": datetime.utcnow().isoformat(),
        }

        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_user_id,
                event=f"senepay_sandbox_{action}",
                payload=trace,
                ip_address=ip_address,
            )
        )

        return {
            "success": result.get("success", False),
            "message": result.get("message"),
            "reference_interne": internal_reference,
            "reference_provider": result.get("reference"),
            "statut_senepay": senepay_status,
            "operation": result.get("operation"),
            "trace": trace,
            "payload": result.get("payload", {}),
        }

    @staticmethod
    def recent_logs(limit: int = 20):
        return (
            AuditLog.query
            .filter(AuditLog.event.like("senepay_sandbox_%"))
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def _normalize_payload(cls, *, action: str, payload: Dict[str, Any], internal_reference: str) -> Dict[str, Any]:
        cleaned = {key: value for key, value in payload.items() if value not in (None, "", [])}

        if action in {"create_checkout_session", "create_direct_payin", "estimate_payout", "create_payout"}:
            cleaned.setdefault("reference", internal_reference)

        if action == "get_checkout_session_status":
            return {"session_token": cleaned.get("session_token")}
        if action == "get_direct_payin_status":
            return {"token": cleaned.get("token")}
        if action == "get_payout_status":
            return {"payout_id": cleaned.get("payout_id")}
        if action == "get_wallet_balance":
            return {}
        if action == "estimate_payout":
            return {
                "amount": cleaned.get("amount"),
                "country": cleaned.get("country") or cleaned.get("beneficiary_country"),
                "operator": (cleaned.get("operator") or "").lower() or None,
            }
        if action == "create_payout":
            return {
                "external_id": cleaned.get("reference") or internal_reference,
                "amount": cleaned.get("amount"),
                "phone": cleaned.get("beneficiary_phone"),
                "recipient_name": cleaned.get("beneficiary_name"),
                "country": cleaned.get("country") or cleaned.get("beneficiary_country"),
                "operator": (cleaned.get("operator") or "").lower() or None,
                "callback_url": cleaned.get("callback_url"),
            }
        return cleaned

    @staticmethod
    def _generate_internal_reference(action: str) -> str:
        return f"SENEPAY-SBX-{action.upper()}-{uuid.uuid4().hex[:10].upper()}"

    @staticmethod
    def _safe_log_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        safe = dict(payload)
        for key in ("secret", "secret_key", "api_key", "token"):
            if key in safe:
                safe[key] = "***redacted***"
        return safe
