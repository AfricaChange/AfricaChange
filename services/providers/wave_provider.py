import os
import requests
from services.providers.base_provider import BaseProvider


class WaveProvider(BaseProvider):

    API_URL = "https://api.wave.com/v1/checkout/sessions"

    def __init__(self):
        self.api_key = os.getenv("WAVE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Clé API Wave manquante")

    # --------------------------------------------------
    # 💳 INIT PAYMENT
    # --------------------------------------------------
    def create_payment(self, *, amount: float, reference: str, return_url: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "amount": int(amount),
            "currency": "XOF",
            "client_reference": reference,  # 🔐 ID DB
            "success_redirect_url": return_url,
            "cancel_redirect_url": return_url,
        }

        r = requests.post(self.API_URL, headers=headers, json=payload, timeout=10)

        if r.status_code != 200:
            raise RuntimeError(f"Wave error: {r.text}")

        data = r.json()

        return {
            "payment_url": data.get("checkout_url"),
            "provider_reference": reference,
        }

    # --------------------------------------------------
    # 🔐 CALLBACK VALIDATION (LOGIQUE)
    # --------------------------------------------------
    def verify_callback(self, payload, headers) -> bool:
        """
        Wave n’a PAS de signature.
        La validation repose sur :
        - présence reference
        - flux retour Wave (success URL)
        """
        return bool(payload.get("client_reference") or payload.get("reference"))

    def is_valid_status(self, payload) -> bool:
        # Wave = succès si retour sur success URL
        return True

    def extract_nonce(self, payload, headers):
        # 🔐 Idempotence par référence
        return payload.get("client_reference")
