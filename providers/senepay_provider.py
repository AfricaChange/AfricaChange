import hmac
import json
import os
from typing import Any, Dict, Optional

import requests
from flask import current_app, has_app_context

from providers.base_provider import BaseProvider
from providers.registry import ProviderRegistry


def _config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    if has_app_context():
        return current_app.config.get(key, default)
    return os.getenv(key, default)


@ProviderRegistry.register
class SenePayProvider(BaseProvider):
    provider_name = "senepay"

    def __init__(
        self,
        mode: Optional[str] = None,
        base_url: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        timeout: int = 20,
        session: Optional[requests.Session] = None,
    ):
        self.mode = (mode or _config_value("SENEPAY_MODE", "sandbox")).strip().lower()
        self.base_url = (base_url or _config_value("SENEPAY_BASE_URL", "https://api.sene-pay.com")).rstrip("/")
        self.public_key = public_key or _config_value("SENEPAY_PUBLIC_KEY")
        self.secret_key = secret_key or _config_value("SENEPAY_SECRET_KEY")
        self.webhook_secret = webhook_secret or _config_value("SENEPAY_WEBHOOK_SECRET")
        self.custom_ca_bundle = _config_value("AFRICACHANGEX_CUSTOM_CA_BUNDLE")
        self.timeout = timeout
        self.session = session or requests.Session()

    def payin(self, **kwargs):
        result = self.initiate_direct_payin(**kwargs)
        result["operation"] = "payin"
        return result

    def payout(self, **kwargs):
        result = self.create_payout(**kwargs)
        result["operation"] = "payout"
        return result

    def get_status(self, reference: str, resource_type: str = "payment"):
        resource = (resource_type or "payment").strip().lower()
        if resource == "checkout":
            result = self.get_checkout_session_status(reference)
            result["operation"] = "status"
            return result
        if resource == "payout":
            result = self.get_payout_status(reference)
            result["operation"] = "status"
            return result
        result = self.get_direct_payin_status(reference)
        result["operation"] = "status"
        return result

    def get_balance(self, **kwargs):
        result = self.get_wallet_balance()
        result["operation"] = "balance"
        return result

    def verify_webhook(self, payload, headers) -> bool:
        if not self.webhook_secret or not headers:
            return False

        signature = (
            headers.get("X-SenePay-Signature")
            or headers.get("x-senepay-signature")
        )
        if not signature:
            return False

        if isinstance(payload, bytes):
            raw_payload = payload
        elif isinstance(payload, str):
            raw_payload = payload.encode("utf-8")
        else:
            raw_payload = json.dumps(payload or {}, separators=(",", ":"), sort_keys=True).encode("utf-8")

        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_payload,
            "sha256",
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    def handle_webhook(self, payload, headers):
        is_valid = self.verify_webhook(payload, headers)
        reference = payload.get("reference") if isinstance(payload, dict) else None
        status = payload.get("status") if isinstance(payload, dict) else None
        return self.normalize_result(
            success=is_valid,
            operation="webhook",
            reference=reference,
            status=status or ("received" if is_valid else "invalid"),
            message="Webhook SenePay traite" if is_valid else "Signature webhook invalide",
            payload=payload if isinstance(payload, dict) else {"raw_payload": str(payload)},
        )

    def create_checkout_session(self, **kwargs):
        payload = self._build_checkout_session_payload(kwargs)
        return self._request(
            "POST",
            "/api/v1/checkout/sessions",
            operation="checkout_session_create",
            reference=payload.get("OrderReference") or kwargs.get("reference"),
            json_payload=payload,
            include_public_key=True,
        )

    def get_checkout_session_status(self, session_token: str):
        return self._request(
            "GET",
            f"/api/v1/checkout/sessions/{session_token}",
            operation="checkout_session_status",
            reference=session_token,
            include_public_key=True,
        )

    def initiate_direct_payin(self, **kwargs):
        return self._request(
            "POST",
            "/api/v1/payments/initiate",
            operation="payin_direct_create",
            reference=kwargs.get("reference"),
            json_payload=kwargs,
            include_public_key=True,
        )

    def get_direct_payin_status(self, token: str):
        return self._request(
            "GET",
            f"/api/v1/payments/{token}/status",
            operation="payin_direct_status",
            reference=token,
            include_public_key=True,
        )

    def get_wallet_balance(self):
        return self._request(
            "GET",
            "/api/v1/merchant/wallet/balance",
            operation="wallet_balance",
            include_public_key=False,
        )

    def estimate_payout(self, **kwargs):
        return self._request(
            "POST",
            "/api/v1/payouts/estimate",
            operation="payout_estimate",
            reference=kwargs.get("reference"),
            json_payload=kwargs,
            include_public_key=True,
        )

    def create_payout(self, **kwargs):
        return self._request(
            "POST",
            "/api/v1/payouts",
            operation="payout_create",
            reference=kwargs.get("reference"),
            json_payload=kwargs,
            include_public_key=True,
        )

    def get_payout_status(self, payout_id: str):
        return self._request(
            "GET",
            f"/api/v1/payouts/{payout_id}",
            operation="payout_status",
            reference=payout_id,
            include_public_key=True,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        reference: Optional[str] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        include_public_key: bool = False,
    ):
        if not self.secret_key or not self.public_key:
            return self.normalize_result(
                success=False,
                operation=operation,
                reference=reference,
                status="configuration_error",
                message="SENEPAY_PUBLIC_KEY ou SENEPAY_SECRET_KEY manquante",
                payload={},
            )

        url = f"{self.base_url}{path}"
        headers = self._build_headers(include_public_key=include_public_key)
        safe_request = {
            "method": method,
            "url": url,
            "params": params or {},
            "json": json_payload or {},
            "headers": self._redact_headers(headers),
            "mode": self.mode,
        }

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_payload,
                params=params,
                timeout=self.timeout,
                verify=self.custom_ca_bundle or True,
            )
            body = self._parse_response(response)
            success = response.ok
            status = self._extract_status(body, response.status_code)
            provider_reference = self._extract_reference(body, reference)
            message = self._extract_message(body, response.reason)
            return self.normalize_result(
                success=success,
                operation=operation,
                reference=provider_reference,
                status=status,
                message=message,
                payload={
                    "request": safe_request,
                    "response": body,
                    "http_status_code": response.status_code,
                },
            )
        except requests.RequestException as exc:
            return self.normalize_result(
                success=False,
                operation=operation,
                reference=reference,
                status="request_error",
                message=str(exc),
                payload={
                    "request": safe_request,
                    "response": {},
                    "http_status_code": None,
                },
            )

    def _build_headers(self, *, include_public_key: bool) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Secret": self.secret_key,
        }

        if include_public_key and self.public_key:
            headers["X-Api-Key"] = self.public_key
        elif self.public_key:
            headers["X-Api-Key"] = self.public_key
        return headers

    @staticmethod
    def _build_checkout_session_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        raw = dict(payload or {})
        order_reference = (
            raw.get("OrderReference")
            or raw.get("reference")
            or raw.get("internal_reference")
        )

        normalized = {
            "OrderReference": order_reference,
            "amount": raw.get("amount"),
            "currency": raw.get("currency"),
        }

        optional_fields = {
            "customer_name": "customer_name",
            "customer_phone": "customer_phone",
            "customer_email": "customer_email",
            "success_url": "success_url",
            "cancel_url": "cancel_url",
            "callback_url": "callback_url",
            "country": "country",
            "operator": "operator",
        }
        for source_key, target_key in optional_fields.items():
            if raw.get(source_key) not in (None, ""):
                normalized[target_key] = raw.get(source_key)

        return {key: value for key, value in normalized.items() if value not in (None, "")}

    @staticmethod
    def _parse_response(response: requests.Response):
        try:
            return response.json()
        except ValueError:
            return {"raw_body": response.text}

    @staticmethod
    def _extract_status(body: Any, http_status_code: Optional[int]):
        if isinstance(body, dict):
            for key in ("status", "state", "paymentStatus", "sessionStatus"):
                if body.get(key):
                    return str(body[key])
        if http_status_code is None:
            return "unknown"
        return "success" if 200 <= http_status_code < 300 else "error"

    @staticmethod
    def _extract_reference(body: Any, fallback: Optional[str]):
        if isinstance(body, dict):
            for key in ("reference", "token", "sessionToken", "id"):
                if body.get(key):
                    return str(body[key])
        return fallback

    @staticmethod
    def _extract_message(body: Any, fallback: Optional[str]):
        if isinstance(body, dict):
            for key in ("message", "detail", "error"):
                value = body.get(key)
                if value:
                    return str(value)
        return fallback or "Aucune reponse textuelle fournie"

    @staticmethod
    def _redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        redacted = {}
        for key, value in headers.items():
            lower_key = key.lower()
            if "authorization" in lower_key or "key" in lower_key or "secret" in lower_key:
                redacted[key] = "***redacted***"
            else:
                redacted[key] = value
        return redacted
