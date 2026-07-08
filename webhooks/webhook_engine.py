class WebhookEngine:
    @staticmethod
    def process(*, provider, payload, headers, raw_payload=None):
        signature_valid = provider.verify_webhook(raw_payload if raw_payload is not None else payload, headers)
        if not signature_valid:
            return {
                "accepted": False,
                "reason": "invalid_signature",
            }

        provider_result = provider.handle_webhook(payload, headers)
        return {
            "accepted": True,
            "provider_result": provider_result,
        }
