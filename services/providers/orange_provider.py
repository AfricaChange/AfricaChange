import requests
import base64
import os
from services.constants import PaymentStatus


class OrangeProvider:

    ORANGE_STATUS_MAP = {
        "SUCCESS": PaymentStatus.VALIDE.value,
        "PENDING": PaymentStatus.EN_ATTENTE.value,
        "FAILED": PaymentStatus.ECHOUE.value,
        "CANCELLED": PaymentStatus.ECHOUE.value,
        "EXPIRED": PaymentStatus.ECHOUE.value,
    }

    def __init__(self):
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")

        # ✅ ORANGE SONATEL SANDBOX
        self.oauth_url = "https://api.sandbox.orange-sonatel.com/oauth/token"
        self.webpay_url = (
            "https://api.sandbox.orange-sonatel.com/api/eWallet/v1/payments"
        )

    # --------------------------------------------------
    # 🔐 OAuth Token
    # --------------------------------------------------
    def get_access_token(self):
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {"grant_type": "client_credentials"}

        r = requests.post(self.oauth_url, headers=headers, data=data, timeout=10)
        r.raise_for_status()

        return r.json()["access_token"]

    # --------------------------------------------------
    # 💳 INIT WEB PAYMENT
    # --------------------------------------------------
    def init_payment(self, amount, phone, reference):
        token = self.get_access_token()

        url = "https://api.sandbox.orange-sonatel.com/api/eWallet/v1/payments"

        payload = {
            "partner": {
            "idType": "CODE",
            "id": "TEST"
            },
            "customer": {
            "idType": "MSISDN",
            "id": phone
            },
            "amount": {
            "value": int(amount),
            "unit": "XOF"
            },
            "reference": reference,
            "description": "AfricaChange paiement"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()

        return r.json()

    
    # --------------------------------------------------
    # 🔁 CALLBACK
    # --------------------------------------------------
    def map_status(self, orange_status: str) -> str:
        status = self.ORANGE_STATUS_MAP.get(orange_status)
        if not status:
            raise ValueError(f"Statut Orange inconnu : {orange_status}")
        return status
