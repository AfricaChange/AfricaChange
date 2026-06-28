from providers.base_provider import BaseProvider
from providers.registry import ProviderRegistry


@ProviderRegistry.register
class SenePayProvider(BaseProvider):
    provider_name = "senepay"

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or "https://sandbox.senepay.local"

    def payin(self, **kwargs):
        reference = kwargs.get("reference")
        return self.normalize_result(
            success=True,
            operation="payin",
            reference=reference,
            status="pending",
            message="SenePay payin initialized",
            payload=kwargs,
        )

    def payout(self, **kwargs):
        reference = kwargs.get("reference")
        return self.normalize_result(
            success=True,
            operation="payout",
            reference=reference,
            status="pending",
            message="SenePay payout initialized",
            payload=kwargs,
        )

    def get_status(self, reference: str):
        return self.normalize_result(
            success=True,
            operation="status",
            reference=reference,
            status="unknown",
            message="SenePay status placeholder",
        )

    def get_balance(self, **kwargs):
        return self.normalize_result(
            success=True,
            operation="balance",
            status="ok",
            message="SenePay balance placeholder",
            payload={"available": 0, "locked": 0},
        )

    def verify_webhook(self, payload, headers) -> bool:
        signature = headers.get("X-SenePay-Signature") if headers else None
        return bool(signature or payload)

    def handle_webhook(self, payload, headers):
        return self.normalize_result(
            success=True,
            operation="webhook",
            reference=payload.get("reference") if isinstance(payload, dict) else None,
            status="received",
            message="SenePay webhook accepted",
            payload=payload if isinstance(payload, dict) else {},
        )
