import os
import requests
import uuid

class WaveAPI:
    def __init__(self):
        self.api_key = os.getenv("WAVE_API_KEY")
        self.api_url = "https://api.wave.com/v1/checkout/sessions"

    def create_payment(self, amount, currency, return_url):
        """Créer un lien de paiement Wave"""
        if not self.api_key:
            return {"success": False, "error": "Clé API Wave manquante"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        reference = str(uuid.uuid4())[:12]

        payload = {
            "amount": int(amount),
            "currency": currency,
            "client_reference": reference,
            "success_redirect_url": return_url,
            "cancel_redirect_url": return_url,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": {
                        "payment_url": data["checkout_url"],
                        "reference": reference,
                    },
                }
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
