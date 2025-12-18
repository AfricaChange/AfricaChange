import os
import requests

class WaveProvider:

    API_URL = "https://api.wave.com/v1/checkout/sessions"

    def __init__(self):
        self.api_key = os.getenv("WAVE_API_KEY")

    def create_payment(self, *, amount: float, reference: str, return_url: str):
        if not self.api_key:
            raise RuntimeError("Clé API Wave manquante")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "amount": int(amount),
            "currency": "XOF",
            "client_reference": reference,  # 🔐 vient de la DB
            "success_redirect_url": return_url,
            "cancel_redirect_url": return_url,
        }

        r = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if r.status_code != 200:
            raise RuntimeError(f"Wave error: {r.text}")

        data = r.json()

        return {
            "payment_url": data.get("checkout_url"),
            "provider_reference": reference,
        }
